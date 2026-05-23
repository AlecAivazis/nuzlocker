"""
Fetch warp connections from pret Pokémon decomp repos on GitHub.

Supported repos / format types:
  pokered       Gen 1 RBY   ASM  warp_event x, y, CONST, warp_idx  (1-based idx)
  pokecrystal   Gen 2 GSC   ASM  warp_event x, y, CONST, warp_idx  (1-based idx)
  pokeemerald   Gen 3 RSE   JSON warp_events [{x,y,dest_map,dest_warp_id}]  (0-based)
  pokefirered   Gen 3 FRLG  JSON warp_events [{x,y,dest_map,dest_warp_id}]  (0-based)
  pokeplatinum  Gen 4 Pt    JSON warp_events [{x,z,dest_header_id,dest_warp_id}] (0-based)
  pokeheartgold Gen 4 HGSS  JSON warps [{x,z,header,anchor}]  (0-based)

Each floor in _PRET_MAPS maps a floor_id to repo-specific identifiers:
  pokered / pokecrystal  : SCREAMING_SNAKE_CASE map constant used in warp_event macros
  pokeemerald/pokefirered: directory name inside data/maps/ (e.g. "GraniteCave_B1F")
  pokeplatinum           : stem of events_*.json file (e.g. "iron_island_1f"),
                           or list of stems for floors split across multiple zone files
  pokeheartgold          : MAP_ constant from include/constants/maps.h

Returns {floor_id: [{"x", "y", "destFloorID", "destX", "destY"}]}.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp

GITHUB_RAW = "https://raw.githubusercontent.com/pret"

# ── Per-version pret repo config ───────────────────────────────────────────────
# version → (repo_name, format_type)
_PRET_CONFIG: dict[str, tuple[str, str]] = {
    "red":        ("pokered",       "gen1_asm"),
    "blue":       ("pokered",       "gen1_asm"),
    "yellow":     ("pokered",       "gen1_asm"),
    "gold":       ("pokecrystal",   "gen2_asm"),
    "silver":     ("pokecrystal",   "gen2_asm"),
    "crystal":    ("pokecrystal",   "gen2_asm"),
    "firered":    ("pokefirered",   "gen3_json"),
    "leafgreen":  ("pokefirered",   "gen3_json"),
    "ruby":       ("pokeemerald",   "gen3_json"),
    "sapphire":   ("pokeemerald",   "gen3_json"),
    "emerald":    ("pokeemerald",   "gen3_json"),
    "heartgold":  ("pokeheartgold", "gen4_hgss"),
    "soulsilver": ("pokeheartgold", "gen4_hgss"),
    "platinum":   ("pokeplatinum",  "gen4_pt"),
}

# ── Floor → pret identifiers ───────────────────────────────────────────────────
# pret_id conventions:
#   pokered / pokecrystal  : SCREAMING_SNAKE_CASE constant (= warp_event dest value)
#   pokeemerald/pokefirered: directory name in data/maps/
#   pokeplatinum           : stem of res/field/events/events_{stem}.json; list for split floors
#   pokeheartgold          : MAP_ constant from maps.h (= warp header value in zone file)

_PretId = str | list[str]
_PRET_MAPS: dict[str, dict[str, _PretId]] = {

    # ── Johto ─────────────────────────────────────────────────────────────────

    "sprout-tower-1f": {
        "pokecrystal":   "SPROUT_TOWER_1F",
        "pokeheartgold": "MAP_SPROUT_TOWER_1F",
    },
    "sprout-tower-2f": {
        "pokecrystal":   "SPROUT_TOWER_2F",
        "pokeheartgold": "MAP_SPROUT_TOWER_2F",
    },
    "sprout-tower-3f": {
        "pokecrystal":   "SPROUT_TOWER_3F",
        "pokeheartgold": "MAP_SPROUT_TOWER_3F",
    },

    "union-cave-1f": {
        "pokecrystal":   "UNION_CAVE_1F",
        "pokeheartgold": "MAP_UNION_CAVE_1F",
    },
    "union-cave-b1f": {
        "pokecrystal":   "UNION_CAVE_B1F",
        "pokeheartgold": "MAP_UNION_CAVE_B1F",
    },
    "union-cave-b2f": {
        "pokecrystal":   "UNION_CAVE_B2F",
        "pokeheartgold": "MAP_UNION_CAVE_B2F",
    },

    "slowpoke-well-b1f": {
        "pokecrystal":   "SLOWPOKE_WELL_B1F",
        "pokeheartgold": "MAP_SLOWPOKE_WELL_B1F",
    },
    "slowpoke-well-b2f": {
        "pokecrystal":   "SLOWPOKE_WELL_B2F",
        "pokeheartgold": "MAP_SLOWPOKE_WELL_B2F",
    },

    "ilex-forest": {
        "pokecrystal":   "ILEX_FOREST",
        "pokeheartgold": "MAP_ILEX_FOREST",
    },

    "mt-mortar-entrance": {
        "pokecrystal":   "MOUNT_MORTAR_1F_OUTSIDE",
        "pokeheartgold": "MAP_MOUNT_MORTAR_1F_ENTRANCE",
    },
    "mt-mortar-basement": {
        "pokecrystal":   "MOUNT_MORTAR_B1F",
        "pokeheartgold": "MAP_MOUNT_MORTAR_B1F",
    },
    "mt-mortar-upper-cave": {
        "pokecrystal":   "MOUNT_MORTAR_1F_INSIDE",
        "pokeheartgold": "MAP_MOUNT_MORTAR_1F_BACK",
    },
    "mt-mortar-lower-cave": {
        "pokecrystal":   "MOUNT_MORTAR_2F_INSIDE",
        "pokeheartgold": "MAP_MOUNT_MORTAR_2F",
    },

    "burned-tower-1f": {
        "pokecrystal":   "BURNED_TOWER_1F",
        "pokeheartgold": "MAP_BURNED_TOWER_1F",
    },
    "burned-tower-b1f": {
        "pokecrystal":   "BURNED_TOWER_B1F",
        "pokeheartgold": "MAP_BURNED_TOWER_B1F",
    },

    # Crystal calls it Tin Tower; HGSS calls it Bell Tower. 10F is "Roof" in Crystal.
    "bell-tower-1f":  {"pokecrystal": "TIN_TOWER_1F",  "pokeheartgold": "MAP_BELL_TOWER_1F"},
    "bell-tower-2f":  {"pokecrystal": "TIN_TOWER_2F",  "pokeheartgold": "MAP_BELL_TOWER_2F"},
    "bell-tower-3f":  {"pokecrystal": "TIN_TOWER_3F",  "pokeheartgold": "MAP_BELL_TOWER_3F"},
    "bell-tower-4f":  {"pokecrystal": "TIN_TOWER_4F",  "pokeheartgold": "MAP_BELL_TOWER_4F"},
    "bell-tower-5f":  {"pokecrystal": "TIN_TOWER_5F",  "pokeheartgold": "MAP_BELL_TOWER_5F"},
    "bell-tower-6f":  {"pokecrystal": "TIN_TOWER_6F",  "pokeheartgold": "MAP_BELL_TOWER_6F"},
    "bell-tower-7f":  {"pokecrystal": "TIN_TOWER_7F",  "pokeheartgold": "MAP_BELL_TOWER_7F"},
    "bell-tower-8f":  {"pokecrystal": "TIN_TOWER_8F",  "pokeheartgold": "MAP_BELL_TOWER_8F"},
    "bell-tower-9f":  {"pokecrystal": "TIN_TOWER_9F",  "pokeheartgold": "MAP_BELL_TOWER_9F"},
    "bell-tower-10f": {"pokecrystal": "TIN_TOWER_ROOF", "pokeheartgold": "MAP_BELL_TOWER_10F"},

    # Dark Cave: Crystal uses VIOLET/BLACKTHORN_ENTRANCE; HGSS uses ROUTE_31/45_SIDE
    "dark-cave-1": {
        "pokecrystal":   "DARK_CAVE_VIOLET_ENTRANCE",
        "pokeheartgold": "MAP_DARK_CAVE_ROUTE_31_SIDE",
    },
    "dark-cave-2": {
        "pokecrystal":   "DARK_CAVE_BLACKTHORN_ENTRANCE",
        "pokeheartgold": "MAP_DARK_CAVE_ROUTE_45_SIDE",
    },

    "ice-path-1f":  {"pokecrystal": "ICE_PATH_1F",  "pokeheartgold": "MAP_ICE_PATH_1F"},
    "ice-path-b1f": {"pokecrystal": "ICE_PATH_B1F", "pokeheartgold": "MAP_ICE_PATH_B1F"},
    # Crystal B2F is split into two halves; HGSS combines them
    "ice-path-b2f": {
        "pokecrystal":   ["ICE_PATH_B2F_BLACKTHORN_SIDE", "ICE_PATH_B2F_MAHOGANY_SIDE"],
        "pokeheartgold": "MAP_ICE_PATH_B2F",
    },
    "ice-path-b3f": {"pokecrystal": "ICE_PATH_B3F", "pokeheartgold": "MAP_ICE_PATH_B3F"},

    "dragons-den-entrance": {
        "pokecrystal":   "DRAGONS_DEN_1F",
        "pokeheartgold": "MAP_DRAGONS_DEN_ENTRANCE",
    },
    "dragons-den-interior": {
        "pokecrystal":   "DRAGONS_DEN_B1F",
        "pokeheartgold": "MAP_DRAGONS_DEN",
    },

    # Whirl Islands — Crystal has 4 separate 1F maps; HGSS has one shared MAP_WHIRL_ISLANDS_1F
    "whirl-islands-1f-nw": {"pokecrystal": "WHIRL_ISLAND_NW"},
    "whirl-islands-1f-ne": {"pokecrystal": "WHIRL_ISLAND_NE"},
    "whirl-islands-1f-sw": {"pokecrystal": "WHIRL_ISLAND_SW"},
    "whirl-islands-1f-se": {"pokecrystal": "WHIRL_ISLAND_SE"},
    "whirl-islands-b1f": {
        "pokecrystal":   "WHIRL_ISLAND_B1F",
        "pokeheartgold": "MAP_WHIRL_ISLANDS_B1F",
    },
    "whirl-islands-b2f": {
        "pokecrystal":   "WHIRL_ISLAND_B2F",
        "pokeheartgold": "MAP_WHIRL_ISLANDS_B2F",
    },
    "whirl-islands-b3f": {
        "pokecrystal":   "WHIRL_ISLAND_LUGIA_CHAMBER",
        "pokeheartgold": "MAP_WHIRL_ISLANDS_B3F_LUGIA_CAVE",
    },

    # Mt. Silver — HGSS has a complex cave network; Crystal uses SilverCave naming
    "mt-silver-exterior": {
        "pokecrystal":   "SILVER_CAVE_OUTSIDE",
        "pokeheartgold": "MAP_MOUNT_SILVER",
    },
    "mt-silver-1f": {
        "pokecrystal":   "SILVER_CAVE_ROOM_1",
        "pokeheartgold": "MAP_MOUNT_SILVER_CAVE_1F",
    },
    "mt-silver-2f": {
        "pokeheartgold": "MAP_MOUNT_SILVER_CAVE_2F",
    },
    "mt-silver-3f": {
        "pokeheartgold": "MAP_MOUNT_SILVER_CAVE_3F",
    },
    "mt-silver-summit": {
        "pokeheartgold": "MAP_MOUNT_SILVER_CAVE_SUMMIT",
    },

    # ── Kanto (HGSS and Red/FireRed share these; Gold/Crystal also has Kanto) ──

    "mt-moon-1f": {
        "pokered":       "MT_MOON_1F",
        "pokefirered":   "MtMoon_1F",
        "pokecrystal":   "MOUNT_MOON",   # Crystal: MountMoon.asm
        "pokeheartgold": "MAP_MT_MOON_1F",
    },
    "mt-moon-square": {
        "pokecrystal":   "MOUNT_MOON_SQUARE",
        "pokeheartgold": "MAP_MT_MOON_SQUARE",
    },

    # Red/FireRed-only: Mt Moon has B1F/B2F; HGSS combined them into one area
    "mt-moon-b1f": {
        "pokered":     "MT_MOON_B1F",
        "pokefirered": "MtMoon_B1F",
    },
    "mt-moon-b2f": {
        "pokered":     "MT_MOON_B2F",
        "pokefirered": "MtMoon_B2F",
    },

    "rock-tunnel-1": {
        "pokered":       "ROCK_TUNNEL_1F",
        "pokefirered":   "RockTunnel_1F",
        "pokecrystal":   "ROCK_TUNNEL_1F",
        "pokeheartgold": "MAP_ROCK_TUNNEL_1F",
    },
    "rock-tunnel-2": {
        "pokered":       "ROCK_TUNNEL_B1F",
        "pokefirered":   "RockTunnel_B1F",
        "pokecrystal":   "ROCK_TUNNEL_B1F",
        "pokeheartgold": "MAP_ROCK_TUNNEL_B1F",
    },
    "rock-tunnel-1f": {
        "pokered":     "ROCK_TUNNEL_1F",
        "pokefirered": "RockTunnel_1F",
    },
    "rock-tunnel-b1f": {
        "pokered":     "ROCK_TUNNEL_B1F",
        "pokefirered": "RockTunnel_B1F",
    },

    "pokemon-tower-1f": {"pokered": "POKEMON_TOWER_1F", "pokefirered": "PokemonTower_1F"},
    "pokemon-tower-2f": {"pokered": "POKEMON_TOWER_2F", "pokefirered": "PokemonTower_2F"},
    "pokemon-tower-3f": {"pokered": "POKEMON_TOWER_3F", "pokefirered": "PokemonTower_3F"},
    "pokemon-tower-4f": {"pokered": "POKEMON_TOWER_4F", "pokefirered": "PokemonTower_4F"},
    "pokemon-tower-5f": {"pokered": "POKEMON_TOWER_5F", "pokefirered": "PokemonTower_5F"},
    "pokemon-tower-6f": {"pokered": "POKEMON_TOWER_6F", "pokefirered": "PokemonTower_6F"},
    "pokemon-tower-7f": {"pokered": "POKEMON_TOWER_7F", "pokefirered": "PokemonTower_7F"},

    "silph-co-1f":  {"pokered": "SILPH_CO_1F",  "pokefirered": "SilphCo_1F"},
    "silph-co-2f":  {"pokered": "SILPH_CO_2F",  "pokefirered": "SilphCo_2F"},
    "silph-co-3f":  {"pokered": "SILPH_CO_3F",  "pokefirered": "SilphCo_3F"},
    "silph-co-4f":  {"pokered": "SILPH_CO_4F",  "pokefirered": "SilphCo_4F"},
    "silph-co-5f":  {"pokered": "SILPH_CO_5F",  "pokefirered": "SilphCo_5F"},
    "silph-co-6f":  {"pokered": "SILPH_CO_6F",  "pokefirered": "SilphCo_6F"},
    "silph-co-7f":  {"pokered": "SILPH_CO_7F",  "pokefirered": "SilphCo_7F"},
    "silph-co-8f":  {"pokered": "SILPH_CO_8F",  "pokefirered": "SilphCo_8F"},
    "silph-co-9f":  {"pokered": "SILPH_CO_9F",  "pokefirered": "SilphCo_9F"},
    "silph-co-10f": {"pokered": "SILPH_CO_10F", "pokefirered": "SilphCo_10F"},
    "silph-co-11f": {"pokered": "SILPH_CO_11F", "pokefirered": "SilphCo_11F"},

    "victory-road-1f": {
        "pokered":     "VICTORY_ROAD_1F",
        "pokefirered": "VictoryRoad_1F",
    },
    "victory-road-2f": {
        "pokered":     "VICTORY_ROAD_2F",
        "pokefirered": "VictoryRoad_2F",
    },
    "victory-road-3f": {
        "pokered":     "VICTORY_ROAD_3F",
        "pokefirered": "VictoryRoad_3F",
    },
    # Crystal has a single-floor Kanto Victory Road (VictoryRoad.asm = constant VICTORY_ROAD)
    "victory-road-kanto-1f": {
        "pokered":       "VICTORY_ROAD_1F",
        "pokefirered":   "VictoryRoad_1F",
        "pokecrystal":   "VICTORY_ROAD",
        "pokeheartgold": "MAP_VICTORY_ROAD_1F",
    },
    "victory-road-kanto-2f": {
        "pokered":       "VICTORY_ROAD_2F",
        "pokefirered":   "VictoryRoad_2F",
        "pokeheartgold": "MAP_VICTORY_ROAD_2F",
    },
    "victory-road-kanto-3f": {
        "pokered":       "VICTORY_ROAD_3F",
        "pokefirered":   "VictoryRoad_3F",
        "pokeheartgold": "MAP_VICTORY_ROAD_3F",
    },

    "seafoam-islands-1f":  {
        "pokered":       "SEAFOAM_ISLANDS_1F",
        "pokefirered":   "SeafoamIslands_1F",
        "pokeheartgold": "MAP_SEAFOAM_ISLANDS_1F",
    },
    "seafoam-islands-b1f": {
        "pokered":       "SEAFOAM_ISLANDS_B1F",
        "pokefirered":   "SeafoamIslands_B1F",
        "pokeheartgold": "MAP_SEAFOAM_ISLANDS_B1F",
    },
    "seafoam-islands-b2f": {
        "pokered":       "SEAFOAM_ISLANDS_B2F",
        "pokefirered":   "SeafoamIslands_B2F",
        "pokeheartgold": "MAP_SEAFOAM_ISLANDS_B2F",
    },
    "seafoam-islands-b3f": {
        "pokered":       "SEAFOAM_ISLANDS_B3F",
        "pokefirered":   "SeafoamIslands_B3F",
        "pokeheartgold": "MAP_SEAFOAM_ISLANDS_B3F",
    },
    "seafoam-islands-b4f": {
        "pokered":       "SEAFOAM_ISLANDS_B4F",
        "pokefirered":   "SeafoamIslands_B4F",
        "pokeheartgold": "MAP_SEAFOAM_ISLANDS_B4F",
    },

    "cerulean-cave-1f":  {
        "pokered":       "CERULEAN_CAVE_1F",
        "pokefirered":   "CeruleanCave_1F",
        "pokeheartgold": "MAP_CERULEAN_CAVE_1F",
    },
    "cerulean-cave-b1f": {
        "pokered":       "CERULEAN_CAVE_B1F",
        "pokefirered":   "CeruleanCave_B1F",
        "pokeheartgold": "MAP_CERULEAN_CAVE_B1F",
    },
    "cerulean-cave-2f":  {
        "pokered":       "CERULEAN_CAVE_2F",
        "pokefirered":   "CeruleanCave_2F",
        "pokeheartgold": "MAP_CERULEAN_CAVE_2F",
    },

    "power-plant": {
        "pokered":     "POWER_PLANT",
        "pokefirered": "PowerPlant",
    },

    # ── Sevii Islands (FireRed/LeafGreen only) ─────────────────────────────────

    "mt-ember-exterior":       {"pokefirered": "MtEmber_Exterior"},
    "mt-ember-summit":         {"pokefirered": "MtEmber_Summit"},
    "mt-ember-summit-path-1f": {"pokefirered": "MtEmber_SummitPath_1F"},
    "mt-ember-summit-path-2f": {"pokefirered": "MtEmber_SummitPath_2F"},
    "mt-ember-summit-path-3f": {"pokefirered": "MtEmber_SummitPath_3F"},
    "mt-ember-ruby-path-b1f":  {"pokefirered": "MtEmber_RubyPath_B1F"},
    "mt-ember-ruby-path-b3f":  {"pokefirered": "MtEmber_RubyPath_B3F"},
    "mt-ember-ruby-path-b4f":  {"pokefirered": "MtEmber_RubyPath_B4F"},
    "mt-ember-ruby-path-b5f":  {"pokefirered": "MtEmber_RubyPath_B5F"},

    # ── Hoenn (Emerald/Ruby/Sapphire) ─────────────────────────────────────────

    "granite-cave-1f":  {"pokeemerald": "GraniteCave_1F"},
    "granite-cave-b1f": {"pokeemerald": "GraniteCave_B1F"},
    "granite-cave-b2f": {"pokeemerald": "GraniteCave_B2F"},

    "meteor-falls-entrance": {"pokeemerald": "MeteorFalls_1F_1R"},
    "meteor-falls-1f-1r":    {"pokeemerald": "MeteorFalls_1F_1R"},
    "meteor-falls-b1f-1r":   {"pokeemerald": "MeteorFalls_B1F_1R"},
    "meteor-falls-b1f-2r":   {"pokeemerald": "MeteorFalls_B1F_2R"},

    "fiery-path":  {"pokeemerald": "FieryPath"},
    "jagged-pass": {"pokeemerald": "JaggedPass"},

    "seafloor-cavern-entrance": {"pokeemerald": "SeafloorCavern_Entrance"},
    "seafloor-cavern-room1":    {"pokeemerald": "SeafloorCavern_Room1"},
    "seafloor-cavern-room2":    {"pokeemerald": "SeafloorCavern_Room2"},
    "seafloor-cavern-room3":    {"pokeemerald": "SeafloorCavern_Room3"},
    "seafloor-cavern-room4":    {"pokeemerald": "SeafloorCavern_Room4"},
    "seafloor-cavern-room5":    {"pokeemerald": "SeafloorCavern_Room5"},
    "seafloor-cavern-room6":    {"pokeemerald": "SeafloorCavern_Room6"},
    "seafloor-cavern-room7":    {"pokeemerald": "SeafloorCavern_Room7"},
    "seafloor-cavern-room8":    {"pokeemerald": "SeafloorCavern_Room8"},
    "seafloor-cavern-room9":    {"pokeemerald": "SeafloorCavern_Room9"},

    "cave-of-origin-1f":  {"pokeemerald": "CaveOfOrigin_1F"},
    "cave-of-origin-b1f": {"pokeemerald": "CaveOfOrigin_B1F"},
    "cave-of-origin-b2f": {"pokeemerald": "CaveOfOrigin_B2F"},
    "cave-of-origin-b3f": {"pokeemerald": "CaveOfOrigin_B3F"},
    "cave-of-origin-b4f": {"pokeemerald": "CaveOfOrigin_B4F"},

    "shoal-cave-lowtide-entrance":  {"pokeemerald": "ShoalCave_LowTideEntranceRoom"},
    "shoal-cave-lowtide-inner":     {"pokeemerald": "ShoalCave_LowTideInnerRoom"},
    "shoal-cave-hightide-entrance": {"pokeemerald": "ShoalCave_HighTideEntranceRoom"},
    "shoal-cave-hightide-inner":    {"pokeemerald": "ShoalCave_HighTideInnerRoom"},

    "sky-pillar-1f":  {"pokeemerald": "SkyPillar_1F"},
    "sky-pillar-2f":  {"pokeemerald": "SkyPillar_2F"},
    "sky-pillar-3f":  {"pokeemerald": "SkyPillar_3F"},
    "sky-pillar-4f":  {"pokeemerald": "SkyPillar_4F"},
    "sky-pillar-5f":  {"pokeemerald": "SkyPillar_5F"},
    "sky-pillar-roof": {"pokeemerald": "SkyPillar_Top"},

    "victory-road-b1f": {
        "pokeemerald": "VictoryRoad_B1F",
    },

    # ── Sinnoh (Platinum) ──────────────────────────────────────────────────────

    "oreburgh-gate-1f":  {"pokeplatinum": "oreburgh_gate_1f"},
    "oreburgh-gate-b1f": {"pokeplatinum": "oreburgh_gate_b1f"},

    "oreburgh-mine-1f":  {"pokeplatinum": "oreburgh_mine_1f"},
    "oreburgh-mine-b1f": {"pokeplatinum": "oreburgh_mine_b1f"},

    # Mt. Coronet has separate north/south 1F files in pokeplatinum
    "mt-coronet-1f": {"pokeplatinum": ["mt_coronet_1f_south", "mt_coronet_1f_north"]},
    "mt-coronet-2f": {"pokeplatinum": "mt_coronet_2f"},
    "mt-coronet-3f": {"pokeplatinum": "mt_coronet_3f"},
    "mt-coronet-4f": {"pokeplatinum": "mt_coronet_4f"},
    "mt-coronet-5f": {"pokeplatinum": "mt_coronet_5f"},
    "mt-coronet-6f": {"pokeplatinum": "mt_coronet_6f"},
    "mt-coronet-exterior": {"pokeplatinum": "mt_coronet_exterior"},
    "mt-coronet-summit":   {"pokeplatinum": "spear_pillar"},
    "mt-coronet-b1f":      {"pokeplatinum": "mt_coronet_b1f"},

    "wayward-cave-1f": {"pokeplatinum": "wayward_cave_1f"},
    "wayward-cave-2f": {"pokeplatinum": "wayward_cave_2f"},

    # Iron Island B1F/B2F are each split into left_room + right_room files
    "iron-island-1f":  {"pokeplatinum": "iron_island_1f"},
    "iron-island-b1f": {"pokeplatinum": ["iron_island_b1f_left_room", "iron_island_b1f_right_room"]},
    "iron-island-b2f": {"pokeplatinum": ["iron_island_b2f_left_room", "iron_island_b2f_right_room"]},

    "victory-road-sinnoh-1f": {"pokeplatinum": "victory_road_1f"},
    "victory-road-sinnoh-2f": {"pokeplatinum": "victory_road_2f"},
    "victory-road-sinnoh-3f": {"pokeplatinum": "victory_road_3f"},

    "snowpoint-temple-1f": {"pokeplatinum": "snowpoint_temple_1f"},
    "snowpoint-temple-2f": {"pokeplatinum": "snowpoint_temple_2f"},
    "snowpoint-temple-3f": {"pokeplatinum": "snowpoint_temple_3f"},
    "snowpoint-temple-4f": {"pokeplatinum": "snowpoint_temple_4f"},
    "snowpoint-temple-5f": {"pokeplatinum": "snowpoint_temple_5f"},

    "distortion-world": {"pokeplatinum": "distortion_world"},
}


# ── Helpers ────────────────────────────────────────────────────────────────────

# Known abbreviations and floor codes that should stay uppercase in file stems
_KEEP_UPPER: frozenset[str] = frozenset({
    "NW", "NE", "SW", "SE",
    "1F", "2F", "3F", "4F", "5F", "6F", "7F", "8F", "9F", "10F", "11F",
    "B1F", "B2F", "B3F", "B4F", "B5F",
    "1R", "2R",
})

_WARP_RE = re.compile(r'warp_event\s+(\d+),\s*(\d+),\s+(\w+),\s+(\d+)')


def _asm_const_to_stem(const: str) -> str:
    """Convert SCREAMING_SNAKE_CASE ASM constant to CamelCase file stem.

    MT_MOON_B1F → MtMoonB1F
    WHIRL_ISLAND_NW → WhirlIslandNW
    """
    parts = const.split("_")
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if p in _KEEP_UPPER:
            out.append(p)
        elif p[0].isdigit():
            out.append(p)  # plain digit prefix (should be in _KEEP_UPPER but defensive)
        else:
            out.append(p.capitalize())
    return "".join(out)


# ── HTTP + cache ───────────────────────────────────────────────────────────────

async def _fetch_text(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    cache_dir: Path,
) -> str | None:
    key = hashlib.sha1(url.encode()).hexdigest()
    cp = cache_dir / f"pret_{key}.txt"
    if cp.exists():
        content = cp.read_text()
        return content if content else None  # empty file = cached 404
    async with sem:
        try:
            async with session.get(url) as r:
                if r.status == 404:
                    cp.write_text("")   # cache the miss
                    return None
                r.raise_for_status()
                text = await r.text()
                cp.write_text(text)
                return text
        except Exception as exc:
            print(f"    [pret] {url} → {exc}")
            return None


async def _fetch_json(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    url: str,
    cache_dir: Path,
) -> dict | None:
    text = await _fetch_text(session, sem, url, cache_dir)
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


# ── Per-format fetchers ────────────────────────────────────────────────────────
# Each returns {pret_id: [raw_warp_dict, ...]} where raw_warp_dict has:
#   src_x, src_y    — source tile position
#   dest_id         — destination identifier (const/dir name/header) in this repo's format
#   dest_warp_idx   — destination warp index in the dest map's warp list


async def _fetch_gen1_asm(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    repo: str,
    pret_ids: list[str],
    cache_dir: Path,
) -> dict[str, list[dict]]:
    """pokered-style ASM from data/maps/objects/."""
    results: dict[str, list[dict]] = {}
    for pid in pret_ids:
        stem = _asm_const_to_stem(pid)
        url = f"{GITHUB_RAW}/{repo}/master/data/maps/objects/{stem}.asm"
        text = await _fetch_text(session, sem, url, cache_dir)
        if not text:
            print(f"    [pret] {repo} miss: {stem}.asm")
            continue
        warps = [
            {"src_x": int(m[1]), "src_y": int(m[2]), "dest_id": m[3], "dest_warp_idx": int(m[4])}
            for m in _WARP_RE.finditer(text)
        ]
        results[pid] = warps
    return results


async def _fetch_gen2_asm(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    repo: str,
    pret_ids: list[str],
    cache_dir: Path,
) -> dict[str, list[dict]]:
    """pokecrystal-style ASM from maps/."""
    results: dict[str, list[dict]] = {}
    for pid in pret_ids:
        stem = _asm_const_to_stem(pid)
        url = f"{GITHUB_RAW}/{repo}/master/maps/{stem}.asm"
        text = await _fetch_text(session, sem, url, cache_dir)
        if not text:
            print(f"    [pret] {repo} miss: {stem}.asm")
            continue
        warps = [
            {"src_x": int(m[1]), "src_y": int(m[2]), "dest_id": m[3], "dest_warp_idx": int(m[4])}
            for m in _WARP_RE.finditer(text)
        ]
        results[pid] = warps
    return results


async def _fetch_gen3_json(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    repo: str,
    pret_ids: list[str],
    cache_dir: Path,
) -> tuple[dict[str, list[dict]], dict[str, str]]:
    """pokeemerald/pokefirered JSON from data/maps/{dir}/map.json.

    Returns (raw_warps, map_const_to_pret_id) where the second dict maps
    the JSON id field (e.g. MAP_GRANITE_CAVE_B1F) to the pret_id directory name.
    """
    raw_warps: dict[str, list[dict]] = {}
    const_to_pid: dict[str, str] = {}
    for pid in pret_ids:
        url = f"{GITHUB_RAW}/{repo}/master/data/maps/{pid}/map.json"
        data = await _fetch_json(session, sem, url, cache_dir)
        if not data:
            print(f"    [pret] {repo} miss: {pid}/map.json")
            continue
        if c := data.get("id"):
            const_to_pid[c] = pid
        warps = [
            {
                "src_x": w["x"], "src_y": w["y"],
                "dest_id": w["dest_map"],
                "dest_warp_idx": int(w["dest_warp_id"]),
            }
            for w in data.get("warp_events", [])
        ]
        raw_warps[pid] = warps
    return raw_warps, const_to_pid


async def _load_hgss_maps_h(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    cache_dir: Path,
) -> dict[str, tuple[int, str]]:
    """Parse pokeheartgold maps.h → {MAP_CONST: (numeric_value, internal_code)}."""
    url = f"{GITHUB_RAW}/pokeheartgold/master/include/constants/maps.h"
    text = await _fetch_text(session, sem, url, cache_dir)
    if not text:
        return {}
    result: dict[str, tuple[int, str]] = {}
    for m in re.finditer(r'#define\s+(MAP_\w+)\s+(\d+)\s*//\s*MAP_(\w+)', text):
        result[m.group(1)] = (int(m.group(2)), m.group(3))
    return result


async def _fetch_hgss_zone(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    const_value: int,
    internal_code: str,
    cache_dir: Path,
) -> dict | None:
    """Scan a range of file indices to find the HGSS zone file for a given map."""
    # The file index ≠ const_value. HGSS zone files are numbered by game-internal order.
    # Johto 1F maps: offset ≈ -3 to -7. Deeper Johto floors: ≈ -14. Kanto dungeons: ≈ -45.
    # Use a wide range and rely on caching (all 404s are stored as empty files).
    tasks = []
    indices = []
    for offset in range(-50, 5):
        idx = const_value + offset
        if idx < 0:
            continue
        url = f"{GITHUB_RAW}/pokeheartgold/master/files/fielddata/eventdata/zone_event/{idx:03d}_{internal_code}.json"
        tasks.append(_fetch_json(session, sem, url, cache_dir))
        indices.append(idx)
    if not tasks:
        return None
    results = await asyncio.gather(*tasks)
    for data in results:
        if data is not None:
            return data
    return None


async def _fetch_gen4_hgss(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    pret_ids: list[str],
    maps_h: dict[str, tuple[int, str]],
    cache_dir: Path,
) -> dict[str, list[dict]]:
    """pokeheartgold zone JSON. pret_id = MAP_ constant from maps.h."""
    raw_warps: dict[str, list[dict]] = {}
    for pid in pret_ids:
        if pid not in maps_h:
            print(f"    [pret] pokeheartgold: {pid} not in maps.h")
            continue
        const_value, internal_code = maps_h[pid]
        data = await _fetch_hgss_zone(session, sem, const_value, internal_code, cache_dir)
        if not data:
            print(f"    [pret] pokeheartgold miss: {pid} ({internal_code})")
            continue
        warps = [
            {
                "src_x": w["x"], "src_y": w["z"],   # z = tile y in Gen 4
                "dest_id": w["header"],               # "MAP_ICE_PATH_B1F"
                "dest_warp_idx": w["anchor"],         # 0-based
            }
            for w in data.get("warps", [])
        ]
        raw_warps[pid] = warps
    return raw_warps


async def _fetch_gen4_pt_single(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    repo: str,
    stem: str,
    cache_dir: Path,
) -> list[dict]:
    url = f"{GITHUB_RAW}/{repo}/master/res/field/events/events_{stem}.json"
    data = await _fetch_json(session, sem, url, cache_dir)
    if not data:
        print(f"    [pret] {repo} miss: events_{stem}.json")
        return []
    return [
        {
            "src_x": w["x"], "src_y": w["z"],
            "dest_id": w["dest_header_id"],   # "MAP_HEADER_IRON_ISLAND_1F"
            "dest_warp_idx": w["dest_warp_id"],
        }
        for w in data.get("warp_events", [])
    ]


async def _fetch_gen4_pt(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    repo: str,
    pret_ids: list[_PretId],
    cache_dir: Path,
) -> dict[str, list[dict]]:
    """pokeplatinum events JSON from res/field/events/events_{stem}.json."""
    raw_warps: dict[str, list[dict]] = {}
    for pid in pret_ids:
        stems = pid if isinstance(pid, list) else [pid]
        all_warps: list[dict] = []
        for stem in stems:
            all_warps.extend(await _fetch_gen4_pt_single(session, sem, repo, stem, cache_dir))
        raw_warps[pid if isinstance(pid, str) else pid[0]] = all_warps
    return raw_warps


# ── Warp resolution ────────────────────────────────────────────────────────────

def _resolve_warps(
    floor_id_to_pret_id: dict[str, _PretId],
    raw_warps: dict[str, list[dict]],
    dest_id_to_floor_id: dict[str, str],
    one_based: bool,
) -> dict[str, list[dict]]:
    """Convert raw warp records to our output format.

    For each floor, looks up the destination floor_id and the destination
    tile coordinates by reading that floor's warp list at dest_warp_idx.

    one_based: True for Gen 1/2 ASM (warp_event indices are 1-based);
               False for Gen 3/4 JSON (0-based).
    """
    result: dict[str, list[dict]] = {}

    for floor_id, pret_id in floor_id_to_pret_id.items():
        # The canonical key in raw_warps for this floor
        key = pret_id[0] if isinstance(pret_id, list) else pret_id
        src_warps = raw_warps.get(key, [])
        out: list[dict] = []

        for w in src_warps:
            dest_floor_id = dest_id_to_floor_id.get(w["dest_id"])
            if not dest_floor_id:
                continue  # exit to outdoor; skip

            # Find dest coordinates from the dest floor's warp list
            dest_pret_id = floor_id_to_pret_id.get(dest_floor_id)
            if dest_pret_id is None:
                continue
            dest_key = dest_pret_id[0] if isinstance(dest_pret_id, list) else dest_pret_id
            dest_warps = raw_warps.get(dest_key, [])

            idx = w["dest_warp_idx"]
            if one_based:
                idx -= 1   # Gen 1/2: warp_event arg is 1-based
            dest_x, dest_y = 0, 0
            if 0 <= idx < len(dest_warps):
                dest_x = dest_warps[idx]["src_x"]
                dest_y = dest_warps[idx]["src_y"]

            out.append({
                "x":            w["src_x"],
                "y":            w["src_y"],
                "dest_floor_id": dest_floor_id,
                "dest_x":       dest_x,
                "dest_y":       dest_y,
            })

        if out:
            result[floor_id] = out

    return result


# ── Main entry point ───────────────────────────────────────────────────────────

async def scrape_pret_warps(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    version: str,
    cave_map_locs: list[dict],
    cache_dir: Path,
) -> dict[str, list[dict]]:
    """Return {floor_id: [warp_dict]} for all floors that have pret warp data.

    Warps whose destination is not in our floor set (exits to outdoor routes)
    are silently dropped.
    """
    config = _PRET_CONFIG.get(version)
    if not config:
        return {}
    repo, fmt = config

    # Collect floors that have pret mappings for this repo
    floor_id_to_pret_id: dict[str, _PretId] = {}
    for loc in cave_map_locs:
        for floor in loc["floors"]:
            pid = _PRET_MAPS.get(floor["id"], {}).get(repo)
            if pid:
                floor_id_to_pret_id[floor["id"]] = pid

    if not floor_id_to_pret_id:
        return {}

    print(f"  [pret] {repo} ({fmt}): {len(floor_id_to_pret_id)} floors")

    # Flatten pret_ids for fetching
    all_pret_ids: list[_PretId] = list(floor_id_to_pret_id.values())
    flat_ids: list[str] = []
    for pid in all_pret_ids:
        if isinstance(pid, list):
            flat_ids.extend(pid)
        else:
            flat_ids.append(pid)

    # ── Fetch raw warp data ────────────────────────────────────────────────────

    one_based = False
    raw_warps: dict[str, list[dict]] = {}
    dest_id_to_floor_id: dict[str, str] = {}   # pret dest identifier → our floor_id

    if fmt == "gen1_asm":
        one_based = True
        raw_warps = await _fetch_gen1_asm(session, sem, repo, flat_ids, cache_dir)
        for floor_id, pid in floor_id_to_pret_id.items():
            for p in ([pid] if isinstance(pid, str) else pid):
                dest_id_to_floor_id[p] = floor_id

    elif fmt == "gen2_asm":
        one_based = True
        raw_warps = await _fetch_gen2_asm(session, sem, repo, flat_ids, cache_dir)
        for floor_id, pid in floor_id_to_pret_id.items():
            for p in ([pid] if isinstance(pid, str) else pid):
                dest_id_to_floor_id[p] = floor_id

    elif fmt == "gen3_json":
        raw_warps, const_to_pid = await _fetch_gen3_json(session, sem, repo, flat_ids, cache_dir)
        # dest_id in raw warps is "MAP_GRANITE_CAVE_B1F"; resolve via const_to_pid → pret_id → floor_id
        pid_to_floor_id = {pid: fid for fid, pid in floor_id_to_pret_id.items()
                           if isinstance(pid, str)}
        for c, pid in const_to_pid.items():
            if pid in pid_to_floor_id:
                dest_id_to_floor_id[c] = pid_to_floor_id[pid]

    elif fmt == "gen4_hgss":
        maps_h = await _load_hgss_maps_h(session, sem, cache_dir)
        raw_warps = await _fetch_gen4_hgss(session, sem, flat_ids, maps_h, cache_dir)
        for floor_id, pid in floor_id_to_pret_id.items():
            if isinstance(pid, str):
                dest_id_to_floor_id[pid] = floor_id   # MAP_ const matches warp header

    elif fmt == "gen4_pt":
        raw_warps = await _fetch_gen4_pt(session, sem, repo, all_pret_ids, cache_dir)
        # dest_id = "MAP_HEADER_IRON_ISLAND_1F" → strip prefix + lowercase → "iron_island_1f"
        stem_to_floor_id: dict[str, str] = {}
        for floor_id, pid in floor_id_to_pret_id.items():
            stems = pid if isinstance(pid, list) else [pid]
            for s in stems:
                stem_to_floor_id[s] = floor_id
        for dest_header in {
            w["dest_id"]
            for warps in raw_warps.values()
            for w in warps
        }:
            stem = dest_header.removeprefix("MAP_HEADER_").lower()
            if stem in stem_to_floor_id:
                dest_id_to_floor_id[dest_header] = stem_to_floor_id[stem]

    # ── Resolve dest coordinates ───────────────────────────────────────────────

    return _resolve_warps(floor_id_to_pret_id, raw_warps, dest_id_to_floor_id, one_based)
