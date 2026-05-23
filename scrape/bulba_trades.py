"""
Scrape in-game trades from Bulbapedia's In-game_trade article.

Uses the MediaWiki parse API to fetch the rendered HTML for the section
corresponding to the current game's version group, then parses trade tables
with BeautifulSoup.

Location cells in the tables contain <a href="/wiki/Location_Name"> links.
The slug is extracted from the href, lowercased and underscores replaced
with hyphens, giving a route ID that matches ROUTE_ORDER entries.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from bs4 import BeautifulSoup, Tag

if TYPE_CHECKING:
    import aiohttp

BULBA_API  = "https://bulbapedia.bulbagarden.net/w/api.php"
POKEAPI    = "https://pokeapi.co/api/v2"

# ── Version → section title substring ─────────────────────────────────────────
# Matched case-insensitively against the "line" field of each MediaWiki section.

_SECTION_HINT: dict[str, str] = {
    # Actual Bulbapedia section titles (matched as case-insensitive substrings):
    #   "Pokémon Red and Green (Japan), Pokémon Red and Blue (Western)"
    #   "Pokémon Yellow"
    #   "Pokémon Gold, Silver, and Crystal"      ← no separate Crystal section
    #   "Pokémon Ruby and Sapphire"
    #   "Pokémon Emerald"
    #   "Pokémon FireRed and LeafGreen"
    #   "Pokémon Diamond, Pearl, and Platinum"
    #   "Pokémon HeartGold and SoulSilver"
    #   "Pokémon Black and White"
    #   "Pokémon Black 2 and White 2"
    #   "Pokémon X and Y"
    #   "Pokémon Omega Ruby and Alpha Sapphire"
    #   "Pokémon Sun and Moon"
    #   "Pokémon Ultra Sun and Ultra Moon"
    "red":            "Red and Blue (Western)",
    "blue":           "Red and Blue (Western)",
    "yellow":         "Pokémon Yellow",
    "gold":           "Gold, Silver",
    "silver":         "Gold, Silver",
    "crystal":        "Gold, Silver",
    "ruby":           "Ruby and Sapphire",
    "sapphire":       "Ruby and Sapphire",
    "emerald":        "Pokémon Emerald",
    "firered":        "FireRed and LeafGreen",
    "leafgreen":      "FireRed and LeafGreen",
    "diamond":        "Diamond, Pearl",
    "pearl":          "Diamond, Pearl",
    "platinum":       "Diamond, Pearl",
    "heartgold":      "HeartGold and SoulSilver",
    "soulsilver":     "HeartGold and SoulSilver",
    "black":          "Black and White",
    "white":          "Black and White",
    "black-2":        "Black 2 and White 2",
    "white-2":        "Black 2 and White 2",
    "x":              "X and Y",
    "y":              "X and Y",
    "omega-ruby":     "Omega Ruby and Alpha Sapphire",
    "alpha-sapphire": "Omega Ruby and Alpha Sapphire",
    "sun":            "Sun and Moon",
    "moon":           "Sun and Moon",
    "ultra-sun":      "Ultra Sun and Ultra Moon",
    "ultra-moon":     "Ultra Sun and Ultra Moon",
}

# Bulbapedia version abbreviations used as <img alt="..."> in the Games column.
_VERSION_ICON: dict[str, str] = {
    "red": "R", "blue": "B", "yellow": "Y",
    "gold": "G", "silver": "S", "crystal": "C",
    "ruby": "Ru", "sapphire": "Sa", "emerald": "E",
    "firered": "FR", "leafgreen": "LG",
    "diamond": "D", "pearl": "P", "platinum": "Pt",
    "heartgold": "HG", "soulsilver": "SS",
    "black": "Bl", "white": "W",
    "black-2": "B2", "white-2": "W2",
    "x": "X", "y": "Y",
    "omega-ruby": "OR", "alpha-sapphire": "AS",
    "sun": "Su", "moon": "Mo",
    "ultra-sun": "US", "ultra-moon": "UM",
}

# Pokémon display name → PokeAPI slug for names that don't normalize cleanly.
_POKE_OVERRIDES: dict[str, str] = {
    "nidoran♂":           "nidoran-m",
    "nidoran♀":           "nidoran-f",
    "nidoran-m":          "nidoran-m",
    "nidoran-f":          "nidoran-f",
    "mr. mime":           "mr-mime",
    "mime jr.":           "mime-jr",
    "farfetch'd":         "farfetchd",
    "flabébé":            "flabebe",
    "type: null":         "type-null",
    "jangmo-o":           "jangmo-o",
    "hakamo-o":           "hakamo-o",
    "kommo-o":            "kommo-o",
    "tapu koko":          "tapu-koko",
    "tapu lele":          "tapu-lele",
    "tapu bulu":          "tapu-bulu",
    "tapu fini":          "tapu-fini",
    "porygon-z":          "porygon-z",
    "ho-oh":              "ho-oh",
    "will-o-wisp":        "will-o-wisp",
    # Basculin — PokeAPI requires the form suffix
    "red-striped-basculin":  "basculin-red-striped",
    "blue-striped-basculin": "basculin-blue-striped",
    "basculin":              "basculin-red-striped",   # default form
    # Alolan forms in trade tables → PokeAPI slugs
    "alolan-golem":       "golem-alola",
    "alolan-graveler":    "graveler-alola",
    "alolan-raichu":      "raichu-alola",
    "golem":              "golem",        # plain "Golem" in SM trade = Alolan context but same ID
}


# ── Name / slug helpers ────────────────────────────────────────────────────────

def _poke_slug(name: str) -> str:
    """Convert a Pokémon display name to a PokeAPI slug."""
    name = name.lower().strip()
    # ♂/♀ is species-defining for Nidoran; for everything else it marks the
    # received Pokémon's gender and should be stripped before slugifying.
    if not name.startswith("nidoran"):
        name = re.sub(r"\s*[♂♀]", "", name).strip()
    slug = (name
            .replace("♂", "-m").replace("♀", "-f")
            .replace(" ", "-").replace(".", "").replace("'", "").replace(":", ""))
    slug = re.sub(r"-+", "-", slug).strip("-")
    return _POKE_OVERRIDES.get(slug, slug)


def _location_slug(href: str) -> str:
    """Convert a /wiki/Location_Name href to a route-id slug."""
    slug = unquote(href.split("/wiki/")[-1])
    slug = re.sub(r"_\([^)]+\)$", "", slug)   # strip disambiguation
    slug = slug.lower().replace("_", "-").replace("'", "")
    slug = re.sub(r"-+", "-", slug).strip("-").rstrip(".")
    return slug


# Region-prefixed route names (e.g. "unova-route-7") → bare "route-7"
_REGION_ROUTE_RE = re.compile(
    r"^(?:kanto|johto|hoenn|sinnoh|unova|kalos|alola|galar)-route-(\d+)$"
)

_LOCATION_FIXUPS: dict[str, str] = {
    "kanto-power-plant":          "power-plant",
    "goldenrod-department-store": "goldenrod-city",
    "hotel-richissime":           "lumiose-city",
    "kalos-hotels":               "lumiose-city",
}


def _normalize_location(slug: str) -> str:
    """Map scraper-derived slugs to the IDs used in ROUTE_ORDER."""
    if slug in _LOCATION_FIXUPS:
        return _LOCATION_FIXUPS[slug]
    m = _REGION_ROUTE_RE.match(slug)
    if m:
        return f"route-{m.group(1)}"
    return slug


# ── HTTP + caching ─────────────────────────────────────────────────────────────

def _cache_key(tag: str, params: dict) -> str:
    raw = tag + json.dumps(params, sort_keys=True)
    return "trades_" + hashlib.sha1(raw.encode()).hexdigest()


async def _api_json(
    session: "aiohttp.ClientSession",
    sem: asyncio.Semaphore,
    cache_dir: Path,
    params: dict,
) -> dict | None:
    cp = cache_dir / (_cache_key("api", params) + ".json")
    if cp.exists():
        return json.loads(cp.read_text())
    async with sem:
        for attempt in range(3):
            try:
                async with session.get(BULBA_API, params=params) as r:
                    r.raise_for_status()
                    data = await r.json(content_type=None)
                    cp.write_text(json.dumps(data))
                    return data
            except Exception as exc:
                if attempt == 2:
                    print(f"  [trades] API error: {exc}")
                    return None
                await asyncio.sleep(2 ** attempt)
    return None


async def _lookup_pokemon_id(
    session: "aiohttp.ClientSession",
    sem: asyncio.Semaphore,
    cache_dir: Path,
    slug: str,
) -> int | None:
    url = f"{POKEAPI}/pokemon/{slug}"
    cp = cache_dir / (_cache_key("poke", {"url": url}) + ".json")
    if cp.exists():
        data = json.loads(cp.read_text())
        return data.get("id")
    async with sem:
        for attempt in range(3):
            try:
                async with session.get(url) as r:
                    if r.status == 404:
                        cp.write_text(json.dumps({"id": None}))
                        return None
                    r.raise_for_status()
                    data = await r.json(content_type=None)
                    cp.write_text(json.dumps({"id": data["id"]}))
                    return data["id"]
            except Exception as exc:
                if attempt == 2:
                    print(f"  [trades] PokeAPI miss '{slug}': {exc}")
                    return None
                await asyncio.sleep(2 ** attempt)
    return None


# ── Bulbapedia section lookup ─────────────────────────────────────────────────

async def _fetch_section_index(
    session: "aiohttp.ClientSession",
    sem: asyncio.Semaphore,
    cache_dir: Path,
    hint: str,
) -> str | None:
    data = await _api_json(session, sem, cache_dir, {
        "action": "parse",
        "page":   "In-game_trade",
        "prop":   "sections",
        "format": "json",
    })
    if not data:
        return None
    for sec in data.get("parse", {}).get("sections", []):
        if hint.lower() in sec.get("line", "").lower():
            return sec["index"]
    return None


async def _fetch_section_html(
    session: "aiohttp.ClientSession",
    sem: asyncio.Semaphore,
    cache_dir: Path,
    section_idx: str,
) -> str | None:
    data = await _api_json(session, sem, cache_dir, {
        "action":  "parse",
        "page":    "In-game_trade",
        "prop":    "text",
        "section": section_idx,
        "format":  "json",
    })
    return data.get("parse", {}).get("text", {}).get("*") if data else None


# ── Table parsing ──────────────────────────────────────────────────────────────
#
# All generations use the same roundtable structure:
#   col 0 : Location
#   col 1 : Give Pokémon sprite (image only)
#   col 2 : Give Pokémon name  ← always col 2
#   col 3 : Recv Pokémon sprite (image only)
#   col 4 : Recv Pokémon name  ← always col 4, may have ♂/♀ suffix
#   col 5 : English nickname
#   col 6 : Japanese nickname
#   col 7 : Level (Gen 5+) OR Held-item sprite (Gen 1–4, no Level column)
#   ...
#   col 12 : EN Original Trainer name (Gen 1–4, no Level column)
#   col 13 : EN Original Trainer name (Gen 5+, Level column shifts everything +1)
#
# Whether "Level" is present is detected from the first header row.


def _has_level_column(table: Tag) -> bool:
    """Return True if this table's header includes a standalone 'Level' column."""
    for row in table.find_all("tr")[:3]:
        for th in row.find_all("th"):
            text = th.get_text(strip=True).lower()
            if text == "level" or text.startswith("lv"):
                return True
    return False


