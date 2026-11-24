import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


def main():
    with tempfile.TemporaryDirectory() as directory:
        app = create_app(Path(directory) / "load.sqlite3", processing_delay=0.1)
        count = 12
        start = Barrier(count)

        def send(i):
            with app.test_client() as client:
                start.wait(timeout=5)
                response = client.post("/api/claims", json={
                    "employee": "E001", "amount": 1000, "reference": f"C{i:03}"
                }, headers={"Idempotency-Key": f"request-{i}"})
                return response.status_code

        with ThreadPoolExecutor(max_workers=count) as pool:
            statuses = list(pool.map(send, range(count)))

        service = app.extensions["budget"]
        account = service.accounts.get("E001")
        movements = service.ledger.list("E001")
        expected = account["opening"] + sum(row["delta"] for row in movements)
        print(json.dumps({
            "http_statuses": statuses,
            "committed_claims": len(movements),
            "expected_balance_from_ledger": expected,
            "database_balance": account["balance"],
            "api_balance": service.balances.get("E001"),
            "audit_count": len(service.audit.list()),
        }, indent=2))


if __name__ == "__main__":
    main()
