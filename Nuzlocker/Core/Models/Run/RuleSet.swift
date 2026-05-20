import Foundation

struct RuleSet: Codable, Equatable {
    var preset: RulePreset
    var firstEncounterOnly: Bool
    var deathIsPermanent: Bool
    var nicknameAll: Bool
    var dupesClause: Bool
    var shinyClause: Bool
    var speciesClause: Bool
    var levelCapMode: LevelCapMode

    static let standard = RuleSet(
        preset: .standard,
        firstEncounterOnly: true,
        deathIsPermanent: true,
        nicknameAll: true,
        dupesClause: true,
        shinyClause: false,
        speciesClause: false,
        levelCapMode: .gymBased
    )

    static let hardcore = RuleSet(
        preset: .hardcore,
        firstEncounterOnly: true,
        deathIsPermanent: true,
        nicknameAll: true,
        dupesClause: false,
        shinyClause: false,
        speciesClause: false,
        levelCapMode: .gymBased
    )
}

enum RulePreset: String, Codable {
    case standard, hardcore, custom
}

enum LevelCapMode: String, Codable {
    case none, gymBased, custom
}
