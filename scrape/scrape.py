#!/usr/bin/env python3
"""
Pokémon game data scraper for Nuzlocke Tracker.

Sources:
  - PokeAPI (pokeapi.co)       : Pokédex, moves, encounter tables, evolution chains
  - Bulbapedia (MediaWiki API) : Trainer teams (wikitext), TM locations, floor map images

Usage:
    python scrape.py "soul silver"
    python scrape.py platinum
    python scrape.py "heart gold"

Output: output/<version>.json — top-level keys:
  game, version_group, generation, scraped_at
  hm_moves          — {move_name: "hmNN"}
  badge_obedience   — [{badges, level_cap}]
  starters          — [{pokemon_id, ...}]
  static_encounters — [{pokemon_id, level, ...}]
  gift_pokemon      — [{pokemon_id, ...}]
  in_game_trades    — [{...}]
  route_order       — [{id, display_name, prerequisite?, note?}]
  routes            — {area_name: {location, area, display_name,
                      encounters: [{method, conditions, pokemon_id, chance, min_level, max_level}]}}
  dungeon_floors    — {location_id: [{id, display_name, image_url, pokeapi_areas,
                      warps: [{x, y, dest_floor_id, dest_x, dest_y}]}]}
                      warp coordinates are tile-grid units (1 tile = 16 px)
  trainers          — [{class, name, team, ...}]
  tms               — [{number, name, move, location?}]
  species           — {pokemon_id: {name, types, stats, moves, abilities, ...}}
  moves             — {move_name: {type, power, accuracy, effect, ...}}
  abilities         — {ability_name: {effect, short_effect, description}}

`routes` and `dungeon_floors` are kept separate because PokeAPI encounter areas do not
map 1-to-1 with dungeon floors. transform.py merges them using the `pokeapi_areas`
list on each floor entry to assign encounters to the correct floor.

Cache:  cache/<sha1>.json  (skip re-fetching on re-runs)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp

from game_data import HM_MOVES, BADGE_OBEDIENCE, TRAINER_DEFS, GAME_STATIC, ROUTE_ORDER, CAVE_MAPS
from transform import build_and_write_zip

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent
CACHE_DIR   = ROOT / "cache"
OUTPUT_DIR  = ROOT / "output"
SPRITES_DIR = OUTPUT_DIR / "sprites"
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
SPRITES_DIR.mkdir(exist_ok=True)

POKEAPI    = "https://pokeapi.co/api/v2"
BULBA_API  = "https://bulbapedia.bulbagarden.net/w/api.php"
CONCURRENT = 20   # max simultaneous HTTP requests

# ── Game slug maps ─────────────────────────────────────────────────────────────

GAME_SLUGS: dict[str, str] = {
    "red": "red", "blue": "blue", "yellow": "yellow",
    "gold": "gold", "silver": "silver", "crystal": "crystal",
    "ruby": "ruby", "sapphire": "sapphire", "emerald": "emerald",
    "fire red": "firered", "firered": "firered",
    "leaf green": "leafgreen", "leafgreen": "leafgreen",
    "diamond": "diamond", "pearl": "pearl", "platinum": "platinum",
    "heart gold": "heartgold", "heartgold": "heartgold",
    "soul silver": "soulsilver", "soulsilver": "soulsilver",
    "black": "black", "white": "white",
    "black 2": "black-2", "black2": "black-2",
    "white 2": "white-2", "white2": "white-2",
    "x": "x", "y": "y",
    "omega ruby": "omega-ruby", "omegaruby": "omega-ruby",
    "alpha sapphire": "alpha-sapphire", "alphasapphire": "alpha-sapphire",
    "sun": "sun", "moon": "moon",
    "ultra sun": "ultra-sun", "ultrasun": "ultra-sun",
    "ultra moon": "ultra-moon", "ultramoon": "ultra-moon",
}

VERSION_GROUP: dict[str, str] = {
    "red": "red-blue", "blue": "red-blue", "yellow": "yellow",
    "gold": "gold-silver", "silver": "gold-silver", "crystal": "crystal",
    "ruby": "ruby-sapphire", "sapphire": "ruby-sapphire", "emerald": "emerald",
    "firered": "firered-leafgreen", "leafgreen": "firered-leafgreen",
    "diamond": "diamond-pearl", "pearl": "diamond-pearl", "platinum": "platinum",
    "heartgold": "heartgold-soulsilver", "soulsilver": "heartgold-soulsilver",
    "black": "black-white", "white": "black-white",
    "black-2": "black-2-white-2", "white-2": "black-2-white-2",
    "x": "x-y", "y": "x-y",
    "omega-ruby": "omega-ruby-alpha-sapphire", "alpha-sapphire": "omega-ruby-alpha-sapphire",
    "sun": "sun-moon", "moon": "sun-moon",
    "ultra-sun": "ultra-sun-ultra-moon", "ultra-moon": "ultra-sun-ultra-moon",
}

VERSION_GEN: dict[str, int] = {
    "red": 1, "blue": 1, "yellow": 1,
    "gold": 2, "silver": 2, "crystal": 2,
    "ruby": 3, "sapphire": 3, "emerald": 3, "firered": 3, "leafgreen": 3,
    "diamond": 4, "pearl": 4, "platinum": 4, "heartgold": 4, "soulsilver": 4,
    "black": 5, "white": 5, "black-2": 5, "white-2": 5,
    "x": 6, "y": 6, "omega-ruby": 6, "alpha-sapphire": 6,
    "sun": 7, "moon": 7, "ultra-sun": 7, "ultra-moon": 7,
}

# Codes used inside {{gameabbrevN|CODE}} in {{TMtable/row}} templates.
# Gen 1 groups all three games as RBY (different from the RGB/Y split used in party templates).
TM_CODE: dict[str, str] = {
    "red": "RBY", "blue": "RBY", "yellow": "RBY",
    "gold": "GSC", "silver": "GSC", "crystal": "GSC",
    "ruby": "RSE", "sapphire": "RSE", "emerald": "RSE",
    "firered": "FRLG", "leafgreen": "FRLG",
    "diamond": "DPPt", "pearl": "DPPt", "platinum": "DPPt",
    "heartgold": "HGSS", "soulsilver": "HGSS",
    "black": "BW", "white": "BW",
    "black-2": "B2W2", "white-2": "B2W2",
    "x": "XY", "y": "XY",
    "omega-ruby": "ORAS", "alpha-sapphire": "ORAS",
    "sun": "SM", "moon": "SM",
    "ultra-sun": "USUM", "ultra-moon": "USUM",
}

# Bulbapedia uses these codes inside {{Pokémon/3|game=...}} templates
BULBA_CODE: dict[str, str] = {
    "red": "RGB", "blue": "RGB", "yellow": "Y",
    "gold": "GSC", "silver": "GSC", "crystal": "GSC",
    "ruby": "RSE", "sapphire": "RSE", "emerald": "RSE",
    "firered": "FRLG", "leafgreen": "FRLG",
    "diamond": "DPPt", "pearl": "DPPt", "platinum": "DPPt",
    "heartgold": "HGSS", "soulsilver": "HGSS",
    "black": "BW", "white": "BW",
    "black-2": "B2W2", "white-2": "B2W2",
    "x": "XY", "y": "XY",
    "omega-ruby": "ORAS", "alpha-sapphire": "ORAS",
    "sun": "SM", "moon": "SM",
    "ultra-sun": "USUM", "ultra-moon": "USUM",
}

# ── Type effectiveness (Gen 6+ chart) ─────────────────────────────────────────
# ATTACK_EFF[attacker][defender] = multiplier; 1.0 if omitted.
# Note: steel vs ghost/dark was 0.5 in Gen 1-5, changed to 1.0 in Gen 6+.

ALL_TYPES = [
    "normal","fire","water","electric","grass","ice","fighting","poison",
    "ground","flying","psychic","bug","rock","ghost","dragon","dark","steel","fairy",
]

ATTACK_EFF: dict[str, dict[str, float]] = {
    "normal":   {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0},
    "water":    {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5},
    "electric": {"water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5},
    "grass":    {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5},
    "ice":      {"water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dark": 2.0, "steel": 2.0, "fairy": 0.5},
    "poison":   {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0.0, "fairy": 2.0},
    "ground":   {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0, "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0},
    "flying":   {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0, "steel": 0.5},
    "bug":      {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5},
    "rock":     {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0, "bug": 2.0, "steel": 0.5},
    "ghost":    {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon":   {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark":     {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "steel": 0.5, "fairy": 2.0},
    "fairy":    {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0, "dark": 2.0, "steel": 0.5},
}


def compute_weaknesses(types: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for atk in ALL_TYPES:
        mult = 1.0
        for def_type in types:
            mult *= ATTACK_EFF.get(atk, {}).get(def_type, 1.0)
        if mult != 1.0:
            result[atk] = mult
    return result


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def _cache_path(url: str, params: dict | None = None) -> Path:
    key = url + json.dumps(params or {}, sort_keys=True)
    return CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest() + ".json")


async def _get_json(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    params: dict | None = None,
    *,
    cache: bool = True,
) -> dict | None:
    cp = _cache_path(url, params)
    if cache and cp.exists():
        return json.loads(cp.read_text())
    async with sem:
        for attempt in range(4):
            try:
                async with session.get(url, params=params) as r:
                    if r.status == 404:
                        return None
                    if r.status == 429:
                        wait = int(r.headers.get("Retry-After", 60))
                        print(f"  [rate-limit] {url} — waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    r.raise_for_status()
                    data = await r.json(content_type=None)
                    if cache:
                        cp.write_text(json.dumps(data))
                    return data
            except Exception as exc:
                if attempt == 3:
                    print(f"  [warn] {url} → {exc}")
                    return None
                await asyncio.sleep(2 ** attempt)
    return None


async def _get_text(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    params: dict | None = None,
) -> str | None:
    cp = _cache_path(url, params).with_suffix(".txt")
    if cp.exists():
        return cp.read_text()
    async with sem:
        for attempt in range(4):
            try:
                async with session.get(url, params=params) as r:
                    if r.status == 404:
                        return None
                    if r.status == 429:
                        wait = int(r.headers.get("Retry-After", 60))
                        print(f"  [rate-limit] {url} — waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    r.raise_for_status()
                    text = await r.text()
                    cp.write_text(text)
                    return text
            except Exception as exc:
                if attempt == 3:
                    print(f"  [warn] {url} → {exc}")
                    return None
                await asyncio.sleep(2 ** attempt)
    return None


async def _download_sprite(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    ndex: int,
    url: str,
) -> None:
    dest = SPRITES_DIR / f"{ndex}.png"
    if dest.exists():
        return
    async with sem:
        for attempt in range(4):
            try:
                async with session.get(url) as r:
                    if r.status == 429:
                        wait = int(r.headers.get("Retry-After", 60))
                        print(f"  [rate-limit] sprite {ndex} — waiting {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    r.raise_for_status()
                    dest.write_bytes(await r.read())
                    return
            except Exception as exc:
                if attempt == 3:
                    print(f"  [warn] sprite {ndex} → {exc}")
                await asyncio.sleep(2 ** attempt)


# ── PokeAPI: evolution chain ───────────────────────────────────────────────────

def _parse_evo_chain(node: dict, stage: int = 0) -> list[dict]:
    entries: list[dict] = []
    methods: list[dict] = []
    for detail in node.get("evolution_details", []):
        m: dict = {"trigger": detail["trigger"]["name"]}
        if detail.get("min_level"):           m["min_level"]     = detail["min_level"]
        if detail.get("item"):                m["item"]          = detail["item"]["name"]
        if detail.get("held_item"):           m["held_item"]     = detail["held_item"]["name"]
        if detail.get("known_move"):          m["known_move"]    = detail["known_move"]["name"]
        if detail.get("time_of_day"):         m["time_of_day"]   = detail["time_of_day"]
        if detail.get("min_happiness"):       m["min_happiness"] = detail["min_happiness"]
        if detail.get("min_beauty"):          m["min_beauty"]    = detail["min_beauty"]
        if detail.get("needs_overworld_rain"):m["needs_overworld_rain"] = True
        if detail.get("relative_physical_stats") is not None:
            m["relative_physical_stats"] = detail["relative_physical_stats"]
        if detail.get("gender") is not None:  m["gender"]        = detail["gender"]
        methods.append(m)
    entries.append({
        "pokemon":    node["species"]["name"],
        "stage":      stage,
        "evolves_via": methods,
    })
    for child in node.get("evolves_to", []):
        entries.extend(_parse_evo_chain(child, stage + 1))
    return entries


# ── PokeAPI: single Pokémon ────────────────────────────────────────────────────

async def _fetch_pokemon(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    pokemon_id: int,
    version_group: str,
    hm_moves: dict[str, str],
) -> dict | None:
    data = await _get_json(session, sem, f"{POKEAPI}/pokemon/{pokemon_id}")
    if not data:
        return None

    species = await _get_json(session, sem, f"{POKEAPI}/pokemon-species/{pokemon_id}")

    evo_chain: list = []
    if species and species.get("evolution_chain"):
        evo_data = await _get_json(session, sem, species["evolution_chain"]["url"])
        if evo_data:
            evo_chain = _parse_evo_chain(evo_data["chain"])

    types = [t["type"]["name"] for t in data["types"]]

    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

    abilities = [
        {"name": a["ability"]["name"], "is_hidden": a["is_hidden"]}
        for a in data["abilities"]
    ]

    level_moves: list[dict] = []
    machine_moves: list[dict] = []
    for move_entry in data["moves"]:
        move_name = move_entry["move"]["name"]
        for vgd in move_entry["version_group_details"]:
            if vgd["version_group"]["name"] != version_group:
                continue
            method = vgd["move_learn_method"]["name"]
            if method == "level-up":
                level_moves.append({"move": move_name, "level": vgd["level_learned_at"]})
            elif method == "machine":
                machine_id = hm_moves.get(move_name)
                machine_moves.append({"move": move_name, "machine": machine_id or "tm", "is_hm": move_name in hm_moves})
    level_moves.sort(key=lambda x: x["level"])

    # Download sprite to sprites/<ndex>.png (shared across all games; skipped if already present)
    # Prefer Gen 5 (B/W) pixel art — peak of 2D sprite work and consistent across gens 1–5.
    # Fall back to front_default for Gen 6+ Pokémon (derived from 3D models).
    sprites = data.get("sprites", {})
    sprite_url = (
        ((sprites.get("versions", {}).get("generation-v", {}).get("black-white", {}) or {}).get("front_default"))
        or sprites.get("front_default")
    )
    if sprite_url:
        await _download_sprite(session, sem, pokemon_id, sprite_url)

    genus = ""
    flavor = ""
    if species:
        for g in species.get("genera", []):
            if g["language"]["name"] == "en":
                genus = g["genus"]
                break
        for ft in reversed(species.get("flavor_text_entries", [])):
            if ft["language"]["name"] == "en":
                flavor = ft["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

    trade_evolution = any(
        detail.get("trigger") == "trade"
        for stage in evo_chain
        for detail in stage.get("evolves_via", [])
    )

    return {
        "id":              pokemon_id,
        "name":            data["name"],
        "types":           types,
        "weaknesses":      compute_weaknesses(types),
        "base_stats":      stats,
        "base_experience": data.get("base_experience"),
        "abilities":       abilities,
        "evolution_chain": evo_chain,
        "trade_evolution": trade_evolution,
        "moves_by_level":  level_moves,
        "moves_by_machine": machine_moves,
        "genus":           genus,
        "flavor_text":     flavor,
    }


async def scrape_species(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    pokemon_ids: set[int],
    version_group: str,
    hm_moves: dict[str, str],
) -> dict[str, dict]:
    print(f"  Fetching {len(pokemon_ids)} Pokémon entries…")
    results = await asyncio.gather(*[
        _fetch_pokemon(session, sem, pid, version_group, hm_moves)
        for pid in sorted(pokemon_ids)
    ])
    return {str(e["id"]): e for e in results if e}


# ── PokeAPI: encounter tables ──────────────────────────────────────────────────

async def _fetch_area_encounters(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    area_name: str,
    version: str,
) -> dict | None:
    data = await _get_json(session, sem, f"{POKEAPI}/location-area/{area_name}")
    if not data:
        return None

    encounters: list[dict] = []
    for pe in data.get("pokemon_encounters", []):
        pokemon_url  = pe["pokemon"]["url"]
        pokemon_id   = int(pokemon_url.rstrip("/").split("/")[-1])
        pokemon_name = pe["pokemon"]["name"]
        for ver in pe["version_details"]:
            if ver["version"]["name"] != version:
                continue
            for enc in ver["encounter_details"]:
                encounters.append({
                    "pokemon_id":  pokemon_id,
                    "pokemon":     pokemon_name,
                    "method":      enc["method"]["name"],
                    "conditions":  [c["name"] for c in enc.get("condition_values", [])],
                    "min_level":   enc["min_level"],
                    "max_level":   enc["max_level"],
                    "chance":      enc["chance"],
                })

    # Collapse duplicate slots: same (pokemon, method, conditions) → sum chance, widen level range
    merged: dict[tuple, dict] = {}
    for enc in encounters:
        key = (enc["pokemon_id"], enc["method"], tuple(sorted(enc["conditions"])))
        if key in merged:
            merged[key]["chance"]    += enc["chance"]
            merged[key]["min_level"]  = min(merged[key]["min_level"], enc["min_level"])
            merged[key]["max_level"]  = max(merged[key]["max_level"], enc["max_level"])
        else:
            merged[key] = dict(enc)
    encounters = sorted(merged.values(), key=lambda e: (-e["chance"], e["pokemon_id"]))

    if not encounters:
        return None

    return {
        "location":     data["location"]["name"],
        "area":         data["name"],
        "display_name": data["name"].replace("-", " ").title(),
        "encounters":   encounters,
    }


async def scrape_encounters(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    version: str,
) -> dict[str, dict]:
    print("  Fetching location-area list…")
    all_areas: list[dict] = []
    url: str | None = f"{POKEAPI}/location-area/?limit=1000"
    while url:
        page = await _get_json(session, sem, url)
        if not page:
            break
        all_areas.extend(page["results"])
        url = page.get("next")

    print(f"  Checking {len(all_areas)} areas for version '{version}'…")
    results = await asyncio.gather(*[
        _fetch_area_encounters(session, sem, a["name"], version)
        for a in all_areas
    ])
    routes = {r["area"]: r for r in results if r}
    print(f"  Found {len(routes)} areas with encounters.")
    return routes


def collect_pokemon_ids(routes: dict[str, dict]) -> set[int]:
    return {enc["pokemon_id"] for r in routes.values() for enc in r["encounters"]}


# ── PokeAPI: moves ─────────────────────────────────────────────────────────────

async def _fetch_move(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    move_name: str,
    version_group: str,
) -> dict | None:
    data = await _get_json(session, sem, f"{POKEAPI}/move/{move_name}")
    if not data:
        return None

    description = ""
    for ft in reversed(data.get("flavor_text_entries", [])):
        if ft["language"]["name"] != "en":
            continue
        if ft.get("version_group", {}).get("name") == version_group:
            description = ft["flavor_text"].replace("\n", " ").replace("\f", " ")
            break
    if not description:
        for ft in reversed(data.get("flavor_text_entries", [])):
            if ft["language"]["name"] == "en":
                description = ft["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

    effect = ""
    for e in data.get("effect_entries", []):
        if e["language"]["name"] == "en":
            chance = str(data.get("effect_chance") or "")
            effect = e.get("short_effect", "").replace("$effect_chance", chance)
            break

    return {
        "name":          move_name,
        "type":          data["type"]["name"] if data.get("type") else None,
        "power":         data.get("power"),
        "accuracy":      data.get("accuracy"),
        "pp":            data.get("pp"),
        "damage_class":  data["damage_class"]["name"] if data.get("damage_class") else None,
        "priority":      data.get("priority", 0),
        "target":        data["target"]["name"] if data.get("target") else None,
        "effect_chance": data.get("effect_chance"),
        "description":   description or effect,
        "effect":        effect,
    }


async def scrape_moves(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    move_names: set[str],
    version_group: str,
) -> dict[str, dict]:
    print(f"  Fetching {len(move_names)} move entries…")
    results = await asyncio.gather(*[
        _fetch_move(session, sem, name, version_group)
        for name in sorted(move_names)
    ])
    return {e["name"]: e for e in results if e}


def collect_move_names(species: dict[str, dict]) -> set[str]:
    names: set[str] = set()
    for entry in species.values():
        for lm in entry.get("moves_by_level", []):
            names.add(lm["move"])
        for mm in entry.get("moves_by_machine", []):
            names.add(mm["move"])
    return names


# ── PokeAPI: abilities ─────────────────────────────────────────────────────────

async def _fetch_ability(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    ability_name: str,
    version_group: str,
) -> dict | None:
    data = await _get_json(session, sem, f"{POKEAPI}/ability/{ability_name}")
    if not data:
        return None

    effect = ""
    short_effect = ""
    for e in data.get("effect_entries", []):
        if e["language"]["name"] == "en":
            effect       = e.get("effect", "").replace("\n", " ")
            short_effect = e.get("short_effect", "")
            break

    description = ""
    for ft in reversed(data.get("flavor_text_entries", [])):
        if ft["language"]["name"] != "en":
            continue
        if ft.get("version_group", {}).get("name") == version_group:
            description = ft["flavor_text"].replace("\n", " ").replace("\f", " ")
            break
    if not description:
        for ft in reversed(data.get("flavor_text_entries", [])):
            if ft["language"]["name"] == "en":
                description = ft["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

    return {
        "name":         ability_name,
        "effect":       effect,
        "short_effect": short_effect,
        "description":  description or short_effect,
    }


async def scrape_abilities(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    ability_names: set[str],
    version_group: str,
) -> dict[str, dict]:
    print(f"  Fetching {len(ability_names)} ability entries…")
    results = await asyncio.gather(*[
        _fetch_ability(session, sem, name, version_group)
        for name in sorted(ability_names)
    ])
    return {e["name"]: e for e in results if e}


def collect_ability_names(species: dict[str, dict]) -> set[str]:
    return {
        a["name"]
        for entry in species.values()
        for a in entry.get("abilities", [])
    }


# ── Bulbapedia wikitext: template parser ───────────────────────────────────────

def _find_template_end(wikitext: str, start: int) -> int:
    """Return the index just past the closing }} of a template starting at start."""
    depth = 0
    i = start
    n = len(wikitext)
    while i < n - 1:
        if wikitext[i:i+2] == "{{":
            depth += 1
            i += 2
        elif wikitext[i:i+2] == "}}":
            depth -= 1
            if depth == 0:
                return i + 2
            i += 2
        else:
            i += 1
    return n


def _split_params(inner: str) -> list[str]:
    """Split template body by | at bracket depth 0."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    n = len(inner)
    while i < n:
        ch2 = inner[i:i+2]
        if ch2 in ("{{", "[["):
            depth += 1
            buf.append(inner[i:i+2])
            i += 2
        elif ch2 in ("}}", "]]"):
            depth -= 1
            buf.append(inner[i:i+2])
            i += 2
        elif inner[i] == "|" and depth == 0:
            parts.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(inner[i])
            i += 1
    parts.append("".join(buf))
    return parts


