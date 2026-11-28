import unittest
from fastapi.testclient import TestClient
from quantedge.api import app

class APITests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(TestClient(app).get("/health").json()["mode"], "research_only")
    def test_invalid_request(self):
        self.assertEqual(TestClient(app).post("/research",json={}).status_code,422)

    def test_paper_valuation_defaults_to_ecb(self):
        schema = TestClient(app).get("/openapi.json").json()
        params = schema["paths"]["/paper/valuation"]["get"]["parameters"]
        defaults = {p["name"]: p["schema"]["default"] for p in params}
        self.assertEqual(defaults, {"provider": "yahoo", "fx_provider": "ecb"})
