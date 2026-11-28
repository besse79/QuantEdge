import unittest
from unittest.mock import MagicMock
from quantedge.paper_ledger import initialize, calculate_cash

class LedgerTests(unittest.TestCase):
    def test_cash(self):
        self.assertEqual(calculate_cash(500,0,"BUY",3,30,1),409)
        self.assertEqual(calculate_cash(409,3,"SELL",3,35,1),513)
    def test_block_invalid(self):
        for args in [(500,0,"SELL",1,10,0),(500,0,"BUY",51,10,0),(500,0,"BUY",True,10,0)]:
            with self.assertRaises(ValueError):
                calculate_cash(*args)
    def test_wrong_database(self):
        connection=MagicMock()
        cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value=("market_data_hub",)
        with self.assertRaises(ValueError):
            initialize(connection)
        self.assertEqual(cursor.execute.call_count,1)
