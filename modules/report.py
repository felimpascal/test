from .cache import ReportCache
class Reports:
    def __init__(self,database):
        self.db=database
        self.cache=ReportCache()
    def get(self,location):
        def load():
            with self.db.read() as db:
                sql='SELECT location,sku,physical,reserved,physical-reserved AS available FROM stock'
                return [dict(r) for r in db.execute(sql+(' WHERE location=?' if location else ''),(location,) if location else ())]
        return self.cache.get(location,load)
    def changed(self,*locations):
        for location in locations:
            self.cache.invalidate(location)
