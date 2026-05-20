import SwiftUI
import UIKit

private let spriteCache = NSCache<NSString, UIImage>()

struct SpriteImage: View {
    let variantID: String
    let monster: EncounteredMonster
    var size: CGFloat = 64

    var body: some View {
        if let image = loadImage() {
            Image(uiImage: image)
                .interpolation(.none)
                .resizable()
                .frame(width: size, height: size)
        } else {
            placeholder
        }
    }

    private var placeholder: some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(Color.secondary.opacity(0.2))
            .frame(width: size, height: size)
            .overlay(
                Image(systemName: "questionmark")
                    .foregroundStyle(.secondary)
            )
    }

    private func loadImage() -> UIImage? {
        let key = "\(variantID)-\(monster.monsterNumber)" as NSString
        if let cached = spriteCache.object(forKey: key) { return cached }

        let filename = String(format: "%03d.png", monster.monsterNumber)
        let path = StorageLocations.variantDir(variantID)
            .appendingPathComponent("sprites")
            .appendingPathComponent(filename)
            .path

        guard let image = UIImage(contentsOfFile: path) else { return nil }
        spriteCache.setObject(image, forKey: key)
        return image
    }
}