def _parse_template(text: str) -> dict[str, str]:
    """Parse a {{Template|key=val|...}} block into a dict."""
    inner = text
    if inner.startswith("{{"):
        inner = inner[2:]
    if inner.endswith("}}"):
        inner = inner[:-2]
    params: dict[str, str] = {}
    for seg in _split_params(inner)[1:]:   # skip template name
        seg = seg.strip().lstrip("|").strip()
        if "=" in seg:
            k, _, v = seg.partition("=")
            params[k.strip()] = v.strip()
    return params


def _slug(s: str) -> str:
    return s.lower().replace(" ", "-").replace("'", "").replace(".", "").strip("-")


def _build_pokemon_entry(params: dict[str, str]) -> dict | None:
    name = params.get("pokemon", "").strip()
    if not name:
        return None
    ndex = params.get("ndex", "").strip()
    level_s = params.get("level", "").strip()
    moves = [
        _slug(params[f"move{i}"])
        for i in range(1, 5)
        if params.get(f"move{i}", "").strip()
    ]
    ability = params.get("ability", "").strip()
    held    = (params.get("held") or params.get("item") or "").strip()
    gender  = params.get("gender", "").strip() or None
    return {
        "pokemon":    _slug(name),
        "pokemon_id": int(ndex) if ndex.isdigit() else None,
        "level":      int(level_s) if level_s.isdigit() else None,
        "moves":      moves,
        "ability":    _slug(ability) if ability else None,
        "held_item":  _slug(held) if held else None,
        "gender":     gender,
    }