def _poke_name(cell: Tag) -> str | None:
    """Extract Pokémon name from a name cell; None if 'any Pokémon'."""
    text = cell.get_text(" ", strip=True)
    if not text or re.search(r"\bany\b", text, re.I):
        return None
    # Cell may show an evolution chain (e.g. "Haunter → Alolan Golem") — use result only
    if "→" in text:
        text = text.split("→", 1)[1]
    # Strip bracket/parenthetical annotations: [A], [-a-], (foreign), (Alola Form), etc.
    text = re.sub(r"\s*[\[\(][^\]\)]*[\]\)]\s*", "", text)
    # Strip footnote markers (keep ♂/♀ — _poke_slug converts them to -m/-f)
    text = re.sub(r"\s*[†‡*]\s*", "", text).strip()
    return text or None


def _location_from_cell(cell: Tag) -> str | None:
    for a in cell.find_all("a"):
        href = a.get("href", "")
        if "/wiki/" in href and "File:" not in href:
            return _normalize_location(_location_slug(href))
    text = cell.get_text(strip=True)
    text = re.sub(r"[†‡*].*$", "", text).strip()  # strip footnote markers
    if text:
        slug = re.sub(r"-+", "-",
               text.lower().replace(" ", "-").replace("'", "").replace(".", "")).strip("-")
        return _normalize_location(slug)
    return None


