#!/usr/bin/env bash
# Serves the variant ZIPs over HTTP for local development.
# Usage: ./scripts/serve-variants.sh [port]

set -euo pipefail
PORT="${1:-8080}"
FIXTURES_DIR="$(cd "$(dirname "$0")/../variants" && pwd)"

cd "$FIXTURES_DIR"
echo "Serving $FIXTURES_DIR on port $PORT"
ls -1 *.zip | sed "s|^|  http://localhost:$PORT/|"
exec python3 -m http.server "$PORT"
