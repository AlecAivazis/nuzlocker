import SwiftUI

struct RootView: View {
    @Environment(AppState.self) private var app

    var body: some View {
        if app.isReady {
            Text("Nuzlocker")
        } else {
            SplashView()
        }
    }
}

private struct SplashView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "gamecontroller.fill")
                .font(.system(size: 60))
                .foregroundStyle(Color.accentColor)
            Text("Nuzlocker")
                .font(.largeTitle.bold())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
    }
}
