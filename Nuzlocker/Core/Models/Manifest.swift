import Foundation

struct Manifest: Codable {
    let manifestVersion: Int
    let games: [Game]
    let updatedAt: Date
}
