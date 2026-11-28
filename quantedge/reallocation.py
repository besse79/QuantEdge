"""Compute sell-first rebalance from qualified EUR execution prices."""
from decimal import Decimal
from uuid import UUID, uuid5, NAMESPACE_URL

def rebalance(account, ranked, prices, *, session, fee=0, max_positions=5):
    cash=Decimal(str(account["cash"]))
    fee=Decimal(str(fee))
    if not cash.is_finite() or cash<0 or not fee.is_finite() or fee<0:
        raise ValueError("invalid account")
    if type(max_positions) is not int or not 1<=max_positions<=5:
        raise ValueError("invalid limit")
    rows={}
    for r in ranked:
        key=str(UUID(str(r["instrument_id"])))
        if key in rows or r.get("paper_eligible") is not True:
            raise ValueError("unqualified or duplicate candidate")
        rows[key]=r
    held={}
    for p in account["positions"]:
        key=str(UUID(str(p["instrument_id"])))
        q=p["quantity"]
        if key in held or type(q) is not int or q<=0 or key not in rows:
            raise ValueError("unqualified holding")
        held[key]=q
    targets=sorted((k for k,r in rows.items() if r.get("research_candidate") is True),key=lambda k:(-rows[k]["momentum"],k))[:max_positions]
    relevant=set(targets)|set(held)
    px={k:Decimal(str(prices[k])) for k in relevant}
    if any(not p.is_finite() or p<=0 for p in px.values()):
        raise ValueError("invalid execution price")
    equity=cash+sum((px[k]*q for k,q in held.items()),Decimal(0))
    budget=equity*Decimal("0.20")
    desired={k:int(budget/px[k]) for k in targets}
    orders=[]
    def add(k,side,q):
        orders.append(dict(event_id=str(uuid5(NAMESPACE_URL,f"qe:{session}:{k}:{side}")),instrument_id=k,side=side,quantity=q))
    for k,q in sorted(held.items()):
        n=q-desired.get(k,0)
        if n>0:
            cash+=px[k]*n-fee
            if cash<0: raise ValueError("unfunded sale")
            add(k,"SELL",n)
    for k in targets:
        n=min(desired[k]-held.get(k,0),int(max(Decimal(0),cash-fee)/px[k]))
        if n>0:
            cash-=px[k]*n+fee
            add(k,"BUY",n)
    return orders
