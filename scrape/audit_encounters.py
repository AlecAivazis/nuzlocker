#!/usr/bin/env python3
"""
Audit every game's encounter coverage using the local PokeAPI cache.
Prints a compact report of routes/dungeon floors that have 0 encounters.
"""
import hashlib, json, sys
from collections import defaultdict
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
POKEAPI   = "https://pokeapi.co/api/v2"

sys.path.insert(0, str(Path(__file__).parent))
from game_data import GAME_STATIC, CAVE_MAPS, ROUTE_ORDER

# ── helpers ──────────────────────────────────────────────────────────────────

def _cache_path(url: str) -> Path:
    key = url + "{}"
    return CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest() + ".json")

def _load_area(area_slug: str) -> dict | None:
    p = _cache_path(f"{POKEAPI}/location-area/{area_slug}")
    if not p.exists():
        return None
    return json.loads(p.read_text())

# Build a mega-index: location_slug → {version → [pokemon_names]}
# from all cached location-area files that contain encounters.
print("Building encounter index from cache…", end=" ", flush=True)
_area_version_mons: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))  # area → version → mons

def _build_index():
    # First, load the area list to get all area slugs
    all_area_slugs: list[str] = []
    for f in CACHE_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if isinstance(d, dict) and "results" in d and "count" in d:
            for r in d.get("results", []):
                if "name" in r:
                    all_area_slugs.append(r["name"])
    
    # Now load each area and index encounters by location → version
    loc_version_mons: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    area_version_mons: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    
    for slug in all_area_slugs:
        d = _load_area(slug)
        if not d or not isinstance(d, dict):
            continue
        loc = d.get("location", {}).get("name", "")
        for pe in d.get("pokemon_encounters", []):
            pname = pe["pokemon"]["name"]
            for vd in pe.get("version_details", []):
                ver = vd["version"]["name"]
                if vd.get("encounter_details"):
                    loc_version_mons[loc][ver].add(pname)
                    area_version_mons[slug][ver].add(pname)
    return loc_version_mons, area_version_mons

loc_ver_mons, area_ver_mons = _build_index()
print(f"indexed {len(loc_ver_mons)} locations, {len(area_ver_mons)} areas.")

# ── region strip (mirrors transform.py) ──────────────────────────────────────
_REGION_PREFIXES = ("johto-", "kanto-", "hoenn-", "sinnoh-", "unova-", "kalos-", "alola-")

def _strip_region(loc: str) -> str:
    for prefix in _REGION_PREFIXES:
        if loc.startswith(prefix):
            loc = loc[len(prefix):]
            break
    if loc.startswith("sea-route-"):
        loc = loc[4:]
    return loc

