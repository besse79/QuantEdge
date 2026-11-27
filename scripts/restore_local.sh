#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
backup="$(realpath "${1:?backup directory required}")"
[[ "$backup" == "$HOME"/quantedge-backup.* ]]
(cd "$backup" && sha256sum -c SHA256SUMS)
tar -tzf "$backup/runtime.tar.gz" >/dev/null
rm -rf -- .venv web/.next web/node_modules web/package-lock.json
tar -xzf "$backup/runtime.tar.gz"
echo "Runtime restored from $backup"
