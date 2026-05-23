# Data format

## Producing variants

Use `scripts/seed.sh` (which handles the venv for you) or invoke the scraper directly:

```bash
cd scrape
.venv/bin/python3 scrape.py soulsilver
# writes output/soulsilver.json  (raw debug data)
# writes output/soulsilver.zip   (app-ready artifact)
# updates output/manifest.json   (global variant catalog)
```

`scrape.py` is the single entry point. It fetches data from PokeAPI and Bulbapedia, then immediately calls `transform.py` to shape and package the result. The two steps always run together — there is no intermediate script to invoke separately. HTTP responses are cached under `scrape/cache/` so re-running is fast.

## `manifest.json` (CDN catalog)

Fetched by the app at launch from `Constants.remoteManifestURL` and cached to `Application Support/Nuzlocker/manifest.json`. On subsequent launches the cached copy is shown immediately while a background refresh runs. On first launch with no network the game list is empty.

The scraper writes an intermediate `output/manifest.json` with per-variant metadata but no SHA256 or file size — those are only known after uploading to the CDN. The content deploy step uploads ZIPs to CDN storage, then runs `rewrite_manifest.py` against the real CDN base URL to compute SHA256s and sizes and uploads the resulting manifest.

```json
{
  "manifestVersion": 1,
  "updatedAt": "2026-05-20T00:00:00Z",
  "games": [
    {
      "id":                    "heartgold",
      "displayName":           "HeartGold",
      "generation":            4,
      "generationDisplayName": "Generation IV",
      "zipURL":                "https://cdn.example.com/heartgold.zip",
      "zipSHA256":             "abc123…",
      "sizeBytes":             12345678,
      "contentVersion":        "1.0.0",
      "layoutVersion":         1
    }
  ]
}
```

Each game is a flat entry — grouping paired versions (HeartGold/SoulSilver, Red/Blue) is a UI concern, not a manifest concern.

**`Manifest`**

| Field             | Type       | Description                                   |
| ----------------- | ---------- | --------------------------------------------- |
| `manifestVersion` | integer    | Schema version; increment on breaking changes |
| `updatedAt`       | ISO 8601   | Timestamp of last update                      |
| `games`           | `Game[]`   | All purchasable games                         |

**`Game`**

| Field                   | Type    | Description                                                       |
| ----------------------- | ------- | ----------------------------------------------------------------- |
| `id`                    | string  | Game identifier (e.g. `"soulsilver"`)                             |
| `displayName`           | string  | Human-readable title (e.g. `"SoulSilver"`)                        |
| `generation`            | integer | Generation number (1–9)                                           |
| `generationDisplayName` | string  | Human-readable generation label (e.g. `"Generation IV"`)          |
| `zipURL`                | string  | CDN URL for the game ZIP                                          |
| `zipSHA256`             | string  | SHA-256 hex digest of the ZIP; verified before install            |
| `sizeBytes`             | integer | Compressed ZIP size in bytes; shown in the download UI            |
| `contentVersion`        | string  | Semver string; bump when game data changes                        |
| `layoutVersion`         | integer | ZIP layout schema version; app evicts cached installs on mismatch |

## Variant ZIP

Each variant ZIP is installed to `Library/Application Support/Nuzlocker/Variants/<variantID>/`.

```
<variantID>.zip
├── game.json          — routes, gyms, moves
├── species.json       — creature entries for every species in this game
├── sprites/
│   ├── 001.png        — species ID, zero-padded to 3 digits
│   └── …
└── maps/
    ├── route-29.png   — floor ID, matches imageFile in game.json
    └── …
```

## `game.json`

Every location is represented as a `Route` with one or more `Floor` entries. Single-floor routes have exactly one floor with `imageURL: null` and no warps. Multi-floor dungeons have one entry per floor with a Bulbapedia map image and tile-grid warp connections. Encounter sub-areas (grass, surfing, fishing) live inside their specific floor.

| Field       | Type                 | Description                                                                  |
| ----------- | -------------------- | ---------------------------------------------------------------------------- |
| `variantID` | string               | Matches the variant's entry in the global `manifest.json`                    |
| `routes`    | `Route[]`            | Encounter locations in story order                                           |
| `gyms`      | `Gym[]`              | Gym leaders in badge order                                                   |
| `moves`     | `{string: MoveData}` | Move slug → full move data for every move in the learnsets and trainer teams |

### Route

| Field         | Type      | Description                                                                          |
| ------------- | --------- | ------------------------------------------------------------------------------------ |
| `id`          | string    | Kebab-case location slug                                                             |
| `displayName` | string    | Human-readable location name                                                         |
| `floors`      | `Floor[]` | One entry per floor; outdoor routes have exactly one entry with `imageURL: null`      |

#### Floor

