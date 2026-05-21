import Foundation
import StoreKit
import ZIPFoundation
import Observation

@Observable
final class GameLibrary {

    // MARK: - Observable state

    private(set) var games: [Game] = []
    private(set) var installedVariantIDs: Set<String> = []
    private(set) var freePicksRemaining: Int = 0

    // MARK: - Private

    private var purchasedGameIDs: Set<String> = []
    private var freePickGameIDs: Set<String> = []
    private var gameDataCache: [String: VariantContent] = [:]
    private var speciesCache: [String: SpeciesContent] = [:]
    private let kvs = NSUbiquitousKeyValueStore.default
    private let downloader = Downloader()

    // MARK: - Init

    init() { loadCatalog() }

    // MARK: - Bootstrap

    func bootstrap() async {
        try? StorageLocations.ensureDirectories()
        await scanInstalled()
        subscribeToKVSChanges()
        kvs.synchronize()
        if kvs.object(forKey: Constants.kvsKeyFreePickGameIDs) == nil {
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            kvs.synchronize()
        }
        await refreshEntitlements()
        Task { await refreshCatalog() }
    }

    func startTransactionListener() -> Task<Void, Never> {
        Task {
            for await result in Transaction.updates {
                if case .verified(_) = result { await refreshEntitlements() }
            }
        }
    }

    // MARK: - Queries

    func isInstalled(_ variantID: String) -> Bool {
        installedVariantIDs.contains(variantID)
    }

    func isAvailable(_ game: Game) -> Bool {
        purchasedGameIDs.contains(game.id) || freePickGameIDs.contains(game.id)
    }

    func game(withID id: String) -> Game? {
        games.first { $0.id == id }
    }

    func game(forVariantID variantID: String) -> Game? {
        games.first { $0.variants.contains { $0.id == variantID } }
    }

    func variant(withID id: String) -> GameVariant? {
        games.flatMap(\.variants).first { $0.id == id }
    }

    func gamesByGeneration() -> [(Int, String, [Game])] {
        var grouped: [Int: (String, [Game])] = [:]
        for game in games {
            if var entry = grouped[game.generation] {
                entry.1.append(game)
                grouped[game.generation] = entry
            } else {
                grouped[game.generation] = (game.generationDisplayName, [game])
            }
        }
        return grouped
            .sorted { $0.key < $1.key }
            .map { ($0.key, $0.value.0, $0.value.1.sorted { $0.displayName < $1.displayName }) }
    }

    // MARK: - Acquisition

    func purchaseAndInstall(
        _ variant: GameVariant,
        for game: Game,
        onProgress: ((Double) -> Void)? = nil
    ) async throws {
        let transaction = try await purchase(game)
        let zipURL = try await download(variant, onProgress: onProgress)
        try await install(zipAt: zipURL, variant: variant, game: game)
        await transaction.finish()
        await refreshEntitlements()
    }

    func claimFreeAndInstall(
        _ variant: GameVariant,
        for game: Game,
        onProgress: ((Double) -> Void)? = nil
    ) async throws {
        guard claimFreePick(game.id) else { throw LibraryError.freePickUnavailable }
        if !isInstalled(variant.id) {
            let zipURL = try await download(variant, onProgress: onProgress)
            try await install(zipAt: zipURL, variant: variant, game: game)
        }
    }

    func installOwned(
        _ variant: GameVariant,
        for game: Game,
        onProgress: ((Double) -> Void)? = nil
    ) async throws {
        guard isAvailable(game), !isInstalled(variant.id) else { return }
        let zipURL = try await download(variant, onProgress: onProgress)
        try await install(zipAt: zipURL, variant: variant, game: game)
    }

    func remove(_ variantID: String) async throws {
        try FileManager.default.removeItem(at: StorageLocations.variantDir(variantID))
        await MainActor.run {
            installedVariantIDs.remove(variantID)
            gameDataCache.removeValue(forKey: variantID)
            speciesCache.removeValue(forKey: variantID)
        }
    }

    // MARK: - Content

    func content(for variantID: String) -> VariantContent? {
        if let cached = gameDataCache[variantID] { return cached }
        let url = StorageLocations.variantDir(variantID).appendingPathComponent("game.json")
        guard let data = try? Data(contentsOf: url),
              let gd = try? JSONDecoder().decode(VariantContent.self, from: data) else { return nil }
        gameDataCache[variantID] = gd
        return gd
    }

    func speciesContent(for variantID: String) -> SpeciesContent? {
        if let cached = speciesCache[variantID] { return cached }
        let url = StorageLocations.variantDir(variantID).appendingPathComponent("species.json")
        guard let data = try? Data(contentsOf: url),
              let sc = try? JSONDecoder().decode(SpeciesContent.self, from: data) else { return nil }
        speciesCache[variantID] = sc
        return sc
    }

    func routeDisplayName(for routeID: String, variantID: String) -> String {
        content(for: variantID)?.routes.first { $0.id == routeID }?.displayName ?? routeID
    }

    func restorePurchases() async throws {
        try await AppStore.sync()
        await refreshEntitlements()
    }

    // MARK: - Catalog

