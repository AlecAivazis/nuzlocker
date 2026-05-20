import Foundation
import SwiftData

@Model
final class RouteEncounter {
    var id: UUID = UUID()
    var run: Run?
    var routeID: String = ""
    var encounteredAt: Date = Date()
    var outcome: EncounterOutcome = EncounterOutcome.skipped
    var monsterNumber: Int?
    var caughtMonsterID: UUID?
    var notes: String = ""

    init() {}
}

enum EncounterOutcome: String, Codable {
    case caught, fled, ko, missed, skipped
}