def _extract_teams(wikitext: str, game_code: str) -> list[dict]:
    """
    Walk wikitext and group {{Pokémon}} templates between {{Party}} / {{Party/end}} markers.

    The game code lives in the {{Party}} header (| game = HGSS), not in each
    {{Pokémon}} block, so we set in_matching_party on the header and collect
    Pokémon entries only while inside a matching party.
    """
    teams: list[dict] = []
    current: list[dict] = []
    last_section = ""
    in_matching_party = False

    i = 0
    n = len(wikitext)

    while i < n:
        # Track == Section Headers ==
        if (i == 0 or wikitext[i-1] == "\n") and wikitext[i] == "=":
            end = wikitext.find("\n", i)
            line = wikitext[i: end if end != -1 else n]
            if re.match(r"={2,4}[^=]", line):
                title = re.sub(r"={2,}|\{\{[^}]*\}\}|''", "", line).strip()
                if title:
                    last_section = title

        if wikitext[i:i+2] != "{{":
            i += 1
            continue

        end = _find_template_end(wikitext, i)
        block = wikitext[i:end]
        name_end = min(
            (block.find(c, 2) for c in ("|", "\n", "}}") if block.find(c, 2) != -1),
            default=len(block)
        )
        tname = block[2:name_end].strip().lower()

        if "party/footer" in tname or "party/end" in tname:
            if in_matching_party and current:
                teams.append({"location_hint": last_section, "team": current})
            current = []
            in_matching_party = False

        elif tname == "party":
            # Party header — the game code is here, not in the Pokémon blocks
            m = re.search(r'\|\s*game\s*=\s*(\S+)', block)
            in_matching_party = bool(m and m.group(1).upper() == game_code.upper())
            current = []

        elif tname.startswith("pok") and in_matching_party:
            params = _parse_template(block)
            entry = _build_pokemon_entry(params)
            if entry:
                current.append(entry)

        i = end

    if in_matching_party and current:
        teams.append({"location_hint": last_section, "team": current})

    return teams


