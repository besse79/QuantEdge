"""Research-only momentum strategy and performance reporting."""
from math import sqrt, isfinite
from statistics import mean, stdev
from .factors import Observation, momentum_score
from .mkd_backtest import run_mkd_backtest

def momentum_signal(history, day):
    if len(history) < 253:
        return None
    score = momentum_score([Observation(b.day.isoformat(), b.close) for b in history], day.isoformat())
    return score["momentum_12_1"] > 0

def performance(result, initial_cash):
    if not isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("invalid initial cash")
    values = [initial_cash] + [s.equity for s in result.snapshots]
    if any(not isfinite(v) or v <= 0 for v in values):
        raise ValueError("invalid equity series")
    peak, drawdown = initial_cash, 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = max(drawdown, 1 - value / peak)
    returns = [b / a - 1 for a, b in zip(values, values[1:])]
    volatility = stdev(returns) if len(returns) > 1 else 0
    return {"total_return": values[-1] / initial_cash - 1,
            "max_drawdown": drawdown,
            "sharpe_zero_rf_252": sqrt(252) * mean(returns) / volatility if volatility else None,
            "trade_count": len(result.trades), "paper_eligible": False}

def run_momentum(connection, **kwargs):
    result = run_mkd_backtest(connection, signal=momentum_signal, **kwargs)
    return result, performance(result, kwargs.get("initial_cash", 500.0))
