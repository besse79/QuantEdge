import unittest
from datetime import date
from unittest.mock import patch
from quantedge.calendar import exchange_sessions

class CalendarTests(unittest.TestCase):
    def test_invalid_range(self):
        with self.assertRaises(ValueError):
            exchange_sessions("XNYS", date(2026,11,20), date(2026,11,19))

    def test_actual_calendar_if_installed(self):
        try:
            import exchange_calendars
        except ImportError:
            self.skipTest("optional exchange_calendars not installed")
        sessions = exchange_sessions("XNYS", date(2026,11,25), date(2026,11,27))
        self.assertEqual([s.day.day for s in sessions], [25,27])
        self.assertEqual(sessions[1].cutoff.hour, 15)
