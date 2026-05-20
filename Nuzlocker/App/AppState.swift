import Foundation
import Observation

@Observable
final class AppState {
    let library: GameLibrary
    let runs: RunService

    private(set) var isReady = false
    var currentRun: Run?

    // MARK: - Derived from current run

    var currentGame: Game? {
        currentRun.flatMap { library.game(withID: $0.gameID) }
    }

    var currentGameData: GameData? {
        currentRun.flatMap { library.gameData(for: $0.variantID) }
    }

    // MARK: - Init

    init() throws {
        let container = try ModelContainerSetup.makeContainer()
        self.library = GameLibrary()
        self.runs = RunService(modelContainer: container)
    }

    // MARK: - Bootstrap

    func bootstrap() async {
        await library.bootstrap()
        await restoreCurrentRun()
        await MainActor.run { isReady = true }
    }

    // MARK: - Current run

    func setCurrentRun(_ run: Run?) {
        currentRun = run
        if let run {
            UserDefaults.standard.set(run.id.uuidString, forKey: Constants.userDefaultsKeyCurrentRunID)
        } else {
            UserDefaults.standard.removeObject(forKey: Constants.userDefaultsKeyCurrentRunID)
        }
    }

    @MainActor
    private func restoreCurrentRun() async {
        guard let stored = UserDefaults.standard.string(forKey: Constants.userDefaultsKeyCurrentRunID),
              let uuid = UUID(uuidString: stored),
              let run = try? runs.run(withID: uuid) else {
            UserDefaults.standard.removeObject(forKey: Constants.userDefaultsKeyCurrentRunID)
            return
        }
        currentRun = run
    }
}
