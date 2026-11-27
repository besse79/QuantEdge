"""Opt-in PAPER scheduler consuming independently approved dated manifests."""
import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta, date
from quantedge.calendar import exchange_sessions

def main():
    if os.environ.get("QE_ENABLE_PAPER")!="1":
        raise SystemExit("PAPER disabled")
    root=Path(os.environ["QE_APPROVED_MANIFEST_DIR"])
    now=datetime.now(timezone.utc)
    for path in sorted(root.glob("*.json"),reverse=True):
        manifest=json.loads(path.read_text())
        day=date.fromisoformat(manifest["as_of"])
        if day>=now.date() or (now.date()-day).days>14:
            continue
        markets={m["mic"] for rows in manifest["markets"].values() for m in rows if m["currency"] in ("EUR","USD")}
        if not markets:
            raise ValueError("empty universe")
        sessions=[exchange_sessions(m,day+timedelta(days=1),day+timedelta(days=14))[0] for m in markets]
        dates={s.day for s in sessions}
        if len(dates)!=1:
            raise ValueError("mixed next sessions; execution blocked")
        if any(s.cutoff>now for s in sessions):
            return
        subprocess.run([sys.executable,"-m","quantedge.cycle_cli","--manifest",str(path),"--execution-day",next(iter(dates)).isoformat(),"--execute-paper"],check=True)
        return
    raise ValueError("no recent approved membership manifest")

if __name__=="__main__":
    main()
