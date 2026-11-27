def record(db,user,action,rid):
    db.execute('INSERT INTO audit(actor,action,request_id) VALUES(?,?,?)',(user[0],action,rid))
