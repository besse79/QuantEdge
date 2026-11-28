"""Read-only MKD observed prices; never a certified backtest or execution source."""
from datetime import datetime, timezone, date
from decimal import Decimal
from urllib.request import urlopen
from urllib.parse import urlencode
from uuid import UUID
import json

def observed_history(instrument_id, *, currency, start, end, as_of):
    iid = str(UUID(str(instrument_id)))
    if currency not in ("EUR", "USD") or not isinstance(as_of, datetime) or as_of.utcoffset() is None or as_of > datetime.now(timezone.utc) or type(start) is not date or type(end) is not date or not start <= end < as_of.date():
        raise ValueError("invalid observation request")
    query = urlencode(dict(instrument_id=iid,start=start.isoformat(),end=end.isoformat(),as_of=as_of.isoformat(),limit=1000))
    with urlopen("http://127.0.0.1:8100/v1/observations/bars?"+query, timeout=10) as response:
        doc = json.load(response)
    if doc.get("instrument_id") != iid or doc.get("paper_eligible") is not False or doc.get("point_in_time_verified") is not False:
        raise ValueError("unexpected observation provenance")
    previous = None
    for row in doc["items"]:
        day = date.fromisoformat(row["date"])
        observed = datetime.fromisoformat(row["observed_at"].replace("Z","+00:00"))
        if row["currency"] != currency or row["quality_status"] != "staged_unverified" or not start <= day <= end or (previous is not None and day <= previous) or observed.utcoffset() is None or not day < observed.date() or observed > as_of:
            raise ValueError("invalid observation")
        prices = [Decimal(str(row[k])) for k in ("open","high","low","close")]
        if not all(p.is_finite() and p>0 for p in prices) or prices[1]<max(prices) or prices[2]>min(prices) or type(row["volume"]) is not int or row["volume"]<0:
            raise ValueError("invalid OHLCV")
        previous = day
    return doc
