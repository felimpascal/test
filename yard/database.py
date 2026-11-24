import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS berths (
    berth TEXT PRIMARY KEY,
    opening INTEGER NOT NULL,
    free INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    berth TEXT NOT NULL REFERENCES berths(berth),
    kind TEXT NOT NULL,
    reference TEXT NOT NULL,
    delta INTEGER NOT NULL,
    UNIQUE(kind, reference, berth)
);
CREATE TABLE IF NOT EXISTS success_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    berth TEXT NOT NULL,
    reference TEXT NOT NULL,
    metres INTEGER NOT NULL
);
"""


class Database:
    def __init__(self, path):
        self.path = str(path)
        with self.transaction() as conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT OR IGNORE INTO berths VALUES (?, ?, ?)",
                [("Q1", 1000, 1000), ("Q2", 1000, 1000)],
            )

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def query(self, sql, params=()):
        conn = self.connect()
        try:
            return [dict(row) for row in conn.execute(sql, params)]
        finally:
            conn.close()
