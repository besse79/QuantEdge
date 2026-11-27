import unittest
from datetime import date
from quantedge.membership_import import parse_export

class MembershipTests(unittest.TestCase):
    def test_dated_export(self):
        raw=b"as_of,symbol,mic,currency\n2026-11-27,ABC,XPAR,EUR\n"
        self.assertEqual(parse_export(raw,date(2026,11,27))[0]["currency"],"EUR")
        with self.assertRaises(ValueError):
            parse_export(raw,date(2026,11,26))
        with self.assertRaises(ValueError):
            parse_export(raw+b"2026-11-27,ABC,XPAR,EUR\n",date(2026,11,27))