def _npc_name(cell: Tag) -> str:
    text = cell.get_text(" ", strip=True)
    # Strip gender symbol and footnote markers
    return re.sub(r"\s*[♂♀†‡*]\s*", "", text).strip()


def _parse_trades_from_html(html: str, version: str) -> list[dict]:
    """Parse trade rows from a section's rendered HTML.

    Relies on the fixed column layout of Bulbapedia's roundtable format:
      col 0=location, 2=give name, 4=recv name, 7=level (Gen5+) or held-sprite (Gen1-4),
      12=OT EN name (no level col) or 13=OT EN name (with level col).
    """
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict] = []

    for table in soup.find_all("table", class_=lambda c: c and "roundtable" in (c or [])):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        level_col = 7 if _has_level_column(table) else None
        npc_col   = 13 if level_col else 12

        current_location: str | None = None

        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells or all(c.name == "th" for c in cells):
                continue
            if len(cells) < 5:
                continue

            # Location (col 0) — update running value to handle rowspans
            loc = _location_from_cell(cells[0])
            if loc:
                current_location = loc
            if not current_location:
                continue

            give_name = _poke_name(cells[2]) if len(cells) > 2 else None
            recv_name = _poke_name(cells[4]) if len(cells) > 4 else None
            if not give_name or not recv_name:
                continue

            level: int | None = None
            if level_col and len(cells) > level_col:
                m = re.search(r"\b(\d+)\b", cells[level_col].get_text())
                if m:
                    level = int(m.group(1))

            npc = _npc_name(cells[npc_col]) if len(cells) > npc_col else ""

            results.append({
                "give_pokemon":    _poke_slug(give_name),
                "receive_pokemon": _poke_slug(recv_name),
                "receive_level":   level,
                "npc":             npc,
                "location":        current_location,
            })

    return results


