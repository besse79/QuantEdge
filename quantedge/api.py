"""Read-only research API. No order placement or database mutations."""
import os
from dataclasses import asdict
from datetime import date
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
        return {"metrics": metrics, "result": asdict(result)}
    except (ValueError, KeyError):
        raise HTTPException(422, "Invalid request or insufficient qualified history") from None
    except psycopg.Error:
        raise HTTPException(503, "MarketDataHub unavailable") from None
