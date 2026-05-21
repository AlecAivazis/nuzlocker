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

SCRAPE_PYTHON="$ROOT/scrape/.venv/bin/python3"
if [[ ! -x "$SCRAPE_PYTHON" ]]; then
    echo "Scraper venv not found. Run: cd scrape && python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

echo "==> Scraping and packaging"
for variant in "${VARIANTS[@]}"; do
    echo "    $variant"
    (cd "$ROOT/scrape" && "$SCRAPE_PYTHON" scrape.py "$variant")
done

echo ""
echo "==> Installing"
for variant in "${VARIANTS[@]}"; do
    python3 "$ROOT/scripts/install_variant.py" "$variant" "${INSTALL_ARGS[@]}"
done

echo ""
echo "Restart the app in the simulator."
