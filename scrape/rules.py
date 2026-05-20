#!/usr/bin/env python3
"""
Fetch Nuzlocke optional rules from nuzlockeuniversity.ca and write NuzlockeRule.swift.
Re-run whenever the source page is updated to refresh descriptions.

Usage:
    python3 scrape/rules.py
"""

import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

URL = "https://nuzlockeuniversity.ca/optional-rules/"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "Nuzlocker" / "Core" / "Models" / "Run" / "NuzlockeRule.swift"

# ── Rule catalogue ─────────────────────────────────────────────────────────────
# Each entry is (swiftCaseID, displayName), in the same order as the source page.
# Case IDs are stable compile-time identifiers used for behavior matching.
# Descriptions are fetched from the URL.

HARDER_RULES = [
    ("singlePokemonCenterUse",  "Single Pokémon Center Use"),
    ("noPokemonCenters",        "No Pokémon Centers"),
    ("levelCaps",               "Level Caps"),
    ("teamSizeLimit",           "Team Size Limit"),
    ("gymLockIn",               "Gym Lock-In"),
    ("completionistClause",     "Completionist Clause"),
    ("setBattleMode",           "Set Battle Mode"),
    ("noHealingItems",          "No Healing Items"),
    ("oneItemPerBattle",        "One Item Per Battle"),
    ("foundItemsOnly",          "Found Items Only"),
    ("noBacktracking",          "No Backtracking"),
    ("banSpecificPokemon",      "Ban Specific Pokémon"),
    ("tierBans",                "Tier Bans"),
    ("noStarter",               "No Starter"),
    ("noGiftPokemon",           "No Gift Pokémon"),
    ("noSetupMoves",            "No Setup Moves"),
    ("levelUpMovesOnly",        "Level-Up Moves Only"),
    ("blindRun",                "Blind Run"),
    ("noDamageCalculators",     "No Damage Calculators"),
    ("noHeldItems",             "No Held Items"),
    ("basePowerLimit",          "Base Power Limit"),
    ("noSTABMoves",             "No STAB Moves"),
    ("stabOnly",                "STAB Only"),
    ("noSuperEffectiveMoves",   "No Super-Effective Moves"),
    ("singleStagePokemonOnly",  "Single-Stage Pokémon Only"),
    ("typeBan",                 "Type Ban"),
    ("monolocke",               "Monolocke"),
    ("noDualTypes",             "No Dual-Types"),
    ("dualTypesOnly",           "Dual-Types Only"),
    ("typeDiversity",           "Type Diversity"),
    ("noBoxedPokemon",          "No Boxed Pokémon"),
    ("sequentialRoster",        "Sequential Roster"),
    ("deathlessRun",            "Deathless Run"),
]

EASIER_RULES = [
    ("reviveAllowance",         "Revive Allowance"),
    ("sacrificeRevives",        "Sacrifice Revives"),
    ("giftClause",              "Gift Clause"),
    ("hmSlaveException",        "HM Slave Exception"),
    ("starterLockIn",           "Starter Lock-In"),
    ("eggMovesAccess",          "Egg Moves Access"),
    ("ivNatureModification",    "IV/Nature Modification"),
    ("unlimitedTMs",            "Unlimited TMs"),
    ("unlimitedMasterBalls",    "Unlimited Master Balls"),
    ("escapeReroll",            "Escape Reroll"),
    ("higherLevelCap",          "Higher Level Cap"),
    ("boxSubstitute",           "Box Substitute"),
]

VARIETY_RULES = [
    ("dupesClause",                 "Duplicates Clause"),
    ("shinyClause",                 "Shiny Clause"),
    ("colorTheme",                  "Color Theme"),
    ("customThematicTeam",          "Custom Thematic Team"),
    ("generationRestriction",       "Generation Restriction"),
    ("raidDenEncounters",           "Raid Den Encounters"),
    ("trainerIDStarterRandomizer",  "Trainer ID Starter Randomizer"),
]


# ── Fetch and parse ────────────────────────────────────────────────────────────

