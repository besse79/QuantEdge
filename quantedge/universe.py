"""Compare independently sourced membership manifests against MKD identifiers."""
from datetime import date
from uuid import UUID

def verify_membership(connection, manifest, *, day, provider):
    if manifest["as_of"]!=day.isoformat() or set(manifest["markets"])!={"SP500","EURONEXT"}:
        raise ValueError("missing dated market membership")
    expected=set()
    with connection.cursor() as c:
        for market, members in manifest["markets"].items():
            if not members or (market=="SP500" and len(members)<500):
                raise ValueError("incomplete membership")
            seen=set()
            for member in members:
                if member["currency"] not in ("EUR","USD"):
                    continue
                key=(member["symbol"],member["mic"])
                if key in seen:
                    raise ValueError("duplicate membership")
                seen.add(key)
                c.execute("""SELECT instrument_id FROM public.instrument_identifiers
                WHERE provider=%s AND symbol=%s AND mic=%s
                AND currency=%s AND valid_from<=%s AND (valid_to IS NULL OR valid_to>%s)""",
                (provider,*key,member['currency'],day,day))
                rows=c.fetchall()
                if len(rows)!=1:
                    raise ValueError("missing or ambiguous identifier: "+str(key))
                expected.add(str(UUID(str(rows[0][0]))))
    if not expected:
        raise ValueError('empty EUR/USD universe')
    return expected
