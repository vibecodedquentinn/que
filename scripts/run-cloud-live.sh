#!/usr/bin/env bash
# Jürgen live (Cloud-VM): .env mit LLM_API_KEY + optional cloudflared
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Fehlt: $ROOT/.env (LLM_API_KEY, LLM_BASE_URL, …)" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

export STATIC_DIR="$ROOT/frontend/dist"
export DATA_DIR="$ROOT/backend/data"

if [[ ! -d "$STATIC_DIR" ]]; then
  (cd "$ROOT/frontend" && npm ci && npm run build)
fi

pip3 install -q -r "$ROOT/backend/requirements.txt" --break-system-packages 2>/dev/null || true

echo "==> Jürgen auf http://127.0.0.1:8000"
echo "    Öffentlich: cloudflared tunnel --url http://127.0.0.1:8000"
cd "$ROOT/backend"
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
