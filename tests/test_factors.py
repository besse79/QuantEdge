import unittest
from datetime import date,timedelta
from quantedge.factors import Observation,momentum_score

class FactorsTest(unittest.TestCase):
 def test_future_prices_never_change_historical_score(self):
  rows=[Observation((date(2024,1,1)+timedelta(days=i)).isoformat(),100+i) for i in range(260)]
  asof=rows[-1].day
  before=momentum_score(rows,asof)
  after=momentum_score(rows+[Observation('2026-01-01',100000)],asof)
  self.assertEqual(before,after)
  self.assertFalse(before['paper_eligible'])
 def test_short_history_rejected(self):
  with self.assertRaises(ValueError): momentum_score([], '2026-01-01')
