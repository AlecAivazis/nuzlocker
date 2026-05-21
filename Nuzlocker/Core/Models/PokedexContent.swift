import Foundation

struct SpeciesContent: Codable {
    let creatures: [Creature]
}

struct Creature: Codable, Identifiable {
    let id: Int
    let name: String
    let types: [String]
    let baseStats: BaseStats
    let abilities: [CreatureAbility]
    let evolvesTo: [EvolutionTarget]
    let learnset: [LearnsetEntry]
    let spriteFile: String
}

struct BaseStats: Codable {
    let hp: Int
    let atk: Int
    let def: Int
    let spe: Int
}

struct CreatureAbility: Codable {
    let name: String
    let description: String
    let isHidden: Bool
}

struct EvolutionTarget: Codable {
    let id: Int
    let methods: [EvolutionMethod]
}

struct EvolutionMethod: Codable {
    let trigger: String        // "level-up", "use-item", "trade", etc.
    let minLevel: Int?
    let item: String?          // item slug (use-item trigger)
    let heldItem: String?      // held item slug (trade-holding trigger)
    let knownMove: String?     // move slug required to evolve
    let timeOfDay: String?     // "day" | "night"
    let minHappiness: Int?
}

struct LearnsetEntry: Codable {
    let move: String
    let method: String         // "level-up" | "machine"
    let level: Int?            // set for level-up; nil for machine moves
    let machine: String?       // "hm01", "tm13", etc.; nil for level-up moves
}
