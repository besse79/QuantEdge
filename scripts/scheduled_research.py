"""Generate daily research report for each market's last completed session."""
import json
from datetime import datetime, timedelta, timezone
from quantedge.api import ScanRequest, daily_scan, paper_account
from quantedge.calendar import exchange_sessions
from quantedge.daily_plan import build_plan

def main():
    now=datetime.now(timezone.utc)
    reports={}
    for mic in ("XPAR","XAMS","XBRU","XLIS","XNYS","XNAS"):
        sessions=exchange_sessions(mic,now.date()-timedelta(days=14),now.date())
        completed=[s for s in sessions if s.cutoff<=now]
        if not completed:
            raise RuntimeError("no completed session: "+mic)
        day=completed[-1].day
        reports[mic]=daily_scan(ScanRequest(provider="yahoo",mic=mic,start=day-timedelta(days=550),end=day))
    print(json.dumps({"generated_at":now.isoformat(),"markets":reports,"plan":build_plan(reports,paper_account(),session=now.date().isoformat()),"execution_authorized":False},default=str,allow_nan=False))

if __name__=="__main__":
    main()
