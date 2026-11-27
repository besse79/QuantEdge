"""Read-only research API. No order placement or database mutations."""
import os
from dataclasses import asdict
from datetime import date, datetime, timezone
from uuid import UUID
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .calendar import exchange_sessions
from .research import run_momentum

app = FastAPI(title="QuantEdge Research")

class ResearchRequest(BaseModel):
    instrument_id: UUID
    provider: str = Field(min_length=1, max_length=40)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    calendar: str = Field(pattern=r"^[A-Z0-9]{4}$")
    history_start: date
    start: date
    end: date
    cash: float = Field(default=500, gt=0, le=1000000, allow_inf_nan=False)
    fee: float = Field(default=0, ge=0, le=1000, allow_inf_nan=False)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "research_only"}

@app.post("/research")
def research(request: ResearchRequest):
    if not request.history_start <= request.start <= request.end <= date.today() or (request.end-request.history_start).days > 3653:
        raise HTTPException(422, "Invalid research date range")
    import psycopg
    try:
        sessions = exchange_sessions(request.calendar, request.start, request.end)
        with psycopg.connect(os.environ["MKD_DSN"], connect_timeout=5,
                             options="-c statement_timeout=15000") as connection:
            connection.read_only = True
            connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            result, metrics = run_momentum(connection, instrument_id=request.instrument_id,
                provider=request.provider, currency=request.currency,
                history_start=request.history_start, sessions=sessions,
                initial_cash=request.cash, fee_per_order=request.fee)
        return {"metrics": metrics, "result": asdict(result), "initial_cash": request.cash}
    except (ValueError, KeyError):
        raise HTTPException(422, "Invalid request or insufficient qualified history") from None
    except psycopg.Error:
        raise HTTPException(503, "MarketDataHub unavailable") from None

@app.get("/instruments")
def instruments():
    import psycopg
    try:
        with psycopg.connect(os.environ["MKD_DSN"], connect_timeout=5,
                             options="-c statement_timeout=15000") as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT i.id, i.name, x.symbol, x.provider, x.currency, x.mic
                    FROM public.instruments i
                    JOIN public.instrument_identifiers x ON x.instrument_id=i.id
                    WHERE i.status='active' AND x.valid_from <= CURRENT_TIMESTAMP
                      AND (x.valid_to IS NULL OR x.valid_to > CURRENT_TIMESTAMP)
                    ORDER BY x.symbol, x.provider, x.mic, i.id, x.currency, i.name
                """)
                return [dict(zip(("instrument_id","name","symbol","provider","currency","mic"), row))
                        for row in cursor.fetchall()]
    except (psycopg.Error, KeyError):
        raise HTTPException(503, "MarketDataHub unavailable") from None

class ScanRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    mic: str = Field(pattern=r"^[A-Z0-9]{4}$")
    start: date
    end: date

@app.post("/scan")
def daily_scan(request: ScanRequest):
    from .scanner import Candidate, scan
    import psycopg
    if not request.start <= request.end <= date.today() or (request.end-request.start).days > 1096:
        raise HTTPException(422, "Invalid scan range")
    try:
        session = exchange_sessions(request.mic, request.end, request.end)[0]
        if session.cutoff > datetime.now(timezone.utc):
            raise ValueError("session cutoff not reached")
        with psycopg.connect(os.environ["MKD_DSN"], connect_timeout=5,
                             options="-c statement_timeout=15000") as connection:
            connection.read_only = True
            connection.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT i.id, x.provider, x.currency
                    FROM public.instruments i JOIN public.instrument_identifiers x
                    ON x.instrument_id=i.id
                    WHERE x.provider=%s AND x.mic=%s
                      AND x.valid_from <= %s AND (x.valid_to IS NULL OR x.valid_to > %s)
                    ORDER BY i.id, x.provider, x.currency
                """, (request.provider, request.mic, session.cutoff, session.cutoff))
                candidates = [Candidate(str(i), p, c) for i,p,c in cursor.fetchall()]
            return scan(connection, candidates, start=request.start, end=request.end,
                        as_of=session.cutoff)
    except (ValueError, KeyError):
        raise HTTPException(422, "Invalid scan or unavailable session") from None
    except psycopg.Error:
        raise HTTPException(503, "MarketDataHub unavailable") from None
