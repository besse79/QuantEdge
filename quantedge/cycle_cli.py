"""Run a PAPER cycle from a dated, independently approved membership manifest."""
import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import psycopg
from .calendar import exchange_sessions
from .universe import verify_membership
from .scanner import Candidate, scan
from .paper_cycle import run_cycle

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",required=True)
    parser.add_argument("--execution-day",required=True,type=date.fromisoformat)
    parser.add_argument("--execute-paper",action="store_true")
    args=parser.parse_args()
    if not args.execute_paper or os.environ.get("QE_ENABLE_PAPER")!="1":
        raise SystemExit("PAPER execution disabled")
    manifest=json.loads(Path(args.manifest).read_text())
    day=date.fromisoformat(manifest["as_of"])
    now=datetime.now(timezone.utc)
    if not day<args.execution_day<=now.date():
        raise ValueError("invalid execution day")
    provider="yahoo"
    with psycopg.connect(os.environ["MKD_DSN"]) as mkd, psycopg.connect(os.environ["QE_PAPER_DSN"]) as paper:
        mkd.read_only=True
        mkd.isolation_level=psycopg.IsolationLevel.REPEATABLE_READ
        expected=verify_membership(mkd,manifest,day=day,provider=provider)
        reports={"ranked":[],"rejected":[]}
        sessions={}
        for mic in sorted({m["mic"] for members in manifest["markets"].values() for m in members if m["currency"] in ("EUR","USD")}):
            signal=exchange_sessions(mic,day,day)[0]
            next_session=exchange_sessions(mic,day+timedelta(days=1),day+timedelta(days=14))[0]
            if next_session.day!=args.execution_day or next_session.cutoff>now:
                raise ValueError("execution session not completed or mixed calendars")
            with mkd.cursor() as c:
                c.execute("""SELECT DISTINCT instrument_id,currency FROM public.instrument_identifiers
                WHERE provider=%s AND mic=%s AND currency IN ('EUR','USD')
                AND valid_from<=%s AND (valid_to IS NULL OR valid_to>%s)""",(provider,mic,day,day))
                candidates=[Candidate(str(i),provider,currency) for i,currency in c.fetchall() if str(i) in expected]
            report=scan(mkd,candidates,start=day-timedelta(days=550),end=day,as_of=signal.cutoff)
            for key in reports: reports[key].extend(report[key])
            for candidate in candidates:
                if candidate.instrument_id in sessions: raise ValueError("ambiguous listing")
                sessions[candidate.instrument_id]=dict(signal_at=signal.cutoff.isoformat(),session_close=(next_session.cutoff-timedelta(minutes=120)).isoformat(),execution_session=args.execution_day.isoformat())
        result=run_cycle(mkd,paper,reports,expected,sessions,as_of=now,fx_provider=provider,universe_verified=True,authorized=True)
        print(json.dumps(result,default=str,allow_nan=False))

if __name__=="__main__":
    main()
