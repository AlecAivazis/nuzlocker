import Foundation

struct GameVariant: Codable, Identifiable, Hashable {
    let id: String
    let displayName: String
    let zipURL: URL
    let zipSHA256: String
    let sizeBytes: Int64
    let contentVersion: String
    let layoutVersion: Int
}
