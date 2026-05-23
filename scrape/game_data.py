"""
Static game data for the Nuzlocke scraper.

Contains everything that is hand-authored and game-specific:
  HM_MOVES          — which moves are HMs and their slot number, per version
  BADGE_OBEDIENCE   — badge-count thresholds for outsider-Pokémon obedience
  TRAINER_DEFS      — gym leaders, E4, champions, rivals (Bulbapedia page names)
  GAME_STATIC       — starters, static encounters, gift Pokémon, in-game trades
  ROUTE_ORDER       — location unlock order with prerequisites
  BULBA_ITEM_FIELDS — Bulbapedia {{itemlist}} field names for each version,
                      used to extract TM locations from item pages
  CAVE_MAPS         — multi-floor dungeon definitions: floor images (Bulbapedia),
                      warp connections, and PokeAPI area mappings for encounter assignment
"""

from __future__ import annotations

# ── HM moves per canonical version ────────────────────────────────────────────
# Values are "hmNN" strings; only the representative version is listed and then
# aliased to its pair(s) below.

HM_MOVES: dict[str, dict[str, str]] = {
    "red":       {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","flash":"hm05"},
    "gold":      {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","flash":"hm05","whirlpool":"hm06","waterfall":"hm07"},
    "ruby":      {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","flash":"hm05","rock-smash":"hm06","waterfall":"hm07","dive":"hm08"},
    "firered":   {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","flash":"hm05","rock-smash":"hm06","waterfall":"hm07"},
    "diamond":   {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","defog":"hm05","rock-smash":"hm06","waterfall":"hm07","rock-climb":"hm08"},
    "heartgold": {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","whirlpool":"hm05","rock-smash":"hm06","waterfall":"hm07","rock-climb":"hm08"},
    "black":     {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","waterfall":"hm05","dive":"hm06"},
    "x":         {"cut":"hm01","fly":"hm02","surf":"hm03","strength":"hm04","waterfall":"hm05","rock-smash":"hm06"},
    "sun":       {},  # Gen 7 uses Ride Pokémon — no HMs
}
for _a, _b in [
    ("blue","red"),("yellow","red"),
    ("silver","gold"),("crystal","gold"),
    ("sapphire","ruby"),("emerald","ruby"),
    ("leafgreen","firered"),
    ("pearl","diamond"),("platinum","diamond"),
    ("soulsilver","heartgold"),
    ("white","black"),("black-2","black"),("white-2","black"),
    ("y","x"),("omega-ruby","x"),("alpha-sapphire","x"),
    ("moon","sun"),("ultra-sun","sun"),("ultra-moon","sun"),
]:
    HM_MOVES.setdefault(_a, HM_MOVES.get(_b, {}))


# ── Bulbapedia itemlist field names for TM location scraping ───────────────────
# Each entry is a list of candidate field names tried in order; Bulbapedia's
# {{itemlist}} template is inconsistent across generations and editors.
# Only the canonical version per pair is listed; aliases share the same fields.

BULBA_ITEM_FIELDS: dict[str, list[str]] = {
    "red":          ["Red and Blue", "Red"],
    "yellow":       ["Yellow"],
    "gold":         ["Gold and Silver", "Gold"],
    "crystal":      ["Crystal"],
    "ruby":         ["Ruby and Sapphire", "Ruby"],
    "emerald":      ["Emerald"],
    "firered":      ["FireRed and LeafGreen", "FireRed"],
    "diamond":      ["Diamond and Pearl", "Diamond"],
    "platinum":     ["Platinum"],
    "heartgold":    ["HeartGold and SoulSilver", "HeartGold", "HGSS"],
    "black":        ["Black and White", "Black"],
    "black-2":      ["Black 2 and White 2", "Black 2"],
    "x":            ["X and Y", "X"],
    "omega-ruby":   ["Omega Ruby and Alpha Sapphire", "Omega Ruby", "ORAS"],
    "sun":          ["Sun and Moon", "Sun"],
    "ultra-sun":    ["Ultra Sun and Ultra Moon", "Ultra Sun", "USUM"],
}
for _a, _b in [
    ("blue","red"),
    ("silver","gold"),
    ("sapphire","ruby"),
    ("leafgreen","firered"),
    ("pearl","diamond"),
    ("soulsilver","heartgold"),
    ("white","black"),("white-2","black-2"),
    ("y","x"),("alpha-sapphire","omega-ruby"),
    ("moon","sun"),("ultra-moon","ultra-sun"),
]:
    BULBA_ITEM_FIELDS.setdefault(_a, BULBA_ITEM_FIELDS.get(_b, []))


# ── Badge obedience thresholds ─────────────────────────────────────────────────
# Applies to outsider (traded/transferred) Pokémon only.
# Each entry = {"badges": N, "max_level": M} meaning "after earning N badges,
# outsider Pokémon up to level M obey".

BADGE_OBEDIENCE: dict[str, list[dict]] = {
    # RBY: Cascade Badge (#2), Soul Badge (#5), Volcano Badge (#7), Earth Badge (#8)
    "red":       [{"badges":0,"max_level":10},{"badges":2,"max_level":30},
                  {"badges":5,"max_level":50},{"badges":7,"max_level":70},{"badges":8,"max_level":100}],
    # GSC/HGSS: increments of 10 per badge
    "gold":      [{"badges":0,"max_level":10},{"badges":1,"max_level":20},
                  {"badges":2,"max_level":30},{"badges":3,"max_level":40},
                  {"badges":4,"max_level":50},{"badges":5,"max_level":60},
                  {"badges":6,"max_level":70},{"badges":7,"max_level":80},{"badges":8,"max_level":100}],
    "heartgold": [{"badges":0,"max_level":10},{"badges":1,"max_level":20},
                  {"badges":2,"max_level":30},{"badges":3,"max_level":40},
                  {"badges":4,"max_level":50},{"badges":5,"max_level":60},
                  {"badges":6,"max_level":70},{"badges":7,"max_level":80},{"badges":8,"max_level":100}],
    # RSE: Stone (#1 → 20), Dynamo (#3 → 30), Balance (#5 → 50), Mind (#7 → 70)
    "ruby":      [{"badges":0,"max_level":20},{"badges":2,"max_level":30},
                  {"badges":4,"max_level":50},{"badges":6,"max_level":70},{"badges":8,"max_level":100}],
    # DPPt: Coal (#1 → 20), Forest (#2 → 30), Fen (#4 → 50), Mine (#6 → 70)
    "diamond":   [{"badges":0,"max_level":20},{"badges":2,"max_level":30},
                  {"badges":4,"max_level":50},{"badges":6,"max_level":70},{"badges":8,"max_level":100}],
    # BW: Trio (#1 → 20), Bolt (#4 → 35), Jet (#6 → 50), Legend (#8 → 100 implied)
    "black":     [{"badges":0,"max_level":20},{"badges":2,"max_level":35},
                  {"badges":4,"max_level":50},{"badges":6,"max_level":65},{"badges":8,"max_level":100}],
    # XY: Bug (#1 → 25), Cliff (#2 → 40), Plant (#4 → 55), Psychic (#6 → 70)
    "x":         [{"badges":0,"max_level":10},{"badges":1,"max_level":25},
                  {"badges":2,"max_level":40},{"badges":4,"max_level":55},
                  {"badges":6,"max_level":70},{"badges":8,"max_level":100}],
    "sun":       [],  # No outsider-obedience mechanic in Gen 7
}
for _a, _b in [
    ("blue","red"),("yellow","red"),("firered","red"),("leafgreen","red"),
    ("silver","gold"),("crystal","gold"),("soulsilver","heartgold"),
    ("sapphire","ruby"),("emerald","ruby"),("omega-ruby","ruby"),("alpha-sapphire","ruby"),
    ("pearl","diamond"),("platinum","diamond"),
    ("white","black"),("black-2","black"),("white-2","black"),
    ("y","x"),
    ("moon","sun"),("ultra-sun","sun"),("ultra-moon","sun"),
]:
    BADGE_OBEDIENCE.setdefault(_a, BADGE_OBEDIENCE.get(_b, []))


# ── Trainer definitions ────────────────────────────────────────────────────────
# "class": gym_leader | elite_four | champion | rival | boss
# "page":  Bulbapedia article title (spaces handled by the API)

_KANTO_GYMS_RBY = [
    {"name":"Brock",     "class":"gym_leader","specialty":"rock",    "badge":"Boulder Badge","order":1,"page":"Brock"},
    {"name":"Misty",     "class":"gym_leader","specialty":"water",   "badge":"Cascade Badge","order":2,"page":"Misty"},
    {"name":"Lt. Surge", "class":"gym_leader","specialty":"electric","badge":"Thunder Badge","order":3,"page":"Lt. Surge"},
    {"name":"Erika",     "class":"gym_leader","specialty":"grass",   "badge":"Rainbow Badge","order":4,"page":"Erika"},
    {"name":"Koga",      "class":"gym_leader","specialty":"poison",  "badge":"Soul Badge",   "order":5,"page":"Koga"},
    {"name":"Sabrina",   "class":"gym_leader","specialty":"psychic", "badge":"Marsh Badge",  "order":6,"page":"Sabrina"},
    {"name":"Blaine",    "class":"gym_leader","specialty":"fire",    "badge":"Volcano Badge","order":7,"page":"Blaine"},
    {"name":"Giovanni",  "class":"gym_leader","specialty":"ground",  "badge":"Earth Badge",  "order":8,"page":"Giovanni"},
]
_KANTO_E4_RBY = [
    {"name":"Lorelei","class":"elite_four","specialty":"ice",     "order":1,"page":"Lorelei"},
    {"name":"Bruno",  "class":"elite_four","specialty":"fighting","order":2,"page":"Bruno (Elite Four)"},
    {"name":"Agatha", "class":"elite_four","specialty":"ghost",   "order":3,"page":"Agatha"},
    {"name":"Lance",  "class":"elite_four","specialty":"dragon",  "order":4,"page":"Lance (game)"},
    {"name":"Blue",   "class":"champion",  "specialty":"mixed",           "page":"Blue (game)"},
    {"name":"Gary",   "class":"rival",  "page":"Blue (game)",
     "rival_starter_map": {
         "charmander":"bulbasaur","charmeleon":"bulbasaur","charizard":"bulbasaur",
         "squirtle":"charmander","wartortle":"charmander","blastoise":"charmander",
         "bulbasaur":"squirtle","ivysaur":"squirtle","venusaur":"squirtle",
     }},
]

_JOHTO_GYMS = [
    {"name":"Falkner","class":"gym_leader","specialty":"flying",  "badge":"Zephyr Badge",  "order":1,"page":"Falkner"},
    {"name":"Bugsy",  "class":"gym_leader","specialty":"bug",     "badge":"Hive Badge",    "order":2,"page":"Bugsy"},
    {"name":"Whitney","class":"gym_leader","specialty":"normal",  "badge":"Plain Badge",   "order":3,"page":"Whitney"},
    {"name":"Morty",  "class":"gym_leader","specialty":"ghost",   "badge":"Fog Badge",     "order":4,"page":"Morty"},
    {"name":"Chuck",  "class":"gym_leader","specialty":"fighting","badge":"Storm Badge",   "order":5,"page":"Chuck"},
    {"name":"Jasmine","class":"gym_leader","specialty":"steel",   "badge":"Mineral Badge", "order":6,"page":"Jasmine"},
    {"name":"Pryce",  "class":"gym_leader","specialty":"ice",     "badge":"Glacier Badge", "order":7,"page":"Pryce"},
    {"name":"Clair",  "class":"gym_leader","specialty":"dragon",  "badge":"Rising Badge",  "order":8,"page":"Clair"},
]
_JOHTO_E4 = [
    {"name":"Will",  "class":"elite_four","specialty":"psychic", "order":1,"page":"Will (Elite Four)"},
    {"name":"Koga",  "class":"elite_four","specialty":"poison",  "order":2,"page":"Koga"},
    {"name":"Bruno", "class":"elite_four","specialty":"fighting","order":3,"page":"Bruno (Elite Four)"},
    {"name":"Karen", "class":"elite_four","specialty":"dark",    "order":4,"page":"Karen (Elite Four)"},
    {"name":"Lance", "class":"champion",  "specialty":"dragon",           "page":"Lance (game)"},
    {"name":"Silver","class":"rival",  "page":"Silver (game)",
     "rival_starter_map": {
         "cyndaquil":"chikorita","quilava":"chikorita","typhlosion":"chikorita",
         "totodile":"cyndaquil","croconaw":"cyndaquil","feraligatr":"cyndaquil",
         "chikorita":"totodile","bayleef":"totodile","meganium":"totodile",
     }},
]
_JOHTO_POSTGAME = [
    {"name": "Red", "class": "boss", "specialty": "mixed", "page": "Red (game)"},
]
_KANTO_GYMS_HGSS = [
    {"name":"Brock",     "class":"gym_leader","specialty":"rock",    "badge":"Boulder Badge","order":9, "page":"Brock",        "post_game":True,"region":"kanto"},
    {"name":"Misty",     "class":"gym_leader","specialty":"water",   "badge":"Cascade Badge","order":10,"page":"Misty",        "post_game":True,"region":"kanto"},
    {"name":"Lt. Surge", "class":"gym_leader","specialty":"electric","badge":"Thunder Badge","order":11,"page":"Lt. Surge",    "post_game":True,"region":"kanto"},
    {"name":"Erika",     "class":"gym_leader","specialty":"grass",   "badge":"Rainbow Badge","order":12,"page":"Erika",        "post_game":True,"region":"kanto"},
    {"name":"Janine",    "class":"gym_leader","specialty":"poison",  "badge":"Soul Badge",   "order":13,"page":"Janine",       "post_game":True,"region":"kanto"},
    {"name":"Sabrina",   "class":"gym_leader","specialty":"psychic", "badge":"Marsh Badge",  "order":14,"page":"Sabrina",      "post_game":True,"region":"kanto"},
    {"name":"Blaine",    "class":"gym_leader","specialty":"fire",    "badge":"Volcano Badge","order":15,"page":"Blaine",       "post_game":True,"region":"kanto"},
    {"name":"Blue",      "class":"gym_leader","specialty":"mixed",   "badge":"Earth Badge",  "order":16,"page":"Blue (game)", "post_game":True,"region":"kanto"},
]

_HOENN_GYMS = [
    {"name":"Roxanne",    "class":"gym_leader","specialty":"rock",    "badge":"Stone Badge",   "order":1,"page":"Roxanne"},
    {"name":"Brawly",     "class":"gym_leader","specialty":"fighting","badge":"Knuckle Badge", "order":2,"page":"Brawly"},
    {"name":"Wattson",    "class":"gym_leader","specialty":"electric","badge":"Dynamo Badge",  "order":3,"page":"Wattson"},
    {"name":"Flannery",   "class":"gym_leader","specialty":"fire",    "badge":"Heat Badge",    "order":4,"page":"Flannery"},
    {"name":"Norman",     "class":"gym_leader","specialty":"normal",  "badge":"Balance Badge", "order":5,"page":"Norman"},
    {"name":"Winona",     "class":"gym_leader","specialty":"flying",  "badge":"Feather Badge", "order":6,"page":"Winona"},
    {"name":"Tate & Liza","class":"gym_leader","specialty":"psychic", "badge":"Mind Badge",    "order":7,"page":"Tate and Liza"},
    {"name":"Wallace",    "class":"gym_leader","specialty":"water",   "badge":"Rain Badge",    "order":8,"page":"Wallace"},
]
_HOENN_E4_RS = [
    {"name":"Sidney", "class":"elite_four","specialty":"dark",   "order":1,"page":"Sidney"},
    {"name":"Phoebe", "class":"elite_four","specialty":"ghost",  "order":2,"page":"Phoebe"},
    {"name":"Glacia", "class":"elite_four","specialty":"ice",    "order":3,"page":"Glacia"},
    {"name":"Drake",  "class":"elite_four","specialty":"dragon", "order":4,"page":"Drake (Elite Four)"},
    {"name":"Steven", "class":"champion",  "specialty":"steel",           "page":"Steven Stone"},
    {"name":"Brendan","class":"rival",  "page":"Brendan",
     "rival_starter_map": {
         "torchic":"treecko","combusken":"treecko","blaziken":"treecko",
         "mudkip":"torchic","marshtomp":"torchic","swampert":"torchic",
         "treecko":"mudkip","grovyle":"mudkip","sceptile":"mudkip",
     }},
    {"name":"May",    "class":"rival",  "page":"May",
     "rival_starter_map": {
         "torchic":"treecko","combusken":"treecko","blaziken":"treecko",
         "mudkip":"torchic","marshtomp":"torchic","swampert":"torchic",
         "treecko":"mudkip","grovyle":"mudkip","sceptile":"mudkip",
     }},
]

_HOENN_EXTRA_MAGMA = [
    {"name": "Wally", "class": "rival", "page": "Wally"},
    {"name": "Maxie", "class": "boss", "specialty": "fire",  "page": "Maxie"},
]
_HOENN_EXTRA_AQUA = [
    {"name": "Wally", "class": "rival", "page": "Wally"},
    {"name": "Archie","class": "boss", "specialty": "water", "page": "Archie"},
]
_HOENN_EXTRA_EMERALD = [
    {"name": "Wally", "class": "rival", "page": "Wally"},
    {"name": "Maxie", "class": "boss", "specialty": "fire",  "page": "Maxie"},
    {"name": "Archie","class": "boss", "specialty": "water", "page": "Archie"},
]
_SINNOH_GYMS = [
    {"name":"Roark",        "class":"gym_leader","specialty":"rock",    "badge":"Coal Badge",    "order":1,"page":"Roark"},
    {"name":"Gardenia",     "class":"gym_leader","specialty":"grass",   "badge":"Forest Badge",  "order":2,"page":"Gardenia"},
    {"name":"Maylene",      "class":"gym_leader","specialty":"fighting","badge":"Cobble Badge",  "order":3,"page":"Maylene"},
    {"name":"Crasher Wake", "class":"gym_leader","specialty":"water",   "badge":"Fen Badge",     "order":4,"page":"Crasher Wake"},
    {"name":"Fantina",      "class":"gym_leader","specialty":"ghost",   "badge":"Relic Badge",   "order":5,"page":"Fantina"},
    {"name":"Byron",        "class":"gym_leader","specialty":"steel",   "badge":"Mine Badge",    "order":6,"page":"Byron"},
    {"name":"Candice",      "class":"gym_leader","specialty":"ice",     "badge":"Icicle Badge",  "order":7,"page":"Candice"},
    {"name":"Volkner",      "class":"gym_leader","specialty":"electric","badge":"Beacon Badge",  "order":8,"page":"Volkner"},
]
_SINNOH_E4 = [
    {"name":"Aaron",  "class":"elite_four","specialty":"bug",     "order":1,"page":"Aaron"},
    {"name":"Bertha", "class":"elite_four","specialty":"ground",  "order":2,"page":"Bertha"},
    {"name":"Flint",  "class":"elite_four","specialty":"fire",    "order":3,"page":"Flint (Elite Four)"},
    {"name":"Lucian", "class":"elite_four","specialty":"psychic", "order":4,"page":"Lucian"},
    {"name":"Cynthia","class":"champion",  "specialty":"mixed",           "page":"Cynthia"},
    {"name":"Barry",  "class":"rival",  "page":"Barry",
     "rival_starter_map": {
         "chimchar":"turtwig","monferno":"turtwig","infernape":"turtwig",
         "piplup":"chimchar","prinplup":"chimchar","empoleon":"chimchar",
         "turtwig":"piplup","grotle":"piplup","torterra":"piplup",
     }},
]

_SINNOH_BOSSES = [
    {"name": "Cyrus", "class": "boss", "specialty": "mixed", "page": "Cyrus"},
]
_UNOVA_GYMS_BW = [
    {"name":"Cilan / Chili / Cress","class":"gym_leader","specialty":"grass/fire/water","badge":"Trio Badge",  "order":1,"page":"Cilan"},
    {"name":"Lenora",  "class":"gym_leader","specialty":"normal",  "badge":"Basic Badge",  "order":2,"page":"Lenora"},
    {"name":"Burgh",   "class":"gym_leader","specialty":"bug",     "badge":"Insect Badge", "order":3,"page":"Burgh"},
    {"name":"Elesa",   "class":"gym_leader","specialty":"electric","badge":"Bolt Badge",   "order":4,"page":"Elesa"},
    {"name":"Clay",    "class":"gym_leader","specialty":"ground",  "badge":"Quake Badge",  "order":5,"page":"Clay"},
    {"name":"Skyla",   "class":"gym_leader","specialty":"flying",  "badge":"Jet Badge",    "order":6,"page":"Skyla"},
    {"name":"Brycen",  "class":"gym_leader","specialty":"ice",     "badge":"Freeze Badge", "order":7,"page":"Brycen"},
    {"name":"Iris / Drayden","class":"gym_leader","specialty":"dragon","badge":"Legend Badge","order":8,"page":"Iris"},
]
_UNOVA_E4_BW = [
    {"name":"Shauntal","class":"elite_four","specialty":"ghost",   "order":1,"page":"Shauntal"},
    {"name":"Marshal", "class":"elite_four","specialty":"fighting","order":2,"page":"Marshal"},
    {"name":"Grimsley","class":"elite_four","specialty":"dark",    "order":3,"page":"Grimsley"},
    {"name":"Caitlin", "class":"elite_four","specialty":"psychic", "order":4,"page":"Caitlin"},
    {"name":"Alder",   "class":"champion",  "specialty":"mixed",           "page":"Alder"},
    {"name":"Cheren",  "class":"rival",                                    "page":"Cheren"},
    {"name":"Bianca",  "class":"rival",                                    "page":"Bianca"},
    {"name":"N",       "class":"boss",      "specialty":"mixed",           "page":"N"},
    {"name":"Ghetsis", "class":"boss",      "specialty":"mixed",           "page":"Ghetsis"},
]
_UNOVA_E4_BW2 = [
    {"name":"Shauntal","class":"elite_four","specialty":"ghost",   "order":1,"page":"Shauntal"},
    {"name":"Marshal", "class":"elite_four","specialty":"fighting","order":2,"page":"Marshal"},
    {"name":"Grimsley","class":"elite_four","specialty":"dark",    "order":3,"page":"Grimsley"},
    {"name":"Caitlin", "class":"elite_four","specialty":"psychic", "order":4,"page":"Caitlin"},
    {"name":"Iris",    "class":"champion",  "specialty":"dragon",           "page":"Iris"},
    {"name":"Hugh",    "class":"rival",                                     "page":"Hugh"},
    {"name":"N",       "class":"boss",      "specialty":"mixed",            "page":"N"},
    {"name":"Ghetsis", "class":"boss",      "specialty":"mixed",            "page":"Ghetsis"},
]

_KALOS_GYMS = [
    {"name":"Viola",   "class":"gym_leader","specialty":"bug",     "badge":"Bug Badge",     "order":1,"page":"Viola"},
    {"name":"Grant",   "class":"gym_leader","specialty":"rock",    "badge":"Cliff Badge",   "order":2,"page":"Grant"},
    {"name":"Korrina", "class":"gym_leader","specialty":"fighting","badge":"Rumble Badge",  "order":3,"page":"Korrina"},
    {"name":"Ramos",   "class":"gym_leader","specialty":"grass",   "badge":"Plant Badge",   "order":4,"page":"Ramos"},
    {"name":"Clemont", "class":"gym_leader","specialty":"electric","badge":"Voltage Badge", "order":5,"page":"Clemont"},
    {"name":"Valerie", "class":"gym_leader","specialty":"fairy",   "badge":"Fairy Badge",   "order":6,"page":"Valerie"},
    {"name":"Olympia", "class":"gym_leader","specialty":"psychic", "badge":"Psychic Badge", "order":7,"page":"Olympia"},
    {"name":"Wulfric", "class":"gym_leader","specialty":"ice",     "badge":"Iceberg Badge", "order":8,"page":"Wulfric"},
]
_KALOS_E4 = [
    {"name":"Malva",   "class":"elite_four","specialty":"fire",   "order":1,"page":"Malva"},
    {"name":"Siebold", "class":"elite_four","specialty":"water",  "order":2,"page":"Siebold"},
    {"name":"Wikstrom","class":"elite_four","specialty":"steel",  "order":3,"page":"Wikstrom"},
    {"name":"Drasna",  "class":"elite_four","specialty":"dragon", "order":4,"page":"Drasna"},
    {"name":"Diantha", "class":"champion",  "specialty":"mixed",           "page":"Diantha"},
    {"name":"Calem",   "class":"rival",  "page":"Calem",
     "rival_starter_map": {
         "fennekin":"chespin","braixen":"chespin","delphox":"chespin",
         "froakie":"fennekin","frogadier":"fennekin","greninja":"fennekin",
         "chespin":"froakie","quilladin":"froakie","chesnaught":"froakie",
     }},
    {"name":"Serena",  "class":"rival",  "page":"Serena",
     "rival_starter_map": {
         "fennekin":"chespin","braixen":"chespin","delphox":"chespin",
         "froakie":"fennekin","frogadier":"fennekin","greninja":"fennekin",
         "chespin":"froakie","quilladin":"froakie","chesnaught":"froakie",
     }},
    {"name":"Lysandre","class":"boss",      "specialty":"fire",             "page":"Lysandre"},
]

# Gen 7: trial captains + island kahunas (mapped as gym_leader for consistency)
_ALOLA_CAPTAINS = [
    {"name":"Ilima",    "class":"gym_leader","specialty":"normal",  "badge":"Normalium Z",  "order":1,"page":"Ilima"},
    {"name":"Lana",     "class":"gym_leader","specialty":"water",   "badge":"Waterium Z",   "order":2,"page":"Lana"},
    {"name":"Kiawe",    "class":"gym_leader","specialty":"fire",    "badge":"Firium Z",     "order":3,"page":"Kiawe"},
    {"name":"Mallow",   "class":"gym_leader","specialty":"grass",   "badge":"Grassium Z",   "order":4,"page":"Mallow"},
    {"name":"Sophocles","class":"gym_leader","specialty":"electric","badge":"Electrium Z",  "order":5,"page":"Sophocles"},
    {"name":"Acerola",  "class":"gym_leader","specialty":"ghost",   "badge":"Ghostium Z",   "order":6,"page":"Acerola"},
    {"name":"Mina",     "class":"gym_leader","specialty":"fairy",   "badge":"Fairium Z",    "order":7,"page":"Mina"},
    {"name":"Hapu",     "class":"gym_leader","specialty":"ground",  "badge":"Groundium Z",  "order":8,"page":"Hapu"},
]
_ALOLA_E4 = [
    {"name":"Molayne", "class":"elite_four","specialty":"steel",  "order":1,"page":"Molayne"},
    {"name":"Olivia",  "class":"elite_four","specialty":"rock",   "order":2,"page":"Olivia"},
    {"name":"Acerola", "class":"elite_four","specialty":"ghost",  "order":3,"page":"Acerola"},
    {"name":"Kahili",  "class":"elite_four","specialty":"flying", "order":4,"page":"Kahili"},
    {"name":"Kukui",   "class":"champion",  "specialty":"mixed",           "page":"Professor Kukui"},
    {"name":"Hau",     "class":"rival",  "page":"Hau",
     "rival_starter_map": {
         "popplio":"rowlet","brionne":"rowlet","primarina":"rowlet",
         "rowlet":"litten","dartrix":"litten","decidueye":"litten",
         "litten":"popplio","torracat":"popplio","incineroar":"popplio",
     }},
    {"name":"Gladion", "class":"rival",                                    "page":"Gladion"},
    {"name":"Guzma",   "class":"boss",      "specialty":"bug",             "page":"Guzma"},
    {"name":"Lusamine","class":"boss",      "specialty":"mixed",           "page":"Lusamine"},
]

TRAINER_DEFS: dict[str, list[dict]] = {
    "red":          _KANTO_GYMS_RBY + _KANTO_E4_RBY,
    "blue":         _KANTO_GYMS_RBY + _KANTO_E4_RBY,
    "yellow":       _KANTO_GYMS_RBY + _KANTO_E4_RBY,
    "firered":      _KANTO_GYMS_RBY + _KANTO_E4_RBY,
    "leafgreen":    _KANTO_GYMS_RBY + _KANTO_E4_RBY,
    "gold":         _JOHTO_GYMS + _JOHTO_E4 + _JOHTO_POSTGAME,
    "silver":       _JOHTO_GYMS + _JOHTO_E4 + _JOHTO_POSTGAME,
    "crystal":      _JOHTO_GYMS + _JOHTO_E4 + _JOHTO_POSTGAME,
    "heartgold":    _JOHTO_GYMS + _KANTO_GYMS_HGSS + _JOHTO_E4 + _JOHTO_POSTGAME,
    "soulsilver":   _JOHTO_GYMS + _KANTO_GYMS_HGSS + _JOHTO_E4 + _JOHTO_POSTGAME,
    "ruby":          _HOENN_GYMS + _HOENN_E4_RS + _HOENN_EXTRA_MAGMA,
    "sapphire":      _HOENN_GYMS + _HOENN_E4_RS + _HOENN_EXTRA_AQUA,
    "omega-ruby":    _HOENN_GYMS + _HOENN_E4_RS + _HOENN_EXTRA_MAGMA,
    "alpha-sapphire":_HOENN_GYMS + _HOENN_E4_RS + _HOENN_EXTRA_AQUA,
    "emerald": [
        *[{**t, "name":"Juan", "page":"Juan"} if t["name"] == "Wallace" else t
          for t in _HOENN_GYMS],
        {"name":"Sidney",  "class":"elite_four","specialty":"dark",   "order":1,"page":"Sidney"},
        {"name":"Phoebe",  "class":"elite_four","specialty":"ghost",  "order":2,"page":"Phoebe"},
        {"name":"Glacia",  "class":"elite_four","specialty":"ice",    "order":3,"page":"Glacia"},
        {"name":"Drake",   "class":"elite_four","specialty":"dragon", "order":4,"page":"Drake (Elite Four)"},
        {"name":"Wallace", "class":"champion",  "specialty":"water",           "page":"Wallace"},
        {"name":"Brendan", "class":"rival",  "page":"Brendan",
         "rival_starter_map": {
             "torchic":"treecko","combusken":"treecko","blaziken":"treecko",
             "mudkip":"torchic","marshtomp":"torchic","swampert":"torchic",
             "treecko":"mudkip","grovyle":"mudkip","sceptile":"mudkip",
         }},
        {"name":"May",     "class":"rival",  "page":"May",
         "rival_starter_map": {
             "torchic":"treecko","combusken":"treecko","blaziken":"treecko",
             "mudkip":"torchic","marshtomp":"torchic","swampert":"torchic",
             "treecko":"mudkip","grovyle":"mudkip","sceptile":"mudkip",
         }},
        *_HOENN_EXTRA_EMERALD,
    ],
    "diamond":      _SINNOH_GYMS + _SINNOH_E4 + _SINNOH_BOSSES,
    "pearl":        _SINNOH_GYMS + _SINNOH_E4 + _SINNOH_BOSSES,
    "platinum":     _SINNOH_GYMS + _SINNOH_E4 + _SINNOH_BOSSES,
    "black":        _UNOVA_GYMS_BW + _UNOVA_E4_BW,
    "white":        _UNOVA_GYMS_BW + _UNOVA_E4_BW,
    "black-2":      _UNOVA_GYMS_BW + _UNOVA_E4_BW2,
    "white-2":      _UNOVA_GYMS_BW + _UNOVA_E4_BW2,
    "x":            _KALOS_GYMS + _KALOS_E4,
    "y":            _KALOS_GYMS + _KALOS_E4,
    "sun":          _ALOLA_CAPTAINS + _ALOLA_E4,
    "moon":         _ALOLA_CAPTAINS + _ALOLA_E4,
    "ultra-sun":    _ALOLA_CAPTAINS + _ALOLA_E4,
    "ultra-moon":   _ALOLA_CAPTAINS + _ALOLA_E4,
}


# ── Static per-game data ───────────────────────────────────────────────────────

GAME_STATIC: dict[str, dict] = {
    "heartgold": {
        "starters": [
            {"pokemon":"chikorita","pokemon_id":152,"note":"Choose one at start"},
            {"pokemon":"cyndaquil","pokemon_id":155,"note":"Choose one at start"},
            {"pokemon":"totodile", "pokemon_id":158,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"gyarados",  "pokemon_id":130,"level":30,"location":"lake-of-rage","always_shiny":True,
             "note":"Red Gyarados — scripted shiny"},
            {"pokemon":"snorlax",   "pokemon_id":143,"level":50,"location":"route-11",
             "note":"Requires Poké Flute or Radio Poké Flute channel"},
            {"pokemon":"snorlax",   "pokemon_id":143,"level":50,"location":"route-12",
             "note":"Requires Poké Flute or Radio Poké Flute channel"},
            {"pokemon":"sudowoodo", "pokemon_id":185,"level":20,"location":"route-36",
             "note":"Requires Squirtbottle from Goldenrod flower shop"},
            # Ho-Oh: lv45 primary in HG, lv70 secondary in SS (both catchable in both versions)
            {"pokemon":"ho-oh","pokemon_id":250,"level":45,"location":"bell-tower",
             "version_native":"heartgold","note":"Requires Rainbow Wing; lv45 in HG, lv70 in SS"},
            {"pokemon":"ho-oh","pokemon_id":250,"level":70,"location":"bell-tower",
             "version_native":"soulsilver","note":"Secondary legendary in SS; requires Rainbow Wing"},
            # Lugia: lv45 primary in SS, lv70 secondary in HG
            {"pokemon":"lugia","pokemon_id":249,"level":45,"location":"whirl-islands",
             "version_native":"soulsilver","note":"Requires Silver Wing; lv45 in SS, lv70 in HG"},
            {"pokemon":"lugia","pokemon_id":249,"level":70,"location":"whirl-islands",
             "version_native":"heartgold","note":"Secondary legendary in HG; requires Silver Wing"},
            {"pokemon":"entei",   "pokemon_id":244,"level":40,"location":"johto","roaming":True,
             "note":"Roams Johto after the Burned Tower trio is released"},
            {"pokemon":"raikou",  "pokemon_id":243,"level":40,"location":"johto","roaming":True,
             "note":"Roams Johto after the Burned Tower trio is released"},
            {"pokemon":"suicune", "pokemon_id":245,"level":40,"location":"route-25",
             "note":"Appears at multiple fixed locations; final catchable encounter at Route 25"},
            # Groudon is HG-native; Kyogre is SS-native. Each requires trading the other
            # game's legend to Mr. Pokemon to receive the corresponding Orb.
            {"pokemon":"groudon","pokemon_id":383,"level":50,"location":"embedded-tower",
             "version_native":"heartgold","note":"Red Orb from Mr. Pokemon after showing Kyogre (SS)"},
            {"pokemon":"kyogre", "pokemon_id":382,"level":50,"location":"embedded-tower",
             "version_native":"soulsilver","note":"Blue Orb from Mr. Pokemon after showing Groudon (HG)"},
            {"pokemon":"rayquaza","pokemon_id":384,"level":50,"location":"embedded-tower",
             "note":"Appears after both Groudon and Kyogre are in the party simultaneously"},
            {"pokemon":"mewtwo",  "pokemon_id":150,"level":70,"location":"cerulean-cave","note":"Post-game Kanto"},
            {"pokemon":"articuno","pokemon_id":144,"level":50,"location":"seafoam-islands","note":"Post-game Kanto"},
            {"pokemon":"zapdos",  "pokemon_id":145,"level":50,"location":"power-plant","note":"Post-game Kanto"},
            {"pokemon":"moltres", "pokemon_id":146,"level":50,"location":"mt-silver","note":"Post-game"},
        ],
        "gift_pokemon": [
            {"pokemon":"togepi",  "pokemon_id":175,"level":1, "location":"mr-pokemons-house",
             "source":"Mr. Pokémon (Egg)","note":"Hatch the Mystery Egg received from Elm's errand"},
            {"pokemon":"eevee",   "pokemon_id":133,"level":5, "location":"goldenrod-city","source":"Bill"},
            {"pokemon":"tyrogue", "pokemon_id":236,"level":10,"location":"mt-mortar","source":"Karate King"},
            {"pokemon":"spearow", "pokemon_id":21, "level":20,"location":"route-35",
             "source":"Pokémon Ranger (holds Mail)"},
            {"pokemon":"dratini", "pokemon_id":147,"level":15,"location":"blackthorn-city",
             "source":"Dragon's Den quiz reward"},
            {"pokemon":"larvitar","pokemon_id":246,"level":1, "location":"mt-silver",
             "source":"Riley (Egg)","note":"Post-game"},
        ],
        "in_game_trades": [
            {"give_pokemon":"bellsprout","give_pokemon_id":69,
             "receive_pokemon":"onix",   "receive_pokemon_id":95, "receive_level":5,
             "npc":"Schoolboy Jack","location":"violet-city"},
            {"give_pokemon":"drowzee","give_pokemon_id":96,
             "receive_pokemon":"machop","receive_pokemon_id":66,  "receive_level":5,
             "npc":"Trainer","location":"goldenrod-city"},
            {"give_pokemon":"krabby","give_pokemon_id":98,
             "receive_pokemon":"voltorb","receive_pokemon_id":100,"receive_level":5,
             "npc":"Fisher","location":"olivine-city"},
        ],
    },

    "red": {
        "starters": [
            {"pokemon":"bulbasaur", "pokemon_id":1,"note":"Choose one at start"},
            {"pokemon":"charmander","pokemon_id":4,"note":"Choose one at start"},
            {"pokemon":"squirtle",  "pokemon_id":7,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"snorlax","pokemon_id":143,"level":30,"location":"route-12",
             "note":"Requires Poké Flute"},
            {"pokemon":"snorlax","pokemon_id":143,"level":30,"location":"route-16",
             "note":"Requires Poké Flute"},
            {"pokemon":"articuno","pokemon_id":144,"level":50,"location":"seafoam-islands"},
            {"pokemon":"zapdos",  "pokemon_id":145,"level":50,"location":"power-plant"},
            # Moltres is at Victory Road in RBY; it was moved to Mt. Ember in FRLG
            {"pokemon":"moltres",  "pokemon_id":146,"level":50,"location":"victory-road"},
            {"pokemon":"mewtwo",   "pokemon_id":150,"level":70,"location":"cerulean-cave"},
        ],
        "gift_pokemon": [
            # One-time room pickup (NOT a Game Corner prize — those are Porygon/Scyther/Pinsir)
            {"pokemon":"eevee",    "pokemon_id":133,"level":25,"location":"celadon-city",
             "source":"One-time pickup in Celadon Mansion top floor"},
            {"pokemon":"lapras",   "pokemon_id":131,"level":15,"location":"silph-co",
             "source":"NPC gift on 7F of Silph Co."},
            # Only one of Dome/Helix can be taken; both revived at Cinnabar Lab (not Pallet Town)
            {"pokemon":"aerodactyl","pokemon_id":142,"level":30,"location":"cinnabar-island",
             "source":"Old Amber (from scientist in Pewter Museum)"},
            {"pokemon":"omanyte",  "pokemon_id":138,"level":30,"location":"cinnabar-island",
             "source":"Dome Fossil — mutually exclusive with Helix Fossil"},
            {"pokemon":"kabuto",   "pokemon_id":140,"level":30,"location":"cinnabar-island",
             "source":"Helix Fossil — mutually exclusive with Dome Fossil"},
        ],
        "in_game_trades": [
            # Route 2 south gate: Nidoran-F for Nidoran-M nicknamed MARC
            {"give_pokemon":"nidoran-f","give_pokemon_id":29,
             "receive_pokemon":"nidoran-m","receive_pokemon_id":32,"receive_nickname":"MARC",
             "npc":"Trader","location":"route-2"},
            # Cerulean City: Poliwhirl for Jynx nicknamed LOLA
            {"give_pokemon":"poliwhirl","give_pokemon_id":61,
             "receive_pokemon":"jynx","receive_pokemon_id":124,"receive_nickname":"LOLA",
             "npc":"Girl","location":"cerulean-city"},
            # Vermilion City: Spearow for Farfetch'd nicknamed DUX
            {"give_pokemon":"spearow","give_pokemon_id":21,
             "receive_pokemon":"farfetchd","receive_pokemon_id":83,"receive_nickname":"DUX",
             "npc":"Sailor","location":"vermilion-city"},
        ],
    },

    "yellow": {
        "starters": [
            # Yellow has no starter choice — Pikachu is forced
            {"pokemon":"pikachu","pokemon_id":25,"note":"Forced starter — no choice given"},
        ],
        "static_encounters": [
            {"pokemon":"snorlax","pokemon_id":143,"level":30,"location":"route-12",
             "note":"Requires Poké Flute"},
            {"pokemon":"snorlax","pokemon_id":143,"level":30,"location":"route-16",
             "note":"Requires Poké Flute"},
            {"pokemon":"articuno","pokemon_id":144,"level":50,"location":"seafoam-islands"},
            {"pokemon":"zapdos",  "pokemon_id":145,"level":50,"location":"power-plant"},
            {"pokemon":"moltres", "pokemon_id":146,"level":50,"location":"victory-road"},
            {"pokemon":"mewtwo",  "pokemon_id":150,"level":70,"location":"cerulean-cave"},
        ],
        "gift_pokemon": [
            # The three Kanto starters are NPC gifts in Yellow rather than the opening choice
            {"pokemon":"bulbasaur", "pokemon_id":1,  "level":10,"location":"cerulean-city",
             "source":"Melanie (requires Pikachu sufficiently happy)"},
            {"pokemon":"charmander","pokemon_id":4,  "level":10,"location":"route-24",
             "source":"Damian (requires Pikachu sufficiently happy)"},
            {"pokemon":"squirtle",  "pokemon_id":7,  "level":10,"location":"vermilion-city",
             "source":"Officer Jenny (requires Pikachu sufficiently happy)"},
            {"pokemon":"eevee",    "pokemon_id":133,"level":25,"location":"celadon-city",
             "source":"One-time pickup in Celadon Mansion top floor"},
            {"pokemon":"lapras",   "pokemon_id":131,"level":15,"location":"silph-co",
             "source":"NPC gift on 7F of Silph Co."},
            {"pokemon":"aerodactyl","pokemon_id":142,"level":30,"location":"cinnabar-island",
             "source":"Old Amber (from scientist in Pewter Museum)"},
            {"pokemon":"omanyte",  "pokemon_id":138,"level":30,"location":"cinnabar-island",
             "source":"Dome Fossil — mutually exclusive with Helix Fossil"},
            {"pokemon":"kabuto",   "pokemon_id":140,"level":30,"location":"cinnabar-island",
             "source":"Helix Fossil — mutually exclusive with Dome Fossil"},
        ],
        "in_game_trades": [],
    },

    "firered": {
        "starters": [
            {"pokemon":"bulbasaur", "pokemon_id":1,"note":"Choose one at start"},
            {"pokemon":"charmander","pokemon_id":4,"note":"Choose one at start"},
            {"pokemon":"squirtle",  "pokemon_id":7,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"snorlax","pokemon_id":143,"level":30,"location":"route-12",
             "note":"Requires Poké Flute"},
            {"pokemon":"snorlax","pokemon_id":143,"level":30,"location":"route-16",
             "note":"Requires Poké Flute"},
            {"pokemon":"articuno","pokemon_id":144,"level":50,"location":"seafoam-islands"},
            {"pokemon":"zapdos",  "pokemon_id":145,"level":50,"location":"power-plant"},
            # Moved from Victory Road (RBY) to Mt. Ember on One Island in FRLG
            {"pokemon":"moltres", "pokemon_id":146,"level":50,"location":"mt-ember",
             "note":"Mt. Ember on One Island — not Victory Road as in the original games"},
            {"pokemon":"mewtwo",  "pokemon_id":150,"level":70,"location":"cerulean-cave"},
            # Post-National Pokédex: exactly one beast roams Kanto per file based on starter
            {"pokemon":"raikou","pokemon_id":243,"level":50,"location":"kanto","roaming":True,
             "note":"Roams Kanto post-National Pokédex if Squirtle was the chosen starter"},
            {"pokemon":"entei", "pokemon_id":244,"level":50,"location":"kanto","roaming":True,
             "note":"Roams Kanto post-National Pokédex if Bulbasaur was the chosen starter"},
            {"pokemon":"suicune","pokemon_id":245,"level":50,"location":"kanto","roaming":True,
             "note":"Roams Kanto post-National Pokédex if Charmander was the chosen starter"},
        ],
        "gift_pokemon": [
            {"pokemon":"eevee",    "pokemon_id":133,"level":25,"location":"celadon-city",
             "source":"One-time pickup in Celadon Mansion top floor"},
            {"pokemon":"lapras",   "pokemon_id":131,"level":15,"location":"silph-co",
             "source":"NPC gift on 7F of Silph Co."},
            {"pokemon":"aerodactyl","pokemon_id":142,"level":30,"location":"cinnabar-island",
             "source":"Old Amber (from scientist in Pewter Museum)"},
            {"pokemon":"omanyte",  "pokemon_id":138,"level":30,"location":"cinnabar-island",
             "source":"Dome Fossil — mutually exclusive with Helix Fossil"},
            {"pokemon":"kabuto",   "pokemon_id":140,"level":30,"location":"cinnabar-island",
             "source":"Helix Fossil — mutually exclusive with Dome Fossil"},
        ],
        "in_game_trades": [],
    },

    "gold": {
        "starters": [
            {"pokemon":"chikorita","pokemon_id":152,"note":"Choose one at start"},
            {"pokemon":"cyndaquil","pokemon_id":155,"note":"Choose one at start"},
            {"pokemon":"totodile", "pokemon_id":158,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"gyarados",  "pokemon_id":130,"level":30,"location":"lake-of-rage",
             "always_shiny":True,"note":"Red Gyarados — scripted shiny"},
            {"pokemon":"snorlax",   "pokemon_id":143,"level":50,"location":"route-11",
             "note":"Requires Poké Flute radio channel"},
            {"pokemon":"snorlax",   "pokemon_id":143,"level":50,"location":"route-12",
             "note":"Requires Poké Flute radio channel"},
            {"pokemon":"sudowoodo", "pokemon_id":185,"level":20,"location":"route-36",
             "note":"Requires Squirtbottle from Goldenrod flower shop"},
            {"pokemon":"ho-oh",    "pokemon_id":250,"level":40,"location":"bell-tower",
             "version_native":"gold","note":"Requires Rainbow Wing from Elder of Ecruteak City"},
            {"pokemon":"lugia",    "pokemon_id":249,"level":40,"location":"whirl-islands",
             "version_native":"silver","note":"Requires Silver Wing from Radio Tower director"},
            {"pokemon":"raikou",   "pokemon_id":243,"level":40,"location":"johto",
             "roaming":True,"note":"Roams Johto after Burned Tower trio is released"},
            {"pokemon":"entei",    "pokemon_id":244,"level":40,"location":"johto",
             "roaming":True,"note":"Roams Johto after Burned Tower trio is released"},
            {"pokemon":"suicune",  "pokemon_id":245,"level":40,"location":"route-25",
             "note":"Roams Johto in G/S; Crystal has fixed appearances before Route 25 final encounter"},
            {"pokemon":"mewtwo",   "pokemon_id":150,"level":70,"location":"cerulean-cave",
             "note":"Post-game Kanto"},
            {"pokemon":"articuno", "pokemon_id":144,"level":50,"location":"seafoam-islands",
             "note":"Post-game Kanto"},
            {"pokemon":"zapdos",   "pokemon_id":145,"level":50,"location":"power-plant",
             "note":"Post-game Kanto"},
            {"pokemon":"moltres",  "pokemon_id":146,"level":50,"location":"mt-silver",
             "note":"Post-game; Mt. Silver in G/S/C (moved from Victory Road in RBY)"},
        ],
        "gift_pokemon": [
            {"pokemon":"togepi",  "pokemon_id":175,"level":1, "location":"mr-pokemons-house",
             "source":"Mr. Pokémon (Egg)","note":"Mystery Egg delivered to Prof. Elm; hatches into Togepi"},
            {"pokemon":"eevee",   "pokemon_id":133,"level":5, "location":"goldenrod-city",
             "source":"Bill"},
            {"pokemon":"tyrogue", "pokemon_id":236,"level":10,"location":"mt-mortar",
             "source":"Karate King"},
            {"pokemon":"dratini", "pokemon_id":147,"level":15,"location":"blackthorn-city",
             "source":"Dragon's Den quiz reward"},
        ],
        "in_game_trades": [
            {"give_pokemon":"bellsprout","give_pokemon_id":69,
             "receive_pokemon":"onix",   "receive_pokemon_id":95, "receive_level":5,
             "npc":"Schoolboy Jack","location":"violet-city"},
            {"give_pokemon":"drowzee",   "give_pokemon_id":96,
             "receive_pokemon":"machop", "receive_pokemon_id":66, "receive_level":5,
             "npc":"Trainer","location":"goldenrod-city"},
            {"give_pokemon":"krabby",    "give_pokemon_id":98,
             "receive_pokemon":"voltorb","receive_pokemon_id":100,"receive_level":5,
             "npc":"Fisher","location":"olivine-city"},
        ],
    },

    "crystal": {
        "starters": [
            {"pokemon":"chikorita","pokemon_id":152,"note":"Choose one at start"},
            {"pokemon":"cyndaquil","pokemon_id":155,"note":"Choose one at start"},
            {"pokemon":"totodile", "pokemon_id":158,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"gyarados",  "pokemon_id":130,"level":30,"location":"lake-of-rage",
             "always_shiny":True,"note":"Red Gyarados — scripted shiny"},
            {"pokemon":"snorlax",   "pokemon_id":143,"level":50,"location":"route-11",
             "note":"Requires Poké Flute radio channel"},
            {"pokemon":"snorlax",   "pokemon_id":143,"level":50,"location":"route-12",
             "note":"Requires Poké Flute radio channel"},
            {"pokemon":"sudowoodo", "pokemon_id":185,"level":20,"location":"route-36",
             "note":"Requires Squirtbottle from Goldenrod flower shop"},
            # Ho-Oh and Lugia are both obtainable in Crystal at lv60 (vs lv40 in G/S)
            {"pokemon":"ho-oh",    "pokemon_id":250,"level":60,"location":"bell-tower",
             "note":"Requires Rainbow Wing; only available after defeating the Elite Four"},
            {"pokemon":"lugia",    "pokemon_id":249,"level":60,"location":"whirl-islands",
             "note":"Requires Silver Wing from Radio Tower director"},
            {"pokemon":"raikou",   "pokemon_id":243,"level":40,"location":"johto",
             "roaming":True,"note":"Roams Johto after Burned Tower trio is released"},
            {"pokemon":"entei",    "pokemon_id":244,"level":40,"location":"johto",
             "roaming":True,"note":"Roams Johto after Burned Tower trio is released"},
            # Suicune: Crystal replaces roaming behaviour with a fixed 4-encounter sequence.
            # First three appearances are scripted cutscenes (not catchable).
            {"pokemon":"suicune",  "pokemon_id":245,"level":40,"location":"cianwood-city",
             "note":"Scripted appearance — not catchable; first of 4 Crystal-exclusive encounters"},
            {"pokemon":"suicune",  "pokemon_id":245,"level":40,"location":"mt-mortar",
             "note":"Scripted appearance — not catchable; second Crystal encounter (Route 42 entrance)"},
            {"pokemon":"suicune",  "pokemon_id":245,"level":40,"location":"vermilion-city",
             "note":"Scripted appearance — not catchable; third Crystal encounter (Kanto)"},
            {"pokemon":"suicune",  "pokemon_id":245,"level":40,"location":"route-25",
             "note":"Final catchable encounter; preceded by three scripted appearances earlier in the game"},
            {"pokemon":"mewtwo",   "pokemon_id":150,"level":70,"location":"cerulean-cave",
             "note":"Post-game Kanto"},
            {"pokemon":"articuno", "pokemon_id":144,"level":50,"location":"seafoam-islands",
             "note":"Post-game Kanto"},
            {"pokemon":"zapdos",   "pokemon_id":145,"level":50,"location":"power-plant",
             "note":"Post-game Kanto"},
            {"pokemon":"moltres",  "pokemon_id":146,"level":50,"location":"mt-silver",
             "note":"Post-game; Mt. Silver in G/S/C (moved from Victory Road in RBY)"},
        ],
        "gift_pokemon": [
            {"pokemon":"togepi",  "pokemon_id":175,"level":1, "location":"mr-pokemons-house",
             "source":"Mr. Pokémon (Egg)","note":"Mystery Egg delivered to Prof. Elm; hatches into Togepi"},
            {"pokemon":"eevee",   "pokemon_id":133,"level":5, "location":"goldenrod-city",
             "source":"Bill"},
            {"pokemon":"tyrogue", "pokemon_id":236,"level":10,"location":"mt-mortar",
             "source":"Karate King"},
            {"pokemon":"dratini", "pokemon_id":147,"level":15,"location":"blackthorn-city",
             "source":"Dragon's Den quiz reward"},
        ],
        "in_game_trades": [
            {"give_pokemon":"bellsprout","give_pokemon_id":69,
             "receive_pokemon":"onix",   "receive_pokemon_id":95, "receive_level":5,
             "npc":"Schoolboy Jack","location":"violet-city"},
            {"give_pokemon":"drowzee",   "give_pokemon_id":96,
             "receive_pokemon":"machop", "receive_pokemon_id":66, "receive_level":5,
             "npc":"Trainer","location":"goldenrod-city"},
            {"give_pokemon":"krabby",    "give_pokemon_id":98,
             "receive_pokemon":"voltorb","receive_pokemon_id":100,"receive_level":5,
             "npc":"Fisher","location":"olivine-city"},
        ],
    },

    "ruby": {
        "starters": [
            {"pokemon":"treecko","pokemon_id":252,"note":"Choose one at start"},
            {"pokemon":"torchic","pokemon_id":255,"note":"Choose one at start"},
            {"pokemon":"mudkip", "pokemon_id":258,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"groudon",  "pokemon_id":383,"level":45,"location":"cave-of-origin",
             "version_native":"ruby",
             "note":"lv45 in RS; lv70 in Emerald (Terra Cave roaming post-story)"},
            {"pokemon":"kyogre",   "pokemon_id":382,"level":45,"location":"cave-of-origin",
             "version_native":"sapphire",
             "note":"lv45 in RS; lv70 in Emerald (Marine Cave roaming post-story)"},
            {"pokemon":"rayquaza", "pokemon_id":384,"level":70,"location":"sky-pillar",
             "note":"Sky Pillar roof; accessible after the Sootopolis story arc"},
            {"pokemon":"regirock", "pokemon_id":377,"level":40,"location":"route-111",
             "note":"Desert Ruins (Route 111 desert); requires Relicanth + Wailord Sealed Chamber puzzle"},
            {"pokemon":"regice",   "pokemon_id":378,"level":40,"location":"route-105",
             "note":"Island Cave (Route 105); requires Sealed Chamber puzzle"},
            {"pokemon":"registeel","pokemon_id":379,"level":40,"location":"route-120",
             "note":"Ancient Tomb (Route 120); requires Sealed Chamber puzzle"},
            {"pokemon":"latias",   "pokemon_id":380,"level":40,"location":"hoenn",
             "roaming":True,"version_native":"ruby",
             "note":"Roams Hoenn post-credits in Ruby; Latios roams in Sapphire"},
            {"pokemon":"latios",   "pokemon_id":381,"level":40,"location":"hoenn",
             "roaming":True,"version_native":"sapphire",
             "note":"Roams Hoenn post-credits in Sapphire; Latias roams in Ruby"},
        ],
        "gift_pokemon": [
            {"pokemon":"castform","pokemon_id":351,"level":25,"location":"route-119",
             "source":"Weather Institute researcher (after clearing Team Aqua/Magma)"},
            {"pokemon":"wynaut",  "pokemon_id":360,"level":1, "location":"lavaridge-town",
             "source":"Old lady in Lavaridge Town hot springs (Egg)"},
            {"pokemon":"beldum",  "pokemon_id":374,"level":5, "location":"mossdeep-city",
             "source":"Steven's house (post-game)"},
            {"pokemon":"lileep",  "pokemon_id":345,"level":20,"location":"rustboro-city",
             "source":"Root Fossil revived at Devon Corporation",
             "version_native":"ruby","note":"Root Fossil from Mirage Tower desert; Claw Fossil in Sapphire"},
            {"pokemon":"anorith", "pokemon_id":347,"level":20,"location":"rustboro-city",
             "source":"Claw Fossil revived at Devon Corporation",
             "version_native":"sapphire","note":"Claw Fossil from Mirage Tower; Root Fossil in Ruby"},
        ],
        "in_game_trades": [],
    },

    "diamond": {
        "starters": [
            {"pokemon":"turtwig", "pokemon_id":387,"note":"Choose one at start"},
            {"pokemon":"chimchar","pokemon_id":390,"note":"Choose one at start"},
            {"pokemon":"piplup",  "pokemon_id":393,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"dialga",   "pokemon_id":483,"level":47,"location":"mt-coronet",
             "version_native":"diamond","note":"Spear Pillar; Palkia in Pearl"},
            {"pokemon":"palkia",   "pokemon_id":484,"level":47,"location":"mt-coronet",
             "version_native":"pearl","note":"Spear Pillar; Dialga in Diamond"},
            {"pokemon":"giratina", "pokemon_id":487,"level":47,"location":"distortion-world",
             "version_native":"platinum",
             "note":"Distortion World in Platinum; post-game Turnback Cave in Diamond/Pearl (not tracked)"},
            {"pokemon":"uxie",     "pokemon_id":480,"level":50,"location":"lake-acuity",
             "note":"Lake Acuity; available after the Spear Pillar arc"},
            {"pokemon":"mesprit",  "pokemon_id":481,"level":50,"location":"route-201",
             "roaming":True,"note":"Lake Verity (Route 201 area); roams Sinnoh after first visit"},
            {"pokemon":"azelf",    "pokemon_id":482,"level":50,"location":"route-214",
             "note":"Lake Valor (Route 214 / Pastoria area)"},
            {"pokemon":"heatran",  "pokemon_id":485,"level":70,"location":"stark-mountain",
             "note":"Post-game; Stark Mountain interior (Route 227)"},
            {"pokemon":"regigigas","pokemon_id":486,"level":1, "location":"snowpoint-temple",
             "note":"Post-game; requires Regirock, Regice, and Registeel in party"},
            {"pokemon":"cresselia","pokemon_id":488,"level":50,"location":"route-205",
             "roaming":True,
             "note":"Fullmoon Island (via Canalave City sailor); roams Sinnoh after first encounter"},
            {"pokemon":"rotom",    "pokemon_id":479,"level":15,"location":"eterna-forest",
             "note":"Old Chateau in Eterna Forest; appears only at night"},
        ],
        "gift_pokemon": [
            {"pokemon":"riolu",   "pokemon_id":447,"level":1, "location":"iron-island",
             "source":"Riley (Egg)","note":"Hatches into Riolu after clearing Iron Island with Riley"},
            {"pokemon":"cranidos","pokemon_id":408,"level":20,"location":"oreburgh-city",
             "source":"Skull Fossil revived at Oreburgh Museum",
             "version_native":"diamond","note":"Armor Fossil (Shieldon) in Pearl"},
            {"pokemon":"shieldon","pokemon_id":410,"level":20,"location":"oreburgh-city",
             "source":"Armor Fossil revived at Oreburgh Museum",
             "version_native":"pearl","note":"Skull Fossil (Cranidos) in Diamond"},
            {"pokemon":"eevee",   "pokemon_id":133,"level":5, "location":"hearthome-city",
             "source":"Bebe (PC system developer)"},
        ],
        "in_game_trades": [],
    },

    "black": {
        "starters": [
            {"pokemon":"snivy",   "pokemon_id":495,"note":"Choose one at start"},
            {"pokemon":"tepig",   "pokemon_id":498,"note":"Choose one at start"},
            {"pokemon":"oshawott","pokemon_id":501,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"reshiram", "pokemon_id":643,"level":50,"location":"pokemon-league",
             "version_native":"black",
             "note":"Light Stone awakens at N's Castle (attached to Pokémon League); required catch"},
            {"pokemon":"zekrom",   "pokemon_id":644,"level":50,"location":"pokemon-league",
             "version_native":"white",
             "note":"Dark Stone awakens at N's Castle; required catch before final N battle"},
            {"pokemon":"cobalion", "pokemon_id":638,"level":42,"location":"route-6",
             "note":"Mistralton Cave (Route 6 area); meet after obtaining HM Strength"},
            {"pokemon":"terrakion","pokemon_id":639,"level":42,"location":"victory-road",
             "note":"Victory Road; requires meeting Cobalion first"},
            {"pokemon":"virizion", "pokemon_id":640,"level":42,"location":"pinwheel-forest",
             "note":"Rumination Field in Pinwheel Forest; requires meeting Cobalion first"},
            {"pokemon":"tornadus", "pokemon_id":641,"level":40,"location":"unova",
             "roaming":True,"version_native":"black",
             "note":"Roams Unova during storms; first appears on Route 7"},
            {"pokemon":"thundurus","pokemon_id":642,"level":40,"location":"unova",
             "roaming":True,"version_native":"white",
             "note":"Roams Unova during thunderstorms; first appears on Route 7"},
        ],
        "gift_pokemon": [
            {"pokemon":"tirtouga","pokemon_id":564,"level":25,"location":"nacrene-city",
             "source":"Cover Fossil revived at Nacrene City Museum",
             "version_native":"black","note":"Plume Fossil (Archen) in White"},
            {"pokemon":"archen",  "pokemon_id":566,"level":25,"location":"nacrene-city",
             "source":"Plume Fossil revived at Nacrene City Museum",
             "version_native":"white","note":"Cover Fossil (Tirtouga) in Black"},
        ],
        "in_game_trades": [],
    },

    "black-2": {
        "starters": [
            {"pokemon":"snivy",   "pokemon_id":495,"note":"Choose one at start"},
            {"pokemon":"tepig",   "pokemon_id":498,"note":"Choose one at start"},
            {"pokemon":"oshawott","pokemon_id":501,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"zekrom",   "pokemon_id":644,"level":70,"location":"giant-chasm",
             "version_native":"black-2",
             "note":"Black 2: Zekrom freed from Kyurem fusion at Giant Chasm; must be caught"},
            {"pokemon":"reshiram", "pokemon_id":643,"level":70,"location":"giant-chasm",
             "version_native":"white-2",
             "note":"White 2: Reshiram freed from Kyurem fusion at Giant Chasm; must be caught"},
            {"pokemon":"kyurem",   "pokemon_id":646,"level":70,"location":"giant-chasm",
             "note":"Giant Chasm; Kyurem-Black in B2, Kyurem-White in W2"},
            {"pokemon":"cobalion", "pokemon_id":638,"level":45,"location":"route-6",
             "note":"Mistralton Cave (Route 6 area); available after badge 5"},
            {"pokemon":"terrakion","pokemon_id":639,"level":42,"location":"victory-road",
             "note":"Victory Road; requires meeting Cobalion first"},
            {"pokemon":"virizion", "pokemon_id":640,"level":45,"location":"pinwheel-forest",
             "note":"Pinwheel Forest (not in BW2 ROUTE_ORDER; generates a data warning)"},
            {"pokemon":"thundurus","pokemon_id":642,"level":40,"location":"unova",
             "roaming":True,"version_native":"black-2",
             "note":"Roams in Black 2; Tornadus roams in White 2"},
            {"pokemon":"tornadus", "pokemon_id":641,"level":40,"location":"unova",
             "roaming":True,"version_native":"white-2",
             "note":"Roams in White 2; Thundurus roams in Black 2"},
        ],
        "gift_pokemon": [
            {"pokemon":"tirtouga","pokemon_id":564,"level":25,"location":"nacrene-city",
             "source":"Cover Fossil revived at Nacrene City Museum",
             "version_native":"black-2","note":"Plume Fossil (Archen) in White 2"},
            {"pokemon":"archen",  "pokemon_id":566,"level":25,"location":"nacrene-city",
             "source":"Plume Fossil revived at Nacrene City Museum",
             "version_native":"white-2","note":"Cover Fossil (Tirtouga) in Black 2"},
        ],
        "in_game_trades": [],
    },

    "x": {
        "starters": [
            {"pokemon":"chespin",  "pokemon_id":650,"note":"Choose one at start"},
            {"pokemon":"fennekin", "pokemon_id":653,"note":"Choose one at start"},
            {"pokemon":"froakie",  "pokemon_id":656,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"xerneas","pokemon_id":716,"level":50,"location":"geosenge-town",
             "version_native":"x",
             "note":"Team Flare Secret HQ beneath Geosenge Town; forced story catch"},
            {"pokemon":"yveltal", "pokemon_id":717,"level":50,"location":"geosenge-town",
             "version_native":"y",
             "note":"Team Flare Secret HQ beneath Geosenge Town; forced story catch"},
            {"pokemon":"zygarde", "pokemon_id":718,"level":70,"location":"terminus-cave",
             "note":"Terminus Cave (Route 18); post-game"},
            {"pokemon":"mewtwo",  "pokemon_id":150,"level":70,"location":"route-20",
             "note":"Pokémon Village (Winding Woods / Route 20); post-game"},
            {"pokemon":"articuno","pokemon_id":144,"level":70,"location":"azure-bay",
             "note":"Roams 10 Kalos routes then settles at Sea Spirit's Den (Azure Bay); which bird depends on starter"},
            {"pokemon":"zapdos",  "pokemon_id":145,"level":70,"location":"azure-bay",
             "note":"Roams 10 Kalos routes then settles at Sea Spirit's Den (Azure Bay); which bird depends on starter"},
            {"pokemon":"moltres", "pokemon_id":146,"level":70,"location":"azure-bay",
             "note":"Roams 10 Kalos routes then settles at Sea Spirit's Den (Azure Bay); which bird depends on starter"},
        ],
        "gift_pokemon": [
            {"pokemon":"bulbasaur", "pokemon_id":1,  "level":10,"location":"lumiose-city",
             "source":"Professor Sycamore","note":"Choose one of the three Kanto starters"},
            {"pokemon":"charmander","pokemon_id":4,  "level":10,"location":"lumiose-city",
             "source":"Professor Sycamore","note":"Choose one of the three Kanto starters"},
            {"pokemon":"squirtle", "pokemon_id":7,  "level":10,"location":"lumiose-city",
             "source":"Professor Sycamore","note":"Choose one of the three Kanto starters"},
            {"pokemon":"lucario",  "pokemon_id":448,"level":32,"location":"tower-of-mastery",
             "source":"Korrina","note":"Korrina's Lucario with Mega Stone"},
            {"pokemon":"tyrunt",   "pokemon_id":696,"level":20,"location":"ambrette-town",
             "source":"Jaw Fossil revived at Fossil Lab",
             "version_native":"x","note":"Sail Fossil (Amaura) in Y"},
            {"pokemon":"amaura",   "pokemon_id":698,"level":20,"location":"ambrette-town",
             "source":"Sail Fossil revived at Fossil Lab",
             "version_native":"y","note":"Jaw Fossil (Tyrunt) in X"},
        ],
        "in_game_trades": [],
    },

    "sun": {
        "starters": [
            {"pokemon":"rowlet",  "pokemon_id":722,"note":"Choose one at start"},
            {"pokemon":"litten",  "pokemon_id":725,"note":"Choose one at start"},
            {"pokemon":"popplio", "pokemon_id":728,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"solgaleo","pokemon_id":791,"level":53,"location":"altar-of-sunne",
             "version_native":"sun",
             "note":"Evolves from Cosmoem at Altar of the Sunne during the story"},
            {"pokemon":"lunala",  "pokemon_id":792,"level":53,"location":"altar-of-sunne",
             "version_native":"moon",
             "note":"Evolves from Cosmoem at Altar of the Moone during the story"},
            {"pokemon":"tapu-koko","pokemon_id":785,"level":60,"location":"iki-town",
             "note":"Post-game; Ruins of Conflict on Melemele Island"},
            {"pokemon":"tapu-lele","pokemon_id":786,"level":60,"location":"ruins-of-life",
             "note":"Post-game; Ruins of Life on Akala Island"},
            {"pokemon":"tapu-bulu","pokemon_id":787,"level":60,"location":"poni-plains",
             "note":"Post-game; Ruins of Abundance on Poni Island (Poni Meadow)"},
            {"pokemon":"tapu-fini","pokemon_id":788,"level":60,"location":"ancient-poni-path",
             "note":"Post-game; Ruins of Hope at the end of Ancient Poni Path"},
            {"pokemon":"cosmog",  "pokemon_id":789,"level":5, "location":"altar-of-sunne",
             "note":"Post-game; second Cosmog at the Lake of the Sunne/Moone"},
        ],
        "gift_pokemon": [
            {"pokemon":"type-null","pokemon_id":772,"level":40,"location":"aether-paradise",
             "source":"Gladion (post-game)","note":"Given after becoming Champion; comes with Memories"},
        ],
        "in_game_trades": [],
    },

    "emerald": {
        "starters": [
            {"pokemon":"treecko","pokemon_id":252,"note":"Choose one at start"},
            {"pokemon":"torchic","pokemon_id":255,"note":"Choose one at start"},
            {"pokemon":"mudkip", "pokemon_id":258,"note":"Choose one at start"},
        ],
        "static_encounters": [
            # Both available post-E4; location rotates daily via Weather Institute TV
            {"pokemon":"groudon",  "pokemon_id":383,"level":70,"location":"hoenn","roaming":True,
             "note":"Terra Cave — roams Hoenn post-E4; exact location broadcast by Weather Institute TV"},
            {"pokemon":"kyogre",   "pokemon_id":382,"level":70,"location":"hoenn","roaming":True,
             "note":"Marine Cave — roams Hoenn post-E4; exact location broadcast by Weather Institute TV"},
            {"pokemon":"rayquaza", "pokemon_id":384,"level":70,"location":"sky-pillar",
             "note":"Sky Pillar roof; accessible after the Sootopolis story arc"},
            {"pokemon":"regirock", "pokemon_id":377,"level":40,"location":"route-111",
             "note":"Desert Ruins; requires Relicanth + Wailord Sealed Chamber puzzle"},
            {"pokemon":"regice",   "pokemon_id":378,"level":40,"location":"route-105",
             "note":"Island Cave; requires Sealed Chamber puzzle"},
            {"pokemon":"registeel","pokemon_id":379,"level":40,"location":"route-120",
             "note":"Ancient Tomb; requires Sealed Chamber puzzle"},
            # After the E4, a TV broadcast lets the player choose one to roam;
            # the other is catchable at Southern Island via the Eon Ticket.
            {"pokemon":"latias","pokemon_id":380,"level":40,"location":"hoenn","roaming":True,
             "note":"Player's choice roamer from post-E4 TV; other available at Southern Island (Eon Ticket)"},
            {"pokemon":"latios","pokemon_id":381,"level":40,"location":"hoenn","roaming":True,
             "note":"Player's choice roamer from post-E4 TV; other available at Southern Island (Eon Ticket)"},
        ],
        "gift_pokemon": [
            {"pokemon":"castform","pokemon_id":351,"level":25,"location":"route-119",
             "source":"Weather Institute researcher (after clearing Team Aqua/Magma)"},
            {"pokemon":"wynaut",  "pokemon_id":360,"level":1, "location":"lavaridge-town",
             "source":"Old lady in Lavaridge Town hot springs (Egg)"},
            {"pokemon":"beldum",  "pokemon_id":374,"level":5, "location":"mossdeep-city",
             "source":"Steven's house (post-game; received via e-mail)"},
            # Both fossils are eventually obtainable in Emerald via the Mirage Tower desert
            {"pokemon":"lileep",  "pokemon_id":345,"level":20,"location":"rustboro-city",
             "source":"Root Fossil revived at Devon Corporation"},
            {"pokemon":"anorith", "pokemon_id":347,"level":20,"location":"rustboro-city",
             "source":"Claw Fossil revived at Devon Corporation"},
        ],
        "in_game_trades": [],
    },

    "omega-ruby": {
        "starters": [
            {"pokemon":"treecko","pokemon_id":252,"note":"Choose one at start"},
            {"pokemon":"torchic","pokemon_id":255,"note":"Choose one at start"},
            {"pokemon":"mudkip", "pokemon_id":258,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"groudon",  "pokemon_id":383,"level":45,"location":"cave-of-origin",
             "version_native":"omega-ruby",
             "note":"Primal Groudon; required story encounter"},
            {"pokemon":"kyogre",   "pokemon_id":382,"level":45,"location":"cave-of-origin",
             "version_native":"alpha-sapphire",
             "note":"Primal Kyogre; required story encounter"},
            # Delta Episode: Rayquaza must be caught to advance the story
            {"pokemon":"rayquaza", "pokemon_id":384,"level":70,"location":"sky-pillar",
             "note":"Delta Episode; Sky Pillar summit — must be caught to continue the story"},
            # Deoxys appears in space at the climax of the Delta Episode
            {"pokemon":"deoxys",   "pokemon_id":386,"level":80,"location":"sky-pillar",
             "note":"Delta Episode; space encounter accessible via Sky Pillar"},
            {"pokemon":"regirock", "pokemon_id":377,"level":40,"location":"route-111",
             "note":"Desert Ruins; requires Relicanth + Wailord Sealed Chamber puzzle"},
            {"pokemon":"regice",   "pokemon_id":378,"level":40,"location":"route-105",
             "note":"Island Cave; requires Sealed Chamber puzzle"},
            {"pokemon":"registeel","pokemon_id":379,"level":40,"location":"route-120",
             "note":"Ancient Tomb; requires Sealed Chamber puzzle"},
            {"pokemon":"regigigas","pokemon_id":486,"level":50,"location":"route-105",
             "note":"Island Cave; requires all three Regis in party (Regice holding Snowball, Registeel holding Magnet)"},
            {"pokemon":"latias","pokemon_id":380,"level":40,"location":"southern-island",
             "version_native":"omega-ruby",
             "note":"Given as story companion via Eon Flute; catchable at Southern Island"},
            {"pokemon":"latios","pokemon_id":381,"level":40,"location":"southern-island",
             "version_native":"alpha-sapphire",
             "note":"Given as story companion via Eon Flute; catchable at Southern Island"},
        ],
        "gift_pokemon": [
            {"pokemon":"castform","pokemon_id":351,"level":25,"location":"route-119",
             "source":"Weather Institute researcher (after clearing Team Aqua/Magma)"},
            {"pokemon":"wynaut",  "pokemon_id":360,"level":1, "location":"lavaridge-town",
             "source":"Old lady in Lavaridge Town hot springs (Egg)"},
            {"pokemon":"beldum",  "pokemon_id":374,"level":5, "location":"mossdeep-city",
             "source":"Steven's house (post-game)"},
            {"pokemon":"lileep",  "pokemon_id":345,"level":20,"location":"rustboro-city",
             "source":"Root Fossil revived at Devon Corporation",
             "version_native":"omega-ruby","note":"Claw Fossil (Anorith) in Alpha Sapphire"},
            {"pokemon":"anorith", "pokemon_id":347,"level":20,"location":"rustboro-city",
             "source":"Claw Fossil revived at Devon Corporation",
             "version_native":"alpha-sapphire","note":"Root Fossil (Lileep) in Omega Ruby"},
        ],
        "in_game_trades": [],
    },

    "ultra-sun": {
        "starters": [
            {"pokemon":"rowlet",  "pokemon_id":722,"note":"Choose one at start"},
            {"pokemon":"litten",  "pokemon_id":725,"note":"Choose one at start"},
            {"pokemon":"popplio", "pokemon_id":728,"note":"Choose one at start"},
        ],
        "static_encounters": [
            {"pokemon":"solgaleo","pokemon_id":791,"level":55,"location":"altar-of-sunne",
             "version_native":"ultra-sun",
             "note":"Evolves from Cosmoem at the Altar of the Sunne during the story"},
            {"pokemon":"lunala",  "pokemon_id":792,"level":55,"location":"altar-of-sunne",
             "version_native":"ultra-moon",
             "note":"Evolves from Cosmoem at the Altar of the Moone during the story"},
            # Necrozma fuses with the version mascot during the story; catchable post-E4
            {"pokemon":"necrozma","pokemon_id":800,"level":75,"location":"mount-lanakila",
             "note":"Appears at the summit of Mount Lanakila after first clearing the Elite Four"},
            {"pokemon":"tapu-koko","pokemon_id":785,"level":60,"location":"iki-town",
             "note":"Post-game; Ruins of Conflict on Melemele Island"},
            {"pokemon":"tapu-lele","pokemon_id":786,"level":60,"location":"ruins-of-life",
             "note":"Post-game; Ruins of Life on Akala Island"},
            {"pokemon":"tapu-bulu","pokemon_id":787,"level":60,"location":"poni-plains",
             "note":"Post-game; Ruins of Abundance on Poni Island"},
            {"pokemon":"tapu-fini","pokemon_id":788,"level":60,"location":"ancient-poni-path",
             "note":"Post-game; Ruins of Hope at the end of Ancient Poni Path"},
            # Version-exclusive Ultra Beasts (post-game)
            {"pokemon":"blacephalon","pokemon_id":806,"level":60,"location":"poni-grove",
             "version_native":"ultra-sun",
             "note":"Post-game; UB Burst — appears in Poni Grove and adjacent areas"},
            {"pokemon":"stakataka",  "pokemon_id":805,"level":60,"location":"poni-grove",
             "version_native":"ultra-moon",
             "note":"Post-game; UB Assembly — appears in Poni Grove and adjacent areas"},
            {"pokemon":"cosmog","pokemon_id":789,"level":5,"location":"altar-of-sunne",
             "note":"Post-game; second Cosmog at the Lake of the Sunne / Moone"},
        ],
        "gift_pokemon": [
            {"pokemon":"type-null","pokemon_id":772,"level":40,"location":"aether-paradise",
             "source":"Gladion (post-game)","note":"Given after becoming Champion; comes with Memories"},
            {"pokemon":"poipole",  "pokemon_id":803,"level":40,"location":"poni-island",
             "source":"Ultra Recon Squad member (post-game)",
             "note":"Given after defeating the Elite Four for the first time"},
        ],
        "in_game_trades": [],
    },
}
# Alias version pairs to the same static data dict
GAME_STATIC["soulsilver"]     = GAME_STATIC["heartgold"]
GAME_STATIC["silver"]         = GAME_STATIC["gold"]
GAME_STATIC["blue"]           = GAME_STATIC["red"]
GAME_STATIC["leafgreen"]      = GAME_STATIC["firered"]
GAME_STATIC["sapphire"]       = GAME_STATIC["ruby"]
GAME_STATIC["alpha-sapphire"] = GAME_STATIC["omega-ruby"]
GAME_STATIC["pearl"]          = GAME_STATIC["diamond"]
GAME_STATIC["platinum"]       = GAME_STATIC["diamond"]
GAME_STATIC["white"]          = GAME_STATIC["black"]
GAME_STATIC["white-2"]        = GAME_STATIC["black-2"]
GAME_STATIC["y"]              = GAME_STATIC["x"]
GAME_STATIC["moon"]           = GAME_STATIC["sun"]
GAME_STATIC["ultra-moon"]     = GAME_STATIC["ultra-sun"]


# ── Route unlock order ─────────────────────────────────────────────────────────
# "badges"  = number of badges already earned before this area is first reachable
# "hm"      = HM move required to enter (move slug, e.g. "surf")
# "event"   = short story-event key (informational; app maps these to display text)

def _r(order: int, location: str, display: str, *,
       badges: int = 0, hm: str | None = None,
       event: str | None = None, note: str | None = None) -> dict:
    entry: dict = {
        "order":        order,
        "location":     location,
        "display_name": display,
        "prerequisites": {"badges": badges, "hm": hm, "event": event},
    }
    if note:
        entry["note"] = note
    return entry


ROUTE_ORDER: dict[str, list[dict]] = {
    # ── HeartGold / SoulSilver ──────────────────────────────────────────────
    "heartgold": [
        _r(1,  "new-bark-town",    "New Bark Town"),
        _r(2,  "route-29",         "Route 29"),
        _r(3,  "cherrygrove-city", "Cherrygrove City"),
        _r(4,  "route-30",         "Route 30"),
        _r(5,  "route-31",         "Route 31"),
        _r(5,  "dark-cave",        "Dark Cave",          note="Entrance from Route 31; eastern exit to Route 45 needs Surf"),
        _r(6,  "violet-city",      "Violet City",        event="gym1_zephyr"),
        _r(6,  "sprout-tower",     "Sprout Tower",       note="Three floors; Bellsprout/Gastly encounters"),
        _r(6,  "mr-pokemons-house","Mr. Pokémon's House", note="Togepi egg received here during Elm's errand"),
        _r(7,  "ruins-of-alph",    "Ruins of Alph",      note="Entrance via Route 32; full access needs Rock Smash"),
        _r(8,  "route-32",         "Route 32"),
        _r(9,  "union-cave",       "Union Cave",         note="Lower floors require Surf"),
        _r(10, "route-33",         "Route 33"),
        _r(11, "slowpoke-well",    "Slowpoke Well",      event="defeat_rockets_slowpoke_well"),
        _r(12, "azalea-town",      "Azalea Town",        event="gym2_hive"),
        # HM01 Cut obtained from the Charcoal Man's apprentice inside Ilex Forest
        _r(13, "ilex-forest",      "Ilex Forest",        hm="cut", event="gym2_hive"),
        _r(14, "route-34",         "Route 34",           hm="cut"),
        _r(15, "goldenrod-city",   "Goldenrod City",     event="gym3_plain"),
        _r(16, "route-35",         "Route 35"),
        _r(17, "national-park",    "National Park"),
        # Sudowoodo blocks Route 36; Squirtbottle from Goldenrod flower shop clears it
        _r(18, "route-36",         "Route 36",           event="squirtbottle_sudowoodo"),
        _r(19, "route-37",         "Route 37"),
        _r(20, "ecruteak-city",    "Ecruteak City",      event="gym4_fog"),
        _r(20, "burned-tower",     "Burned Tower",       note="Three floors; Suicune/Raikou/Entei release event"),
        _r(20, "bell-tower",       "Bell Tower",         note="Ten floors; Ho-Oh at top requires Rainbow Wing"),
        # HM03 Surf given by Kimono Girls in the Ecruteak Dance Theater
        _r(21, "route-38",         "Route 38"),
        _r(22, "route-39",         "Route 39"),
        _r(23, "olivine-city",     "Olivine City",       note="Jasmine at lighthouse until SecretPotion delivered"),
        _r(24, "route-40",         "Route 40",           hm="surf"),
        _r(25, "route-41",         "Route 41",           hm="surf"),
        _r(26, "whirl-islands",    "Whirl Islands",      hm="surf", note="Inner floors need Whirlpool + Strength"),
        _r(27, "cianwood-city",    "Cianwood City",      hm="surf", note="HM02 Fly from woman near gym; Storm Badge enables Fly"),
        # Return to Olivine after obtaining SecretPotion from Cianwood pharmacy
        _r(28, "olivine-city",     "Olivine City (Gym)", badges=5, event="gym6_mineral",
           note="Jasmine returns to gym after SecretPotion delivered to Ampharos"),
        _r(29, "route-42",         "Route 42",           note="Ecruteak↔Mahogany; Mt. Mortar entrance on this route"),
        _r(30, "mt-mortar",        "Mt. Mortar",         hm="surf", note="Tyrogue gift from Karate King inside"),
        _r(31, "route-43",         "Route 43"),
        _r(32, "lake-of-rage",     "Lake of Rage",       event="red_gyarados", note="Red Gyarados; Lance appears"),
        _r(33, "mahogany-town",    "Mahogany Town",      event="defeat_rockets_mahogany"),
        _r(34, "team-rocket-hq",   "Team Rocket HQ",     event="defeat_rockets_mahogany"),
        _r(35, "route-44",         "Route 44",           badges=7),
        _r(36, "ice-path",         "Ice Path",           badges=7, hm="strength", note="Strength for boulder puzzles"),
        _r(37, "blackthorn-city",  "Blackthorn City",    event="gym8_rising"),
        _r(38, "dragons-den",      "Dragon's Den",       event="gym8_rising", note="Dratini gift from quiz"),
        _r(39, "route-45",         "Route 45",           note="Connects Blackthorn south toward New Bark Town area"),
        _r(40, "route-46",         "Route 46"),
        # Radio Tower Rockets must be defeated before the route to Kanto is cleared
        _r(41, "route-27",         "Route 27",           badges=8, hm="surf"),
        _r(42, "route-26",         "Route 26",           badges=8, hm="surf"),
        _r(42, "victory-road-kanto", "Victory Road",     badges=8, hm="surf"),
        _r(43, "pokemon-league",   "Pokémon League",     badges=8,
           note="Johto E4: Will → Koga → Bruno → Karen → Lance"),
        # ── Kanto (post-game) ──────────────────────────────────────────────
        _r(44, "pallet-town",      "Pallet Town",        badges=8, event="beat_johto_champion",
           note="Post-game Kanto begins here"),
        _r(45, "route-1",          "Route 1",            badges=8),
        _r(46, "viridian-city",    "Viridian City",      badges=8),
        _r(47, "route-2",          "Route 2",            badges=8),
        _r(48, "pewter-city",      "Pewter City",        badges=8,  note="Gym 9: Brock (Rock)"),
        _r(49, "route-3",          "Route 3",            badges=9),
        _r(50, "mt-moon",          "Mt. Moon",           badges=9),
        _r(51, "route-4",          "Route 4",            badges=9),
        _r(52, "cerulean-city",    "Cerulean City",      badges=9,  note="Gym 10: Misty (Water)"),
        _r(53, "route-24",         "Route 24",           badges=10),
        _r(54, "route-25",         "Route 25",           badges=10, note="Suicune final encounter here"),
        _r(55, "route-5",          "Route 5",            badges=10),
        _r(56, "route-6",          "Route 6",            badges=10),
        _r(57, "vermilion-city",   "Vermilion City",     badges=10, note="Gym 11: Lt. Surge (Electric)"),
        _r(58, "route-11",         "Route 11",           badges=11, note="Snorlax — needs Poké Flute/Radio"),
        _r(59, "route-12",         "Route 12",           badges=11, note="Snorlax — needs Poké Flute/Radio"),
        _r(60, "route-13",         "Route 13",           badges=11),
        _r(61, "route-14",         "Route 14",           badges=11),
        _r(62, "route-15",         "Route 15",           badges=11),
        _r(63, "fuchsia-city",     "Fuchsia City",       badges=11, note="Gym 13: Janine (Poison)"),
        _r(64, "celadon-city",     "Celadon City",       badges=11, note="Gym 12: Erika (Grass)"),
        _r(65, "route-16",         "Route 16",           badges=13),
        _r(66, "route-17",         "Route 17",           badges=13),
        _r(67, "route-18",         "Route 18",           badges=13),
        _r(68, "route-7",          "Route 7",            badges=12),
        _r(69, "route-8",          "Route 8",            badges=12),
        _r(70, "lavender-town",    "Lavender Town",      badges=12),
        _r(71, "rock-tunnel",      "Rock Tunnel",        badges=12),
        _r(72, "route-9",          "Route 9",            badges=12),
        _r(73, "route-10",         "Route 10",           badges=12),
        _r(74, "power-plant",      "Power Plant",        badges=12, note="Zapdos lv50 here"),
        _r(75, "saffron-city",     "Saffron City",       badges=12, note="Gym 14: Sabrina (Psychic)"),
        _r(76, "route-19",         "Route 19",           badges=13, hm="surf"),
        _r(77, "route-20",         "Route 20",           badges=13, hm="surf"),
        _r(78, "seafoam-islands",  "Seafoam Islands",    badges=13, hm="surf", note="Articuno lv50 here"),
        _r(79, "cinnabar-island",  "Cinnabar Island",    badges=13, hm="surf",
           note="Gym 15: Blaine (Fire) — note: Moltres is at Mt. Silver in HGSS, not here"),
        _r(80, "route-21",         "Route 21",           badges=15, hm="surf"),
        _r(81, "viridian-city",    "Viridian City (Gym)",badges=15,
           note="Gym 16: Blue — requires all 15 other Kanto badges"),
        _r(82, "mt-silver",        "Mt. Silver",         badges=16, hm="rock-climb",
           note="Moltres lv50 here; Red (final boss) at the summit"),
        _r(83, "cerulean-cave",    "Cerulean Cave",      badges=16, hm="surf", note="Mewtwo lv70"),
        _r(83, "embedded-tower",   "Embedded Tower",     badges=16,
           note="Groudon (HG) / Kyogre (SS) / Rayquaza (both, after catching the other two)"),
    ],

    # ── Red / Blue / Yellow ─────────────────────────────────────────────────
    "red": [
        _r(1,  "pallet-town",     "Pallet Town"),
        _r(2,  "route-1",         "Route 1"),
        _r(3,  "viridian-city",   "Viridian City"),
        _r(4,  "route-2",         "Route 2"),
        _r(5,  "viridian-forest", "Viridian Forest"),
        _r(6,  "pewter-city",     "Pewter City",        event="gym1_boulder"),
        _r(7,  "route-3",         "Route 3",            badges=1),
        _r(8,  "mt-moon",         "Mt. Moon",           badges=1),
        _r(9,  "route-4",         "Route 4",            badges=1),
        _r(10, "cerulean-city",   "Cerulean City",      event="gym2_cascade"),
        _r(11, "route-24",        "Route 24",           badges=2),
        _r(12, "route-25",        "Route 25",           badges=2),
        _r(13, "route-5",         "Route 5",            badges=2),
        _r(14, "route-6",         "Route 6",            badges=2),
        _r(15, "vermilion-city",  "Vermilion City",     event="gym3_thunder"),
        _r(16, "ss-anne",         "S.S. Anne",          badges=2, note="HM01 Cut from the Captain"),
        _r(17, "route-11",        "Route 11",           hm="cut"),
        _r(18, "route-12",        "Route 12",           hm="cut", note="Snorlax — needs Poké Flute"),
        _r(19, "route-13",        "Route 13"),
        _r(20, "route-14",        "Route 14"),
        _r(21, "route-15",        "Route 15"),
        _r(22, "route-9",         "Route 9",            hm="cut"),
        _r(23, "route-10",        "Route 10",           hm="cut"),
        _r(24, "rock-tunnel",     "Rock Tunnel"),
        _r(25, "lavender-town",   "Lavender Town"),
        _r(26, "route-8",         "Route 8"),
        _r(27, "route-7",         "Route 7"),
        _r(28, "celadon-city",    "Celadon City",       event="gym4_rainbow"),
        _r(29, "route-16",        "Route 16",           hm="cut", note="Snorlax — needs Poké Flute"),
        _r(30, "route-17",        "Route 17"),
        _r(31, "route-18",        "Route 18"),
        _r(32, "fuchsia-city",    "Fuchsia City",       event="gym5_soul"),
        _r(33, "route-19",        "Route 19",           hm="surf"),
        _r(34, "route-20",        "Route 20",           hm="surf"),
        _r(35, "seafoam-islands", "Seafoam Islands",    hm="surf", note="Articuno lv50 here"),
        _r(36, "cinnabar-island", "Cinnabar Island",    hm="surf", event="gym7_volcano"),
        _r(37, "route-21",        "Route 21",           hm="surf"),
        _r(38, "saffron-city",    "Saffron City",       event="gym6_marsh"),
        _r(39, "power-plant",     "Power Plant",        hm="surf", note="Zapdos lv50 here"),
        _r(40, "route-22",        "Route 22",           badges=7),
        _r(41, "route-23",        "Route 23",           badges=7),
        _r(42, "victory-road",    "Victory Road",       badges=7, hm="strength",
           note="Moltres lv50 inside — NOT at Mt. Ember (that's FRLG only)"),
        _r(43, "viridian-city",   "Viridian City (Gym)",badges=7, note="Gym 8: Giovanni (Ground)"),
        _r(44, "pokemon-league",  "Pokémon League",     badges=8,
           note="E4: Lorelei → Bruno → Agatha → Lance → Blue"),
        _r(45, "cerulean-cave",   "Cerulean Cave",      badges=8, hm="surf", note="Mewtwo lv70"),
    ],

    # ── Hoenn (Ruby / Sapphire / Emerald / ORAS) ────────────────────────────
    "ruby": [
        _r(1,  "littleroot-town",  "Littleroot Town"),
        _r(2,  "route-101",        "Route 101"),
        _r(3,  "oldale-town",      "Oldale Town"),
        _r(4,  "route-103",        "Route 103"),
        _r(5,  "route-102",        "Route 102"),
        _r(6,  "petalburg-city",   "Petalburg City"),
        _r(7,  "route-104",        "Route 104"),
        _r(8,  "petalburg-woods",  "Petalburg Woods"),
        _r(9,  "rustboro-city",    "Rustboro City",       event="gym1_stone"),
        _r(10, "route-116",        "Route 116",           badges=1),
        _r(11, "rusturf-tunnel",   "Rusturf Tunnel",      hm="rock-smash"),
        _r(12, "route-105",        "Route 105",           hm="surf"),
        _r(13, "route-106",        "Route 106",           hm="surf"),
        _r(14, "dewford-town",     "Dewford Town",        event="gym2_knuckle"),
        _r(15, "granite-cave",     "Granite Cave"),
        _r(16, "route-107",        "Route 107",           hm="surf"),
        _r(17, "route-108",        "Route 108",           hm="surf"),
        _r(18, "route-109",        "Route 109",           hm="surf"),
        _r(19, "slateport-city",   "Slateport City"),
        _r(20, "route-110",        "Route 110"),
        _r(21, "mauville-city",    "Mauville City",       event="gym3_dynamo"),
        _r(22, "route-117",        "Route 117",           badges=3),
        _r(23, "route-111",        "Route 111",           badges=3),
        _r(24, "route-112",        "Route 112",           badges=3),
        _r(24, "meteor-falls",     "Meteor Falls",        badges=3),
        _r(25, "fiery-path",       "Fiery Path",          badges=3),
        _r(25, "mt-chimney",       "Mt. Chimney",         badges=3),
        _r(25, "jagged-pass",      "Jagged Pass",         badges=3),
        _r(26, "lavaridge-town",   "Lavaridge Town",      event="gym4_heat"),
        _r(26, "petalburg-city",   "Petalburg City (Gym)",badges=4, event="gym5_balance"),
        _r(27, "route-118",        "Route 118",           badges=5, hm="surf"),
        _r(28, "route-119",        "Route 119",           badges=5, hm="surf"),
        _r(29, "fortree-city",     "Fortree City",        event="gym6_feather"),
        _r(30, "route-120",        "Route 120",           badges=6),
        _r(31, "route-121",        "Route 121",           badges=6),
        _r(32, "lilycove-city",    "Lilycove City",       badges=6),
        _r(33, "route-122",        "Route 122",           hm="surf"),
        _r(34, "mt-pyre",          "Mt. Pyre",            hm="surf"),
        _r(35, "route-123",        "Route 123",           badges=6),
        _r(36, "mossdeep-city",    "Mossdeep City",       event="gym7_mind"),
        _r(37, "route-124",        "Route 124",           hm="surf"),
        _r(38, "route-125",        "Route 125",           hm="surf"),
        _r(38, "shoal-cave",       "Shoal Cave",          hm="surf"),
        _r(39, "route-126",        "Route 126",           hm="surf"),
        _r(39, "seafloor-cavern",  "Seafloor Cavern",     hm="dive"),
        _r(40, "cave-of-origin",   "Cave of Origin",      hm="dive"),
        _r(41, "sootopolis-city",  "Sootopolis City",     hm="surf", event="gym8_rain"),
        _r(41, "route-127",        "Route 127",           hm="surf"),
        _r(42, "route-128",        "Route 128",           hm="surf"),
        _r(43, "route-129",        "Route 129",           hm="surf"),
        _r(44, "route-130",        "Route 130",           hm="surf"),
        _r(45, "route-131",        "Route 131",           hm="surf"),
        _r(46, "pacifidlog-town",  "Pacifidlog Town",     hm="surf"),
        _r(47, "ever-grande-city", "Ever Grande City",    hm="surf"),
        _r(48, "victory-road",     "Victory Road",        badges=8, hm="strength"),
        _r(49, "pokemon-league",   "Pokémon League",      badges=8,
           note="E4: Sidney → Phoebe → Glacia → Drake → Steven"),
        _r(50, "sky-pillar",       "Sky Pillar",          hm="surf", note="Rayquaza lv70 (post-story)"),
    ],

    # ── Sinnoh (Diamond / Pearl / Platinum) ─────────────────────────────────
    "diamond": [
        _r(1,  "twinleaf-town",    "Twinleaf Town"),
        _r(2,  "route-201",        "Route 201"),
        _r(3,  "sandgem-town",     "Sandgem Town"),
        _r(4,  "route-202",        "Route 202"),
        _r(5,  "jubilife-city",    "Jubilife City"),
        _r(6,  "route-203",        "Route 203"),
        _r(7,  "oreburgh-gate",    "Oreburgh Gate"),
        _r(8,  "oreburgh-city",    "Oreburgh City",       event="gym1_coal"),
        _r(9,  "oreburgh-mine",    "Oreburgh Mine"),
        _r(10, "route-204",        "Route 204"),
        _r(11, "ravaged-path",     "Ravaged Path",        hm="rock-smash"),
        _r(12, "floaroma-town",    "Floaroma Town"),
        _r(13, "route-205",        "Route 205"),
        _r(14, "eterna-city",      "Eterna City",         event="gym2_forest"),
        _r(15, "eterna-forest",    "Eterna Forest"),
        _r(16, "route-206",        "Route 206",           hm="cut"),
        _r(16, "wayward-cave",     "Wayward Cave",        badges=2, hm="cut"),
        _r(17, "route-207",        "Route 207"),
        _r(18, "mt-coronet",       "Mt. Coronet",         note="Accessible early; full traverse unlocked later"),
        _r(19, "route-208",        "Route 208",           badges=2),
        _r(20, "hearthome-city",   "Hearthome City",      badges=2),
        _r(21, "route-209",        "Route 209",           badges=2),
        _r(22, "solaceon-town",    "Solaceon Town",       badges=2),
        _r(23, "route-210",        "Route 210",           badges=2),
        _r(24, "route-215",        "Route 215",           badges=2),
        _r(25, "veilstone-city",   "Veilstone City",      event="gym3_cobble"),
        _r(26, "route-214",        "Route 214",           badges=3),
        _r(27, "pastoria-city",    "Pastoria City",       event="gym4_fen"),
        _r(28, "route-212",        "Route 212",           badges=4, hm="surf"),
        _r(29, "route-213",        "Route 213",           badges=4, hm="surf"),
        _r(30, "hearthome-city",   "Hearthome City (Gym)",badges=4, event="gym5_relic"),
        _r(31, "route-218",        "Route 218",           hm="surf"),
        _r(32, "canalave-city",    "Canalave City",       hm="surf", event="gym6_mine"),
        _r(32, "iron-island",      "Iron Island",         badges=6, hm="surf"),
        _r(33, "route-216",        "Route 216",           badges=6),
        _r(34, "route-217",        "Route 217",           badges=6),
        _r(35, "snowpoint-city",   "Snowpoint City",      event="gym7_icicle"),
        _r(36, "lake-acuity",      "Lake Acuity",         badges=7),
        _r(37, "distortion-world", "Distortion World",    badges=7, note="Platinum only"),
        _r(37, "route-222",        "Route 222",           badges=7),
        _r(38, "sunyshore-city",   "Sunyshore City",      event="gym8_beacon"),
        _r(39, "route-223",        "Route 223",           badges=8, hm="surf"),
        _r(40, "victory-road-sinnoh", "Victory Road",     badges=8, hm="rock-climb"),
        _r(41, "pokemon-league",   "Pokémon League",      badges=8,
           note="E4: Aaron → Bertha → Flint → Lucian → Cynthia"),
        _r(42, "snowpoint-temple", "Snowpoint Temple",    badges=8, note="Post-game; requires all lake guardians defeated"),
        _r(43, "route-227",        "Route 227",           badges=8, hm="rock-climb"),
        _r(43, "stark-mountain",   "Stark Mountain",      badges=8, hm="rock-climb",
           note="Post-game; Heatran lv70"),
    ],

    # ── Unova (Black / White) ────────────────────────────────────────────────
    "black": [
        _r(1,  "nuvema-town",       "Nuvema Town"),
        _r(2,  "route-1",           "Route 1"),
        _r(3,  "accumula-town",     "Accumula Town"),
        _r(4,  "route-2",           "Route 2"),
        _r(5,  "striaton-city",     "Striaton City",        event="gym1_trio",
           note="Gym 1: Cilan/Chili/Cress (Grass/Fire/Water — chosen by starter)"),
        _r(6,  "dreamyard",         "Dreamyard",            badges=1),
        _r(7,  "route-3",           "Route 3",              badges=1),
        _r(8,  "wellspring-cave",   "Wellspring Cave",      badges=1),
        _r(9,  "route-4",           "Route 4 (west)",       badges=1,
           note="Desert area west of Nacrene"),
        _r(10, "desert-resort",     "Desert Resort",        badges=1),
        _r(11, "relic-castle",      "Relic Castle",         badges=1,
           note="Inside Desert Resort"),
        _r(12, "nacrene-city",      "Nacrene City",         event="gym2_basic",
           note="Gym 2: Lenora (Normal)"),
        _r(13, "pinwheel-forest",   "Pinwheel Forest"),
        _r(14, "skyarrow-bridge",   "Skyarrow Bridge"),
        _r(15, "castelia-city",     "Castelia City",        event="gym3_insect",
           note="Gym 3: Burgh (Bug)"),
        _r(16, "castelia-sewers",   "Castelia Sewers",      badges=3),
        _r(17, "route-4",           "Route 4 (east)",       badges=3,
           note="East of Castelia heading to Nimbasa"),
        _r(18, "nimbasa-city",      "Nimbasa City",         event="gym4_bolt",
           note="Gym 4: Elesa (Electric)"),
        _r(19, "route-16",          "Route 16",             badges=4),
        _r(20, "lostlorn-forest",   "Lostlorn Forest",      badges=4),
        _r(21, "route-5",           "Route 5",              badges=4),
        _r(22, "driftveil-drawbridge","Driftveil Drawbridge",badges=4),
        _r(23, "driftveil-city",    "Driftveil City",       event="gym5_quake",
           note="Gym 5: Clay (Ground)"),
        _r(24, "cold-storage",      "Cold Storage",         badges=5),
        _r(25, "route-6",           "Route 6",              badges=5),
        _r(26, "chargestone-cave",  "Chargestone Cave",     badges=5),
        _r(27, "mistralton-city",   "Mistralton City",      event="gym6_jet",
           note="Gym 6: Skyla (Flying)"),
        _r(28, "celestial-tower",   "Celestial Tower",      badges=6),
        _r(29, "route-7",           "Route 7",              badges=6),
        _r(30, "twist-mountain",    "Twist Mountain",       badges=6),
        _r(31, "icirrus-city",      "Icirrus City",         event="gym7_freeze",
           note="Gym 7: Brycen (Ice)"),
        _r(32, "dragonspiral-tower","Dragonspiral Tower",   badges=7),
        _r(33, "route-8",           "Route 8",              badges=7),
        _r(34, "moor-of-icirrus",   "Moor of Icirrus",      badges=7),
        _r(35, "lacunosa-town",     "Lacunosa Town",        badges=7),
        _r(36, "route-9",           "Route 9",              badges=7),
        _r(37, "opelucid-city",     "Opelucid City",        event="gym8_legend",
           note="Gym 8: Drayden (Black) / Iris (White) — Dragon"),
        _r(38, "route-10",          "Route 10",             badges=8),
        _r(39, "victory-road",      "Victory Road",         badges=8, hm="strength"),
        _r(40, "pokemon-league",    "Pokémon League",       badges=8,
           note="E4: Shauntal → Grimsley → Caitlin → Marshal → Alder"),
    ],

    # ── Unova (Black 2 / White 2) ────────────────────────────────────────────
    "black-2": [
        _r(1,  "aspertia-city",     "Aspertia City",        event="gym1_aspertia",
           note="Gym 1: Cheren (Normal)"),
        _r(2,  "route-19",          "Route 19"),
        _r(3,  "floccesy-town",     "Floccesy Town"),
        _r(4,  "floccesy-ranch",    "Floccesy Ranch"),
        _r(5,  "route-20",          "Route 20",             badges=1),
        _r(6,  "virbank-city",      "Virbank City",         event="gym2_virbank",
           note="Gym 2: Roxie (Poison)"),
        _r(7,  "virbank-complex",   "Virbank Complex",      badges=2),
        _r(8,  "castelia-city",     "Castelia City",        event="gym3_insect",
           note="Gym 3: Burgh (Bug)"),
        _r(9,  "castelia-sewers",   "Castelia Sewers",      badges=3),
        _r(10, "route-4",           "Route 4",              badges=3),
        _r(11, "desert-resort",     "Desert Resort",        badges=3),
        _r(12, "nimbasa-city",      "Nimbasa City",         event="gym4_bolt",
           note="Gym 4: Elesa (Electric)"),
        _r(13, "route-16",          "Route 16",             badges=4),
        _r(14, "lostlorn-forest",   "Lostlorn Forest",      badges=4),
        _r(15, "route-5",           "Route 5",              badges=4),
        _r(16, "driftveil-drawbridge","Driftveil Drawbridge",badges=4),
        _r(17, "driftveil-city",    "Driftveil City",       event="gym5_quake",
           note="Gym 5: Clay (Ground)"),
        _r(18, "route-6",           "Route 6",              badges=5),
        _r(19, "chargestone-cave",  "Chargestone Cave",     badges=5),
        _r(20, "mistralton-city",   "Mistralton City",      event="gym6_jet",
           note="Gym 6: Skyla (Flying)"),
        _r(21, "celestial-tower",   "Celestial Tower",      badges=6),
        _r(22, "route-7",           "Route 7",              badges=6),
        _r(23, "twist-mountain",    "Twist Mountain",       badges=6),
        _r(24, "icirrus-city",      "Icirrus City",         badges=6,
           note="No gym in BW2; Brycen became a movie star"),
        _r(25, "route-8",           "Route 8",              badges=6),
        _r(26, "moor-of-icirrus",   "Moor of Icirrus",      badges=6),
        _r(27, "lacunosa-town",     "Lacunosa Town",        badges=6),
        _r(28, "route-9",           "Route 9 (west)",       badges=6),
        _r(29, "opelucid-city",     "Opelucid City",        event="gym7_legend",
           note="Gym 7: Drayden (Dragon)"),
        _r(30, "route-9",           "Route 9 (east)",       badges=7),
        _r(31, "seaside-cave",      "Seaside Cave",         badges=7),
        _r(32, "humilau-city",      "Humilau City",         event="gym8_wave",
           note="Gym 8: Marlon (Water)"),
        _r(33, "marine-tube",       "Marine Tube",          badges=8),
        _r(34, "undella-town",      "Undella Town",         badges=8),
        _r(35, "route-13",          "Route 13",             badges=8),
        _r(36, "giant-chasm",       "Giant Chasm",          badges=8),
        _r(37, "route-22",          "Route 22",             badges=8),
        _r(38, "route-23",          "Route 23",             badges=8, hm="strength"),
        _r(39, "victory-road",      "Victory Road",         badges=8, hm="strength"),
        _r(40, "pokemon-league",    "Pokémon League",       badges=8,
           note="E4: Shauntal → Grimsley → Caitlin → Marshal → Iris"),
    ],

    # ── Kalos (X / Y) ────────────────────────────────────────────────────────
    "x": [
        _r(1,  "vaniville-town",    "Vaniville Town"),
        _r(2,  "route-1",           "Route 1"),
        _r(3,  "aquacorde-town",    "Aquacorde Town"),
        _r(4,  "route-2",           "Route 2"),
        _r(5,  "santalune-forest",  "Santalune Forest"),
        _r(6,  "santalune-city",    "Santalune City",       event="gym1_bug",
           note="Gym 1: Viola (Bug)"),
        _r(7,  "route-3",           "Route 3",              badges=1),
        _r(8,  "lumiose-city",      "Lumiose City (partial)",badges=1,
           note="Full access after defeating Clemont"),
        _r(9,  "route-4",           "Route 4",              badges=1),
        _r(10, "route-22",          "Route 22",             badges=1),
        _r(11, "camphrier-town",    "Camphrier Town",       badges=1),
        _r(12, "route-5",           "Route 5",              badges=1),
        _r(13, "connecting-cave",   "Connecting Cave",      badges=1),
        _r(14, "route-6",           "Route 6",              badges=1),
        _r(15, "parfum-palace",     "Parfum Palace",        badges=1),
        _r(16, "route-7",           "Route 7",              badges=1),
        _r(17, "glittering-cave",   "Glittering Cave",      badges=1),
        _r(18, "route-8",           "Route 8",              badges=1),
        _r(19, "ambrette-town",     "Ambrette Town",        badges=1),
        _r(20, "cyllage-city",      "Cyllage City",         event="gym2_cliff",
           note="Gym 2: Grant (Rock)"),
        _r(21, "route-9",           "Route 9",              badges=2),
        _r(22, "spiky-passage",     "Spiky Passage",        badges=2),
        _r(23, "geosenge-town",     "Geosenge Town",        badges=2),
        _r(24, "route-10",          "Route 10",             badges=2),
        _r(25, "route-11",          "Route 11",             badges=2),
        _r(26, "shalour-city",      "Shalour City",         event="gym3_rumble",
           note="Gym 3: Korrina (Fighting)"),
        _r(27, "tower-of-mastery",  "Tower of Mastery",     badges=3),
        _r(28, "route-12",          "Route 12",             badges=3),
        _r(29, "azure-bay",         "Azure Bay",            badges=3),
        _r(30, "coumarine-city",    "Coumarine City",       event="gym4_grass",
           note="Gym 4: Ramos (Grass)"),
        _r(31, "route-13",          "Route 13",             badges=4),
        _r(32, "lumiose-city",      "Lumiose City (Gym)",   event="gym5_voltage",
           note="Gym 5: Clemont (Electric)"),
        _r(33, "route-14",          "Route 14",             badges=5),
        _r(34, "laverre-city",      "Laverre City",         event="gym6_fairy",
           note="Gym 6: Valerie (Fairy)"),
        _r(35, "poke-ball-factory", "Poké Ball Factory",    badges=6),
        _r(36, "route-15",          "Route 15",             badges=6),
        _r(37, "route-16",          "Route 16",             badges=6),
        _r(38, "dendemille-town",   "Dendemille Town",      badges=6),
        _r(39, "route-17",          "Route 17",             badges=6),
        _r(39, "frost-cavern",      "Frost Cavern",         badges=6),
        _r(40, "anistar-city",      "Anistar City",         event="gym7_psychic",
           note="Gym 7: Olympia (Psychic)"),
        _r(41, "route-18",          "Route 18",             badges=7),
        _r(42, "terminus-cave",     "Terminus Cave",        badges=7),
        _r(43, "couriway-town",     "Couriway Town",        badges=7),
        _r(44, "snowbelle-city",    "Snowbelle City",       event="gym8_iceberg",
           note="Gym 8: Wulfric (Ice)"),
        _r(45, "route-20",          "Route 20 (Winding Woods)",badges=8),
        _r(46, "victory-road",      "Victory Road",         badges=8),
        _r(47, "pokemon-league",    "Pokémon League",       badges=8,
           note="E4: Malva → Siebold → Wikstrom → Drasna → Diantha"),
    ],

    # ── Alola (Sun / Moon) ───────────────────────────────────────────────────
    "sun": [
        _r(1,  "iki-town",          "Iki Town"),
        _r(2,  "route-1",           "Route 1 (south)"),
        _r(3,  "route-1",           "Route 1 (north)",      event="trial0_ilima",
           note="Captain Ilima's trial (Normal)"),
        _r(4,  "trainer-school",    "Trainer School"),
        _r(5,  "hauoli-city",       "Hau'oli City"),
        _r(6,  "route-2",           "Route 2"),
        _r(7,  "berry-fields",      "Berry Fields"),
        _r(8,  "route-3",           "Route 3"),
        _r(9,  "melemele-sea",      "Melemele Sea",         hm=None,
           note="No HMs in Gen 7; Ride Pokémon used instead"),
        _r(10, "kala-e-bay",        "Kala'e Bay"),
        _r(11, "ten-carat-hill",    "Ten Carat Hill"),
        _r(12, "melemele-grand-trial","Melemele Grand Trial",event="grand_trial1_hala",
           note="Kahuna Hala (Fighting)"),
        _r(13, "route-4",           "Route 4"),
        _r(14, "paniola-town",      "Paniola Town"),
        _r(15, "paniola-ranch",     "Paniola Ranch"),
        _r(16, "route-5",           "Route 5"),
        _r(17, "brooklet-hill",     "Brooklet Hill",        event="trial1_lana",
           note="Trial Captain Lana (Water) — Totem Wishiwashi"),
        _r(18, "route-6",           "Route 6"),
        _r(19, "royal-avenue",      "Royal Avenue"),
        _r(20, "route-7",           "Route 7"),
        _r(21, "wela-volcano-park", "Wela Volcano Park",    event="trial2_kiawe",
           note="Trial Captain Kiawe (Fire) — Totem Marowak"),
        _r(22, "route-8",           "Route 8"),
        _r(23, "lush-jungle",       "Lush Jungle",          event="trial3_mallow",
           note="Trial Captain Mallow (Grass) — Totem Lurantis"),
        _r(24, "route-9",           "Route 9"),
        _r(25, "konikoni-city",     "Konikoni City"),
        _r(26, "ruins-of-life",     "Ruins of Life"),
        _r(27, "akala-grand-trial", "Akala Grand Trial",    event="grand_trial2_olivia",
           note="Kahuna Olivia (Rock)"),
        _r(28, "route-10",          "Route 10"),
        _r(29, "route-11",          "Route 11"),
        _r(30, "aether-house",      "Aether House"),
        _r(31, "route-12",          "Route 12"),
        _r(32, "blush-mountain",    "Blush Mountain"),
        _r(33, "route-13",          "Route 13"),
        _r(34, "tapu-village",      "Tapu Village"),
        _r(35, "route-14",          "Route 14"),
        _r(36, "route-15",          "Route 15"),
        _r(37, "ula-ula-meadow",    "Ula'ula Meadow"),
        _r(38, "route-16",          "Route 16"),
        _r(39, "malie-city",        "Malie City"),
        _r(40, "mount-hokulani",    "Mount Hokulani",       event="trial4_sophocles",
           note="Trial Captain Sophocles (Electric) — Totem Vikavolt"),
        _r(41, "route-17",          "Route 17"),
        _r(42, "po-town",           "Po Town"),
        _r(43, "aether-paradise",   "Aether Paradise",      event="aether_story"),
        _r(44, "ula-ula-grand-trial","Ula'ula Grand Trial",  event="grand_trial3_nanu",
           note="Kahuna Nanu (Dark)"),
        _r(45, "route-14",          "Route 14 (south)"),
        _r(46, "seafolk-village",   "Seafolk Village"),
        _r(47, "poni-wilds",        "Poni Wilds"),
        _r(48, "ancient-poni-path", "Ancient Poni Path"),
        _r(49, "poni-plains",       "Poni Plains"),
        _r(50, "vast-poni-canyon",  "Vast Poni Canyon",     event="trial5_hapu",
           note="Trial: Hapu (Ground) — leads to Grand Trial"),
        _r(51, "poni-grand-trial",  "Poni Grand Trial",     event="grand_trial4_hapu",
           note="Kahuna Hapu (Ground)"),
        _r(52, "altar-of-sunne",    "Altar of the Sunne/Moone", event="story_legendary",
           note="Cosmog evolves; Solgaleo (Sun) / Lunala (Moon) encounter"),
        _r(53, "mount-lanakila",    "Mount Lanakila",       event="story_complete"),
        _r(54, "pokemon-league",    "Pokémon League",
           note="E4: Hala → Olivia → Acerola → Kahili → Professor Kukui"),
    ],

    # ── Ultra Alola (Ultra Sun / Ultra Moon) ─────────────────────────────────
    # Core route order matches Sun/Moon; Ultra adds Wormhole encounters and
    # a different post-game but the main island challenge path is identical.
    "ultra-sun": [
        _r(1,  "iki-town",          "Iki Town"),
        _r(2,  "route-1",           "Route 1 (south)"),
        _r(3,  "route-1",           "Route 1 (north)",      event="trial0_ilima",
           note="Captain Ilima's trial (Normal)"),
        _r(4,  "trainer-school",    "Trainer School"),
        _r(5,  "hauoli-city",       "Hau'oli City"),
        _r(6,  "route-2",           "Route 2"),
        _r(7,  "berry-fields",      "Berry Fields"),
        _r(8,  "route-3",           "Route 3"),
        _r(9,  "melemele-sea",      "Melemele Sea"),
        _r(10, "kala-e-bay",        "Kala'e Bay"),
        _r(11, "ten-carat-hill",    "Ten Carat Hill"),
        _r(12, "melemele-grand-trial","Melemele Grand Trial",event="grand_trial1_hala",
           note="Kahuna Hala (Fighting)"),
        _r(13, "route-4",           "Route 4"),
        _r(14, "paniola-town",      "Paniola Town"),
        _r(15, "paniola-ranch",     "Paniola Ranch"),
        _r(16, "route-5",           "Route 5"),
        _r(17, "brooklet-hill",     "Brooklet Hill",        event="trial1_lana",
           note="Trial Captain Lana (Water) — Totem Araquanid (USUM)"),
        _r(18, "route-6",           "Route 6"),
        _r(19, "royal-avenue",      "Royal Avenue"),
        _r(20, "route-7",           "Route 7"),
        _r(21, "wela-volcano-park", "Wela Volcano Park",    event="trial2_kiawe",
           note="Trial Captain Kiawe (Fire) — Totem Salazzle (USUM)"),
        _r(22, "route-8",           "Route 8"),
        _r(23, "lush-jungle",       "Lush Jungle",          event="trial3_mallow",
           note="Trial Captain Mallow (Grass) — Totem Lurantis"),
        _r(24, "route-9",           "Route 9"),
        _r(25, "konikoni-city",     "Konikoni City"),
        _r(26, "ruins-of-life",     "Ruins of Life"),
        _r(27, "akala-grand-trial", "Akala Grand Trial",    event="grand_trial2_olivia",
           note="Kahuna Olivia (Rock)"),
        _r(28, "route-10",          "Route 10"),
        _r(29, "route-11",          "Route 11"),
        _r(30, "aether-house",      "Aether House"),
        _r(31, "route-12",          "Route 12"),
        _r(32, "blush-mountain",    "Blush Mountain"),
        _r(33, "route-13",          "Route 13"),
        _r(34, "tapu-village",      "Tapu Village"),
        _r(35, "route-14",          "Route 14"),
        _r(36, "route-15",          "Route 15"),
        _r(37, "ula-ula-meadow",    "Ula'ula Meadow"),
        _r(38, "route-16",          "Route 16"),
        _r(39, "malie-city",        "Malie City"),
        _r(40, "mount-hokulani",    "Mount Hokulani",       event="trial4_sophocles",
           note="Trial Captain Sophocles (Electric) — Totem Togedemaru (USUM)"),
        _r(41, "route-17",          "Route 17"),
        _r(42, "po-town",           "Po Town"),
        _r(43, "mount-lanakila",    "Mount Lanakila (partial)",event="aether_story"),
        _r(44, "aether-paradise",   "Aether Paradise",      event="aether_story2"),
        _r(45, "ultra-space-wilds", "Ultra Space Wilds",    event="ultra_wormhole",
           note="USUM only — Legendary Pokémon via Wormholes"),
        _r(46, "ula-ula-grand-trial","Ula'ula Grand Trial",  event="grand_trial3_nanu",
           note="Kahuna Nanu (Dark)"),
        _r(47, "seafolk-village",   "Seafolk Village"),
        _r(48, "poni-wilds",        "Poni Wilds"),
        _r(49, "ancient-poni-path", "Ancient Poni Path"),
        _r(50, "poni-plains",       "Poni Plains"),
        _r(51, "vast-poni-canyon",  "Vast Poni Canyon",     event="trial5_hapu"),
        _r(52, "poni-grand-trial",  "Poni Grand Trial",     event="grand_trial4_hapu",
           note="Kahuna Hapu (Ground)"),
        _r(53, "altar-of-sunne",    "Altar of the Sunne/Moone",event="story_legendary",
           note="Necrozma storyline; Solgaleo/Lunala encounter"),
        _r(54, "mount-lanakila",    "Mount Lanakila"),
        _r(55, "pokemon-league",    "Pokémon League",
           note="E4: Hala → Olivia → Acerola → Kahili → Professor Kukui / Necroz-Kukui"),
    ],
}

# ── Aliases ────────────────────────────────────────────────────────────────────
ROUTE_ORDER["soulsilver"]     = ROUTE_ORDER["heartgold"]
ROUTE_ORDER["gold"]           = ROUTE_ORDER["heartgold"]
ROUTE_ORDER["silver"]         = ROUTE_ORDER["heartgold"]
ROUTE_ORDER["crystal"]        = ROUTE_ORDER["heartgold"]
ROUTE_ORDER["blue"]           = ROUTE_ORDER["red"]
ROUTE_ORDER["yellow"]         = ROUTE_ORDER["red"]
ROUTE_ORDER["firered"]        = ROUTE_ORDER["red"]
ROUTE_ORDER["leafgreen"]      = ROUTE_ORDER["red"]
ROUTE_ORDER["sapphire"]       = ROUTE_ORDER["ruby"]
ROUTE_ORDER["emerald"]        = ROUTE_ORDER["ruby"]
ROUTE_ORDER["omega-ruby"]     = ROUTE_ORDER["ruby"]
ROUTE_ORDER["alpha-sapphire"] = ROUTE_ORDER["ruby"]
ROUTE_ORDER["pearl"]          = ROUTE_ORDER["diamond"]
ROUTE_ORDER["platinum"]       = ROUTE_ORDER["diamond"]

ROUTE_ORDER["white"]          = ROUTE_ORDER["black"]
ROUTE_ORDER["white-2"]        = ROUTE_ORDER["black-2"]
ROUTE_ORDER["y"]              = ROUTE_ORDER["x"]
ROUTE_ORDER["moon"]           = ROUTE_ORDER["sun"]
ROUTE_ORDER["ultra-moon"]     = ROUTE_ORDER["ultra-sun"]


# ── Cave / dungeon maps ────────────────────────────────────────────────────────
#
# Multi-floor locations where players benefit from a visual floor map.
#
# Floor fields:
#   id             — stable slug used as a foreign key in warp destinations and
#                    in make_variants.py output (e.g. "ice-path-b1f")
#   display_name   — label shown in the UI (e.g. "B1F")
#   bulbapedia_image — Bulbapedia File: title without the "File:" prefix; the
#                    scraper resolves this to a direct CDN URL at scrape time
#   warps          — connections to other floors:
#                    [{x, y, dest_floor_id, dest_x, dest_y}]
#                    coordinates are tile-grid units (1 tile = 16 px in all mainline
#                    gens). This matches the format pret decomp repos use, so warp data
#                    pulled from pret requires no conversion. Rendering: multiply by 16
#                    to get pixel position, or divide by image tile dimensions to normalize.
#   pokeapi_areas  — PokeAPI location-area slugs whose wild encounters belong to
#                    this floor (e.g. ["ice-path-area"]). Used by make_variants.py
#                    to assign the correct encounter rows to each floor. Leave empty
#                    when the mapping is unknown; encounters will be unassigned.

def _floor(
    fid: str,
    display: str,
    image: str,
    warps: list[dict] | None = None,
    pokeapi_areas: list[str] | None = None,
) -> dict:
    # warps shape: [{x, y, dest_floor_id, dest_x, dest_y}]
    # coordinates are tile-grid units (1 tile = 16 px); matches pret decomp format
    return {
        "id":               fid,
        "display_name":     display,
        "bulbapedia_image": image,
        "warps":            warps or [],
        "pokeapi_areas":    pokeapi_areas or [],
    }

def _loc(lid: str, display: str, floors: list) -> dict:
    return {"id": lid, "display_name": display, "floors": floors}


_GSC_CAVE_MAPS: list[dict] = [
    _loc("sprout-tower", "Sprout Tower", [
        _floor("sprout-tower-1f", "1F", "Sprout Tower 1F GSC.png"),
        _floor("sprout-tower-2f", "2F", "Sprout Tower 2F GSC.png"),
        _floor("sprout-tower-3f", "3F", "Sprout Tower 3F GSC.png"),
    ]),
    _loc("union-cave", "Union Cave", [
        _floor("union-cave-1f",  "1F",  "Union Cave 1F GSC.png"),
        _floor("union-cave-b1f", "B1F", "Union Cave B1F GSC.png"),
        _floor("union-cave-b2f", "B2F", "Union Cave B2F GSC.png"),
    ]),
    _loc("slowpoke-well", "Slowpoke Well", [
        _floor("slowpoke-well-b1f", "B1F", "Slowpoke Well B1F GSC.png"),
        _floor("slowpoke-well-b2f", "B2F", "Slowpoke Well B2F GSC.png"),
    ]),
    _loc("ilex-forest", "Ilex Forest", [
        _floor("ilex-forest", "Forest", "Ilex Forest GSC.png"),
    ]),
    _loc("mt-mortar", "Mt. Mortar", [
        _floor("mt-mortar-entrance",   "Entrance",   "Mt Mortar Entrance GSC.png"),
        _floor("mt-mortar-basement",   "Basement",   "Mt Mortar Basement GSC.png"),
        _floor("mt-mortar-upper-cave", "Upper Cave", "Mt Mortar Upper Cave GSC.png"),
        _floor("mt-mortar-lower-cave", "Lower Cave", "Mt Mortar Lower Cave GSC.png"),
    ]),
    _loc("burned-tower", "Burned Tower", [
        _floor("burned-tower-1f",  "1F",  "Burned Tower 1F GSC.png"),
        _floor("burned-tower-b1f", "B1F", "Burned Tower B1F GSC.png"),
    ]),
    _loc("bell-tower", "Bell Tower", [
        _floor("bell-tower-1f",  "1F",  "Bell Tower 1F GSC.png"),
        _floor("bell-tower-2f",  "2F",  "Bell Tower 2F GSC.png"),
        _floor("bell-tower-3f",  "3F",  "Bell Tower 3F GSC.png"),
        _floor("bell-tower-4f",  "4F",  "Bell Tower 4F GSC.png"),
        _floor("bell-tower-5f",  "5F",  "Bell Tower 5F GSC.png"),
        _floor("bell-tower-6f",  "6F",  "Bell Tower 6F GSC.png"),
        _floor("bell-tower-7f",  "7F",  "Bell Tower 7F GSC.png"),
        _floor("bell-tower-8f",  "8F",  "Bell Tower 8F GSC.png"),
        _floor("bell-tower-9f",  "9F",  "Bell Tower 9F GSC.png"),
        _floor("bell-tower-10f", "10F", "Bell Tower 10F GSC.png"),
    ]),
    _loc("dark-cave", "Dark Cave", [
        _floor("dark-cave-1", "Violet City Side",    "Dark Cave 1 GSC.png"),
        _floor("dark-cave-2", "Blackthorn City Side","Dark Cave 2 GSC.png"),
    ]),
    _loc("ice-path", "Ice Path", [
        _floor("ice-path-1f",  "1F",  "Ice Path 1F GSC.png"),
        _floor("ice-path-b1f", "B1F", "Ice Path B1F GSC.png"),
        _floor("ice-path-b2f", "B2F", "Ice Path B2F GSC.png"),
        _floor("ice-path-b3f", "B3F", "Ice Path B3F GSC.png"),
    ]),
    _loc("dragons-den", "Dragon's Den", [
        _floor("dragons-den-entrance", "Entrance", "Dragons Den Entrance GSC.png"),
        _floor("dragons-den-interior", "Interior", "Dragons Den GSC.png"),
    ]),
    _loc("whirl-islands", "Whirl Islands", [
        _floor("whirl-islands-1f-nw", "1F (NW Island)", "Whirl Islands 1F NW GSC.png"),
        _floor("whirl-islands-1f-ne", "1F (NE Island)", "Whirl Islands 1F NE GSC.png"),
        _floor("whirl-islands-1f-sw", "1F (SW Island)", "Whirl Islands 1F SW GSC.png"),
        _floor("whirl-islands-1f-se", "1F (SE Island)", "Whirl Islands 1F SE GSC.png"),
        _floor("whirl-islands-b1f",   "B1F",            "Whirl Islands B1F GSC.png"),
        _floor("whirl-islands-b2f",   "B2F",            "Whirl Islands B2F GSC.png"),
        _floor("whirl-islands-b3f",   "B3F",            "Whirl Islands B3F GSC.png"),
    ]),
    _loc("mt-silver", "Mt. Silver", [
        _floor("mt-silver-exterior", "Exterior", "Mt. Silver Exterior GSC.png"),
        _floor("mt-silver-1f",       "1F",       "Mt. Silver 1F GSC.png"),
        _floor("mt-silver-2f",       "2F",       "Mt. Silver 2F GSC.png"),
        _floor("mt-silver-3f",       "3F",       "Mt. Silver 3F GSC.png"),
        _floor("mt-silver-summit",   "Summit",   "Mt. Silver Summit GSC.png"),
    ]),
    # Kanto dungeons — Mt. Moon has B1F/B2F in GSC (no Square; that's HGSS-only)
    _loc("mt-moon", "Mt. Moon", [
        _floor("mt-moon-1f",    "1F",    "Mt Moon 1F GSC.png"),
        _floor("mt-moon-b1f",   "B1F",   "Mt Moon B1F GSC.png"),
        _floor("mt-moon-square","Square","Mt Moon Square GSC.png"),
    ]),
    _loc("rock-tunnel", "Rock Tunnel", [
        _floor("rock-tunnel-1", "1F",  "Rock Tunnel 1 GSC.png"),
        _floor("rock-tunnel-2", "B1F", "Rock Tunnel 2 GSC.png"),
    ]),
    _loc("victory-road-kanto", "Victory Road", [
        _floor("victory-road-kanto-1f", "1F", "Victory Road 1F GSC.png"),
        _floor("victory-road-kanto-2f", "2F", "Victory Road 2F GSC.png"),
        _floor("victory-road-kanto-3f", "3F", "Victory Road 3F GSC.png"),
    ]),
    _loc("seafoam-islands", "Seafoam Islands", [
        _floor("seafoam-islands-1f",  "1F",  "Seafoam Islands 1F GSC.png"),
        _floor("seafoam-islands-b1f", "B1F", "Seafoam Islands B1F GSC.png"),
        _floor("seafoam-islands-b2f", "B2F", "Seafoam Islands B2F GSC.png"),
        _floor("seafoam-islands-b3f", "B3F", "Seafoam Islands B3F GSC.png"),
        _floor("seafoam-islands-b4f", "B4F", "Seafoam Islands B4F GSC.png"),
    ]),
    _loc("cerulean-cave", "Cerulean Cave", [
        _floor("cerulean-cave-1f",  "1F",  "Cerulean Cave 1F GSC.png"),
        _floor("cerulean-cave-b1f", "B1F", "Cerulean Cave B1F GSC.png"),
        _floor("cerulean-cave-2f",  "2F",  "Cerulean Cave 2F GSC.png"),
    ]),
]

_HGSS_CAVE_MAPS: list[dict] = [
    _loc("sprout-tower", "Sprout Tower", [
        _floor("sprout-tower-1f", "1F", "Sprout Tower 1F HGSS.png"),
        _floor("sprout-tower-2f", "2F", "Sprout Tower 2F HGSS.png"),
        _floor("sprout-tower-3f", "3F", "Sprout Tower 3F HGSS.png"),
    ]),
    _loc("union-cave", "Union Cave", [
        _floor("union-cave-1f",  "1F",  "Union Cave 1F HGSS.png"),
        _floor("union-cave-b1f", "B1F", "Union Cave B1F HGSS.png"),
        _floor("union-cave-b2f", "B2F", "Union Cave B2F HGSS.png"),
    ]),
    _loc("slowpoke-well", "Slowpoke Well", [
        _floor("slowpoke-well-b1f", "B1F", "Slowpoke Well B1F HGSS.png"),
        _floor("slowpoke-well-b2f", "B2F", "Slowpoke Well B2F HGSS.png"),
    ]),
    _loc("ilex-forest", "Ilex Forest", [
        _floor("ilex-forest", "Forest", "Ilex Forest HGSS.png"),
    ]),
    _loc("mt-mortar", "Mt. Mortar", [
        _floor("mt-mortar-entrance",   "Entrance",   "Mt Mortar Entrance HGSS.png"),
        _floor("mt-mortar-basement",   "Basement",   "Mt Mortar Basement HGSS.png"),
        _floor("mt-mortar-upper-cave", "Upper Cave", "Mt Mortar Upper Cave HGSS.png"),
        _floor("mt-mortar-lower-cave", "Lower Cave", "Mt Mortar Lower Cave HGSS.png"),
    ]),
    _loc("burned-tower", "Burned Tower", [
        _floor("burned-tower-1f",  "1F",  "Burned Tower 1F HGSS.png"),
        _floor("burned-tower-b1f", "B1F", "Burned Tower B1F HGSS.png"),
    ]),
    _loc("bell-tower", "Bell Tower", [
        _floor("bell-tower-1f",  "1F",  "Bell Tower 1F HGSS.png"),
        _floor("bell-tower-2f",  "2F",  "Bell Tower 2F HGSS.png"),
        _floor("bell-tower-3f",  "3F",  "Bell Tower 3F HGSS.png"),
        _floor("bell-tower-4f",  "4F",  "Bell Tower 4F HGSS.png"),
        _floor("bell-tower-5f",  "5F",  "Bell Tower 5F HGSS.png"),
        _floor("bell-tower-6f",  "6F",  "Bell Tower 6F HGSS.png"),
        _floor("bell-tower-7f",  "7F",  "Bell Tower 7F HGSS.png"),
        _floor("bell-tower-8f",  "8F",  "Bell Tower 8F HGSS.png"),
        _floor("bell-tower-9f",  "9F",  "Bell Tower 9F HGSS.png"),
        _floor("bell-tower-10f", "10F", "Bell Tower 10F HGSS.png"),
    ]),
    _loc("dark-cave", "Dark Cave", [
        _floor("dark-cave-1", "Violet City Side",    "Dark Cave 1 HGSS.png"),
        _floor("dark-cave-2", "Blackthorn City Side","Dark Cave 2 HGSS.png"),
    ]),
    _loc("ice-path", "Ice Path", [
        _floor("ice-path-1f",  "1F",  "Ice Path 1F HGSS.png"),
        _floor("ice-path-b1f", "B1F", "Ice Path B1F HGSS.png"),
        _floor("ice-path-b2f", "B2F", "Ice Path B2F HGSS.png"),
        _floor("ice-path-b3f", "B3F", "Ice Path B3F HGSS.png"),
    ]),
    _loc("dragons-den", "Dragon's Den", [
        _floor("dragons-den-entrance", "Entrance", "Dragons Den Entrance HGSS.png"),
        _floor("dragons-den-interior", "Interior", "Dragons Den HGSS.png"),
    ]),
    _loc("whirl-islands", "Whirl Islands", [
        _floor("whirl-islands-1f-nw", "1F (NW Island)", "Whirl Islands 1F NW HGSS.png"),
        _floor("whirl-islands-1f-ne", "1F (NE Island)", "Whirl Islands 1F NE HGSS.png"),
        _floor("whirl-islands-1f-sw", "1F (SW Island)", "Whirl Islands 1F SW HGSS.png"),
        _floor("whirl-islands-1f-se", "1F (SE Island)", "Whirl Islands 1F SE HGSS.png"),
        _floor("whirl-islands-b1f",   "B1F",            "Whirl Islands B1F HGSS.png"),
        _floor("whirl-islands-b2f",   "B2F",            "Whirl Islands B2F HGSS.png"),
        _floor("whirl-islands-b3f",   "B3F",            "Whirl Islands B3F HGSS.png"),
    ]),
    _loc("mt-silver", "Mt. Silver", [
        _floor("mt-silver-exterior", "Exterior", "Mt. Silver Exterior HGSS.png"),
        _floor("mt-silver-1f",       "1F",       "Mt. Silver 1F HGSS.png"),
        _floor("mt-silver-2f",       "2F",       "Mt. Silver 2F HGSS.png"),
        _floor("mt-silver-3f",       "3F",       "Mt. Silver 3F HGSS.png"),
        _floor("mt-silver-summit",   "Summit",   "Mt. Silver Summit HGSS.png"),
    ]),
    # Kanto dungeons
    _loc("mt-moon", "Mt. Moon", [
        _floor("mt-moon-1f",    "1F",    "Mt Moon 1F HGSS.png"),
        _floor("mt-moon-square","Square","Mt Moon Square HGSS.png"),
    ]),
    _loc("rock-tunnel", "Rock Tunnel", [
        _floor("rock-tunnel-1", "1F",  "Rock Tunnel 1 HGSS.png"),
        _floor("rock-tunnel-2", "B1F", "Rock Tunnel 2 HGSS.png"),
    ]),
    _loc("victory-road-kanto", "Victory Road", [
        _floor("victory-road-kanto-1f", "1F", "Victory Road 1F HGSS.png"),
        _floor("victory-road-kanto-2f", "2F", "Victory Road 2F HGSS.png"),
        _floor("victory-road-kanto-3f", "3F", "Victory Road 3F HGSS.png"),
    ]),
    _loc("seafoam-islands", "Seafoam Islands", [
        _floor("seafoam-islands-1f",  "1F",  "Seafoam Islands 1F HGSS.png"),
        _floor("seafoam-islands-b1f", "B1F", "Seafoam Islands B1F HGSS.png"),
        _floor("seafoam-islands-b2f", "B2F", "Seafoam Islands B2F HGSS.png"),
        _floor("seafoam-islands-b3f", "B3F", "Seafoam Islands B3F HGSS.png"),
        _floor("seafoam-islands-b4f", "B4F", "Seafoam Islands B4F HGSS.png"),
    ]),
    _loc("cerulean-cave", "Cerulean Cave", [
        _floor("cerulean-cave-1f",  "1F",  "Cerulean Cave 1F HGSS.png"),
        _floor("cerulean-cave-b1f", "B1F", "Cerulean Cave B1F HGSS.png"),
        _floor("cerulean-cave-2f",  "2F",  "Cerulean Cave 2F HGSS.png"),
    ]),
]

_RED_CAVE_MAPS: list[dict] = [
    _loc("mt-moon", "Mt. Moon", [
        _floor("mt-moon-1f",  "1F",  "Mt. Moon 1F RBY.png"),
        _floor("mt-moon-b1f", "B1F", "Mt. Moon B1F RBY.png"),
        _floor("mt-moon-b2f", "B2F", "Mt. Moon B2F RBY.png"),
    ]),
    _loc("rock-tunnel", "Rock Tunnel", [
        _floor("rock-tunnel-1f",  "1F",  "Rock Tunnel 1F RBY.png"),
        _floor("rock-tunnel-b1f", "B1F", "Rock Tunnel B1F RBY.png"),
    ]),
    _loc("pokemon-tower", "Pokémon Tower", [
        _floor("pokemon-tower-1f", "1F", "Pokémon Tower 1F RBY.png"),
        _floor("pokemon-tower-2f", "2F", "Pokémon Tower 2F RBY.png"),
        _floor("pokemon-tower-3f", "3F", "Pokémon Tower 3F RBY.png"),
        _floor("pokemon-tower-4f", "4F", "Pokémon Tower 4F RBY.png"),
        _floor("pokemon-tower-5f", "5F", "Pokémon Tower 5F RBY.png"),
        _floor("pokemon-tower-6f", "6F", "Pokémon Tower 6F RBY.png"),
        _floor("pokemon-tower-7f", "7F", "Pokémon Tower 7F RBY.png"),
    ]),
    _loc("silph-co", "Silph Co.", [
        _floor("silph-co-1f",  "1F",  "Silph Co. 1F RBY.png"),
        _floor("silph-co-2f",  "2F",  "Silph Co. 2F RBY.png"),
        _floor("silph-co-3f",  "3F",  "Silph Co. 3F RBY.png"),
        _floor("silph-co-4f",  "4F",  "Silph Co. 4F RBY.png"),
        _floor("silph-co-5f",  "5F",  "Silph Co. 5F RBY.png"),
        _floor("silph-co-6f",  "6F",  "Silph Co. 6F RBY.png"),
        _floor("silph-co-7f",  "7F",  "Silph Co. 7F RBY.png"),
        _floor("silph-co-8f",  "8F",  "Silph Co. 8F RBY.png"),
        _floor("silph-co-9f",  "9F",  "Silph Co. 9F RBY.png"),
        _floor("silph-co-10f", "10F", "Silph Co. 10F RBY.png"),
        _floor("silph-co-11f", "11F", "Silph Co. 11F RBY.png"),
    ]),
    _loc("victory-road", "Victory Road", [
        _floor("victory-road-1f", "1F", "Victory Road 1F RBY.png"),
        _floor("victory-road-2f", "2F", "Victory Road 2F RBY.png"),
        _floor("victory-road-3f", "3F", "Victory Road 3F RBY.png"),
    ]),
    _loc("seafoam-islands", "Seafoam Islands", [
        _floor("seafoam-islands-1f",  "1F",  "Seafoam Islands 1F RBY.png"),
        _floor("seafoam-islands-b1f", "B1F", "Seafoam Islands B1F RBY.png"),
        _floor("seafoam-islands-b2f", "B2F", "Seafoam Islands B2F RBY.png"),
        _floor("seafoam-islands-b3f", "B3F", "Seafoam Islands B3F RBY.png"),
        _floor("seafoam-islands-b4f", "B4F", "Seafoam Islands B4F RBY.png"),
    ]),
    _loc("cerulean-cave", "Cerulean Cave", [
        _floor("cerulean-cave-1f",  "1F",  "Cerulean Cave 1F RBY.png"),
        _floor("cerulean-cave-b1f", "B1F", "Cerulean Cave B1F RBY.png"),
        _floor("cerulean-cave-2f",  "2F",  "Cerulean Cave 2F RBY.png"),
    ]),
    _loc("power-plant", "Power Plant", [
        _floor("power-plant", "Interior", "Power Plant RBY.png"),
    ]),
    # FRLG-only locations (not present in RBY)
    _loc("mt-ember", "Mt. Ember", [
        _floor("mt-ember-exterior",       "Exterior",         "Mt Ember FRLG.png"),
        _floor("mt-ember-summit",         "Summit",           "Mt. Ember Summit FRLG.png"),
        _floor("mt-ember-summit-path-1f", "Summit Path 1F",   "Mt. Ember Summit Path 1F FRLG.png"),
        _floor("mt-ember-summit-path-2f", "Summit Path 2F",   "Mt. Ember Summit Path 2F FRLG.png"),
        _floor("mt-ember-summit-path-3f", "Summit Path 3F",   "Mt. Ember Summit Path 3F FRLG.png"),
        _floor("mt-ember-ruby-path-b1f",  "Ruby Path B1F",    "Ruby Path B1F FRLG.png"),
        _floor("mt-ember-ruby-path-b3f",  "Ruby Path B3F",    "Ruby Path B3F FRLG.png"),
        _floor("mt-ember-ruby-path-b4f",  "Ruby Path B4F",    "Ruby Path B4F FRLG.png"),
        _floor("mt-ember-ruby-path-b5f",  "Ruby Path B5F",    "Ruby Path B5F FRLG.png"),
    ]),
]

_EMERALD_CAVE_MAPS: list[dict] = [
    _loc("granite-cave", "Granite Cave", [
        _floor("granite-cave-1f",  "1F",  "Granite Cave 1F E.png"),
        _floor("granite-cave-b1f", "B1F", "Granite Cave B1F E.png"),
        _floor("granite-cave-b2f", "B2F", "Granite Cave B2F E.png"),
    ]),
    _loc("meteor-falls", "Meteor Falls", [
        _floor("meteor-falls-entrance",  "Entrance",  "Meteor Falls 1F 1R E.png"),
        _floor("meteor-falls-1f-1r",     "1F, 1R",    "Meteor Falls 1F 1R E.png"),
        _floor("meteor-falls-b1f-1r",    "B1F, 1R",   "Meteor Falls B1F 1R E.png"),
        _floor("meteor-falls-b1f-2r",    "B1F, 2R",   "Meteor Falls B1F 2R E.png"),
    ]),
    _loc("mt-chimney", "Mt. Chimney", [
        _floor("mt-chimney", "Summit", "Mt. Chimney E.png"),
    ]),
    _loc("jagged-pass", "Jagged Pass", [
        _floor("jagged-pass", "Exterior", "Jagged Pass E.png"),
    ]),
    _loc("fiery-path", "Fiery Path", [
        _floor("fiery-path", "Interior", "Fiery Path E.png"),
    ]),
    _loc("seafloor-cavern", "Seafloor Cavern", [
        _floor("seafloor-cavern-entrance", "Entrance",  "Seafloor Cavern Entrance E.png"),
        _floor("seafloor-cavern-room1",    "Room 1",    "Seafloor Cavern Room 1 E.png"),
        _floor("seafloor-cavern-room2",    "Room 2",    "Seafloor Cavern Room 2 E.png"),
        _floor("seafloor-cavern-room3",    "Room 3",    "Seafloor Cavern Room 3 E.png"),
        _floor("seafloor-cavern-room4",    "Room 4",    "Seafloor Cavern Room 4 E.png"),
        _floor("seafloor-cavern-room5",    "Room 5",    "Seafloor Cavern Room 5 E.png"),
        _floor("seafloor-cavern-room6",    "Room 6",    "Seafloor Cavern Room 6 E.png"),
        _floor("seafloor-cavern-room7",    "Room 7",    "Seafloor Cavern Room 7 E.png"),
        _floor("seafloor-cavern-room8",    "Room 8",    "Seafloor Cavern Room 8 E.png"),
        _floor("seafloor-cavern-room9",    "Room 9",    "Seafloor Cavern Room 9 E.png"),
    ]),
    _loc("cave-of-origin", "Cave of Origin", [
        _floor("cave-of-origin-1f",  "1F",  "Cave of Origin 1F E.png"),
        _floor("cave-of-origin-b1f", "B1F", "Cave of Origin B1F E.png"),
    ]),
    _loc("shoal-cave", "Shoal Cave", [
        _floor("shoal-cave-lowtide-entrance",  "Low Tide Entrance",  "Shoal Cave Low Tide Entrance E.png"),
        _floor("shoal-cave-lowtide-inner",     "Low Tide Inner Room","Shoal Cave Low Tide Inner Room E.png"),
        _floor("shoal-cave-hightide-entrance", "High Tide Entrance", "Shoal Cave High Tide Entrance E.png"),
        _floor("shoal-cave-hightide-inner",    "High Tide Inner Room","Shoal Cave High Tide Inner Room E.png"),
    ]),
    _loc("sky-pillar", "Sky Pillar", [
        _floor("sky-pillar-1f", "1F", "Sky Pillar 1F E.png"),
        _floor("sky-pillar-2f", "2F", "Sky Pillar 2F E.png"),
        _floor("sky-pillar-3f", "3F", "Sky Pillar 3F E.png"),
        _floor("sky-pillar-4f", "4F", "Sky Pillar 4F E.png"),
        _floor("sky-pillar-5f", "5F", "Sky Pillar 5F E.png"),
        _floor("sky-pillar-roof", "Roof", "Sky Pillar Roof E.png"),
    ]),
    _loc("victory-road", "Victory Road", [
        _floor("victory-road-1f", "1F", "Victory Road 1F E.png"),
        _floor("victory-road-b1f","B1F","Victory Road B1F E.png"),
    ]),
]

_PLATINUM_CAVE_MAPS: list[dict] = [
    _loc("oreburgh-gate", "Oreburgh Gate", [
        _floor("oreburgh-gate-1f",  "1F",  "Oreburgh Gate 1F Pt.png"),
        _floor("oreburgh-gate-b1f", "B1F", "Oreburgh Gate B1F Pt.png"),
    ]),
    _loc("oreburgh-mine", "Oreburgh Mine", [
        _floor("oreburgh-mine-1f",  "1F",  "Oreburgh Mine 1F Pt.png"),
        _floor("oreburgh-mine-b1f", "B1F", "Oreburgh Mine B1F Pt.png"),
    ]),
    _loc("mt-coronet", "Mt. Coronet", [
        _floor("mt-coronet-1f",      "1F",          "Mt. Coronet 1F Pt.png"),
        _floor("mt-coronet-2f",      "2F",          "Mt. Coronet 2F Pt.png"),
        _floor("mt-coronet-3f",      "3F",          "Mt. Coronet 3F Pt.png"),
        _floor("mt-coronet-4f",      "4F",          "Mt. Coronet 4F Pt.png"),
        _floor("mt-coronet-5f",      "5F",          "Mt. Coronet 5F Pt.png"),
        _floor("mt-coronet-6f",      "6F",          "Mt. Coronet 6F Pt.png"),
        _floor("mt-coronet-exterior","Exterior",     "Mt. Coronet Exterior Pt.png"),
        _floor("mt-coronet-summit",  "Summit",       "Spear Pillar Pt.png"),
    ]),
    _loc("wayward-cave", "Wayward Cave", [
        _floor("wayward-cave-1f", "1F", "Wayward Cave 1F Pt.png"),
        _floor("wayward-cave-2f", "2F", "Wayward Cave 2F Pt.png"),
    ]),
    _loc("mt-coronet-b1f", "Mt. Coronet (Underground)", [
        _floor("mt-coronet-b1f", "B1F", "Mt. Coronet B1F Pt.png"),
    ]),
    _loc("iron-island", "Iron Island", [
        _floor("iron-island-1f",  "1F",  "Iron Island 1F Pt.png"),
        _floor("iron-island-b1f", "B1F", "Iron Island B1F Pt.png"),
        _floor("iron-island-b2f", "B2F", "Iron Island B2F Pt.png"),
    ]),
    _loc("victory-road-sinnoh", "Victory Road", [
        _floor("victory-road-sinnoh-1f", "1F", "Victory Road 1F Pt.png"),
        _floor("victory-road-sinnoh-2f", "2F", "Victory Road 2F Pt.png"),
        _floor("victory-road-sinnoh-3f", "3F", "Victory Road 3F Pt.png"),
    ]),
    _loc("snowpoint-temple", "Snowpoint Temple", [
        _floor("snowpoint-temple-1f",  "1F",  "Snowpoint Temple 1F Pt.png"),
        _floor("snowpoint-temple-2f",  "2F",  "Snowpoint Temple 2F Pt.png"),
        _floor("snowpoint-temple-3f",  "3F",  "Snowpoint Temple 3F Pt.png"),
        _floor("snowpoint-temple-4f",  "4F",  "Snowpoint Temple 4F Pt.png"),
        _floor("snowpoint-temple-5f",  "5F",  "Snowpoint Temple 5F Pt.png"),
    ]),
    _loc("distortion-world", "Distortion World", [
        _floor("distortion-world", "Interior", "Distortion World Pt.png"),
    ]),
]

_UNOVA_CAVE_MAPS: list[dict] = [
    _loc("wellspring-cave", "Wellspring Cave", [
        _floor("wellspring-cave-b1f", "B1F", "Wellspring Cave B1F BW.png"),
        _floor("wellspring-cave-b2f", "B2F", "Wellspring Cave B2F BW.png"),
    ]),
    _loc("relic-castle", "Relic Castle", [
        _floor("relic-castle-1f",  "1F",  "Relic Castle 1F BW.png"),
        _floor("relic-castle-b1f", "B1F", "Relic Castle B1F BW.png"),
        _floor("relic-castle-b2f", "B2F", "Relic Castle B2F BW.png"),
        _floor("relic-castle-b3f", "B3F", "Relic Castle B3F BW.png"),
        _floor("relic-castle-b4f", "B4F", "Relic Castle B4F BW.png"),
        _floor("relic-castle-b5f", "B5F", "Relic Castle B5F BW.png"),
        _floor("relic-castle-b6f", "B6F", "Relic Castle B6F BW.png"),
        _floor("relic-castle-b7f", "B7F", "Relic Castle B7F BW.png"),
    ]),
    _loc("castelia-sewers", "Castelia Sewers", [
        _floor("castelia-sewers-b1f", "B1F", "Castelia Sewers BW.png"),
    ]),
    _loc("cold-storage", "Cold Storage", [
        _floor("cold-storage-b1f", "B1F", "Cold Storage BW.png"),
    ]),
    _loc("chargestone-cave", "Chargestone Cave", [
        _floor("chargestone-cave-b1f", "B1F", "Chargestone Cave B1F BW.png"),
        _floor("chargestone-cave-b2f", "B2F", "Chargestone Cave B2F BW.png"),
        _floor("chargestone-cave-b3f", "B3F", "Chargestone Cave B3F BW.png"),
    ]),
    _loc("celestial-tower", "Celestial Tower", [
        _floor("celestial-tower-2f", "2F", "Celestial Tower 2F BW.png"),
        _floor("celestial-tower-3f", "3F", "Celestial Tower 3F BW.png"),
        _floor("celestial-tower-4f", "4F", "Celestial Tower 4F BW.png"),
        _floor("celestial-tower-5f", "5F", "Celestial Tower 5F BW.png"),
    ]),
    _loc("twist-mountain", "Twist Mountain", [
        _floor("twist-mountain-1f",  "1F",  "Twist Mountain 1F BW.png"),
        _floor("twist-mountain-b1f", "B1F", "Twist Mountain B1F BW.png"),
        _floor("twist-mountain-b2f", "B2F", "Twist Mountain B2F BW.png"),
    ]),
    _loc("dragonspiral-tower", "Dragonspiral Tower", [
        _floor("dragonspiral-tower-exterior", "Exterior", "Dragonspiral Tower Exterior BW.png"),
        _floor("dragonspiral-tower-1f",       "1F",       "Dragonspiral Tower 1F BW.png"),
        _floor("dragonspiral-tower-2f",       "2F",       "Dragonspiral Tower 2F BW.png"),
        _floor("dragonspiral-tower-3f",       "3F",       "Dragonspiral Tower 3F BW.png"),
        _floor("dragonspiral-tower-4f",       "4F",       "Dragonspiral Tower 4F BW.png"),
        _floor("dragonspiral-tower-5f",       "5F",       "Dragonspiral Tower 5F BW.png"),
        _floor("dragonspiral-tower-6f",       "6F",       "Dragonspiral Tower 6F BW.png"),
        _floor("dragonspiral-tower-7f",       "7F",       "Dragonspiral Tower 7F BW.png"),
    ]),
    _loc("victory-road", "Victory Road", [
        _floor("victory-road-exterior", "Exterior", "Victory Road Exterior BW.png"),
        _floor("victory-road-1f",       "1F",       "Victory Road 1F BW.png"),
        _floor("victory-road-2f",       "2F",       "Victory Road 2F BW.png"),
    ]),
    # BW2-only locations
    _loc("virbank-complex", "Virbank Complex", [
        _floor("virbank-complex-outside", "Outside", "Virbank Complex Outside BW2.png"),
        _floor("virbank-complex-inside",  "Inside",  "Virbank Complex Inside BW2.png"),
    ]),
    _loc("seaside-cave", "Seaside Cave", [
        _floor("seaside-cave-1f",  "1F",  "Seaside Cave 1F BW2.png"),
        _floor("seaside-cave-b1f", "B1F", "Seaside Cave B1F BW2.png"),
    ]),
    _loc("giant-chasm", "Giant Chasm", [
        _floor("giant-chasm-exterior", "Exterior", "Giant Chasm BW2.png"),
        _floor("giant-chasm-forest",   "Forest",   "Giant Chasm Forest BW2.png"),
        _floor("giant-chasm-cave",     "Cave",     "Giant Chasm Cave BW2.png"),
    ]),
]

_KALOS_CAVE_MAPS: list[dict] = [
    _loc("connecting-cave", "Connecting Cave", [
        _floor("connecting-cave-1f", "1F", "Connecting Cave XY.png"),
    ]),
    _loc("glittering-cave", "Glittering Cave", [
        _floor("glittering-cave", "Interior", "Glittering Cave XY.png"),
    ]),
    _loc("frost-cavern", "Frost Cavern", [
        _floor("frost-cavern-1f",  "1F",  "Frost Cavern 1F XY.png"),
        _floor("frost-cavern-b1f", "B1F", "Frost Cavern B1F XY.png"),
        _floor("frost-cavern-b2f", "B2F", "Frost Cavern B2F XY.png"),
    ]),
    _loc("terminus-cave", "Terminus Cave", [
        _floor("terminus-cave-b1f", "B1F", "Terminus Cave B1F XY.png"),
        _floor("terminus-cave-b2f", "B2F", "Terminus Cave B2F XY.png"),
        _floor("terminus-cave-b3f", "B3F", "Terminus Cave B3F XY.png"),
    ]),
    _loc("victory-road", "Victory Road", [
        _floor("victory-road-exterior", "Exterior", "Victory Road Exterior XY.png"),
        _floor("victory-road-1f",       "1F",       "Victory Road 1F XY.png"),
        _floor("victory-road-2f",       "2F",       "Victory Road 2F XY.png"),
    ]),
]

CAVE_MAPS: dict[str, list[dict]] = {
    "heartgold": _HGSS_CAVE_MAPS,
    "gold":      _GSC_CAVE_MAPS,
    "red":       _RED_CAVE_MAPS,
    "emerald":   _EMERALD_CAVE_MAPS,
    "platinum":  _PLATINUM_CAVE_MAPS,
    "black":     _UNOVA_CAVE_MAPS,
    "x":         _KALOS_CAVE_MAPS,
}
# Aliases
for _a, _b in [
    ("soulsilver", "heartgold"),
    ("silver", "gold"), ("crystal", "gold"),
    ("blue", "red"), ("yellow", "red"), ("firered", "red"), ("leafgreen", "red"),
    ("ruby", "emerald"), ("sapphire", "emerald"),
    ("omega-ruby", "emerald"), ("alpha-sapphire", "emerald"),
    ("diamond", "platinum"), ("pearl", "platinum"),
    ("white", "black"), ("black-2", "black"), ("white-2", "black"),
    ("y", "x"),
]:
    CAVE_MAPS.setdefault(_a, CAVE_MAPS.get(_b, []))


# ── Trainer route assignments ──────────────────────────────────────────────────
# Maps trainer name → route_id(s) for rivals (list, one per battle group) and
# E4/champion (str, the single route they occupy).
#
# Rival battle groups are detected automatically by cycling player_starter values
# (see transform._group_rival_battles). Bulbapedia rival pages do NOT use
# per-location section headings, so these mappings are hand-authored.
#
# Route IDs must match entries in ROUTE_ORDER. Set an entry to None to skip a
# battle group (it won't appear on any floor). Games not listed here produce no
# trainer encounters in the route data.

_SS_HOENN_RIVAL = [
    "route-103",        # 1 — Professor Birch's field (starter match)
    "route-110",        # 2 — Cycling Road approach (after Slateport)
    "mauville-city",    # 3 — before / after Wattson's gym
    "mt-pyre",          # 4 — summit during Magma/Aqua raid
    "lilycove-city",    # 5 — rival's house area after hideout raid
    "ever-grande-city", # 6 — before Victory Road entrance
]

TRAINER_ROUTES: dict[str, dict[str, list[str | None] | str]] = {

    # ── Gen 1: Red / Blue / Yellow / FireRed / LeafGreen ──────────────────────
    # Gary's 6 rival battles before the champion phase.
    # Champion phase is covered by the separate "Blue" champion entry.
    # Bulbapedia page: "Blue (game)"; game codes RGB / Y / FRLG.
    "red": {
        "Gary": [
            "pallet-town",    # 1 — Oak's lab (1 starter each)
            "route-22",       # 2 — south of Viridian, before forest
            "cerulean-city",  # 3 — Nugget Bridge area
            "ss-anne",        # 4 — ship cabin
            "lavender-town",  # 5 — Pokémon Tower
            "saffron-city",   # 6 — Silph Co.
        ],
        "Blue":    "pokemon-league",
        "Lorelei": "pokemon-league",
        "Bruno":   "pokemon-league",
        "Agatha":  "pokemon-league",
        "Lance":   "pokemon-league",
    },

    # ── Gen 2: Gold / Silver / Crystal ────────────────────────────────────────
    # Route IDs shared with HGSS (ROUTE_ORDER["gold"] = ROUTE_ORDER["heartgold"]).
    # GSC Silver has 5 battle groups vs 8 in HGSS; groups beyond this list are
    # silently dropped by transform.
    "gold": {
        "Silver": [
            "cherrygrove-city",   # 1 — first encounter (stolen starter)
            "azalea-town",        # 2 — after Team Rocket at Slowpoke Well
            "burned-tower",       # 3 — beast release event
            "goldenrod-city",     # 4 — Radio Tower rescue
            "victory-road-kanto", # 5 — pre-E4 Kanto encounter
        ],
        "Will":  "pokemon-league",
        "Koga":  "pokemon-league",
        "Bruno": "pokemon-league",
        "Karen": "pokemon-league",
        "Lance": "pokemon-league",
        "Red":   "mt-silver",     # postgame boss at Mt. Silver summit (lv60–65 team)
    },

    # ── Gen 2: HeartGold / SoulSilver ─────────────────────────────────────────
    # Silver's 8 battle groups × 3 starter variants = 24 raw Bulbapedia entries.
    # Groups 0–5: Johto + early Kanto; groups 6–7: late Kanto / post-game.
    "heartgold": {
        "Silver": [
            "cherrygrove-city",   # 1 — first encounter (stolen starter, lv5)
            "azalea-town",        # 2 — after Team Rocket at Slowpoke Well
            "burned-tower",       # 3 — B1F, legendary beast release
            "goldenrod-city",     # 4 — Radio Tower rescue
            "mt-moon",            # 5 — Kanto (Monday night event)
            "victory-road-kanto", # 6 — before the Kanto E4 gate
            "pokemon-league",     # 7 — Indigo Plateau (pre-Lance area)
            "mt-silver",          # 8 — final encounter (post-16 badges)
        ],
        "Will":  "pokemon-league",
        "Koga":  "pokemon-league",
        "Bruno": "pokemon-league",
        "Karen": "pokemon-league",
        "Lance": "pokemon-league",
        "Red":   "mt-silver",     # postgame boss at Mt. Silver summit (lv80 team)
    },

    # ── Gen 3: Ruby / Sapphire ────────────────────────────────────────────────
    # Both Brendan and May appear as the rival (one per playthrough); both are
    # scraped from Bulbapedia and mapped to the same route sequence.
    "ruby": {
        "Brendan": _SS_HOENN_RIVAL,
        "May":     _SS_HOENN_RIVAL,
        "Wally":   ["victory-road"],  # single mandatory battle pre-E4
        "Maxie":   "route-112",       # Team Magma boss (Mt. Chimney; route-112 is best available proxy)
        "Archie":  "route-128",       # Team Aqua boss (Seafloor Cavern; route-128 is best available proxy)
        "Sidney":  "pokemon-league",
        "Phoebe":  "pokemon-league",
        "Glacia":  "pokemon-league",
        "Drake":   "pokemon-league",
        "Steven":  "pokemon-league",
    },

    # Emerald keeps the same rival route sequence; Wallace replaces Steven.
    "emerald": {
        "Brendan": _SS_HOENN_RIVAL,
        "May":     _SS_HOENN_RIVAL,
        "Wally":   ["route-110", "victory-road"],  # Wattson area + pre-E4
        "Maxie":   "route-112",                    # Team Magma boss (Mt. Chimney approach)
        "Archie":  "route-128",                    # Team Aqua boss (near Seafloor Cavern)
        "Sidney":  "pokemon-league",
        "Phoebe":  "pokemon-league",
        "Glacia":  "pokemon-league",
        "Drake":   "pokemon-league",
        "Wallace": "pokemon-league",
    },

    # ── Gen 4: Diamond / Pearl / Platinum ─────────────────────────────────────
    # Barry has ~7 rival battles; the last one is just before Victory Road.
    "diamond": {
        "Barry": [
            "twinleaf-town",  # 1 — first battle (1 starter each)
            "sandgem-town",   # 2 — after getting Pokédex from Rowan
            "jubilife-city",  # 3 — early Jubilife encounter
            "hearthome-city", # 4 — Contest Hall area
            "pastoria-city",  # 5 — after Crasher Wake's gym
            "canalave-city",  # 6 — before Iron Island / Byron's gym
            "victory-road",   # 7 — pre-E4
        ],
        "Cyrus":  "mt-coronet",     # Team Galactic boss at Spear Pillar
        "Aaron":  "pokemon-league",
        "Bertha": "pokemon-league",
        "Flint":  "pokemon-league",
        "Lucian": "pokemon-league",
        "Cynthia":"pokemon-league",
    },

    # ── Gen 5: Black / White ──────────────────────────────────────────────────
    # Cheren battles you after almost every gym; Bianca is more sporadic.
    # N has 4 mandatory battles; scraper gives team (first) and rematch_team (last),
    # so we place him at the League where his final Reshiram/Zekrom team appears.
    "black": {
        "Cheren": [
            "nuvema-town",      # 1 — your room at the very start
            "striaton-city",    # 2 — after first gym
            "nacrene-city",     # 3 — after Lenora's gym
            "nimbasa-city",     # 4 — Nimbasa area
            "mistralton-city",  # 5 — after Skyla's gym
            "opelucid-city",    # 6 — before 8th gym
            "victory-road",     # 7 — pre-E4
        ],
        "Bianca": [
            "striaton-city",    # 1 — near first gym
            "nacrene-city",     # 2 — museum area
            "castelia-city",    # 3 — Castelia sewers vicinity
            "nimbasa-city",     # 4 — Ferris Wheel area
            "route-5",          # 5 — Driftveil Drawbridge approach
            "chargestone-cave", # 6 — cave entrance
            "victory-road",     # 7 — pre-E4
        ],
        "N":        "pokemon-league",  # final battle (Reshiram/Zekrom)
        "Ghetsis":  "pokemon-league",  # immediately after N
        "Shauntal": "pokemon-league",
        "Grimsley": "pokemon-league",
        "Caitlin":  "pokemon-league",
        "Marshal":  "pokemon-league",
        "Alder":    "pokemon-league",
    },

    # Gen 5: Black 2 / White 2
    # Hugh has 6 rival battles across the story; N and Ghetsis both appear at
    # Giant Chasm near the endgame.
    "black-2": {
        "Hugh": [
            "floccesy-ranch",  # 1 — ranch robbery confrontation
            "virbank-city",    # 2 — outside Roxie's gym
            "castelia-city",   # 3 — Castelia sewers
            "nimbasa-city",    # 4 — stadiums area
            "opelucid-city",   # 5 — after Drayden's gym
            "victory-road",    # 6 — pre-E4
        ],
        "N":        "giant-chasm",     # postgame encounter at Giant Chasm
        "Ghetsis":  "giant-chasm",     # final boss at Giant Chasm
        "Iris":     "pokemon-league",
        "Shauntal": "pokemon-league",
        "Grimsley": "pokemon-league",
        "Caitlin":  "pokemon-league",
        "Marshal":  "pokemon-league",
    },

    # ── Gen 6: X / Y ──────────────────────────────────────────────────────────
    # Calem and Serena are the two rival options; same battle sequence for both.
    "x": {
        "Calem": [
            "aquacorde-town",   # 1 — Pokémon received from Sycamore's aide
            "santalune-forest", # 2 — in the forest
            "route-4",          # 3 — Lumiose approach
            "shalour-city",     # 4 — Tower of Mastery
            "coumarine-city",   # 5 — after Ramos's gym
            "lumiose-city",     # 6 — second Lumiose visit
            "laverre-city",     # 7 — after Valerie's gym area
            "anistar-city",     # 8 — after Olympia's gym
            "victory-road",     # 9 — pre-E4
        ],
        "Serena": [
            "aquacorde-town",
            "santalune-forest",
            "route-4",
            "shalour-city",
            "coumarine-city",
            "lumiose-city",
            "laverre-city",
            "anistar-city",
            "victory-road",
        ],
        "Lysandre": [
            "lumiose-city",     # 1 — Lysandre Café (mandatory story battle)
            "geosenge-town",    # 2 — Team Flare Secret HQ entrance
        ],
        "Malva":    "pokemon-league",
        "Siebold":  "pokemon-league",
        "Wikstrom": "pokemon-league",
        "Drasna":   "pokemon-league",
        "Diantha":  "pokemon-league",
    },

    # ── Gen 7: Sun / Moon / Ultra Sun / Ultra Moon ────────────────────────────
    # Hau battles you throughout the island challenge; Gladion has a shorter arc.
    # Guzma and Lusamine are class "boss" and have 2 mandatory battles each.
    # Note: Hala is listed as gym_leader in TRAINER_DEFS (Grand Trial kahuna)
    # rather than elite_four, so he does not appear here.
    "sun": {
        "Hau": [
            "iki-town",          # 1 — Iki Town festival ceremony
            "hauoli-city",       # 2 — Hau'oli City outskirts
            "paniola-ranch",     # 3 — Akala Island, Paniola Ranch
            "royal-avenue",      # 4 — Royal Avenue (after Brooklet / Wela)
            "malie-city",        # 5 — Ula'ula Island
            "ancient-poni-path", # 6 — Poni Island
            "mount-lanakila",    # 7 — final encounter before E4
        ],
        "Gladion": [
            "aether-house",      # 1 — Route 15 / Aether House warning
            "po-town",           # 2 — Team Skull's Po Town
            "aether-paradise",   # 3 — rescue mission
            "mount-lanakila",    # 4 — final encounter
        ],
        "Guzma":    "po-town",        # Team Skull boss (most important battle)
        "Lusamine":  "aether-paradise", # Aether Foundation boss
        "Molayne":  "pokemon-league",
        "Olivia":   "pokemon-league",
        "Acerola":  "pokemon-league",
        "Kahili":   "pokemon-league",
        "Kukui":    "pokemon-league",
    },
}

# ── Aliases ────────────────────────────────────────────────────────────────────
TRAINER_ROUTES["blue"]          = TRAINER_ROUTES["red"]
TRAINER_ROUTES["yellow"]        = TRAINER_ROUTES["red"]
TRAINER_ROUTES["firered"]       = TRAINER_ROUTES["red"]
TRAINER_ROUTES["leafgreen"]     = TRAINER_ROUTES["red"]
TRAINER_ROUTES["silver"]        = TRAINER_ROUTES["gold"]
TRAINER_ROUTES["crystal"]       = TRAINER_ROUTES["gold"]
TRAINER_ROUTES["soulsilver"]    = TRAINER_ROUTES["heartgold"]
TRAINER_ROUTES["sapphire"]      = TRAINER_ROUTES["ruby"]
TRAINER_ROUTES["omega-ruby"]    = TRAINER_ROUTES["ruby"]
TRAINER_ROUTES["alpha-sapphire"]= TRAINER_ROUTES["ruby"]
TRAINER_ROUTES["pearl"]         = TRAINER_ROUTES["diamond"]
TRAINER_ROUTES["platinum"]      = TRAINER_ROUTES["diamond"]
TRAINER_ROUTES["white"]         = TRAINER_ROUTES["black"]
TRAINER_ROUTES["white-2"]       = TRAINER_ROUTES["black-2"]
TRAINER_ROUTES["y"]             = TRAINER_ROUTES["x"]
TRAINER_ROUTES["moon"]          = TRAINER_ROUTES["sun"]
TRAINER_ROUTES["ultra-sun"]     = TRAINER_ROUTES["sun"]
TRAINER_ROUTES["ultra-moon"]    = TRAINER_ROUTES["sun"]
