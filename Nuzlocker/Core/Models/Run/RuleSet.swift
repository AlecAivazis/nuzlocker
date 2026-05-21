import Foundation

struct RuleSet: Codable, Equatable {
    var preset: RulePreset
    var firstEncounterOnly: Bool
    var deathIsPermanent: Bool
    var nicknameAll: Bool
    var speciesClause: Bool
    var levelCapMode: LevelCapMode
    var optionalRules: Set<NuzlockeRule>

    static let standard = RuleSet(
        preset: .standard,
        firstEncounterOnly: true,
        deathIsPermanent: true,
        nicknameAll: true,
        speciesClause: false,
        levelCapMode: .gymBased,
        optionalRules: [.dupesClause]
    )

    static let hardcore = RuleSet(
        preset: .hardcore,
        firstEncounterOnly: true,
        deathIsPermanent: true,
        nicknameAll: true,
        speciesClause: false,
        levelCapMode: .gymBased,
        optionalRules: [.dupesClause, .setBattleMode, .levelCaps]
    )
}

enum RulePreset: String, Codable {
    case standard, hardcore, custom
}

enum LevelCapMode: String, Codable {
    case none, gymBased, custom
}
