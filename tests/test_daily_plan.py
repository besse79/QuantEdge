import unittest
from quantedge.daily_plan import build_plan

class PlanTests(unittest.TestCase):
    def test_research_never_executes(self):
        row=dict(instrument_id="a",provider="yahoo",currency="EUR",momentum=.2,close=10,research_candidate=True,paper_eligible=False)
        plan=build_plan({"XPAR":{"ranked":[row]}},{"cash":"500","positions":[]})
        self.assertEqual(plan["proposals"],[])
        self.assertFalse(plan["execution_authorized"])
    def test_existing_positions_block_new_allocation(self):
        self.assertEqual(build_plan({},{"cash":"500","positions":[{"instrument_id":"a","quantity":1}]})["proposals"],[])