def fetch_descriptions() -> tuple[list[str], list[str], list[str]]:
    print(f"Fetching {URL} …")
    req = urllib.request.Request(URL, headers={"User-Agent": "NuzlockerApp/1.0 DataScraper"})
    with urllib.request.urlopen(req) as r:
        soup = BeautifulSoup(r.read(), "html.parser")

    content = soup.find("div", class_="entry-content")
    if not content:
        sys.exit("Could not find entry-content div — page structure may have changed.")

    sections: list[list[str]] = []
    current: list[str] = []

    for el in content.children:
        if not hasattr(el, "name") or not el.name:
            continue
        if el.name == "h3" and el.get("class") == ["wp-block-heading"]:
            if current:
                sections.append(current)
            current = []
        elif el.name == "ol":
            for li in el.find_all("li", recursive=False):
                current.append(_clean(li))

    if current:
        sections.append(current)

    if len(sections) != 3:
        sys.exit(f"Expected 3 sections (harder/easier/variety), found {len(sections)}. "
                 "The page structure may have changed.")

    return sections[0], sections[1], sections[2]


def _clean(li) -> str:
    # Drop anchor elements whose text is navigation noise ("click here", etc.)
    for a in li.find_all("a"):
        text = a.get_text(strip=True)
        if re.search(r"click here", text, re.IGNORECASE):
            a.decompose()
        else:
            a.replace_with(text)

    text = li.get_text(separator=" ", strip=True)
    # Remove trailing "– click here …" fragments that survive the above
    text = re.sub(r"\s*[–—-]\s*click here[^.]*", "", text, flags=re.IGNORECASE)
    # Collapse whitespace
    text = " ".join(text.split())
    # Ensure sentence ends with punctuation
    if text and text[-1] not in ".!?":
        text += "."
    return text


# ── Swift generation ───────────────────────────────────────────────────────────

def _swift_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def generate(harder: list[str], easier: list[str], variety: list[str]) -> str:
    def _validate(label: str, catalogue: list, descriptions: list[str]) -> list[tuple[str, str, str]]:
        if len(catalogue) != len(descriptions):
            print(f"  [warn] {label}: catalogue has {len(catalogue)} entries "
                  f"but page has {len(descriptions)} — "
                  "some descriptions will be missing or misaligned.", file=sys.stderr)
        entries = []
        for i, (case_id, display_name) in enumerate(catalogue):
            desc = descriptions[i] if i < len(descriptions) else "(description unavailable)"
            entries.append((case_id, display_name, desc))
        return entries

    harder_entries  = _validate("harder",  HARDER_RULES,  harder)
    easier_entries  = _validate("easier",  EASIER_RULES,  easier)
    variety_entries = _validate("variety", VARIETY_RULES, variety)

    all_entries = harder_entries + easier_entries + variety_entries

    def cases_block(entries):
        return "\n".join(f"    case {e[0]}" for e in entries)

    def switch_block(entries, expr):
        return "\n".join(f"        case .{e[0]}: return {expr(e)}" for e in entries)

    harder_cases  = cases_block(harder_entries)
    easier_cases  = cases_block(easier_entries)
    variety_cases = cases_block(variety_entries)

    category_switch = (
        switch_block(harder_entries,  lambda _: ".harder") + "\n" +
        switch_block(easier_entries,  lambda _: ".easier") + "\n" +
        switch_block(variety_entries, lambda _: ".variety")
    )
    display_switch = switch_block(
        all_entries, lambda e: f'"{_swift_string(e[1])}"'
    )
    desc_switch = switch_block(
        all_entries, lambda e: f'"{_swift_string(e[2])}"'
    )

    return f"""\
// Generated by scrape/rules.py — do not edit by hand.
// Source: {URL}
import Foundation

enum NuzlockeRule: String, Codable, CaseIterable, Identifiable {{
    var id: String {{ rawValue }}

    // MARK: - Harder

{harder_cases}

    // MARK: - Easier

{easier_cases}

    // MARK: - Variety

{variety_cases}

    // MARK: - Metadata

    enum Category {{
        case harder, easier, variety
    }}

    var category: Category {{
        switch self {{
{category_switch}
        }}
    }}

    var displayName: String {{
        switch self {{
{display_switch}
        }}
    }}

    var description: String {{
        switch self {{
{desc_switch}
        }}
    }}
}}
"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    harder, easier, variety = fetch_descriptions()
    print(f"  Harder : {len(harder)} rules")
    print(f"  Easier : {len(easier)} rules")
    print(f"  Variety: {len(variety)} rules")

    swift = generate(harder, easier, variety)
    OUTPUT.write_text(swift)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
