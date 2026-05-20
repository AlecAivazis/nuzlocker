#!/usr/bin/env bash
# Scrapes, packages, and installs game data into the booted simulator in one step.
# Usage: ./scripts/seed.sh <variantID> [<variantID> ...] [-- <install-variant flags>]
#
# Examples:
#   ./scripts/seed.sh red
#   ./scripts/seed.sh red blue yellow
#   ./scripts/seed.sh soulsilver -- --device <UDID>

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ $# -eq 0 ]]; then
    echo "Usage: $(basename "$0") <variantID> [<variantID> ...] [-- <install-variant flags>]" >&2
    exit 1
fi

VARIANTS=()
INSTALL_ARGS=()
saw_separator=false
for arg in "$@"; do
    if [[ "$arg" == "--" ]]; then
        saw_separator=true
    elif $saw_separator; then
        INSTALL_ARGS+=("$arg")
    else
        VARIANTS+=("$arg")
    fi
done

echo "==> Scraping"
for variant in "${VARIANTS[@]}"; do
    echo "    $variant"
    (cd "$ROOT/scrape" && python3 scrape.py "$variant")
done

echo ""
echo "==> Packaging"
python3 "$ROOT/scripts/make_variants.py" "${VARIANTS[@]}"

echo ""
echo "==> Installing"
for variant in "${VARIANTS[@]}"; do
    python3 "$ROOT/scripts/install_variant.py" "$variant" "${INSTALL_ARGS[@]}"
done

echo ""
echo "Restart the app in the simulator."