# ── Bulbapedia: fetch wikitext for a page ──────────────────────────────────────

async def _fetch_wikitext(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    page: str,
) -> str | None:
    params = {
        "action":    "query",
        "titles":    page,
        "redirects": "1",
        "prop":      "revisions",
        "rvprop":    "content",
        "rvslots":   "main",
        "format":    "json",
        "formatversion": "2",
    }
    data = await _get_json(session, sem, BULBA_API, params)
    if not data:
        return None
    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        return None
    revs = pages[0].get("revisions", [])
    if not revs:
        return None
    return revs[0].get("slots", {}).get("main", {}).get("content")


# ── Bulbapedia: scrape all trainers ───────────────────────────────────────────

async def scrape_trainers(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    version: str,
) -> list[dict]:
    defs = TRAINER_DEFS.get(version, [])
    if not defs:
        print(f"  [info] No trainer definitions for '{version}' — skipping.")
        return []

    game_code = BULBA_CODE.get(version, "")
    print(f"  Fetching {len(defs)} trainer pages (game_code={game_code})…")

    async def process(tdef: dict) -> dict | None:
        page = tdef["page"]
        wikitext = await _fetch_wikitext(session, sem, page)
        if not wikitext:
            print(f"    [warn] No wikitext for '{page}'")
            return None

        teams = _extract_teams(wikitext, game_code)
        if not teams:
            print(f"    [warn] No {game_code} teams found on '{page}'")
            return None

        result: dict = {k: v for k, v in tdef.items()
                        if k not in ("page", "rival_starter_map")}

        # Rivals get all battles; fixed trainers get first team + optional rematch
        if tdef["class"] == "rival":
            starter_map = tdef.get("rival_starter_map", {})
            if starter_map:
                for battle in teams:
                    for p in battle["team"]:
                        if p["pokemon"] in starter_map:
                            battle["player_starter"] = starter_map[p["pokemon"]]
                            break
            result["battles"] = teams
        else:
            result["team"]         = teams[0]["team"] if teams else []
            if len(teams) > 1:
                result["rematch_team"] = teams[-1]["team"]

        return result

    results = await asyncio.gather(*[process(t) for t in defs])
    return [r for r in results if r]


