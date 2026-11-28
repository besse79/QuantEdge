import unittest
from unittest.mock import MagicMock, patch
from quantedge.paper_execution import execute_batch

class ExecutionTests(unittest.TestCase):
    def test_execution_gate(self):
        c=MagicMock()
        with self.assertRaises(ValueError):
            execute_batch(c,[],{})
        c.transaction.assert_not_called()
    @patch("quantedge.paper_execution.record_simulated_trade")
    def test_qualified_fill(self,record):
        c=MagicMock()
        intent=dict(event_id="a",instrument_id="b",side="BUY",quantity=2,execution_session="2026-11-27")
        fill=dict(instrument_id="b",quality_status="valid",currency="EUR",session="2026-11-27",signal_at="2026-11-26T20:00:00+00:00",executed_at="2026-11-27T09:00:00+00:00",available_at="2026-11-27T09:01:00+00:00",price=10,fee=1)
        execute_batch(c,[intent],{"a":fill},authorized=True)
        record.assert_called_once()
        with self.assertRaises(ValueError):
            execute_batch(c,[intent],{"a":dict(fill,quality_status="legacy_unverified")},authorized=True)
