import Foundation
import SwiftData

@Model
final class EncounteredMonster {
    var id: UUID = UUID()
    var run: Run?
    var monsterNumber: Int = 0
    var nickname: String?
    var caughtAt: Date = Date()
    var caughtOnRouteID: String = ""
    var caughtAtLevel: Int = 1
    var currentLevel: Int = 1
    var status: MonsterStatus = MonsterStatus.box
    var teamPosition: Int?
    var nature: String?
    var ability: String?
    var heldItem: String?
    var moves: [String] = []
    var notes: String = ""
    var diedAt: Date?
    var diedFrom: String?

    init() {}
}

enum MonsterStatus: String, Codable {
    case team, box, dead
}
