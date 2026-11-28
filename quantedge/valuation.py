"""Read-only portfolio valuation; incomplete quotes never imply zero exposure."""
from decimal import Decimal
from .fx import eur_rate, convert_to_eur

def value_portfolio(connection, account, *, day, as_of, provider, fx_provider):
    cash=Decimal(account["cash"])
    total=cash
    positions=[]
    missing=[]
    for position in account["positions"]:
        instrument=position["instrument_id"]
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT session_date,close,currency,quality_status
                FROM public.eod_bars WHERE instrument_id=%s AND provider=%s
                AND session_date<=%s AND published_at<=%s AND first_available_at<=%s
                ORDER BY session_date DESC,revision DESC LIMIT 1
            """,(instrument,provider,day,as_of,as_of))
            row=cursor.fetchone()
        try:
            if row is None:
                raise ValueError("missing quote")
            session,close,currency,status=row
            close=Decimal(str(close))
            if status!="valid" or not close.is_finite() or close<=0 or (day-session).days>4:
                raise ValueError("invalid or stale quote")
            rate=eur_rate(connection,currency,day=day,as_of=as_of,provider=fx_provider)
            value=convert_to_eur(close*position["quantity"],rate)
            total+=value
            positions.append(dict(position,price=str(close),currency=currency,value_eur=str(value),session=str(session)))
        except ValueError as exc:
            missing.append(dict(position,reason=str(exc)))
    return {"cash_eur":str(cash),"equity_eur":None if missing else str(total),
            "positions":positions,"unpriced":missing,"complete":not missing,
            "execution_authorized":False}
