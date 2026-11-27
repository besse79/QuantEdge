"""Daily decision preview. Never promotes research data to executable orders."""
from .paper_risk import allocate

def build_plan(reports, account):
    if account["positions"]:
        return {"proposals":[],"execution_authorized":False,"reason":"existing positions require reconciliation"}
    ranked=[row for report in reports.values() for row in report["ranked"]]
    ranked.sort(key=lambda r:(-r["momentum"],r["instrument_id"],r["provider"],r["currency"]))
    result=allocate(ranked,cash=account["cash"])
    return dict(result,execution_authorized=False,
                reason="qualification and next-session execution evidence required")
