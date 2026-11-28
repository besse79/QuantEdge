"""Read-only inventory of eligible MKD listings; not a membership certification."""
import json
import os
from datetime import datetime, timezone
import psycopg

def inventory(connection, cutoff):
    with connection.cursor() as c:
        c.execute("""SELECT DISTINCT x.symbol,x.mic,x.currency
        FROM public.instrument_identifiers x JOIN public.instruments i ON i.id=x.instrument_id
        WHERE x.provider='yahoo' AND i.status='active' AND x.currency IN ('EUR','USD')
        AND x.valid_from<=%s AND (x.valid_to IS NULL OR x.valid_to>%s)
        ORDER BY x.mic,x.symbol,x.currency""",(cutoff,cutoff))
        rows=[dict(zip(("symbol","mic","currency"),r)) for r in c.fetchall()]
    return {"as_of":cutoff.isoformat(),"listings":rows,"membership_verified":False}

def main():
    with psycopg.connect(os.environ["MKD_DSN"]) as c:
        c.read_only=True
        print(json.dumps(inventory(c,datetime.now(timezone.utc)),allow_nan=False))

if __name__=="__main__":
    main()
