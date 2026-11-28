import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch
from quantedge.backtest import Bar
from quantedge.mkd_backtest import Session, run_mkd_backtest

def session(day):
    return Session(date(2026,11,day), datetime(2026,11,day,9,tzinfo=timezone.utc),
                   datetime(2026,11,day,22,tzinfo=timezone.utc))

class MKDBacktestTests(unittest.TestCase):
    def setUp(self):
        self.sessions = [session(16), session(17)]
        self.args = dict(instrument_id="test", provider="test", currency="EUR",
                         history_start=date(2026,11,1), sessions=self.sessions,
                         initial_cash=100)

    @patch("quantedge.mkd_backtest.load_history")
    def test_independent_cutoffs_and_next_open(self, load):
        first = Bar(self.sessions[0].day, 10, 11)
        second = Bar(self.sessions[1].day, 20, 21)
        load.side_effect = [(first,), (Bar(first.day, 99, 99), second)]
        seen = []
        def signal(history, day):
            seen.append(history)
            return True
        result = run_mkd_backtest(None, signal=signal, **self.args)
        self.assertEqual(seen[0], (first,))
        self.assertEqual([c.kwargs["as_of"] for c in load.call_args_list],
                         [s.cutoff for s in self.sessions])
        self.assertEqual([(t.day,t.price,t.quantity) for t in result.trades],
                         [(second.day,20,5)])
        self.assertEqual(result.snapshots[0].equity,100)

    @patch("quantedge.mkd_backtest.load_history")
    def test_missing_session_aborts(self, load):
        load.return_value = (Bar(date(2026,11,15),10,11),)
        with self.assertRaisesRegex(ValueError,"missing qualified"):
            run_mkd_backtest(None, signal=lambda *_: True, **self.args)

    @patch("quantedge.mkd_backtest.load_history")
    def test_invalid_chronology_before_query(self, load):
        self.args["sessions"] = list(reversed(self.sessions))
        with self.assertRaises(ValueError):
            run_mkd_backtest(None, signal=lambda *_: True, **self.args)
        load.assert_not_called()
