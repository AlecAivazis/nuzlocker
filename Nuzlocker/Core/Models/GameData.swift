import Foundation

struct GameData: Codable {
    let variantID: String
    let starters: [Int]
    let routes: [GameRoute]
    let gyms: [GymData]
    let tms: [TMData]
}

struct GameRoute: Codable, Identifiable {
    let id: String
    let displayName: String
    let areas: [RouteArea]
}

struct RouteArea: Codable, Identifiable {
    let id: String
    let displayName: String
    let encounters: [RouteEncounterEntry]
}

struct RouteEncounterEntry: Codable {
    let method: String
    let pokedexNumber: Int
    let rate: Double
    let minLevel: Int
    let maxLevel: Int
}

struct GymData: Codable, Identifiable {
    let id: String
    let leader: String
    let badge: String
    let levelCap: Int
    let team: [GymMember]
}

struct GymMember: Codable {
    let pokedexNumber: Int
    let level: Int
}

struct TMData: Codable {
    let number: Int
    let name: String
    let move: String
    let location: String?
}
