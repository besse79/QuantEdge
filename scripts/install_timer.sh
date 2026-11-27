#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
root="$PWD"
[[ "$root" =~ ^/[a-zA-Z0-9_./-]+$ ]] || { echo "Unsupported checkout path"; exit 1; }
test -x .venv/bin/python
config="$HOME/.config/quantedge/research.env"
test -f "$config"
test "$(stat -c %a "$config")" = 600
units="$HOME/.config/systemd/user"
mkdir -p "$units"
for name in quantedge-research.service quantedge-research.timer; do
  test ! -e "$units/$name" || { echo "Existing unit: $name; refusing overwrite"; exit 1; }
done
cat > "$units/quantedge-research.service" <<EOF
[Unit]
Description=QuantEdge read-only daily research
[Service]
Type=oneshot
WorkingDirectory=$root
EnvironmentFile=%h/.config/quantedge/research.env
ExecStart=$root/.venv/bin/python -m scripts.scheduled_research
TimeoutStartSec=1800
EOF
cat > "$units/quantedge-research.timer" <<EOF
[Unit]
Description=QuantEdge daily research schedule
[Timer]
OnCalendar=*-*-* 00:30:00 Europe/Paris
Persistent=true
[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now quantedge-research.timer
systemctl --user list-timers quantedge-research.timer
