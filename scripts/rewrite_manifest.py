#!/usr/bin/env python3
"""
Generate a CDN-format manifest from scrape/output/manifest.json for local dev.

Reads the scraper's intermediate manifest, computes SHA-256 and byte size for
each ZIP in scrape/output/, and writes scrape/output/cdn-manifest.json — the
format the app expects from the CDN.

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

_GEN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def gen_display(n: int) -> str:
    numeral = _GEN_NUMERALS[n - 1] if 1 <= n <= len(_GEN_NUMERALS) else str(n)
    return f"Generation {numeral}"


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

    games = []
    missing_zips = []

    for v in src["variants"]:
        zip_path = SCRAPE_OUT / f"{v['variantID']}.zip"
        if not zip_path.exists():
            missing_zips.append(zip_path.name)
            continue
        games.append({
            "id":                    v["variantID"],
            "displayName":           v["displayName"],
            "generation":            v["generation"],
            "generationDisplayName": gen_display(v["generation"]),
            "zipURL":                f"{base}/{v['variantID']}.zip",
            "zipSHA256":             sha256_of(zip_path),
            "sizeBytes":             zip_path.stat().st_size,
            "contentVersion":        v["contentVersion"],
            "layoutVersion":         v["layoutVersion"],
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

    print(f"Wrote {CDN_MANIFEST.relative_to(ROOT)} ({len(games)} game(s))")
    print()
    print("Next steps:")
    print(f"  1. In Constants.swift set remoteManifestURL to:")
    print(f"       {base}/cdn-manifest.json")
    print(f"  2. Run: scripts/serve-variants.sh {port}")
    print(f"  3. Build and run the app.")


if __name__ == "__main__":
    main()
