"""Deterministic cross-sectional momentum scanner; no orders or writes."""
from dataclasses import dataclass
from math import isfinite
from .mkd_history import load_history
from .factors import Observation, momentum_score

@dataclass(frozen=True)
class Candidate:
    instrument_id: str
    provider: str
    currency: str

def scan(connection, candidates, *, start, end, as_of):
    ranked, rejected = [], []
    seen = set()
    for candidate in candidates:
        key = (candidate.instrument_id, candidate.provider, candidate.currency)
        if key in seen:
            continue
        seen.add(key)
        try:
            bars = load_history(connection, instrument_id=candidate.instrument_id,
                                provider=candidate.provider, currency=candidate.currency,
                                start=start, end=end, as_of=as_of)
            if bars[-1].day != end:
                raise ValueError("missing latest session")
            score = momentum_score([Observation(b.day.isoformat(), b.close) for b in bars], end.isoformat())["momentum_12_1"]
            if not isfinite(score):
                raise ValueError("nonfinite score")
            ranked.append(dict(instrument_id=candidate.instrument_id, provider=candidate.provider,
                               currency=candidate.currency, momentum=score, close=bars[-1].close,
                               research_candidate=score>0, paper_eligible=False))
        except ValueError as exc:
            rejected.append(dict(instrument_id=candidate.instrument_id, provider=candidate.provider,
                                 currency=candidate.currency, reason=str(exc)))
    ranked.sort(key=lambda r:(-r["momentum"],r["instrument_id"],r["provider"],r["currency"]))
    return {"ranked":ranked,"rejected":rejected,"unique_candidates":len(seen),
            "paper_eligible":False}
