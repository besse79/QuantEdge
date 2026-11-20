"""Deterministic, historical-only quantitative factor scoring (no network calls)."""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class Observation:
    day: str
    close: float


def momentum_score(history: list[Observation], as_of: str) -> dict:
    """12-1 month momentum, using only prices known at as_of.

    Requires at least 253 trading-day observations; last 21 days skipped.
    This is research-only, not a trading authorization.
    """
    rows = sorted((x for x in history if x.day <= as_of), key=lambda x: x.day)
    if len(rows) < 253 or len({x.day for x in rows}) != len(rows):
        raise ValueError('insufficient or duplicate history')
    if any(not isfinite(x.close) or x.close <= 0 for x in rows):
        raise ValueError('invalid close')
    start, end = rows[-253], rows[-22]
    return {'as_of': as_of, 'start_day': start.day, 'end_day': end.day,
            'momentum_12_1': end.close / start.close - 1,
            'paper_eligible': False, 'reason': 'RESEARCH_ONLY_UNVERIFIED_PIT'}
