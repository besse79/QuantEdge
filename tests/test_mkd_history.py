import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from quantedge.mkd_history import load_history

class MKDHistoryTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.cutoff = datetime(2026, 11, 20, tzinfo=timezone.utc)
        self.day = date(2026, 11, 18)
        self.published = datetime(2026, 11, 18, 22, tzinfo=timezone.utc)
        self.row = (self.day, 10, 11, "EUR", "valid", self.published, self.published)
        self.args = dict(instrument_id="00000000-0000-0000-0000-000000000001",
                         provider="test", currency="EUR", start=self.day,
                         end=self.day, as_of=self.cutoff)

    def test_valid_history(self):
        self.cursor.fetchall.return_value = [self.row]
        self.assertEqual(load_history(self.connection, **self.args)[0].close, 11)
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("revision DESC", sql)
        self.assertIn("first_available_at <= %s", sql)
        self.assertEqual(params[-2:], (self.cutoff, self.cutoff))
        self.connection.commit.assert_not_called()

    def test_unqualified_history(self):
        for status in ("legacy_unverified", "staged_unverified"):
            self.cursor.fetchall.return_value = [self.row[:4] + (status,) + self.row[5:]]
            with self.assertRaisesRegex(ValueError, "unqualified"):
                load_history(self.connection, **self.args)

    def test_future_availability(self):
        self.cursor.fetchall.return_value = [self.row[:-1] + (datetime(2026, 11, 21, tzinfo=timezone.utc),)]
        with self.assertRaises(ValueError):
            load_history(self.connection, **self.args)

    def test_empty_history(self):
        self.cursor.fetchall.return_value = []
        with self.assertRaises(ValueError):
            load_history(self.connection, **self.args)

    def test_duplicate_session(self):
        self.cursor.fetchall.return_value = [self.row, self.row]
        with self.assertRaises(ValueError):
            load_history(self.connection, **self.args)

    def test_non_trading_currencies_rejected_before_query(self):
        for currency in ("GBP", "CHF", "JPY", "GBX"):
            with self.assertRaisesRegex(ValueError, "currency"):
                load_history(self.connection, **{**self.args, "currency": currency})
        self.cursor.execute.assert_not_called()

    def test_future_cutoff_rejected_before_query(self):
        from datetime import timedelta
        future = datetime.now(timezone.utc) + timedelta(days=1)
        with self.assertRaisesRegex(ValueError, "cutoff"):
            load_history(self.connection, **{**self.args, "as_of": future})
        self.cursor.execute.assert_not_called()

    def test_malformed_prices_rejected(self):
        for bad in (None, True, False, 'invalid', float('nan'), float('inf'), 0, -1):
            for index in (1, 2):
                with self.subTest(price=bad, index=index):
                    row = list(self.row)
                    row[index] = bad
                    self.cursor.fetchall.return_value = [tuple(row)]
                    with self.assertRaisesRegex(ValueError, 'invalid MKD prices'):
                        load_history(self.connection, **self.args)
        self.connection.commit.assert_not_called()
