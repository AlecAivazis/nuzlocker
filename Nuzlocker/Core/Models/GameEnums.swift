enum DamageClass: String, Codable {
    case physical
    case special
    case status
}

enum LearnsetMethod: String, Codable {
    case levelUp = "level-up"
    case machine
}

enum TimeOfDay: String, Codable {
    case day
    case night
    case fullMoon = "full-moon"
}
