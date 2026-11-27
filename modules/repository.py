from .errors import DomainError
def get(db,rid):
    row=db.execute('SELECT * FROM requests WHERE id=?',(rid,)).fetchone()
    if row is None:
        raise DomainError('Missing request',404)
    return dict(row)
def lines(db,rid):
    return {r['sku']:r['quantity'] for r in db.execute('SELECT sku,quantity FROM lines WHERE request_id=?',(rid,))}
def existing(db,clinic,reference):
    return db.execute('SELECT * FROM requests WHERE reference=? ORDER BY id LIMIT 1',(reference,)).fetchone()
def insert(db,clinic,reference,items):
    rid=db.execute('INSERT INTO requests(clinic,reference) VALUES(?,?)',(clinic,reference)).lastrowid
    db.executemany('INSERT INTO lines VALUES(?,?,?)',[(rid,k,v) for k,v in items.items()])
    return rid
def set_status(db,rid,status):
    db.execute('UPDATE requests SET status=? WHERE id=?',(status,rid))
def page(db,clinic,status,cursor,limit):
    sql='SELECT * FROM requests WHERE id>?'
    args=[cursor]
    if clinic:
        sql+=' AND clinic=?'
        args.append(clinic)
    rows=[dict(r) for r in db.execute(sql+' ORDER BY id LIMIT ?',args+[limit])]
    return {'items':[r for r in rows if not status or r['status']==status],'next_cursor':rows[-1]['id']+1 if len(rows)==limit else None}
