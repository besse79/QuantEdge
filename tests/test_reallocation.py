import unittest
from uuid import uuid4
from quantedge.reallocation import rebalance

class ReallocationTests(unittest.TestCase):
    def test_sell_funds_buy(self):
        a,b=str(uuid4()),str(uuid4())
        account={"cash":"0","positions":[{"instrument_id":a,"quantity":50}]}
        rows=[dict(instrument_id=a,paper_eligible=True,research_candidate=False,momentum=-1),dict(instrument_id=b,paper_eligible=True,research_candidate=True,momentum=1)]
        orders=rebalance(account,rows,{a:10,b:10},session="2026-11-27")
        self.assertEqual([(o["side"],o["quantity"]) for o in orders],[("SELL",50),("BUY",10)])
        with self.assertRaises(ValueError):
            rebalance(account,rows[1:],{b:10},session="2026-11-27")
