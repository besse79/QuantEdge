"""Deterministic PAPER rebalance intent; execution requires independent evidence."""
from decimal import Decimal
from uuid import UUID, uuid5, NAMESPACE_URL

def plan_rebalance(account, ranked, *, session, max_positions=5):
    if type(max_positions) is not int or max_positions<1:
        raise ValueError("invalid position limit")
    qualified={}
    for row in ranked:
        key=str(UUID(str(row["instrument_id"])))
        if key in qualified:
            raise ValueError("ambiguous instrument")
        if row.get("paper_eligible") is True:
            qualified[key]=row
    held={str(UUID(str(p["instrument_id"]))):p["quantity"] for p in account["positions"]}
    if any(type(q) is not int or q<=0 for q in held.values()):
        raise ValueError("invalid holdings")
    targets=sorted((r for r in qualified.values() if r.get("research_candidate") is True),
                   key=lambda r:(-r["momentum"],str(r["instrument_id"])))[:max_positions]
    target_ids={str(r["instrument_id"]) for r in targets}
    intents=[]
    for key,quantity in sorted(held.items()):
        if key in qualified and key not in target_ids:
            intents.append({"event_id":str(uuid5(NAMESPACE_URL,f"qe:{session}:{key}:SELL")),
                            "instrument_id":key,"side":"SELL","quantity":quantity})
    return {"intents":intents,"target_ids":sorted(target_ids),
            "unqualified_holdings":sorted(set(held)-set(qualified)),
            "execution_authorized":False}
