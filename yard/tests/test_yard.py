import tempfile
import unittest
from pathlib import Path

from app import create_app


class YardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = create_app(Path(self.tmp.name) / "t.sqlite3")
        self.client = self.app.test_client()

    def post(self, path, data, key=None):
        headers = {"Idempotency-Key": key} if key else {}
        return self.client.post("/api/" + path, json=data, headers=headers)

    def free(self, berth="Q1"):
        return self.client.get("/api/berths/" + berth).json["free"]

    def test_reserve(self):
        result = self.post("reserves", dict(berth="Q1", metres=40, reference="R1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.free(), 960)

    def test_sequential_retry(self):
        data = dict(berth="Q1", metres=40, reference="R1")
        first = self.post("reserves", data, "retry")
        second = self.post("reserves", data, "retry")
        self.assertEqual(first.json, second.json)
        self.assertEqual(self.free(), 960)

    def test_short(self):
        result = self.post("reserves", dict(berth="Q1", metres=5000, reference="R1"))
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.free(), 1000)

    def test_replenish(self):
        result = self.post("replenish", dict(berth="Q1", metres=25, reference="P1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.free(), 1025)

    def test_release(self):
        self.post("reserves", dict(berth="Q1", metres=40, reference="R1"))
        result = self.post("releases", dict(berth="Q1", reference="R1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.free(), 1000)

    def test_shift(self):
        result = self.post("shifts", dict(source="Q1", target="Q2", metres=30, reference="S1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.free("Q1"), 970)
        self.assertEqual(self.free("Q2"), 1030)

    def test_bad_metres(self):
        result = self.post("reserves", dict(berth="Q1", metres=-1, reference="R1"))
        self.assertEqual(result.status_code, 400)

    def test_log(self):
        self.post("reserves", dict(berth="Q1", metres=10, reference="R1"))
        self.assertEqual(len(self.client.get("/api/movements/Q1").json), 1)
        self.assertEqual(len(self.client.get("/api/log").json), 1)


if __name__ == "__main__":
    unittest.main()
