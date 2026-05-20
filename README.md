# Nuzlocker

A native iOS companion app for Pokémon Nuzlocke runs. Tracks encounters, party members, gym progress, and level caps across games. Game data is scraped from PokeAPI and Bulbapedia and distributed as per-game ZIPs via a CDN, unlocked through one-time in-app purchases.

## Prerequisites

- **Xcode 15+** — iOS 17 SDK required (SwiftData, `@Observable`, StoreKit 2)
- **Python 3.9+** — for the scraper and local dev scripts
- **`jq`** — for `rewrite-manifest.sh`: `brew install jq`
- **Apple Developer account** — free tier works for simulator; paid required for device builds and CloudKit

## One-time setup

1. Clone the repo and open `Nuzlocker.xcodeproj`.
2. Add ZIPFoundation via SPM: **File → Add Package Dependencies → `https://github.com/weichsel/ZIPFoundation`** (Up to Next Major Version).
3. In **Signing & Capabilities**, enable:
   - **iCloud** → Key-Value Storage + CloudKit
   - **Background Modes** → Remote notifications
4. Update `cloudKitContainerID` in `Core/Constants.swift` to match your auto-generated container (typically `iCloud.<your-bundle-id>`).
5. Confirm the scheme uses `StoreKitConfig.storekit`: **Edit Scheme → Run → Options → StoreKit Configuration**.
6. Install scraper dependencies: `cd scrape && pip install -r requirements.txt`

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
# Terminal 1
scripts/serve-variants.sh          # serves variants/ on localhost:8080

# Terminal 2 — rewrite manifest URLs, then build and run
scripts/rewrite-manifest.sh        # simulator
scripts/rewrite-manifest.sh <LAN-IP>  # physical device
```

## Common tasks

| Task                     | How                                                                  |
| ------------------------ | -------------------------------------------------------------------- |
| Reset onboarding         | `scripts/reset-app.sh`                                               |
| Full simulator wipe      | Simulator → Device → Erase All Content and Settings                  |
| Reset StoreKit purchases | Xcode → Debug → StoreKit → Manage Transactions → delete all          |
| Wipe iCloud KVS          | Debug screen (long-press version label in Settings → About)          |
| Simulate iCloud off      | Debug screen toggle, or Simulator → Settings → Sign Out of iCloud    |
| Test on device           | `scripts/rewrite-manifest.sh <LAN-IP>`; Mac and device on same Wi-Fi |

## Simulator limitations

- Background download suspension timing — test on device for accurate behaviour
- Cross-device CloudKit sync — requires two real devices on the same Apple ID

## Variant data format

Each variant is a ZIP distributed via CDN and installed to `Library/Application Support/Variants/<variantID>/`.

```
<variantID>.zip
├── manifest.json      — identity and layout metadata
├── game.json          — routes, gyms, TMs, starters
├── pokedex.json       — creature entries for this game's Pokédex
└── sprites/
    ├── 001.png        — national dex number, zero-padded to 3 digits
    └── …
