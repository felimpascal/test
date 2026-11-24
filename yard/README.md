# Quay Slot Service

Local exercise. Synthetic berth ids and integer metres. Not a real port system.

## Run

```sh
cd yard
python -m pip install -r requirements.txt
python app.py
```

Listens on 127.0.0.1:5000. A fresh database has berths Q1 and Q2 with 1000 free metres each. Delete the sqlite file after stopping the process to reset, or point QUAY_DB at a new path.

## Contract

- GET /api/berths/Q1 returns the committed free metres.
- POST /api/reserves JSON {"berth":"Q1","metres":100,"reference":"R001"} with an optional Idempotency-Key header.
  Repeating the same berth, key, and body returns the original response and does not reserve again.
  The same berth and key with a different body returns 409.
  Keys are scoped by berth.
  The stored idempotency result must still be returned after the process restarts, for as long as that reservation row remains in the database.
  References are unique across all reservations, not per berth.
  A failed attempt must not change free metres or the success log.
- POST /api/replenish JSON {"berth":"Q1","metres":100,"reference":"P001"} adds free metres.
- POST /api/releases JSON {"berth":"Q1","reference":"R001"} undoes one reservation, once.
- POST /api/shifts JSON {"source":"Q1","target":"Q2","metres":100,"reference":"S001"}.
  A shift atomically debits the source, credits the target, and writes both movement rows.
  Opposite-direction shifts that each have enough free metres must both commit under concurrency.
- GET /api/movements/Q1 returns committed rows, ascending by id.
- GET /api/log returns successful reservation log rows only.

Free metres equal the opening figure plus the sum of committed movement deltas.
Metres are positive integers.
Reserves and shifts cannot overdraw a berth.
Errors are JSON. Domain conflicts are 409.
Each write uses its own database transaction.
Only one local process is in scope.

## Tests

```sh
python -m unittest discover -s tests -v
python tools/load_test.py
```

The load tool uses a temporary database. The unit tests cover sequential happy paths only.
