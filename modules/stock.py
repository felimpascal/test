from .errors import DomainError
def receive(db,location,sku,q):
    db.execute('INSERT INTO stock(location,sku,physical) VALUES(?,?,?) ON CONFLICT(location,sku) DO UPDATE SET physical=physical+excluded.physical',(location,sku,q))
def reserve(db,sku,q):
    cur=db.execute("UPDATE stock SET reserved=reserved+? WHERE location='warehouse' AND sku=? AND physical>=?",(q,sku,q))
    if cur.rowcount!=1:
        raise DomainError('Insufficient stock',409)
def release(db,sku,q):
    db.execute("UPDATE stock SET reserved=reserved-? WHERE location='warehouse' AND sku=?",(q,sku))
def dispatch(db,clinic,sku,q):
    db.execute("UPDATE stock SET physical=physical-?,reserved=reserved-? WHERE location='warehouse' AND sku=?",(q,q,sku))
    receive(db,clinic,sku,q)