| Field               | Type                 | Description                                                                       |
| ------------------- | -------------------- | --------------------------------------------------------------------------------- |
| `id`                | string               | Stable kebab-case slug; used as a foreign key in `Warp.destFloorID`               |
| `displayName`       | string               | Floor label (e.g. `"1F"`, `"B1F"`); matches route name for single-floor locations |
| `imageFile`         | string \| null       | Filename inside the ZIP's `maps/` folder; `null` for outdoor routes with no map           |
| `warps`             | `Warp[]`             | Tile-grid connections to other floors; empty for single-floor routes              |
| `encounters`        | `Encounter[]`        | Wild Pokémon on this floor across all encounter methods                           |
| `staticEncounters`  | `FixedEncounter[]`   | Scripted one-time encounters on this floor (legendaries, Red Gyarados, etc.)      |
| `gifts`             | `FixedEncounter[]`   | Creatures received from NPCs on this floor                                        |
| `inGameTrades`      | `InGameTrade[]`      | NPC trade offers on this floor                                                    |
| `trainerEncounters` | `TrainerEncounter[]` | Trainer battles on this floor (rivals, notable antagonists, Elite Four, champion); empty for most routes |

**`Warp`**

Coordinates are tile-grid units — 1 tile = 16 px in all mainline generations. Matches the format used by the [pret decomp repos](https://github.com/pret). To render an overlay, multiply by 16 to get pixel position, then scale to the displayed image size.

| Field         | Type    | Description                                               |
| ------------- | ------- | --------------------------------------------------------- |
| `x`           | integer | Tile column of the warp on this floor's map image         |
| `y`           | integer | Tile row of the warp on this floor's map image            |
| `destFloorID` | string  | `id` of the destination floor                             |
| `destX`       | integer | Tile column of the arrival point on the destination floor |
| `destY`       | integer | Tile row of the arrival point on the destination floor    |

**`Encounter`**

| Field        | Type       | Description                                                                                                              |
| ------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------ |
| `method`     | string     | Encounter method: `"walk"`, `"surf"`, `"old-rod"`, `"good-rod"`, `"super-rod"`, `"rock-smash"`, `"gift"`, etc.          |
| `id`         | integer    | Species ID                                                                                         |
| `rate`       | number     | Encounter probability 0–100 (percentage)                                                                                 |
| `minLevel`   | integer    | Minimum wild level                                                                                                       |
| `maxLevel`   | integer    | Maximum wild level                                                                                                       |
| `conditions` | `string[]` | PokeAPI condition slugs that must hold (e.g. `"time-morning"`, `"swarm-yes"`, `"radio-hoenn"`); empty means always active |

**`FixedEncounter`**

Shared type for both `staticEncounters` and `gifts`.

| Field    | Type           | Description                                                                                      |
| -------- | -------------- | ------------------------------------------------------------------------------------------------ |
| `id`     | integer        | Species ID                                                                 |
| `level`  | integer        | Level (1 for eggs)                                                                               |
| `source` | string \| null | NPC or event description for gifts (e.g. `"Professor"`); `null` for static encounters            |
| `note`   | string \| null | Special context (e.g. `"Requires Poké Flute"`, `"Always Shiny"`, `"Always Shiny · Requires …"`) |

**`InGameTrade`**

| Field          | Type    | Description                        |
| -------------- | ------- | ---------------------------------- |
| `giveID`       | integer | Species ID the player gives        |
| `receiveID`    | integer | Species ID the player receives     |
| `receiveLevel` | integer | Level of the received creature     |
| `npc`          | string  | NPC name                           |

**`TrainerEncounter`**

| Field           | Type           | Description                                                                  |
| --------------- | -------------- | ---------------------------------------------------------------------------- |
| `name`          | string         | Trainer's name (e.g. `"Silver"`, `"Lance"`)                                  |
| `specialty`     | string \| null | Type specialty slug; `null` if no specialty                                  |
| `team`          | `Member[]`     | Team in this battle                                                          |
| `isRematch`     | boolean        | `true` for post-game rematch battles                                         |
| `playerStarter` | string \| null | Player starter slug that triggers this team variant; `null` if team is fixed |

**`Member`**

| Field      | Type           | Description                                               |
| ---------- | -------------- | --------------------------------------------------------- |
| `id`       | integer        | Species ID                          |
| `level`    | integer        | Level                                                     |
| `moves`    | `string[]`     | Move slugs (up to 4); may be empty if data is unavailable |
| `ability`  | string \| null | Ability slug; `null` if not listed                        |
| `heldItem` | string \| null | Held item slug; `null` if none                            |

### Gym

| Field         | Type               | Description                                                           |
| ------------- | ------------------ | --------------------------------------------------------------------- |
| `id`          | string             | Leader name slug (e.g. `"falkner"`, `"lt-surge"`)                     |
| `leader`      | string             | Gym leader name                                                       |
| `badge`       | string             | Badge awarded on victory                                              |
| `specialty`   | string \| null     | Type specialty slug (e.g. `"flying"`)                                 |
| `region`      | string \| null     | Region slug for multi-region games (e.g. `"johto"`, `"kanto"`); `null` otherwise |
| `team`        | `Member[]`         | Leader's team in the main battle                                      |
| `rematchTeam` | `Member[]` \| null | Leader's team in the rematch battle; `null` if none                   |

`Member` is defined above under [TrainerEncounter](#trainerencounter).

### Move

| Field          | Type            | Description                                                                             |
| -------------- | --------------- | --------------------------------------------------------------------------------------- |
| `type`         | string          | Type slug (e.g. `"fire"`, `"water"`)                                                   |
| `power`        | integer \| null | Base power; `null` for status moves                                                     |
| `accuracy`     | integer \| null | Accuracy 0–100; `null` for moves that never miss                                        |
| `pp`           | integer         | Base PP                                                                                 |
| `damageClass`  | string          | `"physical"`, `"special"`, or `"status"`                                                |
| `priority`     | integer         | Move priority bracket (0 = normal, +1 = Quick Attack, etc.)                            |
| `effectChance` | integer \| null | Percentage chance of secondary effect; `null` if none                                  |
| `effect`       | string          | Short mechanical description                                                            |
| `description`  | string          | In-game flavour text                                                                    |
| `machine`      | string \| null  | Machine identifier if teachable via TM/HM (e.g. `"tm26"`, `"hm01"`); `null` otherwise |
| `location`     | string \| null  | Where to obtain the TM/HM; `null` for HMs and non-machine moves                        |

## `species.json`

```json
{
  "creatures": [
    {
      "id": 1,
      "name": "bulbasaur",
      "types": ["grass", "poison"],
      "baseStats": { "hp": 45, "atk": 49, "def": 49, "spe": 45 },
      "abilities": [
        { "name": "overgrow",    "description": "Powers up Grass-type moves in a pinch.", "isHidden": false },
        { "name": "chlorophyll", "description": "Boosts the Pokémon's Speed stat in sunshine.", "isHidden": true }
      ],
      "evolvesTo": [
        {
          "id": 2,
          "methods": [ { "trigger": "level-up", "minLevel": 16 } ]
        }
      ],
      "learnset": [
        { "move": "tackle",     "method": "level-up", "level": 1,    "machine": null },
        { "move": "growl",      "method": "level-up", "level": 3,    "machine": null },
        { "move": "solar-beam", "method": "machine",  "level": null, "machine": "tm22" },
        { "move": "cut",        "method": "machine",  "level": null, "machine": "hm01" }
      ],
      "spriteFile": "001.png"
    }
  ]
}
```

### Creature

| Field        | Type                | Description                                                             |
| ------------ | ------------------- | ----------------------------------------------------------------------- |
| `id`         | integer             | Species ID                                        |
| `name`       | string              | PokeAPI species slug (lowercase)                                        |
| `types`      | `string[]`          | One or two type slugs (e.g. `["fire"]`, `["water", "flying"]`)         |
| `baseStats`  | object              | `hp`, `atk`, `def`, `spe` — all integers                               |
| `abilities`  | `Ability[]`         | Abilities available to this species in this game                        |
| `evolvesTo`  | `EvolutionTarget[]` | Direct evolutions from this species                                     |
| `learnset`   | `LearnsetEntry[]`   | Moves available in this game: level-up moves first, then machine moves  |
| `spriteFile` | string              | Sprite filename inside the ZIP's `sprites/` folder (e.g. `"001.png"`)  |

**`Ability`**

| Field         | Type    | Description                                                        |
| ------------- | ------- | ------------------------------------------------------------------ |
| `name`        | string  | PokeAPI ability slug (e.g. `"overgrow"`, `"chlorophyll"`)          |
| `description` | string  | In-game flavour text for this ability in the relevant game version |
| `isHidden`    | boolean | `true` for Hidden Abilities (not obtainable in all games)          |

**`LearnsetEntry`**

| Field     | Type            | Description                                           |
| --------- | --------------- | ----------------------------------------------------- |
| `move`    | string          | PokeAPI move slug                                     |
| `method`  | string          | `"level-up"` or `"machine"`                           |
| `level`   | integer \| null | Level learned at; `null` for machine moves            |
| `machine` | string \| null  | `"hm01"`, `"tm22"`, etc.; `null` for level-up moves  |

### Evolution

**`EvolutionTarget`**

| Field     | Type                | Description                                 |
| --------- | ------------------- | ------------------------------------------- |
| `id`      | integer             | Species ID of the species this evolves into |
| `methods` | `EvolutionMethod[]` | One or more ways to trigger the evolution   |

**`EvolutionMethod`**

| Field          | Type            | Description                                                       |
| -------------- | --------------- | ----------------------------------------------------------------- |
| `trigger`      | string          | PokeAPI trigger slug: `"level-up"`, `"use-item"`, `"trade"`, etc. |
| `minLevel`     | integer \| null | Minimum level required                                            |
| `item`         | string \| null  | Item slug consumed to evolve (use-item trigger)                   |
| `heldItem`     | string \| null  | Item slug the Pokémon must hold (trade trigger)                   |
| `knownMove`    | string \| null  | Move slug the Pokémon must know                                   |
| `timeOfDay`    | string \| null  | `"day"` or `"night"`                                              |
| `minHappiness` | integer \| null | Friendship threshold required                                     |
