"""Point-in-time FX conversion using qualified MKD revisions only."""
from decimal import Decimal
from datetime import timedelta

def eur_rate(connection, currency, *, day, as_of, provider, max_age_days=4):
    if currency not in ("EUR", "USD") or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("unsupported currency or cutoff")
    if currency=="EUR":
        return Decimal(1)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT effective_date,rate,quality_status,base
            FROM public.fx_eod
            WHERE ((base='EUR' AND quote=%s) OR (base=%s AND quote='EUR'))
              AND provider=%s AND effective_date<=%s
              AND published_at<=%s AND first_available_at<=%s
            ORDER BY effective_date DESC, base ASC, revision DESC LIMIT 1
        """,(currency,currency,provider,day,as_of,as_of))
        row=cursor.fetchone()
    if row is None:
        raise ValueError("missing qualified FX")
    effective,rate,status,base=row
    rate=Decimal(str(rate))
    if status!="valid" or not rate.is_finite() or rate<=0 or day-effective>timedelta(days=max_age_days):
        raise ValueError("invalid or stale FX")
    return Decimal(1)/rate if base=="EUR" else rate

def convert_to_eur(amount, rate):
    amount,rate=Decimal(str(amount)),Decimal(str(rate))
    if not amount.is_finite() or not rate.is_finite() or amount<0 or rate<=0:
        raise ValueError("invalid conversion")
    return amount*rate