# ── Public entry point ────────────────────────────────────────────────────────

async def scrape_ingame_trades(
    session: "aiohttp.ClientSession",
    sem: asyncio.Semaphore,
    version: str,
    cache_dir: Path,
) -> list[dict]:
    """Return in-game trades for *version* scraped from Bulbapedia.

    Each entry matches the GAME_STATIC in_game_trades format:
        give_pokemon / give_pokemon_id
        receive_pokemon / receive_pokemon_id
        receive_level   (int or None when the game matches the traded Pokémon's level)
        npc             (OT name on the received Pokémon)
        location        (route-id slug)
    """
    hint = _SECTION_HINT.get(version)
    if not hint:
        return []

    section_idx = await _fetch_section_index(session, sem, cache_dir, hint)
    if not section_idx:
        print(f"  [trades] no Bulbapedia section found for '{version}' (hint={hint!r})")
        return []

    html = await _fetch_section_html(session, sem, cache_dir, section_idx)
    if not html:
        print(f"  [trades] no HTML for section {section_idx} (version={version})")
        return []

    raw = _parse_trades_from_html(html, version)
    if not raw:
        print(f"  [trades] no trades parsed for '{version}'")
        return []

    # Resolve Pokémon IDs in parallel.
    all_slugs = sorted({t["give_pokemon"] for t in raw} | {t["receive_pokemon"] for t in raw})
    ids = await asyncio.gather(*[
        _lookup_pokemon_id(session, sem, cache_dir, slug)
        for slug in all_slugs
    ])
    slug_to_id: dict[str, int] = {
        slug: pid for slug, pid in zip(all_slugs, ids) if pid
    }

    trades: list[dict] = []
    for t in raw:
        give_id = slug_to_id.get(t["give_pokemon"])
        recv_id = slug_to_id.get(t["receive_pokemon"])
        if not give_id:
            print(f"  [trades] unknown give Pokémon slug '{t['give_pokemon']}' — skipping")
            continue
        if not recv_id:
            print(f"  [trades] unknown recv Pokémon slug '{t['receive_pokemon']}' — skipping")
            continue
        trades.append({
            "give_pokemon":       t["give_pokemon"],
            "give_pokemon_id":    give_id,
            "receive_pokemon":    t["receive_pokemon"],
            "receive_pokemon_id": recv_id,
            "receive_level":      t["receive_level"],
            "npc":                t["npc"],
            "location":           t["location"],
        })

    print(f"  [trades] {len(trades)} trades for '{version}'")
    return trades
