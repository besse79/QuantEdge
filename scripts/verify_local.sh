#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m unittest discover -s tests -v
for endpoint in health instruments paper paper/valuation; do
  curl -fsS --max-time 30 "http://127.0.0.1:8012/$endpoint" | .venv/bin/python -m json.tool >/dev/null
  printf 'PASS %s\n' "$endpoint"
done
for page in / /scanner /paper; do
  curl -fsS --max-time 30 "http://127.0.0.1:3012$page" >/dev/null
  printf 'PASS web %s\n' "$page"
done
echo 'Read-only smoke checks passed; PAPER execution and data qualification not certified.'
