class Berths:
    def __init__(self, db):
        self.db = db

    def get(self, berth):
        rows = self.db.query("SELECT * FROM berths WHERE berth = ?", (berth,))
        return rows[0] if rows else None

    def set_free(self, conn, berth, free):
        conn.execute(
            "UPDATE berths SET free = ? WHERE berth = ?",
            (free, berth),
        )

    def adjust(self, conn, berth, delta):
        conn.execute(
            "UPDATE berths SET free = free + ? WHERE berth = ?",
            (delta, berth),
        )


class Movements:
    def __init__(self, db):
        self.db = db

    def append(self, conn, berth, kind, reference, delta):
        conn.execute(
            "INSERT INTO movements(berth, kind, reference, delta) VALUES (?, ?, ?, ?)",
            (berth, kind, reference, delta),
        )

    def reservation(self, reference):
        rows = self.db.query(
            "SELECT * FROM movements WHERE kind = 'reserve' AND reference = ? ORDER BY id",
            (reference,),
        )
        return rows[0] if rows else None

    def released(self, berth, reference):
        return bool(self.db.query(
            "SELECT id FROM movements WHERE kind = 'release' AND berth = ? AND reference = ?",
            (berth, reference),
        ))

    def list(self, berth):
        return self.db.query(
            "SELECT * FROM movements WHERE berth = ? ORDER BY id",
            (berth,),
        )


class SuccessLog:
    def __init__(self, db):
        self.db = db

    def record(self, berth, reference, metres):
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO success_log(berth, reference, metres) VALUES (?, ?, ?)",
                (berth, reference, metres),
            )

    def list(self):
        return self.db.query("SELECT * FROM success_log ORDER BY id")
