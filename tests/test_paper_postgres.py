import os
import unittest
from uuid import uuid4
from quantedge.paper_ledger import initialize, snapshot, record_simulated_trade

@unittest.skipUnless(os.environ.get("QE_TEST_PAPER_DSN"),"disposable PostgreSQL required")
class PostgresLedgerTests(unittest.TestCase):
    def test_roundtrip(self):
        import psycopg
        with psycopg.connect(os.environ["QE_TEST_PAPER_DSN"]) as conn:
            initialize(conn)
            before=snapshot(conn)
            instrument,event=uuid4(),uuid4()
            args=dict(event_id=event,instrument_id=instrument,side="BUY",quantity=2,price=10,fee=1,authorized=True)
            self.assertEqual(record_simulated_trade(conn,**args),"recorded")
            self.assertEqual(record_simulated_trade(conn,**args),"duplicate")
            self.assertEqual(float(snapshot(conn)["cash"]),float(before["cash"])-21)
            with self.assertRaises(ValueError):
                record_simulated_trade(conn,**dict(args,quantity=3))
            self.assertEqual(record_simulated_trade(conn,event_id=uuid4(),instrument_id=instrument,side="SELL",quantity=2,price=11,fee=1,authorized=True),"recorded")
            self.assertEqual(snapshot(conn),before)
            conn.rollback()
