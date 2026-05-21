import Foundation

struct Game: Codable, Identifiable, Hashable {
    let id: String
    let displayName: String
    let generation: Int
    let generationDisplayName: String
    let zipURL: URL
    let zipSHA256: String
    let sizeBytes: Int64
    let contentVersion: String
    let layoutVersion: Int
}
