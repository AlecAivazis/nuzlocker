#!/usr/bin/env python3
"""Convert scrape/output/*.json → variants/*.zip + variants/default-manifest.template.json

Usage:
    python3 scripts/make_variants.py [game ...]   # omit to process all
"""

import datetime, hashlib, io, json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPE_OUTPUT = ROOT / "scrape" / "output"
SPRITES_DIR = SCRAPE_OUTPUT / "sprites"
FIXTURES_DIR = ROOT / "variants"

DISPLAY_NAMES = {
    "red": "Red", "blue": "Blue", "yellow": "Yellow",
    "gold": "Gold", "silver": "Silver", "crystal": "Crystal",
    "ruby": "Ruby", "sapphire": "Sapphire", "emerald": "Emerald",
    "firered": "FireRed", "leafgreen": "LeafGreen",
    "diamond": "Diamond", "pearl": "Pearl", "platinum": "Platinum",
    "heartgold": "HeartGold", "soulsilver": "SoulSilver",
    "black": "Black", "white": "White",
    "black-2": "Black 2", "white-2": "White 2",
    "x": "X", "y": "Y",
    "omega-ruby": "Omega Ruby", "alpha-sapphire": "Alpha Sapphire",
    "sun": "Sun", "moon": "Moon",
    "ultra-sun": "Ultra Sun", "ultra-moon": "Ultra Moon",
    "sword": "Sword", "shield": "Shield",
    "scarlet": "Scarlet", "violet": "Violet",
}

GENERATION_NAMES = {
    1: "Generation I", 2: "Generation II", 3: "Generation III",
    4: "Generation IV", 5: "Generation V", 6: "Generation VI",
    7: "Generation VII", 8: "Generation VIII", 9: "Generation IX",
}


def _area_sublabel(location_slug: str, area_name: str) -> str:
    prefix = location_slug + "-"
    suffix = area_name[len(prefix):] if area_name.startswith(prefix) else area_name
    if suffix == "area":
        return ""
    if re.match(r"^[bB]?\d", suffix):
        return suffix.upper()
    return suffix.replace("-", " ").title()


def build_routes(raw):
    route_order = sorted(raw.get("route_order", []), key=lambda r: r["order"])
    by_location: dict[str, list] = {}
    for area_data in raw.get("routes", {}).values():
        loc = area_data["location"]
        by_location.setdefault(loc, []).append(area_data)

    routes = []
    for loc_entry in route_order:
        loc_slug = loc_entry["location"]
        area_list = sorted(by_location.get(loc_slug, []), key=lambda a: a["area"])

        areas = []
        for area_data in area_list:
            encounters = area_data.get("encounters", [])
            if not encounters:
                continue
            areas.append({
                "id": area_data["area"].replace("-", "_"),
                "displayName": _area_sublabel(loc_slug, area_data["area"]),
                "encounters": [
                    {
                        "method": enc["method"],
                        "pokedexNumber": enc["pokemon_id"],
                        "rate": round(enc["chance"] / 100, 4),
                        "minLevel": enc["min_level"],
                        "maxLevel": enc["max_level"],
                    }
                    for enc in encounters
                ],
            })

        if not areas:
            continue
        routes.append({
            "id": loc_slug.replace("-", "_"),
            "displayName": loc_entry["display_name"],
            "areas": areas,
        })
    return routes


def build_gyms(raw):
    leaders = sorted(
        [t for t in raw.get("trainers", []) if t.get("class") == "gym_leader"],
        key=lambda t: t.get("order", 0),
    )
    gyms = []
    for leader in leaders:
        team = leader.get("team") or []
        if not team and leader.get("battles"):
            team = leader["battles"][0].get("team", [])
        level_cap = max((p["level"] for p in team), default=0)
        gyms.append({
            "id": f"gym_{leader['order']}",
            "leader": leader["name"],
            "badge": leader.get("badge", ""),
            "levelCap": level_cap,
            "team": [{"pokedexNumber": p["pokemon_id"], "level": p["level"]} for p in team],
        })
    return gyms


def build_tms(raw):
    return [
        {
            "number": tm["number"],
            "name": tm["name"],
            "move": tm["move"],
            "location": tm.get("location"),
        }
        for tm in raw.get("tms", [])
    ]


def build_pokedex(raw):
    creatures = []
    for ndex_str, poke in sorted(raw.get("pokedex", {}).items(), key=lambda x: int(x[0])):
        ndex = int(ndex_str)
        bs = poke.get("base_stats", {})
        creatures.append({
            "pokedexNumber": ndex,
            "name": poke["name"],
            "types": poke.get("types", []),
            "baseStats": {
                "hp": bs.get("hp", 0),
                "atk": bs.get("attack", 0),
                "def": bs.get("defense", 0),
                "spe": bs.get("speed", 0),
            },
            "spriteFile": f"sprites/{ndex:03d}.png",
        })
    return {"creatures": creatures}


