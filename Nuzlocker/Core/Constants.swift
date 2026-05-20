import Foundation

enum Constants {
    static let currentLayoutVersion: Int = 1
    static let remoteManifestURL = URL(string: "https://cdn.example.com/manifest.json")!
    static let backgroundDownloadIdentifier = "com.example.nuzlocker.bg-downloads"
    static let manifestFetchTimeout: TimeInterval = 8

    static let kvsKeyFreePickGameIDs = "freePickGameIDs"
    static let userDefaultsKeyCurrentRunID = "currentRunID"

    static let maxFreeGames: Int = 2

    static let cloudKitContainerID = "iCloud.com.example.nuzlocker"
}