# ── Assemble additional Pokémon IDs from static/gift/trade/trainer data ────────

def collect_extra_ids(
    static: dict,
    trainers: list[dict],
) -> set[int]:
    ids: set[int] = set()
    for key in ("static_encounters", "gift_pokemon", "starters"):
        for e in static.get(key, []):
            if e.get("pokemon_id"):
                ids.add(e["pokemon_id"])
    for t in static.get("in_game_trades", []):
        if t.get("give_pokemon_id"):
            ids.add(t["give_pokemon_id"])
        if t.get("receive_pokemon_id"):
            ids.add(t["receive_pokemon_id"])
    for trainer in trainers:
        for team_key in ("team", "rematch_team"):
            for mon in trainer.get(team_key, []):
                if mon.get("pokemon_id"):
                    ids.add(mon["pokemon_id"])
        for battle in trainer.get("battles", []):
            for mon in battle.get("team", []):
                if mon.get("pokemon_id"):
                    ids.add(mon["pokemon_id"])
    ids.discard(0)
    return ids


def collect_trainer_moves(trainers: list[dict]) -> set[str]:
    names: set[str] = set()
    for trainer in trainers:
        for team_key in ("team", "rematch_team"):
            for mon in trainer.get(team_key, []):
                names.update(mon.get("moves", []))
        for battle in trainer.get("battles", []):
            for mon in battle.get("team", []):
                names.update(mon.get("moves", []))
    names.discard("")
    return names


