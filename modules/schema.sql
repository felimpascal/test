CREATE TABLE IF NOT EXISTS stock(location TEXT,sku TEXT,physical INTEGER NOT NULL DEFAULT 0,reserved INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(location,sku),CHECK(physical>=0),CHECK(reserved>=0));
CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,clinic TEXT NOT NULL,reference TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',UNIQUE(clinic,reference));
CREATE TABLE IF NOT EXISTS lines(request_id INTEGER REFERENCES requests(id),sku TEXT,quantity INTEGER NOT NULL CHECK(quantity>0),PRIMARY KEY(request_id,sku));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT,request_id INTEGER);
