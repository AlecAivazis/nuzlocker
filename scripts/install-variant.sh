#!/usr/bin/env bash
# Installs a variant ZIP into the booted simulator's app container.
# Usage: ./scripts/install-variant.sh <variantID> [--device <UDID>]

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/install_variant.py" "$@"
