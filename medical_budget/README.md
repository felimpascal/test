# Medical Budget Service

Local development exercise using synthetic employee IDs and integer currency units. Not for production or real medical records.

## Run
From the repository root:
```sh
cd medical_budget
python -m pip install -r requirements.txt
python app.py
```

The server listens on 127.0.0.1:5000. A new database contains E001 and E002 (100000 each). Delete the local database after stopping the server to reset the demo, or set BUDGET_DB to a new file.

## Contract
- GET /api/accounts/E001: current committed balance.
- POST /api/claims: JSON {"employee":"E001","amount":1000,"reference":"C001"}; optional Idempotency-Key header. Repeating the same employee/key/body must return the original response without applying another debit; the same employee/key with different body must return 409. Keys are scoped by employee. References are unique across claims. An unsuccessful attempt must not alter balance or successful audit history.
- POST /api/topups: JSON {"employee":"E001","amount":1000,"reference":"T001"}.
- POST /api/reversals: JSON {"employee":"E001","reference":"C001"}; each claim may be reversed only once.
- POST /api/transfers: JSON {"source":"E001","target":"E002","amount":1000,"reference":"X001"}. Transfer must atomically debit/credit and record both ledger legs. Opposite-direction transfers with sufficient balances should complete, even under concurrency.
- GET /api/ledger/E001: committed movements, ascending by ID.
- GET /api/audit: successful claim audit events.

Account balance equals opening balance plus the sum of committed ledger deltas. Amounts are positive integers. Claims and transfers cannot overdraw accounts. Errors are JSON; domain conflicts return 409. All writes use an individual database transaction. Only the local process is supported for this exercise.

## Tests
```sh
python -m unittest discover -s tests -v
python tools/load_test.py
```
The load tool uses an isolated temporary database and reports observed request outcomes and ledger reconciliation. Basic tests cover sequential happy paths.