    func refreshCatalog() async {
        let request = URLRequest(
            url: Constants.remoteManifestURL,
            cachePolicy: .reloadIgnoringLocalCacheData,
            timeoutInterval: Constants.manifestFetchTimeout
        )
        guard let (data, response) = try? await URLSession.shared.data(for: request),
              let http = response as? HTTPURLResponse,
              http.statusCode == 200,
              let manifest = try? Self.decoder.decode(Manifest.self, from: data) else { return }
        await MainActor.run { games = manifest.games }
        try? data.write(to: StorageLocations.manifestCache)
    }

    // MARK: - Private — Catalog

    private static let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }()

    private func loadCatalog() {
        if let data = try? Data(contentsOf: StorageLocations.manifestCache),
           let manifest = try? Self.decoder.decode(Manifest.self, from: data) {
            games = manifest.games
            return
        }
        if let url = Bundle.main.url(forResource: "bundled-manifest", withExtension: "json"),
           let data = try? Data(contentsOf: url),
           let manifest = try? Self.decoder.decode(Manifest.self, from: data) {
            games = manifest.games
        }
    }

    // MARK: - Private — Entitlements

    private func subscribeToKVSChanges() {
        NotificationCenter.default.addObserver(
            forName: NSUbiquitousKeyValueStore.didChangeExternallyNotification,
            object: kvs,
            queue: .main
        ) { [weak self] _ in Task { await self?.refreshEntitlements() } }
    }

    private func refreshEntitlements() async {
        let freePickIDs = loadFreePickIDsFromKVS()
        var purchasedIDs = Set<String>()
        for await result in Transaction.currentEntitlements {
            if case .verified(let t) = result, t.revocationDate == nil {
                purchasedIDs.insert(t.productID)
            }
        }
        await MainActor.run {
            purchasedGameIDs = purchasedIDs
            freePickGameIDs = freePickIDs
            freePicksRemaining = max(0, Constants.maxFreeGames - freePickIDs.count)
        }
    }

    @discardableResult
    private func claimFreePick(_ gameID: String) -> Bool {
        if purchasedGameIDs.contains(gameID) || freePickGameIDs.contains(gameID) { return true }
        guard freePicksRemaining > 0 else { return false }
        var updated = freePickGameIDs
        updated.insert(gameID)
        persistFreePickIDs(updated)
        freePickGameIDs = updated
        freePicksRemaining = max(0, Constants.maxFreeGames - updated.count)
        return true
    }

    private func loadFreePickIDsFromKVS() -> Set<String> {
        guard let data = kvs.data(forKey: Constants.kvsKeyFreePickGameIDs),
              let ids = try? JSONDecoder().decode([String].self, from: data) else { return [] }
        return Set(ids)
    }

    private func persistFreePickIDs(_ ids: Set<String>) {
        let data = try? JSONEncoder().encode(Array(ids))
        kvs.set(data, forKey: Constants.kvsKeyFreePickGameIDs)
        kvs.synchronize()
    }

    private func purchase(_ game: Game) async throws -> Transaction {
        let products = try await Product.products(for: [game.id])
        guard let product = products.first else { throw LibraryError.productNotFound }
        switch try await product.purchase() {
        case .success(let result):
            switch result {
            case .verified(let t): return t
            case .unverified(_, let e): throw e
            }
        case .userCancelled: throw LibraryError.purchaseCancelled
        case .pending:       throw LibraryError.purchasePending
        @unknown default:    throw LibraryError.unknown
        }
    }

    // MARK: - Private — Install

    private func scanInstalled() async {
        guard let dirs = try? FileManager.default.contentsOfDirectory(
            at: StorageLocations.variantsRoot, includingPropertiesForKeys: nil
        ) else { return }

        var installed = Set<String>()
        for dir in dirs {
            let variantID = dir.lastPathComponent
            guard let data = try? Data(contentsOf: StorageLocations.installMeta(variantID)),
                  let meta = try? JSONDecoder().decode(InstallMeta.self, from: data) else {
                try? FileManager.default.removeItem(at: dir)
                continue
            }
            if meta.layoutVersion != Constants.currentLayoutVersion {
                try? FileManager.default.removeItem(at: dir)
                continue
            }
            installed.insert(variantID)
        }
        await MainActor.run { installedVariantIDs = installed }
    }

    private func download(
        _ variant: GameVariant,
        onProgress: ((Double) -> Void)?
    ) async throws -> URL {
        for await event in downloader.start(variant) {
            switch event {
            case .progress(let done, let total):
                if total > 0 { onProgress?(Double(done) / Double(total)) }
            case .completed(let url):
                return url
            case .failed(let error, _):
                throw error
            }
        }
        throw LibraryError.downloadFailed
    }

    private func install(zipAt: URL, variant: GameVariant, game: Game) async throws {
        let actualHash = try await Integrity.sha256(of: zipAt)
        guard actualHash == variant.zipSHA256 else {
            throw IntegrityError.checksumMismatch(expected: variant.zipSHA256, actual: actualHash)
        }

        let fm = FileManager.default
        let stagingDir = StorageLocations.stagingRoot.appendingPathComponent(variant.id, isDirectory: true)
        try? fm.removeItem(at: stagingDir)
        try fm.createDirectory(at: stagingDir, withIntermediateDirectories: true)

        try await Task.detached(priority: .utility) {
            let archive = try Archive(url: zipAt, accessMode: .read)
            for entry in archive {
                try Integrity.validateZipEntry(entry.path, destinationDir: stagingDir)
                _ = try archive.extract(entry, to: stagingDir)
            }
        }.value

        let gameJSONURL = stagingDir.appendingPathComponent("game.json")
        guard let gameData = try? Data(contentsOf: gameJSONURL),
              let idCheck = try? JSONDecoder().decode(VariantIDCheck.self, from: gameData),
              idCheck.variantID == variant.id else {
            try? fm.removeItem(at: stagingDir)
            throw LibraryError.invalidContent
        }

        let destDir = StorageLocations.variantDir(variant.id)
        try? fm.removeItem(at: destDir)
        _ = try fm.replaceItemAt(destDir, withItemAt: stagingDir)

        let meta = InstallMeta(
            variantID: variant.id,
            gameID: game.id,
            generation: game.generation,
            contentVersion: variant.contentVersion,
            layoutVersion: variant.layoutVersion,
            installedAt: Date(),
            zipSHA256: variant.zipSHA256
        )
        try JSONEncoder().encode(meta).write(to: StorageLocations.installMeta(variant.id))
        try? StorageLocations.setExcludedFromBackup(destDir)
        try? fm.removeItem(at: zipAt)

        await MainActor.run { installedVariantIDs.insert(variant.id) }
    }
}

