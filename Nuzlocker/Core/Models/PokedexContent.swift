import Foundation

struct SpeciesContent: Codable {
    let creatures: [Creature]
}

struct Creature: Codable, Identifiable {
    let id: Int
    let name: String
    let types: [PokemonType]
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
    let trigger: EvolutionTrigger
    let minLevel: Int?
    let item: String?
    let heldItem: String?
    let knownMove: String?
    let timeOfDay: TimeOfDay?
    let minHappiness: Int?
}

struct LearnsetEntry: Codable {
    let move: String
    let method: LearnsetMethod
    let level: Int?
    let machine: String?
}
