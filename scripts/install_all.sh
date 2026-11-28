#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/install_local.sh
if [[ "${1:-}" == "--schedule" ]]; then
  bash scripts/install_timer.sh
elif [[ $# -ne 0 ]]; then
  echo "Usage: bash scripts/install_all.sh [--schedule]" >&2
  exit 2
fi
echo "Run bash scripts/start_local.sh and then bash scripts/verify_local.sh for local acceptance."
