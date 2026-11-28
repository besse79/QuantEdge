import unittest
from uuid import uuid4
from quantedge.rebalance import plan_rebalance

class RebalanceTests(unittest.TestCase):
    def test_exit_requires_qualified_signal(self):
        key=str(uuid4())
        account={"positions":[{"instrument_id":key,"quantity":2}]}
        row={"instrument_id":key,"paper_eligible":True,"research_candidate":False,"momentum":-.1}
        plan=plan_rebalance(account,[row],session="2026-11-27")
        self.assertEqual(plan["intents"][0]["side"],"SELL")
        self.assertEqual(plan,plan_rebalance(account,[row],session="2026-11-27"))
        self.assertFalse(plan["execution_authorized"])
        self.assertEqual(plan_rebalance(account,[],session="2026-11-27")["unqualified_holdings"],[key])
