import Foundation

// Type effectiveness matrix. ATTACK_EFF[attacker][defender] = multiplier (omitted = 1.0).
// Gen 1 note: no Dark/Steel/Fairy; Poison→Ghost = 1.0, Bug→Poison = 2.0, Ghost→Psychic = 0.0.
// Gen 2–5 note: Steel resists Ghost and Dark (0.5×).
// Gen 6+: Steel vs Ghost and Dark reverts to 1.0×; Fairy type added.

enum TypeChart {

    static func multiplier(attacking: String, defending: String, generation: Int) -> Double {
        var eff = baseEffectiveness[attacking]?[defending] ?? 1.0
        if generation <= 5 {
            // Steel resisted Ghost and Dark before Gen 6
            if attacking == "steel" && (defending == "ghost" || defending == "dark") {
                eff = 0.5
            }
        }
        if generation == 1 {
            // Gen 1 quirks
            if attacking == "poison" && defending == "ghost" { return 1.0 }
            if attacking == "ghost"  && defending == "psychic" { return 0.0 }
            if attacking == "bug"    && defending == "poison" { return 2.0 }
            if attacking == "ice"    && defending == "fire" { return 1.0 }
        }
        return eff
    }

    static func multiplier(attacking: String, against types: [String], generation: Int) -> Double {
        types.reduce(1.0) { $0 * multiplier(attacking: attacking, defending: $1, generation: generation) }
    }

    // Gen 6+ base chart (no Gen 1 quirks, no steel-vs-ghost/dark resistance).
    private static let baseEffectiveness: [String: [String: Double]] = [
        "normal":   ["rock": 0.5, "ghost": 0.0, "steel": 0.5],
        "fire":     ["fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0,
                     "rock": 0.5, "dragon": 0.5, "steel": 2.0],
        "water":    ["fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0,
                     "rock": 2.0, "dragon": 0.5],
        "electric": ["water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0,
                     "flying": 2.0, "dragon": 0.5],
        "grass":    ["fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5,
                     "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0,
                     "dragon": 0.5, "steel": 0.5],
        "ice":      ["water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0,
                     "flying": 2.0, "dragon": 2.0, "steel": 0.5],
        "fighting": ["normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5,
                     "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0,
                     "dark": 2.0, "steel": 2.0, "fairy": 0.5],
        "poison":   ["grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5,
                     "ghost": 0.5, "steel": 0.0, "fairy": 2.0],
        "ground":   ["fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0,
                     "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0],
        "flying":   ["electric": 0.5, "grass": 2.0, "fighting": 2.0,
                     "bug": 2.0, "rock": 0.5, "steel": 0.5],
        "psychic":  ["fighting": 2.0, "poison": 2.0, "psychic": 0.5,
                     "dark": 0.0, "steel": 0.5],
        "bug":      ["fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5,
                     "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0,
                     "steel": 0.5, "fairy": 0.5],
        "rock":     ["fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5,
                     "flying": 2.0, "bug": 2.0, "steel": 0.5],
        "ghost":    ["normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5],
        "dragon":   ["dragon": 2.0, "steel": 0.5, "fairy": 0.0],
        "dark":     ["fighting": 0.5, "psychic": 2.0, "ghost": 2.0,
                     "dark": 0.5, "fairy": 0.5],
        "steel":    ["fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0,
                     "rock": 2.0, "steel": 0.5, "fairy": 2.0],
        "fairy":    ["fire": 0.5, "fighting": 2.0, "poison": 0.5,
                     "dragon": 2.0, "dark": 2.0, "steel": 0.5],
    ]
}
