"""PAPER execution adapter for independently qualified next-session fills."""
from datetime import datetime
from .paper_ledger import record_simulated_trade

def execute_batch(connection, intents, fills, *, authorized=False):
    if authorized is not True:
        raise ValueError("PAPER execution disabled")
    prepared=[]
    seen=set()
    for intent in intents:
        event=intent["event_id"]
        if event in seen:
            raise ValueError("duplicate intent")
        seen.add(event)
        fill=fills[event]
        if fill.get("quality_status")!="valid" or fill.get("currency")!="EUR":
            raise ValueError("qualified EUR fill required")
        if fill["instrument_id"]!=intent["instrument_id"]:
            raise ValueError("instrument mismatch")
        signal, execution, available=(datetime.fromisoformat(fill[k]) for k in ("signal_at","executed_at","available_at"))
        if any(t.utcoffset() is None for t in (signal,execution,available)) or not signal<execution<=available:
            raise ValueError("invalid fill chronology")
        if fill.get("session")!=intent.get("execution_session") or not intent.get("execution_session"):
            raise ValueError("execution session mismatch")
        prepared.append(dict(event_id=event,instrument_id=intent["instrument_id"],side=intent["side"],quantity=intent["quantity"],price=fill["price"],fee=fill["fee"],authorized=True))
    with connection.transaction():
        return [record_simulated_trade(connection,**trade) for trade in prepared]
