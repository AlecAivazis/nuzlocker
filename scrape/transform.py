"""
Transform raw scraper output → app-ready game.json + pokedex.json + ZIP.

Called at the end of each scrape run — never as a standalone script.
"""

from __future__ import annotations

import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Optional


# ── Display names ──────────────────────────────────────────────────────────────

_DISPLAY_NAMES: dict[str, str] = {
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
}


# ── Public entry point ─────────────────────────────────────────────────────────

def build_and_write_zip(version: str, raw: dict, sprites_dir: Path, output_dir: Path) -> Path:
    """Build the variant ZIP and update the global manifest. Returns the ZIP path."""
    game    = _build_game(raw)
    pokedex = _build_pokedex(raw)
    zip_path = _write_zip(version, game, pokedex, sprites_dir, output_dir)
    _update_manifest(raw, output_dir)
    return zip_path


# ── Global manifest (output/manifest.json) ────────────────────────────────────
#
# One entry per scraped variant. Loaded by the app at launch (or fetched from
# the CDN) to know what games are available. Download URLs are placeholders
# here; scripts/rewrite-manifest.sh patches them for local dev or production.

def _update_manifest(raw: dict, output_dir: Path) -> None:
    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"variants": []}

    version = raw["game"]
    entry = {
        "variantID":      version,
        "gameID":         raw["version_group"].replace("-", "_"),
        "generation":     raw["generation"],
        "displayName":    _DISPLAY_NAMES.get(version, version.replace("-", " ").title()),
        "contentVersion": "1.0.0",
        "layoutVersion":  1,
        "downloadURL":    "",
    }

    # Replace existing entry for this variant or append
    variants = manifest["variants"]
    idx = next((i for i, v in enumerate(variants) if v["variantID"] == version), None)
    if idx is not None:
        variants[idx] = entry
    else:
        variants.append(entry)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


# ── game.json (VariantContent) ─────────────────────────────────────────────────

def _build_game(raw: dict) -> dict:
    trainers = raw["trainers"]
    champion = next((_build_trainer(t) for t in trainers if t["class"] == "champion"), None)
    return {
        "variantID":      raw["game"],
        "starters":       [s["pokemon_id"] for s in raw["starters"]],
        "hmMoves":        raw["hm_moves"],
        "badgeObedience": [
            {"badges": b["badges"], "maxLevel": b["max_level"]}
            for b in raw["badge_obedience"]
        ],
        "routes":    _build_routes(raw),
        "gyms":      _build_gyms(trainers),
        "eliteFour": _build_trainers(trainers, "elite_four"),
        "champion":  champion,
        "rivals":    _build_trainers(trainers, "rival"),
        "tms":       [_transform_tm(t) for t in raw["tms"]],
        "moves":     {name: _transform_move(m) for name, m in raw["moves"].items()},
    }


# ── Trainers / gyms ────────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "").replace("/", "-").strip("-")


def _build_gyms(trainers: list[dict]) -> list[dict]:
    gyms = sorted(
        (t for t in trainers if t["class"] == "gym_leader"),
        key=lambda g: g.get("order", 999),
    )
    return [
        {
            "id":          _slug(g["name"]),
            "leader":      g["name"],
            "badge":       g["badge"],
            "specialty":   g.get("specialty"),
            "region":      g.get("region"),
            "team":        [_transform_member(m) for m in g.get("team", [])],
            "rematchTeam": [_transform_member(m) for m in g["rematch_team"]]
                           if g.get("rematch_team") else None,
        }
        for g in gyms
    ]


def _build_trainers(trainers: list[dict], cls: str) -> list[dict]:
    return [_build_trainer(t) for t in trainers if t["class"] == cls]


def _build_trainer(t: dict) -> dict:
    battles: list[dict] = []

    if "battles" in t:
        # Rivals: each battle is already a discrete encounter with location_hint / player_starter
        for b in t["battles"]:
            battles.append({
                "team":          [_transform_member(m) for m in b.get("team", [])],
                "isRematch":     False,
                "locationHint":  b.get("location_hint"),
                "playerStarter": b.get("player_starter"),
            })
    else:
        # E4 / champion: main team + optional rematch
        if t.get("team"):
            battles.append({
                "team":          [_transform_member(m) for m in t["team"]],
                "isRematch":     False,
                "locationHint":  None,
                "playerStarter": None,
            })
        if t.get("rematch_team"):
            battles.append({
                "team":          [_transform_member(m) for m in t["rematch_team"]],
                "isRematch":     True,
                "locationHint":  None,
                "playerStarter": None,
            })

    return {
        "id":           _slug(t["name"]),
        "trainerClass": t["class"],
        "name":         t["name"],
        "specialty":    t.get("specialty"),
        "battles":      battles,
    }