# ── TM scraping ───────────────────────────────────────────────────────────────

def _strip_wiki_markup(text: str) -> str:
    """Remove wikitext markup, leaving plain readable text."""
    # [[Page|Display]] → Display
    text = re.sub(r'\[\[[^\]\|]+\|([^\]]+)\]\]', r'\1', text)
    # [[Page]] → Page
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # {{template|arg}} → arg  (e.g. {{m|Flamethrower}} → Flamethrower)
    text = re.sub(r'\{\{[^|}\n]+\|([^}]+)\}\}', r'\1', text)
    # Remove remaining templates
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    # Bold / italic
    text = re.sub(r"'{2,3}", '', text)
    # HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    return ' '.join(text.split()).strip()


def _extract_tmtable_location(wikitext: str, bulba_code: str) -> str | None:
    """
    Scan wikitext for {{TMtable/row|{{gameabbrevN|CODE}}|location|...}} templates
    and return the cleaned location string for the matching game code.
    """
    i = 0
    n = len(wikitext)
    while i < n:
        if wikitext[i:i+2] != "{{":
            i += 1
            continue
        end = _find_template_end(wikitext, i)
        block = wikitext[i:end]
        name_end = min(
            (block.find(c, 2) for c in ("|", "\n", "}}") if block.find(c, 2) != -1),
            default=len(block),
        )
        tname = block[2:name_end].strip().lower()
        if tname == "tmtable/row":
            parts = _split_params(block[2:-2])  # strip {{ and }}
            if len(parts) >= 3:
                # parts[1] is {{gameabbrevN|CODE}} — extract the CODE after |
                m = re.search(r'\|\s*([A-Z0-9]+)\s*\}\}', parts[1])
                if m and m.group(1).upper() == bulba_code.upper():
                    cleaned = _strip_wiki_markup(parts[2].strip())
                    if cleaned and cleaned.lower() not in ("n/a", "unavailable", "none", ""):
                        return cleaned
        i = end
    return None


