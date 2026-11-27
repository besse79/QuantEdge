import unittest
from unittest.mock import MagicMock
from quantedge.paper_cycle import run_cycle

class CycleTests(unittest.TestCase):
    def test_disabled_cycle_has_no_database_effect(self):
        mkd,paper=MagicMock(),MagicMock()
        with self.assertRaises(ValueError):
            run_cycle(mkd,paper,{},[],{},as_of=None,fx_provider="test")
        paper.transaction.assert_not_called()
        mkd.cursor.assert_not_called()
