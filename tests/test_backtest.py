import unittest
from datetime import date
from quantedge.backtest import Bar, backtest


def d(day):
    return date(2026, 11, day)


class PointInTimeBacktestTests(unittest.TestCase):
    def setUp(self):
        self.bars = [Bar(d(16), 10, 11), Bar(d(17), 20, 21), Bar(d(18), 30, 31)]

    def test_next_open_not_signal_day_close(self):
        result = backtest(self.bars, {d(16): True}, initial_cash=100)
        self.assertEqual([(t.day, t.price, t.quantity) for t in result.trades], [(d(17), 20, 5)])
        self.assertEqual(result.snapshots[0].quantity, 0)

    def test_future_signal_never_executes(self):
        self.assertFalse(backtest(self.bars, {d(19): True}).trades)

    def test_exit_uses_following_open(self):
        result = backtest(self.bars, {d(16): True, d(17): False}, initial_cash=100)
        self.assertEqual([(t.side, t.day) for t in result.trades], [("BUY", d(17)), ("SELL", d(18))])
        self.assertEqual(result.snapshots[-1].cash, 150)

    def test_fees_and_no_negative_cash(self):
        result = backtest(self.bars, {d(16): True}, initial_cash=100, fee_per_order=1)
        self.assertEqual(result.trades[0].quantity, 4)
        self.assertEqual(result.snapshots[1].cash, 19)

    def test_exit_fee_cannot_create_negative_cash(self):
        bars = [Bar(d(16), 10, 10), Bar(d(17), 90, 90), Bar(d(18), 1, 1)]
        with self.assertRaisesRegex(ValueError, "exit fee"):
            backtest(bars, {d(16): True, d(17): False}, initial_cash=100, fee_per_order=10)

    def test_invalid_prices_rejected(self):
        with self.assertRaises(ValueError):
            backtest([Bar(d(16), 0, 10)], {})

    def test_duplicate_or_unsorted_days_rejected(self):
        with self.assertRaises(ValueError):
            backtest([self.bars[1], self.bars[0]], {})

    def test_boolean_cash_and_fee_rejected(self):
        with self.assertRaisesRegex(ValueError, "initial_cash"):
            backtest(self.bars, {}, initial_cash=True)
        with self.assertRaisesRegex(ValueError, "fee_per_order"):
            backtest(self.bars, {}, fee_per_order=False)

    def test_invalid_fee_rejected(self):
        with self.assertRaises(ValueError):
            backtest(self.bars, {}, fee_per_order=-1)

    def test_intraday_bar_rejected(self):
        from datetime import datetime
        with self.assertRaisesRegex(ValueError, "calendar dates"):
            backtest([Bar(datetime(2026, 11, 16, 12), 10, 11)], {})

    def test_intraday_signal_rejected(self):
        from datetime import datetime
        with self.assertRaisesRegex(ValueError, "signals must map dates"):
            backtest(self.bars, {datetime(2026, 11, 16, 12): True})


class PriceTypeTests(unittest.TestCase):
    def test_boolean_price_rejected(self):
        with self.assertRaisesRegex(ValueError, "OHLC"):
            backtest([Bar(d(16), True, 10)], {})


if __name__ == "__main__":
    unittest.main()
