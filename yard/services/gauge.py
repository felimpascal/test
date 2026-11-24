from threading import RLock
from time import monotonic


class TTLCache:
    def __init__(self, ttl=60):
        self.ttl = ttl
        self.items = {}
        self.lock = RLock()

    def get(self, key):
        with self.lock:
            item = self.items.get(key)
            if item is None:
                return None
            deadline, value = item
            if deadline <= monotonic():
                self.items.pop(key, None)
                return None
            return value

    def set(self, key, value):
        with self.lock:
            self.items[key] = (monotonic() + self.ttl, value)

    def invalidate(self, key):
        with self.lock:
            self.items.pop(key, None)


class FreeMetres:
    def __init__(self, berths, cache):
        self.berths = berths
        self.cache = cache

    def get(self, berth):
        cached = self.cache.get(berth)
        if cached is not None:
            return cached
        row = self.berths.get(berth)
        if row is None:
            raise KeyError(berth)
        value = row["free"]
        self.cache.set(berth, value)
        return value

    def publish(self, berth, value):
        self.cache.set(berth, value)

    def invalidate(self, berth):
        self.cache.invalidate(berth)
