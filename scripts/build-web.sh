#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

(cd "$ROOT/frontend" && npm install && npm run build)
rm -rf "$ROOT/backend/static"
mkdir -p "$ROOT/backend/static"
cp -r "$ROOT/frontend/dist/"* "$ROOT/backend/static/"
echo "Frontend → backend/static (bereit für eine URL)"