def _transform_member(m: dict) -> dict:
    return {
        "id":       m["pokemon_id"],
        "level":    m["level"],
        "moves":    m.get("moves", []),
        "ability":  m.get("ability"),
        "heldItem": m.get("held_item"),
    }


# ── TMs / moves ────────────────────────────────────────────────────────────────

def _transform_tm(t: dict) -> dict:
    return {
        "number":   t["number"],
        "name":     t["name"],
        "move":     t["move"],
        "location": t.get("location"),
    }


def _transform_move(m: dict) -> dict:
    return {
        "type":         m.get("type", ""),
        "power":        m.get("power"),
        "accuracy":     m.get("accuracy"),
        "pp":           m.get("pp", 0),
        "damageClass":  m.get("damage_class", ""),
        "priority":     m.get("priority", 0),
        "effectChance": m.get("effect_chance"),
        "effect":       m.get("effect", ""),
        "description":  m.get("description", ""),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

_REGION_PREFIXES = ("johto-", "kanto-", "hoenn-", "sinnoh-", "unova-", "kalos-", "alola-")


def _strip_region(loc: str) -> str:
    for prefix in _REGION_PREFIXES:
        if loc.startswith(prefix):
            return loc[len(prefix):]
    return loc


_METHOD_DISPLAY: dict[str, str] = {
    "walk":             "Walking",
    "surf":             "Surfing",
    "old-rod":          "Old Rod",
    "good-rod":         "Good Rod",
    "super-rod":        "Super Rod",
    "rock-smash":       "Rock Smash",
    "headbutt":         "Headbutt",
    "headbutt-special": "Headbutt (Special)",
    "gift":             "Gift",
    "swarm":            "Swarm",
    "slot2":            "Slot 2",
    "pokeradar":        "PokéRadar",
}


def _method_display(method: str) -> str:
    return _METHOD_DISPLAY.get(method, method.replace("-", " ").title())


def _build_routes(raw: dict) -> list[dict]:
    # Index encounter areas by both the full PokeAPI location slug and its
    # region-stripped form so that route_order entries like "route-29" match
    # PokeAPI slugs like "johto-route-29".
    areas_by_loc: dict[str, list[dict]] = defaultdict(list)
    for area in raw["routes"].values():
        full_loc = area["location"]
        areas_by_loc[full_loc].append(area)
        norm_loc = _strip_region(full_loc)
        if norm_loc != full_loc:
            areas_by_loc[norm_loc].append(area)

    statics_by_loc: dict[str, list[dict]] = defaultdict(list)
    for e in raw["static_encounters"]:
        statics_by_loc[e["location"]].append(e)

    gifts_by_loc: dict[str, list[dict]] = defaultdict(list)
    for g in raw["gift_pokemon"]:
        gifts_by_loc[g["location"]].append(g)

    trades_by_loc: dict[str, list[dict]] = defaultdict(list)
    for t in raw["in_game_trades"]:
        trades_by_loc[t["location"]].append(t)

    dungeon_floors = raw["dungeon_floors"]
    seen_locs: set[str] = set()
    routes_out: list[dict] = []

    for entry in raw["route_order"]:
        loc_id       = entry["location"]
        display_name = entry["display_name"]
        seen_locs.add(loc_id)

        if loc_id in dungeon_floors:
            floors_out = _build_dungeon_floors(
                dungeon_floors[loc_id], raw["routes"],
                statics_by_loc[loc_id], gifts_by_loc[loc_id], trades_by_loc[loc_id],
            )
        else:
            encs = [e for a in areas_by_loc[loc_id] for e in a.get("encounters", [])]
            floors_out = [_build_floor(
                floor_id=loc_id, display_name=display_name,
                image_url=None, warps=[],
                encounters=encs,
                statics=statics_by_loc[loc_id],
                gifts=gifts_by_loc[loc_id],
                trades=trades_by_loc[loc_id],
            )]

        routes_out.append({"id": loc_id, "displayName": display_name, "floors": floors_out})

    # Warn about locations with data that didn't make it into route_order.
    # Region-slug catch-alls (e.g. "johto") are intentionally omitted — they're
    # used by PokeAPI for roaming Pokémon with no fixed encounter tile.
    region_catchalls = set(_REGION_PREFIXES) | {"johto", "kanto", "hoenn", "sinnoh", "unova", "kalos", "alola"}
    for loc_id in set(statics_by_loc) | set(gifts_by_loc) | set(trades_by_loc):
        if loc_id not in seen_locs and loc_id not in region_catchalls:
            print(f"  [warn] location '{loc_id}' has static/gift/trade data but is not in route_order")

    return routes_out


def _build_dungeon_floors(
    floors: list[dict],
    all_areas: dict[str, dict],
    statics: list[dict],
    gifts: list[dict],
    trades: list[dict],
) -> list[dict]:
    floors_out = []
    for i, floor in enumerate(floors):
        encs = [
            enc
            for area_name in floor.get("pokeapi_areas", [])
            for enc in all_areas.get(area_name, {}).get("encounters", [])
        ]
        floors_out.append(_build_floor(
            floor_id=floor["id"],
            display_name=floor["display_name"],
            image_url=floor.get("image_url"),
            warps=floor.get("warps", []),
            encounters=encs,
            statics=statics if i == 0 else [],
            gifts=gifts   if i == 0 else [],
            trades=trades  if i == 0 else [],
        ))
    return floors_out


def _build_floor(
    floor_id: str,
    display_name: str,
    image_url: Optional[str],
    warps: list[dict],
    encounters: list[dict],
    statics: list[dict],
    gifts: list[dict],
    trades: list[dict],
) -> dict:
    return {
        "id":               floor_id,
        "displayName":      display_name,
        "imageURL":         image_url,
        "warps":            [_transform_warp(w) for w in warps],
        "areas":            _build_areas(floor_id, encounters),
        "staticEncounters": [_transform_static(e) for e in statics],
        "giftPokemon":      [_transform_gift(g)  for g in gifts],
        "inGameTrades":     [_transform_trade(t) for t in trades],
    }


def _build_areas(floor_id: str, encounters: list[dict]) -> list[dict]:
    by_method: dict[str, list[dict]] = defaultdict(list)
    for enc in encounters:
        by_method[enc["method"]].append(enc)
    if not by_method:
        return []
    only_one = len(by_method) == 1
    return [
        {
            "id":          f"{floor_id}-{method}",
            "displayName": None if only_one else _method_display(method),
            "encounters":  [_transform_encounter(e) for e in encs],
        }
        for method, encs in sorted(by_method.items())
    ]


def _transform_encounter(e: dict) -> dict:
    return {
        "method":     e["method"],
        "id":         e["pokemon_id"],
        "rate":       float(e["chance"]),
        "minLevel":   e["min_level"],
        "maxLevel":   e["max_level"],
        "conditions": e.get("conditions", []),
    }


def _transform_static(e: dict) -> dict:
    return {
        "id":          e["pokemon_id"],
        "level":       e["level"],
        "alwaysShiny": e.get("always_shiny", False),
        "source":      None,
        "note":        e.get("note"),
    }


def _transform_gift(g: dict) -> dict:
    return {
        "id":          g["pokemon_id"],
        "level":       g["level"],
        "alwaysShiny": g.get("always_shiny", False),
        "source":      g.get("source"),
        "note":        g.get("note"),
    }


def _transform_trade(t: dict) -> dict:
    return {
        "giveID":       t["give_pokemon_id"],
        "receiveID":    t["receive_pokemon_id"],
        "receiveLevel": t["receive_level"],
        "npc":          t["npc"],
    }


def _transform_warp(w: dict) -> dict:
    return {
        "x":          w["x"],
        "y":          w["y"],
        "destFloorID": w["dest_floor_id"],
        "destX":      w["dest_x"],
        "destY":      w["dest_y"],
    }


# ── pokedex.json (PokedexContent) ──────────────────────────────────────────────

def _build_pokedex(raw: dict) -> dict:
    abilities_db = raw.get("abilities", {})

    # Move slug → TM name (e.g. "cut" → "hm01", "earthquake" → "tm26")
    move_to_machine: dict[str, str] = {}
    for t in raw.get("tms", []):
        move_to_machine[t["move"]] = t["name"]
    for move_slug, hm_id in raw.get("hm_moves", {}).items():
        move_to_machine[move_slug] = hm_id

    # Pokemon name → ID (needed to resolve evolution chain targets)
    name_to_id: dict[str, int] = {
        entry["name"]: int(pid)
        for pid, entry in raw["pokedex"].items()
    }

    creatures = [
        _build_creature(entry, abilities_db, move_to_machine, name_to_id)
        for _, entry in sorted(raw["pokedex"].items(), key=lambda x: int(x[0]))
    ]
    return {"creatures": creatures}


def _build_creature(
    entry: dict,
    abilities_db: dict,
    move_to_machine: dict[str, str],
    name_to_id: dict[str, int],
) -> dict:
    stats = entry.get("base_stats", {})

    # evolvesTo: all stage-(N+1) entries in the flat evolution chain.
    # Note: branching lines like Wurmple→Silcoon/Cascoon→Beautifly/Dustox will
    # over-report, but this is an inherent limitation of the flat stage representation.
    evo_chain = entry.get("evolution_chain", [])
    my_name   = entry["name"]
    my_stage  = next((e["stage"] for e in evo_chain if e["pokemon"] == my_name), None)

    evolves_to: list[dict] = []
    if my_stage is not None:
        for evo in evo_chain:
            if evo["stage"] == my_stage + 1 and evo.get("evolves_via"):
                target_id = name_to_id.get(evo["pokemon"])
                if target_id is not None:
                    evolves_to.append({
                        "id":      target_id,
                        "methods": [_transform_evo_method(m) for m in evo["evolves_via"]],
                    })

    # Learnset: level-up moves, then machine moves with resolved TM/HM identifiers
    learnset: list[dict] = []
    for lm in entry.get("moves_by_level", []):
        learnset.append({
            "move":    lm["move"],
            "method":  "level-up",
            "level":   lm["level"],
            "machine": None,
        })
    for mm in entry.get("moves_by_machine", []):
        machine = move_to_machine.get(mm["move"]) or mm.get("machine") or "tm"
        learnset.append({
            "move":    mm["move"],
            "method":  "machine",
            "level":   None,
            "machine": machine,
        })

    # Abilities with descriptions joined from the abilities dict
    abilities: list[dict] = []
    for ab in entry.get("abilities", []):
        ab_info = abilities_db.get(ab["name"], {})
        abilities.append({
            "name":        ab["name"],
            "description": ab_info.get("description") or ab_info.get("short_effect", ""),
            "isHidden":    ab.get("is_hidden", False),
        })

    return {
        "id":         entry["id"],
        "name":       entry["name"],
        "types":      entry.get("types", []),
        "baseStats":  {
            "hp":  stats.get("hp", 0),
            "atk": stats.get("attack", 0),
            "def": stats.get("defense", 0),
            "spe": stats.get("speed", 0),
        },
        "abilities":  abilities,
        "evolvesTo":  evolves_to,
        "learnset":   learnset,
        "spriteFile": f"{entry['id']:03d}.png",
    }


def _transform_evo_method(m: dict) -> dict:
    result: dict = {"trigger": m["trigger"]}
    for src, dst in [
        ("min_level",   "minLevel"),
        ("item",        "item"),
        ("held_item",   "heldItem"),
        ("known_move",  "knownMove"),
        ("time_of_day", "timeOfDay"),
        ("min_happiness", "minHappiness"),
    ]:
        if m.get(src) is not None:
            result[dst] = m[src]
    return result


# ── ZIP ────────────────────────────────────────────────────────────────────────

def _write_zip(version: str, game: dict, pokedex: dict, sprites_dir: Path, output_dir: Path) -> Path:
    out_path = output_dir / f"{version}.zip"
    pokedex_ids = {c["id"] for c in pokedex.get("creatures", [])}

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("game.json",    json.dumps(game,    ensure_ascii=False))
        zf.writestr("pokedex.json", json.dumps(pokedex, ensure_ascii=False))
        for pid in sorted(pokedex_ids):
            sprite = sprites_dir / f"{pid}.png"
            if sprite.exists():
                zf.write(sprite, f"sprites/{pid:03d}.png")

    return out_path
