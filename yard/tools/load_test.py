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
        app = create_app(Path(directory) / "load.sqlite3", delay=0.1)
        count = 12
        start = Barrier(count)

        def send(i):
            with app.test_client() as client:
                start.wait(timeout=5)
                response = client.post("/api/reserves", json={
                    "berth": "Q1", "metres": 10, "reference": f"R{i:03}",
                }, headers={"Idempotency-Key": f"request-{i}"})
                return response.status_code

        with ThreadPoolExecutor(max_workers=count) as pool:
            statuses = list(pool.map(send, range(count)))

        service = app.extensions["yard"]
        row = service.berths.get("Q1")
        movements = service.movements.list("Q1")
        expected = row["opening"] + sum(item["delta"] for item in movements)
        print(json.dumps({
            "http_statuses": statuses,
            "committed_reserves": len(movements),
            "expected_free_from_movements": expected,
            "database_free": row["free"],
            "api_free": service.gauge.get("Q1"),
            "log_count": len(service.log.list()),
        }, indent=2))


if __name__ == "__main__":
    main()