# Known always-empty location IDs (towns, buildings, story-only, or PokeAPI version gaps).
_EXPECTED_EMPTY = {
    # ── Gen 1 ────────────────────────────────────────────────────────────────────
    "ss-anne",              # ship; no wild encounters

    # ── Gen 2 ────────────────────────────────────────────────────────────────────
    "embedded-tower",       # HGSS legendary location; absent from GSC route_order
    "bell-tower-10f",       # top of Bell Tower; Lugia chamber in HGSS, no GSC data
    "mt-silver-3f",         # no encounter data in any Gen 2 cache entry

    # ── Johto towns / cities ─────────────────────────────────────────────────────
    "new-bark-town", "cherrygrove-city", "violet-city", "azalea-town",
    "goldenrod-city", "ecruteak-city", "olivine-city", "cianwood-city",
    "mahogany-town", "blackthorn-city", "pokemon-league",

    # ── Kanto towns / cities (GSC + HGSS + FRLG + RBY) ─────────────────────────
    "lavender-town", "vermilion-city", "cerulean-city",
    "pallet-town", "pewter-city", "fuchsia-city", "saffron-city",
    "celadon-city", "cinnabar-island",

    # ── Misc buildings (shared across gens) ──────────────────────────────────────
    "mr-pokemons-house", "team-rocket-hq", "team-aqua-hideout",
    "team-magma-hideout", "pokemon-mansion",

    # ── Dungeon entrances / rooms with no wild encounters ────────────────────────
    "dragons-den-entrance", "bell-tower-1f", "sprout-tower-1f",
    "distortion-world",
    # Whirl Islands — only the NW 1F has encounters; other entrances are dead-ends
    "whirl-islands-1f-ne", "whirl-islands-1f-sw", "whirl-islands-1f-se",
    # RSE/ORAS — rooms / floors with no encounter tables
    "mt-chimney", "meteor-falls-entrance",
    "seafloor-cavern-room1","seafloor-cavern-room2","seafloor-cavern-room3",
    "seafloor-cavern-room4","seafloor-cavern-room5","seafloor-cavern-room6",
    "seafloor-cavern-room7","seafloor-cavern-room8","seafloor-cavern-room9",
    "shoal-cave-hightide-inner",
    "sky-pillar-2f", "sky-pillar-4f", "sky-pillar-roof",
    # Silph Co. (no wild encounters)
    "silph-co-1f","silph-co-2f","silph-co-3f","silph-co-4f","silph-co-5f",
    "silph-co-6f","silph-co-7f","silph-co-8f","silph-co-9f","silph-co-10f","silph-co-11f",
    # Pokémon Tower 1F/2F (ghost section starts 3F)
    "pokemon-tower-1f", "pokemon-tower-2f",
    # FRLG mt-ember — deepest floor; no encounter data
    "mt-ember-ruby-path-b5f",
    # Dragonspiral Tower middle floors — no encounter tables
    "dragonspiral-tower-3f","dragonspiral-tower-4f",
    "dragonspiral-tower-5f","dragonspiral-tower-6f",
    # Victory Road Unova 1F — no encounter data
    "victory-road-1f",
    # Relic Castle deeper floors — no encounter data
    "relic-castle-b4f","relic-castle-b5f","relic-castle-b6f","relic-castle-b7f",
    # BW Wellspring Cave B2F
    "wellspring-cave-b2f",
    # Twist Mountain 1F
    "twist-mountain-1f",
    # GSC Kanto — floors with no encounter data
    "mt-moon-b1f", "mt-moon-b2f", "mt-moon-square",
    # Cerulean Cave / Seafoam Islands — inaccessible in GSC Johto
    "cerulean-cave-1f", "cerulean-cave-b1f", "cerulean-cave-2f",
    "seafoam-islands-1f","seafoam-islands-b1f","seafoam-islands-b2f",
    "seafoam-islands-b3f","seafoam-islands-b4f",
    # FRLG: PokeAPI has no red/blue encounters for this area
    "rock-tunnel-1f",
    # Power Plant: PokeAPI has no HGSS encounter data
    "power-plant",
    # Sinnoh Victory Road 2F (no encounter data)
    "victory-road-2f",

    # ── Hoenn towns / cities (Ruby / Sapphire / Emerald / ORAS) ─────────────────
    "littleroot-town", "oldale-town", "petalburg-city", "rustboro-city",
    "dewford-town", "mauville-city", "fortree-city",
    "sootopolis-city", "pacifidlog-town", "ever-grande-city",

    # ── Sinnoh towns / cities ────────────────────────────────────────────────────
    "sandgem-town", "jubilife-city", "floaroma-town",
    "solaceon-town", "veilstone-city", "snowpoint-city",
    # Spear Pillar — story event location; no wild encounters
    "mt-coronet-summit",

    # ── Unova towns / transit (BW1) ──────────────────────────────────────────────
    "accumula-town", "nacrene-city", "skyarrow-bridge",
    "nimbasa-city", "mistralton-city", "lacunosa-town", "opelucid-city",

    # ── Unova BW2 transit / replaced areas ──────────────────────────────────────
    "marine-tube",          # underwater tunnel; no wild encounters
    # Cold Storage replaced by Pokemon World Tournament in BW2;
    # cold-storage-area only has BW1 data in PokeAPI
    "cold-storage-b1f",
    # Castelia Sewers: no wild encounters in BW1 (story-only visit); wild Pokemon
    # (Grimer) only added in BW2. PokeAPI confirms BW2-only data for these areas.
    "castelia-sewers-b1f",

    # ── Kalos towns / cities / no-encounter areas ────────────────────────────────
    "vaniville-town",
    "route-1",              # Kalos Route 1: intro path with no wild Pokémon
    "santalune-city", "camphrier-town", "geosenge-town",
    "coumarine-city", "dendemille-town", "anistar-city", "snowbelle-city",
    "spiky-passage",        # Rhyhorn racing area; no wild encounters
    "poke-ball-factory",    # building; no wild encounters

    # ── Alola towns / story / trial locations ────────────────────────────────────
    "iki-town",             # starter town; no wild encounters
    "trainer-school",       # building; no wild encounters
    "royal-avenue",         # Battle Royal venue; no wild encounters
    "aether-house",         # building; no wild encounters
    "po-town",              # Team Skull HQ; no wild encounter tables
    "aether-paradise",      # facility; story encounters only
    "altar-of-sunne",       # story event location; no wild encounters
    # Grand trial arenas — no wild Pokémon
    "melemele-grand-trial", "akala-grand-trial",
    "ula-ula-grand-trial",  "poni-grand-trial",
}

