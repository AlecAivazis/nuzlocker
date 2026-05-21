import Foundation
import SwiftData

@Model
final class Run {
    var id: UUID = UUID()
    var name: String = ""
    var generation: Int = 0
    var gameID: String = ""
    var variantID: String = ""
    var startedAt: Date = Date()
    var lastPlayedAt: Date = Date()
    var status: RunStatus = RunStatus.active
    var notes: String = ""
    var ruleSetData: Data = Data()
    var customRules: [String] = []    // freeform user-defined rules beyond NuzlockeRule presets
    var currentBadgeCount: Int = 0
    var levelCapOverride: Int = 0

    @Relationship(deleteRule: .cascade) var monsters: [EncounteredMonster]?
    @Relationship(deleteRule: .cascade) var routeEncounters: [RouteEncounter]?

    init() {}

    var ruleSet: RuleSet {
        get { (try? JSONDecoder().decode(RuleSet.self, from: ruleSetData)) ?? RuleSet.standard }
        set { ruleSetData = (try? JSONEncoder().encode(newValue)) ?? Data() }
    }
}

enum RunStatus: String, Codable {
    case active, completed, failed, archived
}
