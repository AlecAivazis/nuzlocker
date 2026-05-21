import Foundation

struct VariantContent: Codable {
    let variantID: String
    let starters: [Int]
    let hmMoves: [String: String]            // move slug → "hm01", "hm02", etc.
    let badgeObedience: [BadgeObedience]
    let routes: [GameRoute]
    let gyms: [GymData]
    let eliteFour: [TrainerData]
    let champion: TrainerData?
    let rivals: [TrainerData]
    let tms: [TMData]
    let moves: [String: MoveData]            // move slug → move details
}

// MARK: - Obedience / HMs

struct BadgeObedience: Codable {
    let badges: Int
    let maxLevel: Int
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
    let imageURL: String?
    let warps: [WarpPoint]
    let areas: [RouteArea]
    let staticEncounters: [FixedEncounter]
    let giftPokemon: [FixedEncounter]
    let inGameTrades: [InGameTrade]
}

struct WarpPoint: Codable {
    let x: Int           // tile column on this floor's map image (1 tile = 16 px)
    let y: Int           // tile row
    let destFloorID: String
    let destX: Int
    let destY: Int
}

struct RouteArea: Codable, Identifiable {
    let id: String
    let displayName: String?   // nil when the floor has only one encounter method
    let encounters: [RouteEncounterEntry]
}

struct RouteEncounterEntry: Codable {
    let method: String
    let id: Int
    let rate: Double
    let minLevel: Int
    let maxLevel: Int
    let conditions: [String]
}

struct FixedEncounter: Codable {
    let id: Int
    let level: Int
    let alwaysShiny: Bool
    let source: String?   // nil = scripted battle; non-nil = NPC/source description (gift)
    let note: String?
}

struct InGameTrade: Codable {
    let giveID: Int
    let receiveID: Int
    let receiveLevel: Int
    let npc: String
}

// MARK: - Gyms

struct GymData: Codable, Identifiable {
    let id: String
    let leader: String
    let badge: String
    let specialty: String?
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

// MARK: - Elite Four, Champion, Rivals

struct TrainerData: Codable, Identifiable {
    let id: String
    let trainerClass: String   // "elite_four" | "champion" | "rival"
    let name: String
    let specialty: String?
    let battles: [TrainerBattle]
}

struct TrainerBattle: Codable {
    let team: [GymMember]
    let isRematch: Bool
    let locationHint: String?   // non-nil for rivals; section hint from Bulbapedia
    let playerStarter: String?  // non-nil for rival variant battles
}

// MARK: - TMs

struct TMData: Codable {
    let number: Int
    let name: String
    let move: String
    let location: String?
}

// MARK: - Moves

struct MoveData: Codable {
    let type: String
    let power: Int?
    let accuracy: Int?
    let pp: Int
    let damageClass: String    // "physical" | "special" | "status"
    let priority: Int
    let effectChance: Int?
    let effect: String
    let description: String
}
