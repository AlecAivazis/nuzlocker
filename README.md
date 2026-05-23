# Nuzlocker

A native iOS companion app for Pokémon Nuzlocke runs. Tracks encounters, party members, gym progress, and level caps across games. Game data is scraped from PokeAPI and Bulbapedia and distributed as per-game ZIPs via a CDN, unlocked through one-time in-app purchases.

## Prerequisites

- **Xcode 15+** — iOS 17 SDK required (SwiftData, `@Observable`, StoreKit 2)
- **Python 3.13** — for the scraper venv (`python3.13 -m venv`)
- **Apple Developer account** — free tier works for simulator; paid required for device builds and CloudKit

## One-time setup

1. Clone the repo and open `Nuzlocker.xcodeproj`.
2. Add ZIPFoundation via SPM: **File → Add Package Dependencies → `https://github.com/weichsel/ZIPFoundation`** (Up to Next Major Version).
3. In **Signing & Capabilities**, enable:
   - **iCloud** → Key-Value Storage + CloudKit
   - **Background Modes** → Remote notifications
4. Update `cloudKitContainerID` in `Core/Constants.swift` to match your auto-generated container (typically `iCloud.<your-bundle-id>`).
5. Confirm the scheme uses `StoreKitConfig.storekit`: **Edit Scheme → Run → Options → StoreKit Configuration**.
6. Install scraper dependencies: `cd scrape && python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt`

## Local development

The app treats installed data as the source of truth — no IAP required in development. Build and run the app in the simulator at least once, then seed it with game data:

```bash
scripts/seed.sh red                          # one game
scripts/seed.sh red blue yellow              # several at once
scripts/seed.sh soulsilver -- --device UDID  # target a specific simulator
```

This runs the full pipeline — scrape → package → install — and prompts you to restart the app when done. The scraper caches network responses under `scrape/cache/`, so subsequent runs for the same game are fast.

### Testing the full download flow (optional)

To test the IAP → download → install path instead of injecting directly:

```bash
# Terminal 1 — serve ZIPs and manifest from scrape/output/
scripts/serve-variants.sh

# Terminal 2 — generate cdn-manifest.json with local URLs
scripts/rewrite-manifest.sh              # simulator (localhost:8080)
scripts/rewrite-manifest.sh 192.168.1.42 # physical device (LAN IP, port 8080)
```

The script prints the URL to paste into `remoteManifestURL` in `Core/Constants.swift`. Rebuild the app after updating it. Revert `Constants.swift` before committing.

## Common tasks

| Task                     | How                                                                  |
| ------------------------ | -------------------------------------------------------------------- |
| Reset onboarding         | `scripts/reset-app.sh`                                               |
| Full simulator wipe      | Simulator → Device → Erase All Content and Settings                  |
| Reset StoreKit purchases | Xcode → Debug → StoreKit → Manage Transactions → delete all          |
| Wipe iCloud KVS          | Debug screen (long-press version label in Settings → About)          |
| Simulate iCloud off      | Debug screen toggle, or Simulator → Settings → Sign Out of iCloud    |
| Test on device           | `scripts/rewrite-manifest.sh <LAN-IP>`; update `remoteManifestURL`; Mac and device on same Wi-Fi |

## Simulator limitations

- Background download suspension timing — test on device for accurate behaviour
- Cross-device CloudKit sync — requires two real devices on the same Apple ID

## Scraper

### Producing variants

Use `scripts/seed.sh` (which handles the venv for you) or invoke the scraper directly:

```bash
cd scrape
.venv/bin/python3 scrape.py soulsilver
# writes output/soulsilver.json  (raw debug data)
# writes output/soulsilver.zip   (app-ready artifact)
# updates output/manifest.json   (global variant catalog)
```

`scrape.py` is the single entry point. It fetches data from PokeAPI and Bulbapedia, then immediately calls `transform.py` to shape and package the result. The two steps always run together — there is no intermediate script to invoke separately. HTTP responses are cached under `scrape/cache/` so re-running is fast.

### Data format

See [`scrape/README.md`](scrape/README.md) for the full specification of `manifest.json`, `game.json`, and `species.json`.

### Known data gaps

Some data is absent or incomplete for structural reasons. This section records what's missing, why, and whether it can be fixed.

#### Dungeon warp overlays — Gen 5 and later: not available

Warp connections between dungeon floors (the tile-grid overlays shown on dungeon maps) are scraped from the [pret](https://github.com/pret) decomp repositories, which provide machine-readable warp data in ASM or JSON format.

Mature pret repos exist for Gen 1 (pokefirered), Gen 2 (pokecrystal, pokeheartgold), Gen 3 (pokeemerald, pokefirered), and Gen 4 (pokeplatinum — partial). No equivalent repos exist for Gen 5 (Black/White/BW2), Gen 6 (X/Y/ORAS), or Gen 7 (Sun/Moon/USUM). Those games use 3DS/DS ROMs with closed binary formats that the community has not fully decomposed into warp-level data.

**Result:** All dungeon floors for Gen 5–7 have empty `warps` arrays. The floor structure and encounter data are correct; only the interactive warp overlay is absent.

#### Dungeon map images — Gen 5 and later: filenames unverified

The `bulbapedia_image` filenames in `game_data.py` for Gen 5 (`_UNOVA_CAVE_MAPS`) and Gen 6 (`_KALOS_CAVE_MAPS`) are best-guess approximations based on Bulbapedia's naming conventions. If a filename is wrong, the scraper logs a download warning and the floor's `imageFile` is `null` in the ZIP (the floor's encounter data is still present).

**Fix:** Verify each filename against Bulbapedia's actual file uploads and correct `game_data.py`.


