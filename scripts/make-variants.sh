#!/usr/bin/env bash
# Packages scrape/output/*.json into variants/*.zip and updates the manifest template.
# Usage: ./scripts/make-variants.sh [game ...]   # omit to process all scraped games

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/make_variants.py" "$@"
