#!/usr/bin/env python3
"""
Install a variant ZIP directly into the booted simulator's app container.

Usage:
    python3 scripts/install_variant.py <variantID> [--bundle-id ID] [--device UDID]

Examples:
    python3 scripts/install_variant.py red
    python3 scripts/install_variant.py soulsilver --device <UDID>

Reads the ZIP from scrape/output/<variantID>.zip and metadata from
scrape/output/manifest.json. Run scrape.py for the variant first.
"""

import argparse, hashlib, json, shutil, subprocess, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

# JSONEncoder()/JSONDecoder() use Swift's reference date (Jan 1, 2001 UTC) for
# Date values. This offset converts a Unix timestamp to that epoch.
_APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

ROOT          = Path(__file__).resolve().parent.parent
SCRAPE_OUTPUT = ROOT / "scrape" / "output"
DEFAULT_BUNDLE_ID = "com.example.nuzlocker"


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs).stdout.strip()


def booted_udid(preferred=None):
    if preferred:
        return preferred
    out = run(["xcrun", "simctl", "list", "devices", "--json"])
    devices = json.loads(out)
    for runtime_devices in devices["devices"].values():
        for d in runtime_devices:
            if d.get("state") == "Booted":
                return d["udid"]
    sys.exit("No booted simulator found. Boot one in Xcode or via 'xcrun simctl boot <UDID>'.")


def app_data_container(udid, bundle_id):
    try:
        path = run(["xcrun", "simctl", "get_app_container", udid, bundle_id, "data"])
        return Path(path)
    except subprocess.CalledProcessError:
        sys.exit(
            f"App '{bundle_id}' not installed on simulator {udid}.\n"
            "Build and run the app in the simulator at least once first."
        )


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("variant_id", help="Variant to install (e.g. red, soulsilver)")
    parser.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID)
    parser.add_argument("--device", default=None, help="Simulator UDID (default: booted device)")
    args = parser.parse_args()

    zip_path = SCRAPE_OUTPUT / f"{args.variant_id}.zip"
    if not zip_path.exists():
        sys.exit(
            f"scrape/output/{args.variant_id}.zip not found.\n"
            f"Run: cd scrape && python3 scrape.py {args.variant_id}"
        )

    # Read variant metadata from the scraper's global manifest
    manifest_path = SCRAPE_OUTPUT / "manifest.json"
    if not manifest_path.exists():
        sys.exit("scrape/output/manifest.json not found. Run scrape.py first.")
    manifest = json.loads(manifest_path.read_text())
    entry = next((v for v in manifest["variants"] if v["variantID"] == args.variant_id), None)
    if entry is None:
        sys.exit(
            f"No manifest entry for '{args.variant_id}'.\n"
            f"Run: cd scrape && python3 scrape.py {args.variant_id}"
        )

    # Validate ZIP content: game.json must exist and variantID must match
    with zipfile.ZipFile(zip_path) as zf:
        if "game.json" not in zf.namelist():
            sys.exit(f"{zip_path.name} is missing game.json — re-run scrape.py.")
        game_data = json.loads(zf.read("game.json"))
        if game_data.get("variantID") != args.variant_id:
            sys.exit(f"variantID mismatch in game.json — re-run scrape.py.")

    udid = booted_udid(args.device)
    print(f"Simulator: {udid}")

    container    = app_data_container(udid, args.bundle_id)
    variants_root = container / "Library" / "Application Support" / "Nuzlocker" / "Variants"
    variant_dir  = variants_root / args.variant_id

    print(f"Installing {zip_path.name} → {variant_dir}")
    if variant_dir.exists():
        shutil.rmtree(variant_dir)
    variants_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            dest = variant_dir / member.filename
            if member.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(member.filename))

    # Write .install-meta.json to mirror what the app's install flow produces
    meta = {
        "variantID":      entry["variantID"],
        "gameID":         entry["gameID"],
        "generation":     entry["generation"],
        "contentVersion": entry["contentVersion"],
        "layoutVersion":  entry["layoutVersion"],
        "installedAt":    (datetime.now(timezone.utc) - _APPLE_EPOCH).total_seconds(),
        "zipSHA256":      sha256_of(zip_path),
    }
    (variant_dir / ".install-meta.json").write_text(json.dumps(meta, indent=2))

    print(f"Done. {entry['displayName']} ({args.variant_id}) installed.")
    print("Restart the app in the simulator to pick up the new data.")


if __name__ == "__main__":
    main()
