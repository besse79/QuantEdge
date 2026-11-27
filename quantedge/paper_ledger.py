"""Isolated PostgreSQL PAPER ledger. Explicit initialization; no MKD writes."""
from decimal import Decimal
from uuid import UUID

SCHEMA = """
CREATE TABLE IF NOT EXISTS qe_paper_account (
 id integer PRIMARY KEY CHECK(id=1),
 cash numeric(24,8) NOT NULL CHECK(cash>=0)
);
CREATE TABLE IF NOT EXISTS qe_paper_trade (
 event_id uuid PRIMARY KEY,
 instrument_id uuid NOT NULL,
 side text NOT NULL CHECK(side IN ('BUY','SELL')),
 quantity bigint NOT NULL CHECK(quantity>0),
 price numeric(24,8) NOT NULL CHECK(price>0),
 fee numeric(24,8) NOT NULL CHECK(fee>=0),
 executed_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO qe_paper_account(id,cash) VALUES(1,500) ON CONFLICT DO NOTHING;
"""

def initialize(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        if cursor.fetchone()[0] != "quantedge_paper":
            raise ValueError("isolated PAPER database required")
        cursor.execute(SCHEMA)

def snapshot(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        if cursor.fetchone()[0] != "quantedge_paper":
            raise ValueError("isolated PAPER database required")
        cursor.execute("SELECT cash FROM qe_paper_account WHERE id=1")
        row=cursor.fetchone()
        if row is None:
            raise ValueError("PAPER account not initialized")
        cursor.execute("""
            SELECT instrument_id, SUM(CASE WHEN side='BUY' THEN quantity ELSE -quantity END)
            FROM qe_paper_trade GROUP BY instrument_id
            HAVING SUM(CASE WHEN side='BUY' THEN quantity ELSE -quantity END)<>0
            ORDER BY instrument_id
        """)
        return {"cash":str(row[0]),"currency":"EUR",
                "positions":[{"instrument_id":str(i),"quantity":int(q)} for i,q in cursor.fetchall()],
                "execution_authorized":False}

def calculate_cash(cash, held, side, quantity, price, fee):
    cash,price,fee=(Decimal(str(v)) for v in (cash,price,fee))
    if not all(v.is_finite() for v in (cash,price,fee)) or cash<0 or price<=0 or fee<0:
        raise ValueError("invalid monetary values")
    if type(quantity) is not int or quantity<=0 or type(held) is not int or held<0:
        raise ValueError("invalid quantity")
    if side=="BUY":
        result=cash-quantity*price-fee
    elif side=="SELL" and quantity<=held:
        result=cash+quantity*price-fee
    else:
        raise ValueError("invalid side or insufficient holdings")
    if result<0:
        raise ValueError("insufficient cash")
    return result
