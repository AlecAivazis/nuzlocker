#!/usr/bin/env bash
# Generates a local CDN-format manifest from scrape/output/manifest.json.
# Usage: ./scripts/rewrite-manifest.sh [host] [port]
#   simulator:  ./scripts/rewrite-manifest.sh                # localhost:8080
#   device:     ./scripts/rewrite-manifest.sh 192.168.1.42   # LAN IP, port 8080

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/rewrite_manifest.py" "$@"
