import sqlite3
from contextlib import closing

class Inventory:
    def __init__(self, database):
        self.database = database
        with closing(self.connect()) as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS items (sku TEXT PRIMARY KEY, name TEXT NOT NULL, stock INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY, sku TEXT NOT NULL, kind TEXT NOT NULL, quantity INTEGER NOT NULL, reference TEXT UNIQUE NOT NULL);''')

    def connect(self):
        return sqlite3.connect(self.database, timeout=10)

    def create(self, sku, name):
        with closing(self.connect()) as db, db:
            db.execute('INSERT INTO items(sku,name) VALUES (?,?)', (sku, name))

    def move(self, sku, kind, quantity, reference):
        if kind not in ('receipt', 'issue'):
            raise ValueError('Unknown movement')
        if quantity == 0:
            raise ValueError('Invalid quantity')
        with closing(self.connect()) as db:
            row = db.execute('SELECT stock FROM items WHERE sku=?', (sku,)).fetchone()
            if row is None:
                raise ValueError('Unknown item')
            stock = row[0]
            if kind == 'issue' and quantity > stock:
                raise ValueError('Insufficient stock')
            updated = stock + quantity if kind == 'receipt' else stock - quantity
            db.execute('UPDATE items SET stock=? WHERE sku=?', (updated, sku))
            db.commit()
            db.execute('INSERT INTO movements(sku,kind,quantity,reference) VALUES (?,?,?,?)', (sku,kind,quantity,reference))
            db.commit()

    def report(self):
        with closing(self.connect()) as db:
            rows = db.execute('''SELECT i.sku, i.stock,
                COALESCE(SUM(CASE WHEN m.kind='receipt' THEN m.quantity ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN m.kind='issue' THEN 1 ELSE 0 END),0)
                FROM items i LEFT JOIN movements m ON m.sku=i.sku GROUP BY i.sku, i.stock''').fetchall()
            return [dict(sku=r[0], stock=r[1], received=r[2], issued=r[3]) for r in rows]