def make_zip(variant_manifest, game_json, pokedex_json, ndex_set):
    buf = io.BytesIO()
    ts = (2024, 1, 1, 0, 0, 0)  # deterministic timestamp for reproducible hashes
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(zipfile.ZipInfo("manifest.json", ts), json.dumps(variant_manifest, indent=2))
        zf.writestr(zipfile.ZipInfo("game.json", ts), json.dumps(game_json, indent=2))
        zf.writestr(zipfile.ZipInfo("pokedex.json", ts), json.dumps(pokedex_json, indent=2))
        for ndex in sorted(ndex_set):
            sprite = SPRITES_DIR / f"{ndex}.png"
            if sprite.exists():
                info = zipfile.ZipInfo(f"sprites/{ndex:03d}.png", ts)
                zf.writestr(info, sprite.read_bytes())
    return buf.getvalue()


def process_game(json_path):
    raw = json.loads(json_path.read_text())
    variant_id = raw["game"]
    display_name = DISPLAY_NAMES.get(variant_id, variant_id.replace("-", " ").title())
    game_id = raw.get("version_group", variant_id).replace("-", "_")
    generation = raw.get("generation", 1)
    generation_name = GENERATION_NAMES.get(generation, f"Generation {generation}")

    starters = [s["pokemon_id"] for s in raw.get("starters", [])]
    routes = build_routes(raw)
    gyms = build_gyms(raw)
    tms = build_tms(raw)
    pokedex_json = build_pokedex(raw)
    ndex_set = {c["pokedexNumber"] for c in pokedex_json["creatures"]}

    variant_manifest = {
        "variantID": variant_id,
        "gameID": game_id,
        "generation": generation,
        "displayName": display_name,
        "contentVersion": "1.0.0",
        "layoutVersion": 1,
        "spritesPath": "sprites",
        "pokedexFile": "pokedex.json",
        "gameDataFile": "game.json",
    }
    game_json = {
        "variantID": variant_id,
        "starters": starters,
        "routes": routes,
        "gyms": gyms,
        "tms": tms,
    }

    zip_bytes = make_zip(variant_manifest, game_json, pokedex_json, ndex_set)
    zip_path = FIXTURES_DIR / f"{variant_id}.zip"
    zip_path.write_bytes(zip_bytes)
    sha = hashlib.sha256(zip_bytes).hexdigest()
    print(f"  {variant_id}.zip  {len(zip_bytes):,} bytes  sha256={sha[:16]}…")

    return {
        "variantID": variant_id,
        "displayName": display_name,
        "gameID": game_id,
        "generation": generation,
        "generationName": generation_name,
        "sha256": sha,
        "sizeBytes": len(zip_bytes),
    }


def main():
    filter_ids = set(sys.argv[1:])
    FIXTURES_DIR.mkdir(exist_ok=True)

    json_files = sorted(SCRAPE_OUTPUT.glob("*.json"))
    if filter_ids:
        json_files = [f for f in json_files if f.stem in filter_ids]
    if not json_files:
        print(f"No matching JSON files in {SCRAPE_OUTPUT}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(json_files)} game(s)…")
    results = []
    for path in json_files:
        print(f"\n{path.name}:")
        try:
            results.append(process_game(path))
        except Exception as exc:
            print(f"  [error] {exc}", file=sys.stderr)

    # Build manifest template grouped by gameID
    by_game: dict[str, list] = {}
    for r in results:
        by_game.setdefault(r["gameID"], []).append(r)

    games = []
    for game_id, variants in sorted(by_game.items(), key=lambda x: x[1][0]["generation"]):
        first = variants[0]
        games.append({
            "id": game_id,
            "displayName": "/".join(v["displayName"] for v in variants),
            "generation": first["generation"],
            "generationDisplayName": first["generationName"],
            "variants": [
                {
                    "id": v["variantID"],
                    "displayName": v["displayName"],
                    "zipURL": f"https://cdn.example.com/{v['variantID']}.zip",
                    "zipSHA256": v["sha256"],
                    "sizeBytes": v["sizeBytes"],
                    "contentVersion": "1.0.0",
                    "layoutVersion": 1,
                }
                for v in variants
            ],
        })

    template = {
        "manifestVersion": 1,
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": games,
    }
    template_path = FIXTURES_DIR / "default-manifest.template.json"
    template_path.write_text(json.dumps(template, indent=2) + "\n")
    print(f"\nWrote {template_path}")
    print("\nNext steps:")
    print("  scripts/rewrite-manifest.sh      # rewrite zipURLs → localhost")
    print("  scripts/serve-variants.sh        # start local HTTP server")
    print("  (enable Simulation Mode in app Debug settings and restart)")


if __name__ == "__main__":
    main()
