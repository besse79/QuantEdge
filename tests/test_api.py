import unittest
from fastapi.testclient import TestClient
from quantedge.api import app

class APITests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(TestClient(app).get("/health").json()["mode"], "research_only")
    def test_invalid_request(self):
        self.assertEqual(TestClient(app).post("/research",json={}).status_code,422)
