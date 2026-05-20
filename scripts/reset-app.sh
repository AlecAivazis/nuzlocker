#!/usr/bin/env bash
# Uninstalls the app from the currently booted simulator (without full simulator erase).
# Useful for testing "uninstall and reinstall" flows.
# Usage: ./scripts/reset-app.sh [bundle-id]

set -euo pipefail
BUNDLE_ID="${1:-com.example.nuzlocker}"
xcrun simctl uninstall booted "$BUNDLE_ID"
echo "Uninstalled $BUNDLE_ID from booted simulator"
