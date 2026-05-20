import Foundation

struct Game: Codable, Identifiable, Hashable {
    let id: String
    let displayName: String
    let generation: Int
    let generationDisplayName: String
    let variants: [GameVariant]
}
