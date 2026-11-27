"""Pure PAPER allocation planner; no execution or persistent writes."""
from decimal import Decimal, ROUND_DOWN

def allocate(ranked, *, cash=500, max_positions=5, max_weight="0.20", fee=0, currency="EUR"):
    cash, weight, fee = map(lambda x: Decimal(str(x)), (cash,max_weight,fee))
    if not all(x.is_finite() for x in (cash,weight,fee)) or cash<=0 or not 0<weight<=1 or fee<0 or type(max_positions) is not int or max_positions<1:
        raise ValueError("invalid risk limits")
    remaining=cash
    orders=[]
    seen=set()
    for row in ranked:
        if len(orders)>=max_positions:
            break
        if row.get("paper_eligible") is not True or row.get("research_candidate") is not True or row.get("currency")!=currency or row["instrument_id"] in seen:
            continue
        price=Decimal(str(row["close"]))
        if not price.is_finite() or price<=0:
            raise ValueError("invalid price")
        budget=min(cash*weight,remaining)-fee
        if budget<price:
            continue
        quantity=int((budget/price).to_integral_value(rounding=ROUND_DOWN))
        cost=quantity*price+fee
        remaining-=cost
        seen.add(row["instrument_id"])
        orders.append({"instrument_id":row["instrument_id"],"quantity":quantity,"reference_price":str(price),"estimated_cost":str(cost)})
    return {"proposals":orders,"remaining_cash":str(remaining),"execution_authorized":False}
