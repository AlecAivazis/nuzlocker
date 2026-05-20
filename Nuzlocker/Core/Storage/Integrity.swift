import Foundation
import CryptoKit

enum Integrity {
    static func sha256(of fileURL: URL) async throws -> String {
        let data = try await Task.detached(priority: .utility) {
            try Data(contentsOf: fileURL)
        }.value
        let digest = SHA256.hash(data: data)
        return digest.map { String(format: "%02x", $0) }.joined()
    }

    static func validateZipEntry(_ entryPath: String, destinationDir: URL) throws {
        let resolvedDestination = destinationDir.standardized
        let resolvedEntry = destinationDir.appendingPathComponent(entryPath).standardized
        guard resolvedEntry.path.hasPrefix(resolvedDestination.path + "/") ||
              resolvedEntry.path == resolvedDestination.path else {
            throw IntegrityError.zipSlip(path: entryPath)
        }
    }
}

enum IntegrityError: LocalizedError {
    case zipSlip(path: String)
    case checksumMismatch(expected: String, actual: String)

    var errorDescription: String? {
        switch self {
        case .zipSlip(let path):
            return "Zip entry '\(path)' would escape the destination directory."
        case .checksumMismatch(let expected, let actual):
            return "SHA-256 mismatch: expected \(expected), got \(actual)."
        }
    }
}
