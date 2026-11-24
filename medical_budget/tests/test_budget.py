import tempfile
import unittest
from pathlib import Path

from app import create_app


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = create_app(Path(self.tmp.name) / "test.sqlite3")
        self.client = self.app.test_client()

    def post(self, path, data, key=None):
        headers = {"Idempotency-Key": key} if key else {}
        return self.client.post("/api/" + path, json=data, headers=headers)

    def balance(self, employee="E001"):
        return self.client.get("/api/accounts/" + employee).json["balance"]

    def test_claim(self):
        result = self.post("claims", dict(employee="E001", amount=2000, reference="C1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.balance(), 98000)

    def test_sequential_retry(self):
        data = dict(employee="E001", amount=2000, reference="C1")
        first = self.post("claims", data, "retry")
        second = self.post("claims", data, "retry")
        self.assertEqual(first.json, second.json)
        self.assertEqual(self.balance(), 98000)

    def test_insufficient_balance(self):
        result = self.post("claims", dict(employee="E001", amount=200000, reference="C1"))
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.balance(), 100000)

    def test_topup(self):
        result = self.post("topups", dict(employee="E001", amount=3000, reference="T1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.balance(), 103000)

    def test_reversal(self):
        self.post("claims", dict(employee="E001", amount=1000, reference="C1"))
        result = self.post("reversals", dict(employee="E001", reference="C1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.balance(), 100000)

    def test_transfer(self):
        result = self.post("transfers", dict(source="E001", target="E002",
                                              amount=1000, reference="X1"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.balance("E001"), 99000)
        self.assertEqual(self.balance("E002"), 101000)

    def test_invalid_amount(self):
        result = self.post("claims", dict(employee="E001", amount=-1, reference="C1"))
        self.assertEqual(result.status_code, 400)

    def test_ledger_and_audit(self):
        self.post("claims", dict(employee="E001", amount=1000, reference="C1"))
        self.assertEqual(len(self.client.get("/api/ledger/E001").json), 1)
        self.assertEqual(len(self.client.get("/api/audit").json), 1)


if __name__ == "__main__":
    unittest.main()
