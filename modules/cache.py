from threading import RLock
class ReportCache:
    def __init__(self):
        self.values={}
        self.lock=RLock()
    def get(self,key,loader):
        with self.lock:
            if key not in self.values:
                self.values[key]=loader()
            return self.values[key]
    def invalidate(self,location):
        with self.lock:
            self.values.pop(location,None)
