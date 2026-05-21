#!/usr/bin/env bash
# Serves variant ZIPs and cdn-manifest.json over HTTP for local development.
# Run rewrite-manifest.sh first to generate cdn-manifest.json.
# Usage: ./scripts/serve-variants.sh [port]

set -euo pipefail
PORT="${1:-8080}"
SERVE_DIR="$(cd "$(dirname "$0")/../scrape/output" && pwd)"

cd "$SERVE_DIR"
echo "Serving $SERVE_DIR on port $PORT"
echo ""
shopt -s nullglob
for f in *.zip cdn-manifest.json; do
    echo "  http://localhost:$PORT/$f"
done
echo ""
exec python3 -m http.server "$PORT"
