import Foundation
import SwiftData
import Observation

@Observable
final class RunService {
    let modelContainer: ModelContainer

    init(modelContainer: ModelContainer) {
        self.modelContainer = modelContainer
    }

    // MARK: - Run CRUD

    @MainActor
    func createRun(
        name: String,
        generation: Int,
        gameID: String,
        ruleSet: RuleSet
    ) throws -> Run {
        let context = modelContainer.mainContext
        let run = Run()
        run.name = name
        run.generation = generation
        run.gameID = gameID
        run.ruleSet = ruleSet
        context.insert(run)
        try context.save()
        return run
    }

    @MainActor
    func allRuns() throws -> [Run] {
        let descriptor = FetchDescriptor<Run>(
            sortBy: [SortDescriptor(\.lastPlayedAt, order: .reverse)]
        )
        return try modelContainer.mainContext.fetch(descriptor)
    }

    @MainActor
    func run(withID id: UUID) throws -> Run? {
        let descriptor = FetchDescriptor<Run>(
            predicate: #Predicate { $0.id == id }
        )
        return try modelContainer.mainContext.fetch(descriptor).first
    }

    @MainActor
    func setStatus(_ status: RunStatus, for run: Run) throws {
        run.status = status
        try modelContainer.mainContext.save()
    }

    @MainActor
    func deleteRun(_ run: Run) throws {
        modelContainer.mainContext.delete(run)
        try modelContainer.mainContext.save()
    }

    // MARK: - Encounter operations

    @MainActor
    func logEncounter(
        run: Run,
        routeID: String,
        outcome: EncounterOutcome,
        monsterNumber: Int?,
        nickname: String?,
        level: Int?
    ) throws {
        let context = modelContainer.mainContext
        let routeEncounter = RouteEncounter()
        routeEncounter.run = run
        routeEncounter.routeID = routeID
        routeEncounter.outcome = outcome
        routeEncounter.monsterNumber = monsterNumber
        context.insert(routeEncounter)

        if outcome == .caught, let number = monsterNumber {
            let monster = EncounteredMonster()
            monster.run = run
            monster.monsterNumber = number
            monster.nickname = nickname
            monster.caughtOnRouteID = routeID
            monster.caughtAtLevel = level ?? 1
            monster.currentLevel = level ?? 1
            monster.status = .box
            context.insert(monster)
            routeEncounter.caughtMonsterID = monster.id
        }

        run.lastPlayedAt = Date()
        try context.save()
    }

    @MainActor
    func updateMonsterStatus(
        _ monster: EncounteredMonster,
        to status: MonsterStatus,
        teamPosition: Int?,
        diedFrom: String?
    ) throws {
        monster.status = status
        monster.teamPosition = teamPosition
        if status == .dead {
            monster.diedAt = Date()
            monster.diedFrom = diedFrom
        }
        try modelContainer.mainContext.save()
    }
}
