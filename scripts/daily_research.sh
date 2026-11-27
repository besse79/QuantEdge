#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MKD_DSN:?MKD_DSN required}"
: "${QE_PAPER_DSN:?QE_PAPER_DSN required}"
PYTHON="${QE_PYTHON:-.venv/bin/python}"
exec "$PYTHON" -m quantedge.daily "$@"
