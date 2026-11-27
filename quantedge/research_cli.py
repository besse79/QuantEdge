"""Read-only research CLI; explicit exchange calendar manifest, no broker."""
import argparse
import json
import os
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from .mkd_backtest import Session
from .research import run_momentum

def parse_sessions(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty session manifest required")
    return [Session(date.fromisoformat(r["day"]),
                    datetime.fromisoformat(r["opens_at"]),
                    datetime.fromisoformat(r["cutoff"])) for r in rows]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrument-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--history-start", required=True, type=date.fromisoformat)
    parser.add_argument("--sessions", required=True)
    parser.add_argument("--cash", type=float, default=500)
    parser.add_argument("--fee", type=float, default=0)
    args = parser.parse_args()
    sessions = parse_sessions(args.sessions)
    import psycopg
    with psycopg.connect(os.environ["MKD_DSN"]) as connection:
        connection.read_only = True
        connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        result, metrics = run_momentum(connection, instrument_id=args.instrument_id,
            provider=args.provider, currency=args.currency, history_start=args.history_start,
            sessions=sessions, initial_cash=args.cash, fee_per_order=args.fee)
    print(json.dumps({"metrics": metrics, "result": asdict(result)},
                     default=lambda value: value.isoformat(), allow_nan=False))

if __name__ == "__main__":
    main()