async def _fetch_tm_info(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    tm_number: int,
    version_group: str,
    bulba_code: str,
) -> dict | None:
    item_name = f"tm{tm_number:02d}"

    # PokeAPI: does this TM exist in this version group, and what move does it teach?
    item_data = await _get_json(session, sem, f"{POKEAPI}/item/{item_name}")
    if not item_data:
        return None

    move_name: str | None = None
    for me in item_data.get("machines", []):
        if me["version_group"]["name"] == version_group:
            machine_data = await _get_json(session, sem, me["machine"]["url"])
            if machine_data:
                move_name = machine_data["move"]["name"]
            break

    if not move_name:
        return None  # TM doesn't exist in this version group

    # Bulbapedia: best-effort location lookup via TMtable/row templates
    location: str | None = None
    if bulba_code:
        wikitext = await _fetch_wikitext(session, sem, f"TM{tm_number:03d}")
        if wikitext:
            location = _extract_tmtable_location(wikitext, bulba_code)

    return {"number": tm_number, "name": item_name, "move": move_name, "location": location}


async def scrape_tms(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    version: str,
    version_group: str,
) -> list[dict]:
    bulba_code = TM_CODE.get(version, "")
    print(f"  Fetching TM01–TM100 for {version_group} (game code: {bulba_code or 'none'})…")
    results = await asyncio.gather(*[
        _fetch_tm_info(session, sem, n, version_group, bulba_code)
        for n in range(1, 101)
    ])
    tms = [r for r in results if r]
    with_loc = sum(1 for t in tms if t["location"])
    print(f"  Found {len(tms)} TMs ({with_loc} with locations).")
    return tms


# ── Cave / dungeon maps ────────────────────────────────────────────────────────

async def _fetch_bulba_image_urls(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    filenames: list[str],
) -> dict[str, str]:
    """
    Resolve a list of Bulbapedia File: titles to their direct CDN URLs.
    Uses the MediaWiki imageinfo API, batching up to 50 titles per request.
    Returns {filename: url} for files that exist; missing files are omitted.
    """
    result: dict[str, str] = {}
    batch_size = 50
    for i in range(0, len(filenames), batch_size):
        batch = filenames[i : i + batch_size]
        titles = "|".join(f"File:{name}" for name in batch)
        params = {
            "action":  "query",
            "titles":  titles,
            "prop":    "imageinfo",
            "iiprop":  "url",
            "format":  "json",
        }
        data = await _get_json(session, sem, BULBA_API, params)
        if not data:
            continue
        for page in data.get("query", {}).get("pages", {}).values():
            # Pages in the shared Bulbapedia media repository are marked "missing"
            # on the wiki side but still carry imageinfo with a valid CDN URL.
            # Only skip pages that have no imageinfo at all.
            infos = page.get("imageinfo", [])
            if not infos or not infos[0].get("url"):
                continue
            title = page.get("title", "")
            filename = title.removeprefix("File:")
            result[filename] = infos[0]["url"]
    return result


