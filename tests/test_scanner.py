import unittest
from datetime import date, timedelta, datetime, timezone
from unittest.mock import patch
from quantedge.backtest import Bar
from quantedge.scanner import Candidate, scan

class ScannerTests(unittest.TestCase):
    @patch("quantedge.scanner.load_history")
    def test_ranking_deduplication_and_rejections(self, load):
        start=date(2025,1,1)
        end=start+timedelta(days=252)
        def history(mult):
            return tuple(Bar(start+timedelta(days=i),1+i*mult,1+i*mult) for i in range(253))
        load.side_effect=[history(1),history(2),ValueError("unqualified")]
        a,b,c=[Candidate(x,"test","EUR") for x in ("a","b","c")]
        result=scan(None,[a,a,b,c],start=start,end=end,as_of=datetime(2026,1,1,tzinfo=timezone.utc))
        self.assertEqual([x["instrument_id"] for x in result["ranked"]],["b","a"])
        self.assertEqual(result["unique_candidates"],3)
        self.assertEqual(result["rejected"][0]["instrument_id"],"c")
        self.assertFalse(result["paper_eligible"])
