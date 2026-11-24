from threading import RLock


class Memo:
    def __init__(self, cache):
        self.cache = cache
        self.lock = RLock()

    def lookup(self, berth, key):
        if not key:
            return None
        with self.lock:
            return self.cache.get(key)

    def remember(self, berth, key, result):
        if key:
            with self.lock:
                self.cache.set(key, result)