```

### `manifest.json`

```json
{
  "variantID":      "red",
  "gameID":         "red_blue",
  "generation":     1,
  "displayName":    "Red",
  "contentVersion": "1.0.0",
  "layoutVersion":  1,
  "spritesPath":    "sprites",
  "pokedexFile":    "pokedex.json",
  "gameDataFile":   "game.json"
}
```

| Field            | Type    | Description                                                  |
| ---------------- | ------- | ------------------------------------------------------------ |
| `variantID`      | string  | Unique identifier for this variant (e.g. `"red"`, `"soulsilver"`) |
| `gameID`         | string  | Version-group identifier, shared by paired games (e.g. `"red_blue"`) |
| `generation`     | integer | Generation number (e.g. `1` … `9`)                          |
| `displayName`    | string  | Human-readable game title                                    |
| `contentVersion` | string  | Semver string; bump when game data changes                   |
| `layoutVersion`  | integer | ZIP layout schema version; app evicts installs on mismatch  |
| `spritesPath`    | string  | Subdirectory containing sprite PNGs                          |
| `pokedexFile`    | string  | Filename of the Pokédex JSON inside the ZIP                  |
| `gameDataFile`   | string  | Filename of the game data JSON inside the ZIP                |

### `game.json`

```json
{
  "variantID": "red",
  "starters": [1, 4, 7],
  "routes": [
    {
      "id": "viridian_forest",
      "displayName": "Viridian Forest",
      "areas": [
        {
          "id": "viridian_forest_area",
          "displayName": "",
          "encounters": [
            { "method": "walk", "pokedexNumber": 10, "rate": 0.05, "minLevel": 3, "maxLevel": 5 }
          ]
        }
      ]
    },
    {
      "id": "ice_path",
      "displayName": "Ice Path",
      "areas": [
        {
          "id": "ice_path_1f",
          "displayName": "1F",
          "encounters": [
            { "method": "walk", "pokedexNumber": 220, "rate": 0.1, "minLevel": 18, "maxLevel": 22 }
          ]
        },
        {
          "id": "ice_path_b1f",
          "displayName": "B1F",
          "encounters": [
            { "method": "walk", "pokedexNumber": 225, "rate": 0.05, "minLevel": 20, "maxLevel": 24 }
          ]
        }
      ]
    }
  ],
  "gyms": [
    {
      "id": "gym_1",
      "leader": "Brock",
      "badge": "Boulder Badge",
      "levelCap": 14,
      "team": [
        { "pokedexNumber": 74, "level": 12 },
        { "pokedexNumber": 95, "level": 14 }
      ]
    }
  ],
  "tms": [
    { "number": 1, "name": "TM01", "move": "mega-punch", "location": "Celadon Dept. Store" },
    { "number": 2, "name": "TM02", "move": "razor-wind",  "location": null }
  ]
}
```

**Top-level fields**

| Field       | Type      | Description                                        |
| ----------- | --------- | -------------------------------------------------- |
| `variantID` | string    | Matches `manifest.json`                            |
| `starters`  | `int[]`   | National dex numbers of the game's starter Pokémon |
| `routes`    | `Route[]` | Ordered list of encounter locations                |
| `gyms`      | `Gym[]`   | Ordered list of gym leaders                        |
| `tms`       | `TM[]`    | All TMs available in this game                     |

**`Route`**

| Field         | Type     | Description                                        |
| ------------- | -------- | -------------------------------------------------- |
| `id`          | string   | Snake-case location slug (e.g. `"ice_path"`)       |
| `displayName` | string   | Human-readable location name                       |
| `areas`       | `Area[]` | One entry for simple routes; multiple for multi-floor/multi-section locations |

**`Area`**

| Field         | Type          | Description                                                                 |
| ------------- | ------------- | --------------------------------------------------------------------------- |
| `id`          | string        | Snake-case area slug (e.g. `"ice_path_b1f"`)                                |
| `displayName` | string        | Floor or section label (e.g. `"1F"`, `"B1F"`, `"Violet City Side"`); empty string for simple single-area locations |
| `encounters`  | `Encounter[]` | Possible wild Pokémon for this area                                         |

**`Encounter`**

| Field           | Type    | Description                                              |
| --------------- | ------- | -------------------------------------------------------- |
| `method`        | string  | Encounter method (e.g. `"walk"`, `"surf"`, `"fishing"`) |
| `pokedexNumber` | integer | National dex number                                      |
| `rate`          | number  | Encounter probability 0–1                                |
| `minLevel`      | integer | Minimum wild level                                       |
| `maxLevel`      | integer | Maximum wild level                                       |

**`Gym`**

| Field      | Type         | Description                                       |
| ---------- | ------------ | ------------------------------------------------- |
| `id`       | string       | Stable slug (e.g. `"gym_1"`)                      |
| `leader`   | string       | Gym leader name                                   |
| `badge`    | string       | Badge awarded on victory                          |
| `levelCap` | integer      | Level of the leader's highest-level Pokémon       |
| `team`     | `Member[]`   | Leader's team in final battle                     |

**`Member`** (gym team entry)

| Field           | Type    | Description         |
| --------------- | ------- | ------------------- |
| `pokedexNumber` | integer | National dex number |
| `level`         | integer | Pokémon level       |

**`TM`**

| Field      | Type            | Description                                           |
| ---------- | --------------- | ----------------------------------------------------- |
| `number`   | integer         | TM number (1–100)                                     |
| `name`     | string          | Display name (e.g. `"TM01"`)                          |
| `move`     | string          | PokeAPI move slug (e.g. `"mega-punch"`)               |
| `location` | string \| null  | Where to obtain the TM; `null` if not yet known       |

### `pokedex.json`

```json
{
  "creatures": [
    {
      "pokedexNumber": 1,
      "name": "bulbasaur",
      "types": ["grass", "poison"],
      "baseStats": { "hp": 45, "atk": 49, "def": 49, "spe": 45 },
      "spriteFile": "sprites/001.png"
    }
  ]
}
```

**`Creature`**

| Field           | Type       | Description                                          |
| --------------- | ---------- | ---------------------------------------------------- |
| `pokedexNumber` | integer    | National dex number                                  |
| `name`          | string     | PokeAPI species slug (lowercase)                     |
| `types`         | `string[]` | One or two type slugs (e.g. `["fire"]`, `["water", "flying"]`) |
| `baseStats`     | object     | `hp`, `atk`, `def`, `spe` — all integers             |
| `spriteFile`    | string     | Relative path inside the ZIP (e.g. `"sprites/001.png"`) |
