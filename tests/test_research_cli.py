import unittest
import tempfile
from pathlib import Path
from quantedge.research_cli import parse_sessions

class ResearchCLITests(unittest.TestCase):
    def test_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.json"
            path.write_text('[{"day":"2026-11-16","opens_at":"2026-11-16T09:00:00+01:00","cutoff":"2026-11-16T19:00:00+01:00"}]')
            sessions = parse_sessions(path)
            self.assertEqual(sessions[0].day.isoformat(), "2026-11-16")
            self.assertIsNotNone(sessions[0].cutoff.utcoffset())
            path.write_text("[]")
            with self.assertRaises(ValueError):
                parse_sessions(path)
