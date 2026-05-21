#!/usr/bin/env python3
"""
Generate a CDN-format manifest from scrape/output/manifest.json for local dev.

Reads the scraper's intermediate manifest, computes SHA-256 and byte size for
each ZIP in scrape/output/, groups variants into games, and writes the result
to scrape/output/cdn-manifest.json — the format the app expects from the CDN.

Usage:
    python3 scripts/rewrite_manifest.py [host] [port]

    host  — IP or hostname the app will reach (default: localhost)
    port  — HTTP port served by serve-variants.sh (default: 8080)
"""

import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT         = Path(__file__).resolve().parent.parent
SCRAPE_OUT   = ROOT / "scrape" / "output"
SRC_MANIFEST = SCRAPE_OUT / "manifest.json"
CDN_MANIFEST = SCRAPE_OUT / "cdn-manifest.json"

_GAME_GROUPS: dict[str, tuple[str, str]] = {
    "red_blue":                  ("Red / Blue",                 "Generation I"),
    "yellow":                    ("Yellow",                     "Generation I"),
    "gold_silver":               ("Gold / Silver",              "Generation II"),
    "crystal":                   ("Crystal",                    "Generation II"),
    "ruby_sapphire":             ("Ruby / Sapphire",            "Generation III"),
    "emerald":                   ("Emerald",                    "Generation III"),
    "firered_leafgreen":         ("FireRed / LeafGreen",        "Generation III"),
    "diamond_pearl":             ("Diamond / Pearl",            "Generation IV"),
    "platinum":                  ("Platinum",                   "Generation IV"),
    "heartgold_soulsilver":      ("HeartGold / SoulSilver",     "Generation IV"),
    "black_white":               ("Black / White",              "Generation V"),
    "black_2_white_2":           ("Black 2 / White 2",          "Generation V"),
    "x_y":                       ("X / Y",                      "Generation VI"),
    "omega_ruby_alpha_sapphire": ("Omega Ruby / Alpha Sapphire","Generation VI"),
    "sun_moon":                  ("Sun / Moon",                 "Generation VII"),
    "ultra_sun_ultra_moon":      ("Ultra Sun / Ultra Moon",     "Generation VII"),
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = sys.argv[2] if len(sys.argv) > 2 else "8080"
    base = f"http://{host}:{port}"

    if not SRC_MANIFEST.exists():
        sys.exit(
            "scrape/output/manifest.json not found.\n"
            "Run: cd scrape && python3 scrape.py <variantID>"
        )

    src = json.loads(SRC_MANIFEST.read_text())

    # Group variants by gameID, preserving first-seen insertion order
    groups: dict[str, list[dict]] = {}
    for v in src["variants"]:
        groups.setdefault(v["gameID"], []).append(v)

    games = []
    missing_zips = []

    for game_id, variants in groups.items():
        first = variants[0]
        display_name, gen_display = _GAME_GROUPS.get(
            game_id,
            (game_id.replace("_", " ").title(), f"Generation {first['generation']}")
        )

        variant_list = []
        for v in variants:
            zip_path = SCRAPE_OUT / f"{v['variantID']}.zip"
            if not zip_path.exists():
                missing_zips.append(zip_path.name)
                continue
            variant_list.append({
                "id":             v["variantID"],
                "displayName":    v["displayName"],
                "zipURL":         f"{base}/{v['variantID']}.zip",
                "zipSHA256":      sha256_of(zip_path),
                "sizeBytes":      zip_path.stat().st_size,
                "contentVersion": v["contentVersion"],
                "layoutVersion":  v["layoutVersion"],
            })

        if variant_list:
            games.append({
                "id":                  game_id,
                "displayName":         display_name,
                "generation":          first["generation"],
                "generationDisplayName": gen_display,
                "variants":            variant_list,
            })

    if missing_zips:
        print(f"Warning: skipped {len(missing_zips)} variant(s) with no ZIP:", file=sys.stderr)
        for name in missing_zips:
            print(f"  {name}", file=sys.stderr)

    cdn = {
        "manifestVersion": 1,
        "updatedAt":       datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games":           games,
    }
    CDN_MANIFEST.write_text(json.dumps(cdn, indent=2, ensure_ascii=False))

    total = sum(len(g["variants"]) for g in games)
    print(f"Wrote {CDN_MANIFEST.relative_to(ROOT)} ({total} variant(s))")
    print()
    print("Next steps:")
    print(f"  1. In Constants.swift set remoteManifestURL to:")
    print(f"       {base}/cdn-manifest.json")
    print(f"  2. Run: scripts/serve-variants.sh {port}")
    print(f"  3. Build and run the app.")


if __name__ == "__main__":
    main()
