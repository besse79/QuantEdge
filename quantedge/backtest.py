"""Deterministic, long-only, point-in-time daily PAPER backtest.

A signal dated t is executed at the next available bar's open (t+1).
Only signals with a timestamp strictly earlier than the execution bar may trade.
Prices and signals must be sorted, unique, finite, and positive where applicable.
No network, database access, or real orders.
"""
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Bar:
    day: date
    open: float
    close: float


@dataclass(frozen=True)
class Trade:
    day: date
    side: str
    quantity: int
    price: float
    fee: float


@dataclass(frozen=True)
class Snapshot:
    day: date
    cash: float
    quantity: int
    equity: float


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    snapshots: tuple[Snapshot, ...]


def backtest(
    bars: Sequence[Bar],
    signals: Mapping[date, bool],
    *,
    initial_cash: float = 500.0,
    fee_per_order: float = 0.0,
) -> BacktestResult:
    """Run one-instrument all-in PAPER simulation with next-open execution.

    Signals are boolean target exposures, observed only after their day's close.
    Missing signal means retain the current exposure. Fractional shares are not
    supported. Buy quantity is limited by cash including the transaction fee.
    """
    if isinstance(initial_cash, bool) or not isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be finite and positive")
    if isinstance(fee_per_order, bool) or not isfinite(fee_per_order) or fee_per_order < 0:
        raise ValueError("fee_per_order must be finite and nonnegative")
    days = [bar.day for bar in bars]
    if any(type(day) is not date for day in days):
        raise ValueError("bars must use calendar dates")
    if days != sorted(set(days)):
        raise ValueError("bars must have strictly increasing unique dates")
    for bar in bars:
        if any(isinstance(p, bool) or not isfinite(p) or p <= 0 for p in (bar.open, bar.close)):
            raise ValueError("OHLC prices must be finite and positive")
    if any(type(day) is not date or not isinstance(value, bool) for day, value in signals.items()):
        raise ValueError("signals must map dates to booleans")
    cash, quantity = float(initial_cash), 0
    trades: list[Trade] = []
    snapshots: list[Snapshot] = []
    pending = iter(sorted(signals.items()))
    next_signal = next(pending, None)
    for bar in bars:
        # Consume only signals published before this opening, including gaps.
        target = None
        while next_signal is not None and next_signal[0] < bar.day:
            target = next_signal[1]
            next_signal = next(pending, None)
        if target is not None:
            if target and quantity == 0:
                raw_amount = (cash - fee_per_order) // bar.open
                if not isfinite(raw_amount):
                    raise ValueError("nonfinite position quantity")
                amount = max(0, int(raw_amount))
                if amount:
                    cost = amount * bar.open + fee_per_order
                    cash -= cost
                    quantity = amount
                    trades.append(Trade(bar.day, "BUY", amount, bar.open, fee_per_order))
            elif not target and quantity:
                if cash + quantity * bar.open < fee_per_order:
                    raise ValueError("insufficient cash to cover exit fee")
                cash += quantity * bar.open - fee_per_order
                trades.append(Trade(bar.day, "SELL", quantity, bar.open, fee_per_order))
                quantity = 0
        equity = cash + quantity * bar.close
        if not isfinite(cash) or not isfinite(equity):
            raise ValueError("nonfinite portfolio valuation")
        snapshots.append(Snapshot(bar.day, cash, quantity, equity))
    return BacktestResult(tuple(trades), tuple(snapshots))
