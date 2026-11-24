import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    employee TEXT PRIMARY KEY,
    opening INTEGER NOT NULL,
    balance INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee TEXT NOT NULL REFERENCES accounts(employee),
    kind TEXT NOT NULL,
    reference TEXT NOT NULL,
    delta INTEGER NOT NULL,
    UNIQUE(kind, reference, employee)
);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee TEXT NOT NULL,
    reference TEXT NOT NULL,
    amount INTEGER NOT NULL
);
"""


class Database:
    def __init__(self, path):
        self.path = str(path)
        with self.transaction() as conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT OR IGNORE INTO accounts VALUES (?, ?, ?)",
                [("E001", 100000, 100000), ("E002", 100000, 100000)],
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
