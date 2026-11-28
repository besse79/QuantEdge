"""Daily decision preview. Never promotes research data to executable orders."""
from .paper_risk import allocate
from .rebalance import plan_rebalance

def build_plan(reports, account, *, session=None):
    ranked=[row for report in reports.values() for row in report["ranked"]]
    ranked.sort(key=lambda r:(-r["momentum"],r["instrument_id"],r["provider"],r["currency"]))
    if account["positions"]:
        if session is None:
            return {"proposals":[],"execution_authorized":False,"reason":"session required for reconciliation"}
        return dict(plan_rebalance(account,ranked,session=session),proposals=[])
    result=allocate(ranked,cash=account["cash"])
    return dict(result,execution_authorized=False,
                reason="qualification and next-session execution evidence required")
