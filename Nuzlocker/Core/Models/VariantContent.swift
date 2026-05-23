import Foundation

struct VariantContent: Codable {
    let variantID: String
    let routes: [GameRoute]
    let gyms: [GymData]
    let moves: [String: MoveData]            // move slug → move details
}

// MARK: - Routes

struct GameRoute: Codable, Identifiable {
    let id: String
    let displayName: String
    let floors: [FloorMap]
}

struct FloorMap: Codable, Identifiable {
    let id: String
    let displayName: String
    let imageFile: String?
    let warps: [WarpPoint]
    let encounters: [RouteEncounterEntry]
    let staticEncounters: [FixedEncounter]
    let gifts: [FixedEncounter]
    let inGameTrades: [InGameTrade]
    let trainerEncounters: [TrainerEncounter]
}

struct TrainerEncounter: Codable {
    let name: String
    let specialty: PokemonType?
    let team: [GymMember]
    let isRematch: Bool
    let playerStarter: String?
}

struct WarpPoint: Codable {
    let x: Int           // tile column on this floor's map image (1 tile = 16 px)
    let y: Int           // tile row
    let destFloorID: String
    let destX: Int
    let destY: Int
}

struct RouteEncounterEntry: Codable {
    let method: EncounterMethod
    let id: Int
    let rate: Double
    let minLevel: Int
    let maxLevel: Int
    let conditions: [EncounterCondition]
}

struct FixedEncounter: Codable {
    let id: Int
    let level: Int
    let source: String?
    let note: String?
}

struct InGameTrade: Codable {
    let giveID: Int
    let receiveID: Int
    let receiveLevel: Int?
    let npc: String
}

// MARK: - Gyms

struct GymData: Codable, Identifiable {
    let id: String
    let leader: String
    let badge: String
    let specialty: PokemonType?
    let region: String?      // nil when the game has one region; e.g. "johto" / "kanto" for HGSS
    let team: [GymMember]
    let rematchTeam: [GymMember]?

    var levelCap: Int { team.map(\.level).max() ?? 0 }
}

struct GymMember: Codable {
    let id: Int
    let level: Int
    let moves: [String]
    let ability: String?
    let heldItem: String?
}

// MARK: - Moves

struct MoveData: Codable {
    let type: PokemonType
    let damageClass: DamageClass
    let power: Int?
    let accuracy: Int?
    let pp: Int
    let priority: Int
    let effectChance: Int?
    let effect: String
    let description: String
    let machine: String?       // e.g. "tm26", "hm01"; nil if not a TM/HM
    let location: String?      // where to obtain the TM/HM; nil if not applicable
}
