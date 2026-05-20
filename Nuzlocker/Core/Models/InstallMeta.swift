import Foundation

struct InstallMeta: Codable {
    let variantID: String
    let gameID: String
    let generation: Int
    let contentVersion: String
    let layoutVersion: Int
    let installedAt: Date
    let zipSHA256: String
}
