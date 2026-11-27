"""Fail-closed qualification of a declared point-in-time market universe."""
from math import isfinite
from uuid import UUID

def qualify(report, expected_ids, *, universe_verified=False):
    if universe_verified is not True:
        raise ValueError("unverified market membership")
    expected={str(UUID(str(i))) for i in expected_ids}
    if not expected:
        raise ValueError("empty universe")
    ranked=report["ranked"]
    actual=[str(UUID(str(r["instrument_id"]))) for r in ranked]
    if len(actual)!=len(set(actual)) or set(actual)!=expected or report["rejected"]:
        raise ValueError("incomplete qualified universe")
    result=[]
    for row in ranked:
        if row["currency"] not in ("EUR","USD") or not isfinite(row["momentum"]) or not isfinite(row["close"]) or row["close"]<=0:
            raise ValueError("invalid candidate")
        result.append(dict(row,paper_eligible=True))
    return result
