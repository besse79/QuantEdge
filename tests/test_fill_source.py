import unittest
from datetime import datetime
from unittest.mock import MagicMock
from quantedge.fill_source import load_fill

class FillTests(unittest.TestCase):
    def test_qualified_close_and_missing(self):
        c=MagicMock()
        cursor=c.cursor.return_value.__enter__.return_value
        t=datetime.fromisoformat("2026-11-27T18:00:00+00:00")
        intent=dict(instrument_id="a",signal_at="2026-11-26T20:00:00+00:00",session_close="2026-11-27T16:30:00+00:00",execution_session="2026-11-27")
        cursor.fetchone.return_value=(10,"EUR","valid",t,t)
        self.assertEqual(load_fill(c,intent,provider="test",fx_provider="test",as_of=t)["price"],"10.00000000")
        cursor.fetchone.return_value=None
        with self.assertRaises(ValueError):
            load_fill(c,intent,provider="test",fx_provider="test",as_of=t)
