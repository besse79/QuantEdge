import unittest
from quantedge.paper_risk import allocate

class RiskTests(unittest.TestCase):
    def test_unqualified_and_foreign_currency_blocked(self):
        row=dict(instrument_id="a",close=10,currency="EUR",research_candidate=True,paper_eligible=False)
        self.assertEqual(allocate([row])["proposals"],[])
        self.assertEqual(allocate([dict(row,paper_eligible=True,currency="USD")])["proposals"],[])
    def test_limits_and_duplicate(self):
        row=dict(instrument_id="a",close=30,currency="EUR",research_candidate=True,paper_eligible=True)
        result=allocate([row,row],fee=1)
        self.assertEqual(len(result["proposals"]),1)
        self.assertEqual(result["proposals"][0]["quantity"],3)
        self.assertEqual(result["remaining_cash"],"409")
        self.assertFalse(result["execution_authorized"])