async def resolve_map_floors(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    version: str,
) -> dict[str, list[dict]]:
    """
    Resolve Bulbapedia floor image URLs for all cave/dungeon locations in `version`.

    Returns {location_id: [floor_dict, ...]} where each floor_dict contains:
      id            — stable slug (e.g. "ice-path-b1f")
      display_name  — human-readable label (e.g. "B1F")
      image_url     — direct Bulbapedia CDN URL, or None if the image wasn't found
      warps         — list of {x, y, dest_floor_id, dest_x, dest_y} in tile-grid units
                      (1 tile = 16 px in all mainline gens), matching pret decomp format
      pokeapi_areas — list of PokeAPI location-area slugs whose encounters belong to this
                      floor (e.g. ["ice-path-area"]); empty when not yet mapped. Used by
                      make_variants.py to assign encounters to the correct floor.
    """
    locations = CAVE_MAPS.get(version, [])
    if not locations:
        print(f"  [info] No cave map definitions for '{version}' — skipping.")
        return {}

    all_filenames = [
        floor["bulbapedia_image"]
        for loc in locations
        for floor in loc["floors"]
        if floor.get("bulbapedia_image")
    ]
    print(f"  Resolving {len(all_filenames)} floor image URLs from Bulbapedia…")
    url_map = await _fetch_bulba_image_urls(session, sem, all_filenames)
    found = sum(1 for f in all_filenames if f in url_map)
    print(f"  Resolved {found}/{len(all_filenames)} images.")

    result: dict[str, list[dict]] = {}
    for loc in locations:
        floors_out: list[dict] = []
        for floor in loc["floors"]:
            img_name = floor.get("bulbapedia_image")
            floors_out.append({
                "id":            floor["id"],
                "display_name":  floor["display_name"],
                "image_url":     url_map.get(img_name) if img_name else None,
                "warps":         floor.get("warps", []),
                "pokeapi_areas": floor.get("pokeapi_areas", []),
            })
        result[loc["id"]] = floors_out
    return result


# ── Main ───────────────────────────────────────────────────────────────────────

async def run(version: str) -> None:
    version_group = VERSION_GROUP[version]
    gen           = VERSION_GEN[version]
    hm_moves      = HM_MOVES.get(version, {})
    static        = GAME_STATIC.get(version, {})

    print(f"\n=== Scraping '{version}' (gen {gen}, vg={version_group}) ===")

    sem = asyncio.Semaphore(CONCURRENT)
    headers = {"User-Agent": "NuzlockerApp/1.0 DataScraper (educational non-commercial use)"}

    async with aiohttp.ClientSession(headers=headers) as session:

        # 1. Encounter tables
        print("\n[1/6] Encounter tables")
        routes = await scrape_encounters(session, sem, version)

        # 2. Trainer teams
        print("\n[2/6] Trainer teams (Bulbapedia)")
        trainers = await scrape_trainers(session, sem, version)

        # 3. Species
        print("\n[3/6] Species")
        pokemon_ids = collect_pokemon_ids(routes) | collect_extra_ids(static, trainers)
        species = await scrape_species(session, sem, pokemon_ids, version_group, hm_moves)

        # 4. TMs
        print("\n[4/6] TMs (PokeAPI + Bulbapedia)")
        tms = await scrape_tms(session, sem, version, version_group)

        # 5. Moves
        print("\n[5/7] Moves")
        move_names = collect_move_names(species) | collect_trainer_moves(trainers)
        move_names.update(hm_moves.keys())
        move_names.update(tm["move"] for tm in tms)
        moves = await scrape_moves(session, sem, move_names, version_group)

        # 6. Abilities
        print("\n[6/7] Abilities")
        ability_names = collect_ability_names(species)
        abilities = await scrape_abilities(session, sem, ability_names, version_group)

        # 7. Cave / dungeon maps
        print("\n[7/7] Cave maps (Bulbapedia) + assembling output…")
        dungeon_floors = await resolve_map_floors(session, sem, version)

    output = {
        "game":          version,
        "version_group": version_group,
        "generation":    gen,
        "scraped_at":    datetime.now(timezone.utc).isoformat(),
        "hm_moves":      hm_moves,
        "badge_obedience": BADGE_OBEDIENCE.get(version, []),
        "starters":      static.get("starters", []),
        "static_encounters": static.get("static_encounters", []),
        "gift_pokemon":  static.get("gift_pokemon", []),
        "in_game_trades": static.get("in_game_trades", []),
        "route_order":     ROUTE_ORDER.get(version, []),
        "routes":          routes,
        "dungeon_floors":  dungeon_floors,
        "trainers":        trainers,
        "tms":             tms,
        "species":         species,
        "moves":           moves,
        "abilities":       abilities,
    }

    raw_path = OUTPUT_DIR / f"{version}.json"
    raw_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    zip_path = build_and_write_zip(version, output, SPRITES_DIR, OUTPUT_DIR)

    total_floors = sum(len(floors) for floors in dungeon_floors.values())
    print(f"\nDone")
    print(f"  Raw     → {raw_path}")
    print(f"  ZIP     → {zip_path}")
    print(f"  Pokémon : {len(species)}")
    print(f"  Routes  : {len(routes)}")
    print(f"  Trainers: {len(trainers)}")
    print(f"  TMs     : {len(tms)}")
    print(f"  Dungeons: {len(dungeon_floors)} locations, {total_floors} floors")
    print(f"  Moves   : {len(moves)}")
    print(f"  Abilities: {len(abilities)}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <game-name>")
        print("Examples:")
        print("  python scrape.py 'soul silver'")
        print("  python scrape.py platinum")
        print(f"\nSupported: {', '.join(sorted(GAME_SLUGS))}")
        sys.exit(1)

    raw   = " ".join(sys.argv[1:]).lower().strip()
    slug  = GAME_SLUGS.get(raw)
    if not slug:
        # Fuzzy: try the value directly
        if raw in VERSION_GROUP:
            slug = raw
        else:
            print(f"Unknown game: '{raw}'")
            print(f"Supported: {', '.join(sorted(GAME_SLUGS))}")
            sys.exit(1)

    asyncio.run(run(slug))


if __name__ == "__main__":
    main()
