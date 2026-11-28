#!/usr/bin/env bash
set -euo pipefail
umask 077
root="$HOME/quantedge-preview"
src="$(cd "$(dirname "$0")/.." && pwd)"
sha="$(git -C "$src" rev-parse HEAD)"
runtime="$root/releases/$sha"
units="$HOME/.config/systemd/user"
mkdir -p "$root/backups" "$root/releases" "$units"
exec 9>"$root/install.lock"
flock -n 9
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
systemctl --user show-environment >/dev/null
# Dedicated cluster, never modify the shared MKD or Hippique clusters.
pgbin="$(pg_config --bindir)"
pgdata="$root/postgres"
socket="$root/socket"
mkdir -p "$socket"
if [[ ! -f "$pgdata/PG_VERSION" ]]; then
 "$pgbin/initdb" -D "$pgdata" --auth-local=peer --auth-host=scram-sha-256
fi
backup="$(mktemp -d "$root/backups/preview.XXXXXXXX")"
for unit in quantedge-preview-db.service quantedge-preview-api.service quantedge-preview-web.service; do
 if [[ -f "$units/$unit" ]]; then cp -a "$units/$unit" "$backup/"; fi
 systemctl --user is-active "$unit" > "$backup/$unit.active" || true
 systemctl --user is-enabled "$unit" > "$backup/$unit.enabled" || true
done
(cd "$backup"; sha256sum ./* > SHA256SUMS; sha256sum -c SHA256SUMS)
rollback(){
 trap - ERR
 for unit in quantedge-preview-web.service quantedge-preview-api.service quantedge-preview-db.service; do
  systemctl --user stop "$unit" || true
  systemctl --user disable "$unit" || true
  if [[ -f "$backup/$unit" ]]; then cp -a "$backup/$unit" "$units/$unit"; else rm -f "$units/$unit"; fi
 done
 systemctl --user daemon-reload
 for unit in quantedge-preview-db.service quantedge-preview-api.service quantedge-preview-web.service; do
  if grep -qx enabled "$backup/$unit.enabled"; then systemctl --user enable "$unit"; fi
  if grep -qx active "$backup/$unit.active"; then systemctl --user start "$unit"; fi
 done
}
if [[ ! -f "$runtime/.ready" ]]; then
 mkdir -p "$runtime"
 git -C "$src" archive "$sha" | tar -x -C "$runtime"
 (cd "$runtime"; bash scripts/install_local.sh)
 touch "$runtime/.ready"
fi
node="$(command -v node)"
trap 'rollback; exit 1' ERR
cat > "$units/quantedge-preview-db.service" <<EOF
[Unit]
Description=QuantEdge isolated PAPER PostgreSQL
[Service]
ExecStart=$pgbin/postgres -D $pgdata -k $socket -p 55432 -c listen_addresses=
Restart=on-failure
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now quantedge-preview-db.service
for i in {1..30}; do pg_isready -q -h "$socket" -p 55432 && break; sleep 1; done
pg_isready -h "$socket" -p 55432
if [[ "$(psql -XAt -h "$socket" -p 55432 -d postgres -c "SELECT count(*) FROM pg_database WHERE datname='quantedge_paper'")" == 0 ]]; then
 createdb -h "$socket" -p 55432 quantedge_paper
fi
pg_dump -Fc -h "$socket" -p 55432 -d quantedge_paper -f "$backup/paper.dump"
pg_restore -l "$backup/paper.dump" >/dev/null
(cd "$backup"; sha256sum paper.dump > paper.sha256; sha256sum -c paper.sha256)
export QE_PAPER_DSN="dbname=quantedge_paper host=$socket port=55432"
export MKD_DSN="dbname=market_data_hub host=/var/run/postgresql port=5433"
(cd "$runtime"; .venv/bin/python -c 'import os,psycopg; from quantedge.paper_ledger import initialize; c=psycopg.connect(os.environ["QE_PAPER_DSN"]); initialize(c); c.commit(); c.close()')
cat > "$units/quantedge-preview-api.service" <<EOF
[Unit]
Description=QuantEdge preview API
After=quantedge-preview-db.service
Requires=quantedge-preview-db.service
[Service]
WorkingDirectory=$runtime
Environment="MKD_DSN=$MKD_DSN"
Environment="QE_PAPER_DSN=$QE_PAPER_DSN"
Environment=QE_ENABLE_PAPER=0
ExecStart=$runtime/.venv/bin/python -m uvicorn quantedge.api:app --host 127.0.0.1 --port 8012
Restart=on-failure
[Install]
WantedBy=default.target
EOF
cat > "$units/quantedge-preview-web.service" <<EOF
[Unit]
Description=QuantEdge preview Next.js
After=quantedge-preview-api.service
[Service]
WorkingDirectory=$runtime/web
Environment=QUANTEDGE_API_URL=http://127.0.0.1:8012
ExecStart=$node $runtime/web/node_modules/next/dist/bin/next start -H 127.0.0.1 -p 3012
Restart=on-failure
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable quantedge-preview-api.service quantedge-preview-web.service
systemctl --user restart quantedge-preview-api.service quantedge-preview-web.service
curl --retry 15 --retry-connrefused --retry-delay 2 -fsS http://127.0.0.1:8012/health
curl --retry 15 --retry-connrefused --retry-delay 2 -fsS http://127.0.0.1:3012/ > "$backup/web.html"
curl -fsS http://127.0.0.1:8012/paper | "$runtime/.venv/bin/python" -c 'import json,sys; from decimal import Decimal; d=json.load(sys.stdin); assert Decimal(d["cash"])>=0 and d["execution_authorized"] is False'
trap - ERR
echo "QUANTEDGE_PREVIEW_PASS $sha"
