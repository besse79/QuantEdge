#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MKD_DSN:?MKD_DSN required}"
: "${QE_PAPER_DSN:?QE_PAPER_DSN required}"
test -x .venv/bin/python
test -d web/.next
export QUANTEDGE_API_URL=http://127.0.0.1:8012
.venv/bin/python -m uvicorn quantedge.api:app --host 127.0.0.1 --port 8012 &
api=$!
trap 'kill "$api" "${web:-$api}" 2>/dev/null || true' EXIT
trap 'exit 130' INT TERM
for i in {1..30}; do
  if curl -fsS "$QUANTEDGE_API_URL/health" >/dev/null; then break; fi
  kill -0 "$api"
  sleep 1
done
curl -fsS "$QUANTEDGE_API_URL/health" >/dev/null
(cd web && exec npm run start -- --hostname 127.0.0.1 --port 3012) &
web=$!
wait -n "$api" "$web"
