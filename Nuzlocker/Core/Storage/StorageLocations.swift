import Foundation

enum StorageLocations {
    static var appSupport: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
    }

    static var appRoot: URL {
        appSupport.appendingPathComponent("Nuzlocker", isDirectory: true)
    }

    static var variantsRoot: URL {
        appRoot.appendingPathComponent("Variants", isDirectory: true)
    }

    static func variantDir(_ variantID: String) -> URL {
        variantsRoot.appendingPathComponent(variantID, isDirectory: true)
    }

    static func installMeta(_ variantID: String) -> URL {
        variantDir(variantID).appendingPathComponent(".install-meta.json")
    }

    static var stagingRoot: URL {
        FileManager.default.temporaryDirectory.appendingPathComponent("NuzlockerStaging", isDirectory: true)
    }

    static var manifestCache: URL {
        appRoot.appendingPathComponent("manifest.json")
    }

    static func ensureDirectories() throws {
        let fm = FileManager.default
        try fm.createDirectory(at: appRoot, withIntermediateDirectories: true)
        try fm.createDirectory(at: variantsRoot, withIntermediateDirectories: true)
        try fm.createDirectory(at: stagingRoot, withIntermediateDirectories: true)
    }

    static func setExcludedFromBackup(_ url: URL) throws {
        var mutable = url
        var rv = URLResourceValues()
        rv.isExcludedFromBackup = true
        try mutable.setResourceValues(rv)
    }
}
