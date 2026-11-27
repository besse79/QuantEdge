"""Session-by-session MKD research backtest, without a shared future cutoff."""
from dataclasses import dataclass
from datetime import date, datetime
from .backtest import backtest
from .mkd_history import load_history

@dataclass(frozen=True)
class Session:
    day: date
    opens_at: datetime
    cutoff: datetime

def run_mkd_backtest(connection, *, instrument_id, provider, currency,
                     history_start, sessions, signal, initial_cash=500.0,
                     fee_per_order=0.0):
    """Use explicit exchange-local session timestamps and a historical signal callback.

    The callback receives only the immutable history visible at that session's
    cutoff. Execution uses the next session's recorded open, retrospectively.
    Missing session data aborts the run; no real orders are placed.
    """
    sessions = tuple(sessions)
    if not sessions:
        raise ValueError("sessions required")
    if type(history_start) is not date or history_start > sessions[0].day:
        raise ValueError("invalid history start")
    previous = None
    for session in sessions:
        if (type(session.day) is not date or
                any(not isinstance(t, datetime) or t.utcoffset() is None
                    for t in (session.opens_at, session.cutoff)) or
                session.opens_at.date() != session.day or
                session.cutoff.date() != session.day or
                session.opens_at >= session.cutoff or
                (previous is not None and
                 (previous.day >= session.day or previous.cutoff >= session.opens_at))):
            raise ValueError("invalid session chronology")
        previous = session
    bars, signals = [], {}
    for session in sessions:
        history = load_history(connection, instrument_id=instrument_id,
                               provider=provider, currency=currency,
                               start=history_start, end=session.day,
                               as_of=session.cutoff)
        if history[-1].day != session.day:
            raise ValueError("missing qualified execution session")
        bars.append(history[-1])
        target = signal(history, session.day)
        if target is not None:
            if type(target) is not bool:
                raise ValueError("signal must be boolean or None")
            signals[session.day] = target
    return backtest(bars, signals, initial_cash=initial_cash,
                    fee_per_order=fee_per_order)
