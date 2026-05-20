#!/usr/bin/env python3
"""
Install a variant ZIP directly into the booted simulator's app container.

Usage:
    python3 scripts/install_variant.py <variantID> [--bundle-id ID] [--device UDID]

Examples:
    python3 scripts/install_variant.py red
    python3 scripts/install_variant.py soulsilver --device <UDID>

The script extracts variants/<variantID>.zip to the right Application Support
path and writes .install-meta.json so InstallService recognises it as installed.
"""

import argparse, hashlib, json, shutil, subprocess, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "variants"
DEFAULT_BUNDLE_ID = "com.example.nuzlocker"
LAYOUT_VERSION = 1


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
    parser.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID, help="App bundle ID")
    parser.add_argument("--device", default=None, help="Simulator UDID (default: booted device)")
    args = parser.parse_args()

    zip_path = FIXTURES_DIR / f"{args.variant_id}.zip"
    if not zip_path.exists():
        sys.exit(
            f"variants/{args.variant_id}.zip not found.\n"
            "Run scripts/make-variants.sh first."
        )

    # Read variant manifest from inside the ZIP
    with zipfile.ZipFile(zip_path) as zf:
        try:
            inner = json.loads(zf.read("manifest.json"))
        except KeyError:
            sys.exit(f"{zip_path.name} is missing manifest.json — re-run make-variants.sh.")

    variant_id = inner["variantID"]
    game_id = inner["gameID"]
    generation = inner["generation"]
    display_name = inner["displayName"]
    content_version = inner["contentVersion"]
    layout_version = inner["layoutVersion"]

    udid = booted_udid(args.device)
    print(f"Simulator: {udid}")

    container = app_data_container(udid, args.bundle_id)
    variants_root = container / "Library" / "Application Support" / "Nuzlocker" / "Variants"
    variant_dir = variants_root / variant_id

    # Extract ZIP
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

    # Write .install-meta.json (mirrors InstallService's output)
    meta = {
        "variantID": variant_id,
        "gameID": game_id,
        "generation": generation,
        "contentVersion": content_version,
        "layoutVersion": layout_version,
        "installedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zipSHA256": sha256_of(zip_path),
    }
    meta_path = variant_dir / ".install-meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"Done. {display_name} ({variant_id}) installed.")
    print("Restart the app in the simulator to pick up the new data.")


if __name__ == "__main__":
    main()
