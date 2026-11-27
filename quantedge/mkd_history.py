"""Read-only MKD point-in-time history adapter (DB-API PostgreSQL connection)."""
from datetime import date, datetime, timezone
from math import isfinite
from uuid import UUID
from .backtest import Bar

SQL = """
SELECT session_date, open, close, currency, quality_status,
       published_at, first_available_at
FROM (
    SELECT DISTINCT ON (session_date) session_date, open, close, currency,
           quality_status, published_at, first_available_at
    FROM public.eod_bars
    WHERE instrument_id = %s AND provider = %s
      AND session_date BETWEEN %s AND %s
      AND published_at <= %s AND first_available_at <= %s
    ORDER BY session_date, revision DESC
) AS history
ORDER BY session_date
"""

def load_history(connection, *, instrument_id, provider, currency, start, end, as_of):
    """Load a single instrument/provider/currency as known at a fixed cutoff.

    Use a dedicated read-only MKD connection. A fixed cutoff is suitable for
    a snapshot, not for generating signals at earlier historical cutoffs.
    """
    instrument_id = UUID(str(instrument_id))
    if type(start) is not date or type(end) is not date or start > end:
        raise ValueError("invalid session range")
    if not isinstance(as_of, datetime) or as_of.utcoffset() is None or end > as_of.date() or as_of > datetime.now(timezone.utc):
        raise ValueError("invalid point-in-time cutoff")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("provider required")
    if currency not in ("EUR", "USD"):
        raise ValueError("invalid currency")
    with connection.cursor() as cursor:
        cursor.execute(SQL, (str(instrument_id), provider, start, end, as_of, as_of))
        rows = cursor.fetchall()
    if not rows:
        raise ValueError("no qualified history available")
    bars = []
    for day, opening, closing, row_currency, quality, published, available in rows:
        if (quality != "valid" or row_currency != currency or
                not isinstance(published, datetime) or published.utcoffset() is None or
                not isinstance(available, datetime) or available.utcoffset() is None or
                not published <= available <= as_of or type(day) is not date or
                not start <= day <= end or day > published.date()):
            raise ValueError("unqualified MKD history")
        if bars and day <= bars[-1].day:
            raise ValueError("duplicate or unordered MKD session")
        prices = (float(opening), float(closing))
        if not all(isfinite(p) and p > 0 for p in prices):
            raise ValueError("invalid MKD prices")
        bars.append(Bar(day, *prices))
    return tuple(bars)
