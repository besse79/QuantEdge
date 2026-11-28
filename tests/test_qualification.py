import unittest
from uuid import uuid4
from quantedge.qualification import qualify

class QualificationTests(unittest.TestCase):
    def test_complete_universe(self):
        key=str(uuid4())
        report={"ranked":[dict(instrument_id=key,currency="EUR",momentum=.1,close=10)],"rejected":[]}
        with self.assertRaises(ValueError):
            qualify(report,[key])
        with self.assertRaises(ValueError):
            qualify(report,[key,str(uuid4())],universe_verified=True)
        self.assertTrue(qualify(report,[key],universe_verified=True)[0]["paper_eligible"])
