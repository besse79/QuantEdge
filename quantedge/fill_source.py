"""Conservative next-session PAPER fills using qualified EOD evidence.
Execution is modeled at the close, not at an unobserved intraday price.
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from .fx import eur_rate

def load_fill(connection, intent, *, provider, fx_provider, as_of, fee=0):
    signal=datetime.fromisoformat(intent["signal_at"])
    close=datetime.fromisoformat(intent["session_close"])
    if any(t.utcoffset() is None for t in (signal,close,as_of)) or not signal<close<=as_of:
        raise ValueError("invalid execution chronology")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT close,currency,quality_status,published_at,first_available_at
            FROM public.eod_bars WHERE instrument_id=%s AND provider=%s
            AND session_date=%s AND published_at<=%s AND first_available_at<=%s
            ORDER BY revision DESC LIMIT 1
        """,(intent["instrument_id"],provider,intent["execution_session"],as_of,as_of))
        row=cursor.fetchone()
    if row is None or row[2]!="valid":
        raise ValueError("qualified execution quote unavailable")
    price,currency,_,published,available=row
    if not close<=published<=available<=as_of:
        raise ValueError("invalid quote provenance")
    rate=eur_rate(connection,currency,day=close.date(),as_of=close,provider=fx_provider)
    price=(Decimal(str(price))*rate).quantize(Decimal("0.00000001"),rounding=ROUND_HALF_EVEN)
    if not price.is_finite() or price<=0:
        raise ValueError("invalid execution price")
    return dict(instrument_id=intent["instrument_id"],quality_status="valid",currency="EUR",
                session=intent["execution_session"],signal_at=signal.isoformat(),
                executed_at=close.isoformat(),available_at=available.isoformat(),
                price=str(price),fee=str(fee))
