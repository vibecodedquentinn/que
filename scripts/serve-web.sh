#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/build-web.sh"
cd "$ROOT/backend"
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
