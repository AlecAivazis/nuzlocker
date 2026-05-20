import SwiftUI

@main
struct NuzlockerApp: App {
    @State private var appState: AppState

    init() {
        do {
            let state = try AppState()
            _appState = State(initialValue: state)
            _ = state.library.startTransactionListener()
        } catch {
            fatalError("Failed to initialize AppState: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(appState)
                .task { await appState.bootstrap() }
        }
    }
}
