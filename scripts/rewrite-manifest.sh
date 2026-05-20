#!/usr/bin/env bash
# Rewrites default-manifest.json so zipURLs point at a local server.
# Usage: ./scripts/rewrite-manifest.sh [host] [port]
#   simulator:  ./scripts/rewrite-manifest.sh                # defaults to localhost:8080
#   device:     ./scripts/rewrite-manifest.sh 192.168.1.42 8080

set -euo pipefail
HOST="${1:-localhost}"
PORT="${2:-8080}"
BASE="http://$HOST:$PORT"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/variants/default-manifest.template.json"
TARGET="$ROOT/Nuzlocker/default-manifest.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required. Install via 'brew install jq'." >&2
  exit 1
fi

jq --arg base "$BASE" '
  .games |= map(
    .variants |= map(. + {zipURL: ($base + "/" + .id + ".zip")})
  )
' "$TEMPLATE" > "$TARGET"

echo "Wrote $TARGET → $BASE/<variant>.zip"
