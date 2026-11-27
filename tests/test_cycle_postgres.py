import os
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from uuid import uuid4
from quantedge.paper_cycle import run_cycle
from quantedge.paper_ledger import initialize, snapshot

@unittest.skipUnless(os.environ.get("QE_TEST_PAPER_DSN"), "disposable PostgreSQL required")
class CycleIntegration(unittest.TestCase):
    def test_buy_duplicate_sell(self):
        import psycopg
        key=str(uuid4())
        with psycopg.connect(os.environ["QE_TEST_PAPER_DSN"]) as paper:
            initialize(paper)
            before=snapshot(paper)
            for day,positive in [("2026-01-05",True),("2026-01-06",False)]:
                report={"ranked":[dict(instrument_id=key,provider="yahoo",currency="EUR",momentum=1 if positive else -1,close=10,research_candidate=positive)],"rejected":[]}
                sessions={key:{"execution_session":day}}
                fill=dict(instrument_id=key,currency="EUR",quality_status="valid",price=10,fee=0,session=day,signal_at="2026-01-02T18:00:00+00:00",executed_at=day+"T16:00:00+00:00",available_at=day+"T18:00:00+00:00")
                with patch("quantedge.paper_cycle.load_fill",return_value=fill):
                    args=dict(as_of=datetime(2026,1,7,tzinfo=timezone.utc),fx_provider="yahoo",universe_verified=True,authorized=True)
                    result=run_cycle(None,paper,report,{key},sessions,**args)
                    self.assertEqual(result["status"],"recorded")
                    self.assertEqual(result["orders"][0]["side"],"BUY" if positive else "SELL")
                    self.assertEqual(run_cycle(None,paper,report,{key},sessions,**args)["status"],"duplicate")
            self.assertEqual(snapshot(paper),before)
            paper.rollback()
