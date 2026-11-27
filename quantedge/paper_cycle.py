"""Atomic PAPER cycle for an independently verified, single-session universe."""
from .qualification import qualify
from .fill_source import load_fill
from .reallocation import rebalance
from .paper_execution import execute_batch
from .paper_ledger import snapshot

def run_cycle(mkd, paper, report, expected_ids, sessions, *, as_of, fx_provider,
              universe_verified=False, authorized=False, fee=0):
    if authorized is not True:
        raise ValueError("PAPER cycle disabled")
    ranked=qualify(report,expected_ids,universe_verified=universe_verified)
    if set(sessions)!={r["instrument_id"] for r in ranked}:
        raise ValueError("incomplete execution calendar")
    dates={s["execution_session"] for s in sessions.values()}
    if len(dates)!=1:
        raise ValueError("mixed execution sessions")
    day=next(iter(dates))
    with paper.transaction():
        with paper.cursor() as c:
            c.execute("SELECT current_database()")
            if c.fetchone()[0]!="quantedge_paper":
                raise ValueError("isolated PAPER database required")
            c.execute("SELECT cash FROM qe_paper_account WHERE id=1 FOR UPDATE")
            if c.fetchone() is None:
                raise ValueError("account not initialized")
            c.execute("SELECT pg_advisory_xact_lock(81722026)")
            c.execute("CREATE TABLE IF NOT EXISTS qe_paper_cycle (session_date date PRIMARY KEY)")
            c.execute("INSERT INTO qe_paper_cycle VALUES (%s) ON CONFLICT DO NOTHING RETURNING session_date",(day,))
            if c.fetchone() is None:
                return {"status":"duplicate","orders":[]}
        account=snapshot(paper)
        fills={}
        for row in ranked:
            key=row["instrument_id"]
            fills[key]=load_fill(mkd,dict(sessions[key],instrument_id=key),provider=row["provider"],fx_provider=fx_provider,as_of=as_of,fee=fee)
        orders=rebalance(account,ranked,{k:v["price"] for k,v in fills.items()},session=day,fee=fee)
        for order in orders:
            order["execution_session"]=day
        result=execute_batch(paper,orders,{o["event_id"]:fills[o["instrument_id"]] for o in orders},authorized=True)
        return {"status":"recorded","orders":orders,"results":result}
