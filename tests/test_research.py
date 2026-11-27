import unittest
from datetime import date, timedelta
from quantedge.backtest import Bar, Snapshot, BacktestResult
from quantedge.research import momentum_signal, performance

class ResearchTests(unittest.TestCase):
    def test_momentum_warmup_and_direction(self):
        day = date(2025,1,1)
        bars = [Bar(day + timedelta(days=i), i+1, i+1) for i in range(253)]
        self.assertIsNone(momentum_signal(bars[:-1], bars[-2].day))
        self.assertTrue(momentum_signal(bars, bars[-1].day))
        falling = [Bar(b.day, 300-i, 300-i) for i,b in enumerate(bars)]
        self.assertFalse(momentum_signal(falling, falling[-1].day))

    def test_performance(self):
        result = BacktestResult((), tuple(Snapshot(date(2026,1,i), v, 0, v)
                                         for i,v in enumerate([120,90,110],1)))
        report = performance(result, 100)
        self.assertAlmostEqual(report["total_return"], .1)
        self.assertAlmostEqual(report["max_drawdown"], .25)
        self.assertFalse(report["paper_eligible"])
        self.assertIsNotNone(report["sharpe_zero_rf_252"])

    def test_flat_equity(self):
        self.assertIsNone(performance(BacktestResult((),()),500)["sharpe_zero_rf_252"])
