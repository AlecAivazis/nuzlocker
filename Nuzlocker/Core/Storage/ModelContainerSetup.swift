import Foundation
import SwiftData
import CloudKit

enum ModelContainerSetup {
    static func makeContainer() throws -> ModelContainer {
        let schema = Schema([
            Run.self,
            EncounteredMonster.self,
            RouteEncounter.self,
        ])

        let cloudKitConfig = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            cloudKitDatabase: .private(Constants.cloudKitContainerID)
        )

        do {
            return try ModelContainer(for: schema, configurations: [cloudKitConfig])
        } catch {
            // Fall back to local-only if CloudKit is unavailable (e.g., no iCloud sign-in)
            let localConfig = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)
            return try ModelContainer(for: schema, configurations: [localConfig])
        }
    }
}
