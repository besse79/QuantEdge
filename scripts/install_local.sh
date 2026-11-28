#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
root="$PWD"
command -v python3 >/dev/null
command -v npm >/dev/null
backup="$(mktemp -d "$HOME/quantedge-backup.XXXXXXXX")"
items=()
for p in .venv web/.next web/node_modules web/package-lock.json; do
  if [[ -e "$p" ]]; then items+=("$p"); fi
done
if (("${#items[@]}")); then tar -czf "$backup/runtime.tar.gz" "${items[@]}"; else tar -czf "$backup/runtime.tar.gz" --files-from /dev/null; fi
tar -tzf "$backup/runtime.tar.gz" >/dev/null
(cd "$backup" && sha256sum runtime.tar.gz > SHA256SUMS && sha256sum -c SHA256SUMS)
restore(){
  (cd "$backup" && sha256sum -c SHA256SUMS) || return 1
  cd "$root"
  rm -rf -- .venv web/.next web/node_modules web/package-lock.json
  tar -xzf "$backup/runtime.tar.gz"
}
trap 'rc=$?; trap - ERR; restore || echo "RESTORE FAILED: $backup" >&2; exit "$rc"' ERR
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
(cd web && npm install --no-audit --no-fund && npm run build)
trap - ERR
printf 'Installation OK. Backup: %s\n' "$backup"
printf 'Start: bash scripts/start_local.sh\n'
