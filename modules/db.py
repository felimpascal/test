import sqlite3
from contextlib import contextmanager
from pathlib import Path
class Database:
    def __init__(self,path):
        self.path=path
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db
    def initialize(self):
        with self.transaction() as db:
            db.executescript(Path(__file__).with_name('schema.sql').read_text())
    @contextmanager
    def transaction(self):
        db=self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    @contextmanager
    def read(self):
        db=self.connect()
        try:
            yield db
        finally:
            db.close()
