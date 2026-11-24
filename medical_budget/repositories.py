class Accounts:
    def __init__(self, db):
        self.db = db

    def get(self, employee):
        rows = self.db.query(
            "SELECT * FROM accounts WHERE employee = ?", (employee,)
        )
        return rows[0] if rows else None

    def set_balance(self, conn, employee, balance):
        conn.execute(
            "UPDATE accounts SET balance = ? WHERE employee = ?",
            (balance, employee),
        )

    def adjust(self, conn, employee, delta):
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE employee = ?",
            (delta, employee),
        )


class Ledger:
    def __init__(self, db):
        self.db = db

    def append(self, conn, employee, kind, reference, delta):
        conn.execute(
            "INSERT INTO ledger(employee, kind, reference, delta) VALUES (?, ?, ?, ?)",
            (employee, kind, reference, delta),
        )

    def claim(self, reference):
        rows = self.db.query(
            "SELECT * FROM ledger WHERE kind = 'claim' AND reference = ? ORDER BY id",
            (reference,),
        )
        return rows[0] if rows else None

    def reversed(self, employee, reference):
        return bool(self.db.query(
            "SELECT id FROM ledger WHERE kind = 'reversal' AND employee = ? AND reference = ?",
            (employee, reference),
        ))

    def list(self, employee):
        return self.db.query(
            "SELECT * FROM ledger WHERE employee = ? ORDER BY id", (employee,)
        )


class Audit:
    def __init__(self, db):
        self.db = db

    def record(self, employee, reference, amount):
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO audit(employee, reference, amount) VALUES (?, ?, ?)",
                (employee, reference, amount),
            )

    def list(self):
        return self.db.query("SELECT * FROM audit ORDER BY id")