# ── main audit ────────────────────────────────────────────────────────────────

GAMES = [
    "red","blue","yellow",
    "gold","silver","crystal",
    "ruby","sapphire","emerald",
    "firered","leafgreen",
    "diamond","pearl","platinum",
    "heartgold","soulsilver",
    "black","white","black-2","white-2",
    "x","y",
    "omega-ruby","alpha-sapphire",
    "sun","moon","ultra-sun","ultra-moon",
]

# Mirror the fallback logic from scrape.py: when the primary version has no data
# for an area, try these versions in order before declaring a gap.
_ENCOUNTER_FALLBACKS: dict[str, list[str]] = {
    "omega-ruby":     ["emerald", "ruby",    "sapphire"],
    "alpha-sapphire": ["emerald", "sapphire","ruby"],
}


def _has_encounters(lookup: dict[str, set], version: str, fallbacks: list[str]) -> bool:
    if lookup.get(version):
        return True
    for fb in fallbacks:
        if lookup.get(fb):
            return True
    return False


results: dict[str, list[str]] = {}

for version in GAMES:
    route_order = ROUTE_ORDER.get(version, [])
    cave_maps   = CAVE_MAPS.get(version, [])
    fallbacks   = _ENCOUNTER_FALLBACKS.get(version, [])

    # Build dungeon set
    dungeon_loc_ids = {loc["id"] for loc in cave_maps}
    # Only audit dungeon locations that this version actually visits.
    # Cave maps are shared across related versions (e.g. _RED_CAVE_MAPS covers FRLG
    # too), so iterating all cave_maps without this filter produces false positives
    # for locations not in the current version's route_order.
    route_order_loc_ids = {entry["location"] for entry in route_order}

    missing: list[str] = []

    # Non-dungeon routes
    for entry in route_order:
        loc_id = entry["location"]
        if loc_id in dungeon_loc_ids:
            continue  # handled below
        # Check if any PokeAPI area for this location has encounters for this version
        # (or a fallback version). Try both the bare slug and common regional prefixes.
        found = False
        for candidate in [
            loc_id,
            f"johto-{loc_id}", f"kanto-{loc_id}", f"hoenn-{loc_id}",
            f"sinnoh-{loc_id}", f"unova-{loc_id}", f"kalos-{loc_id}", f"alola-{loc_id}",
        ]:
            if _has_encounters(loc_ver_mons.get(candidate, {}), version, fallbacks):
                found = True
                break
        # Also check sea-route form (e.g. kanto-sea-route-19 → route-19)
        if not found and loc_id.startswith("route-"):
            num = loc_id[6:]
            for region in ["kanto-sea", "johto-sea", "hoenn-sea", "sinnoh-sea"]:
                if _has_encounters(loc_ver_mons.get(f"{region}-route-{num}", {}), version, fallbacks):
                    found = True
                    break
        if not found and loc_id not in _EXPECTED_EMPTY:
            missing.append(f"route:{loc_id}")

    # Dungeon floors — only for locations this version actually visits
    for loc in cave_maps:
        if loc["id"] not in route_order_loc_ids:
            continue
        for floor in loc["floors"]:
            fid = floor["id"]
            areas = floor.get("pokeapi_areas", [])
            if not areas:
                if fid not in _EXPECTED_EMPTY:
                    missing.append(f"dungeon:{loc['id']}/{fid} (no pokeapi_areas)")
                continue
            found = any(
                _has_encounters(area_ver_mons.get(a, {}), version, fallbacks)
                for a in areas
            )
            if not found and fid not in _EXPECTED_EMPTY:
                missing.append(f"dungeon:{loc['id']}/{fid} areas={areas}")

    results[version] = missing

# Print report
print()
total_gaps = 0
for version in GAMES:
    gaps = results[version]
    if gaps:
        total_gaps += len(gaps)
        print(f"\n{'='*60}")
        print(f"  {version}  ({len(gaps)} gaps)")
        print(f"{'='*60}")
        for g in gaps:
            print(f"  {g}")
    else:
        print(f"  {version}: OK")

print(f"\nTotal unexpected gaps: {total_gaps}")
