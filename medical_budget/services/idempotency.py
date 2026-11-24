from threading import RLock


class Idempotency:
    def __init__(self, cache):
        self.cache = cache
        self.lock = RLock()

    def lookup(self, employee, key):
        if not key:
            return None
        with self.lock:
            return self.cache.get(key)

    def remember(self, employee, key, result):
        if key:
            with self.lock:
                self.cache.set(key, result)
