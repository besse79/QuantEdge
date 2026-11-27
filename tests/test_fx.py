import unittest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from quantedge.fx import eur_rate, convert_to_eur

class FxTests(unittest.TestCase):
    def test_conversion_and_staleness(self):
        c=MagicMock()
        cursor=c.cursor.return_value.__enter__.return_value
        day=date(2026,11,26)
        args=dict(day=day,as_of=datetime(2026,11,26,23,tzinfo=timezone.utc),provider="test")
        cursor.fetchone.return_value=(day,Decimal("1.25"),"valid","EUR")
        self.assertEqual(convert_to_eur(100,eur_rate(c,"USD",**args)),80)
        cursor.fetchone.return_value=(day,Decimal(".8"),"valid","USD")
        self.assertEqual(eur_rate(c,"USD",**args),Decimal(".8"))
        for row in (None,(day-timedelta(days=5),1,"valid","EUR"),(day,1,"legacy_unverified","EUR")):
            cursor.fetchone.return_value=row
            with self.assertRaises(ValueError):
                eur_rate(c,"USD",**args)
