import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from quantedge.valuation import value_portfolio

class ValuationTests(unittest.TestCase):
    def test_complete_and_missing(self):
        c=MagicMock()
        cursor=c.cursor.return_value.__enter__.return_value
        day=date(2026,11,26)
        args=dict(day=day,as_of=datetime(2026,11,26,23,tzinfo=timezone.utc),provider="test",fx_provider="test")
        account={"cash":"400","positions":[{"instrument_id":"a","quantity":2}]}
        cursor.fetchone.return_value=(day,60,"EUR","valid")
        self.assertEqual(value_portfolio(c,account,**args)["equity_eur"],"520")
        cursor.fetchone.return_value=None
        result=value_portfolio(c,account,**args)
        self.assertIsNone(result["equity_eur"])
        self.assertFalse(result["complete"])
