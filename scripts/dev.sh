#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -d "$ROOT/.venv" ]]; then
  PY="$ROOT/.venv/bin/python"
  PIP="$ROOT/.venv/bin/pip"
else
  PY="python3"
  PIP="pip3"
fi

$PIP install -r "$ROOT/backend/requirements.txt" 2>/dev/null || $PIP install -r "$ROOT/backend/requirements.txt" --break-system-packages

if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi

trap 'kill 0' EXIT

(cd "$ROOT/backend" && "$PY" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &
(cd "$ROOT/frontend" && npm run dev -- --host 127.0.0.1) &

wait