// MARK: - Errors

enum LibraryError: LocalizedError {
    case freePickUnavailable
    case productNotFound
    case purchaseCancelled
    case purchasePending
    case downloadFailed
    case invalidContent
    case unknown

    var errorDescription: String? {
        switch self {
        case .freePickUnavailable: return "No free games remaining."
        case .productNotFound:     return "This game could not be found in the App Store."
        case .purchaseCancelled:   return "Purchase was cancelled."
        case .purchasePending:     return "Purchase is pending approval."
        case .downloadFailed:      return "Download failed. Please try again."
        case .invalidContent:      return "The downloaded content failed validation. Please try again."
        case .unknown:             return "An unknown error occurred."
        }
    }
}

// MARK: - Private types

private struct VariantIDCheck: Codable {
    let variantID: String
}

private enum DownloadEvent {
    case progress(bytesDownloaded: Int64, totalBytes: Int64)
    case completed(localURL: URL)
    case failed(Error, resumeData: Data?)
}

private final class Downloader: NSObject, URLSessionDownloadDelegate {
    private var session: URLSession!
    private var continuations: [String: AsyncStream<DownloadEvent>.Continuation] = [:]
    private var resumeDataMap: [String: Data] = [:]
    private var taskVariantMap: [URLSessionTask: String] = [:]

    override init() {
        super.init()
        let config = URLSessionConfiguration.background(withIdentifier: Constants.backgroundDownloadIdentifier)
        config.allowsCellularAccess = true
        session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }

    func start(_ variant: GameVariant) -> AsyncStream<DownloadEvent> {
        AsyncStream { continuation in
            self.continuations[variant.id] = continuation
            let task: URLSessionDownloadTask
            if let resumeData = self.resumeDataMap[variant.id] {
                task = self.session.downloadTask(withResumeData: resumeData)
            } else {
                task = self.session.downloadTask(with: variant.zipURL)
            }
            self.taskVariantMap[task] = variant.id
            task.resume()
        }
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didFinishDownloadingTo location: URL) {
        guard let variantID = taskVariantMap[downloadTask] else { return }
        let dest = StorageLocations.stagingRoot.appendingPathComponent("\(variantID).zip")
        try? FileManager.default.removeItem(at: dest)
        do {
            try FileManager.default.moveItem(at: location, to: dest)
            continuations[variantID]?.yield(.completed(localURL: dest))
        } catch {
            continuations[variantID]?.yield(.failed(error, resumeData: nil))
        }
        continuations[variantID]?.finish()
        continuations.removeValue(forKey: variantID)
        taskVariantMap.removeValue(forKey: downloadTask)
        resumeDataMap.removeValue(forKey: variantID)
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didWriteData _: Int64, totalBytesWritten: Int64, totalBytesExpectedToWrite: Int64) {
        guard let variantID = taskVariantMap[downloadTask] else { return }
        continuations[variantID]?.yield(.progress(
            bytesDownloaded: totalBytesWritten,
            totalBytes: totalBytesExpectedToWrite
        ))
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        guard let error, let variantID = taskVariantMap[task] else { return }
        let resumeData = (error as NSError).userInfo[NSURLSessionDownloadTaskResumeData] as? Data
        if let resumeData { resumeDataMap[variantID] = resumeData }
        continuations[variantID]?.yield(.failed(error, resumeData: resumeData))
        continuations[variantID]?.finish()
        continuations.removeValue(forKey: variantID)
        taskVariantMap.removeValue(forKey: task)
    }
}
