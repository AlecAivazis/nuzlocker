import Foundation
import Observation

@Observable
final class AppState {
    let library: GameLibrary
    let runs: RunService

    private(set) var isReady = false

    init() throws {
        let container = try ModelContainerSetup.makeContainer()
        self.library = GameLibrary()
        self.runs = RunService(modelContainer: container)
    }

    func bootstrap() async {
        await library.bootstrap()
        await runs.bootstrap()
        await MainActor.run { isReady = true }
    }
}

enum AppError: LocalizedError {
    case runCreationFailed

    var errorDescription: String? {
        switch self {
        case .runCreationFailed: return "Failed to create the run. Please try again."
        }
    }
}
