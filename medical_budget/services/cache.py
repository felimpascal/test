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


class Balances:
    def __init__(self, accounts, cache):
        self.accounts = accounts
        self.cache = cache

    def get(self, employee):
        cached = self.cache.get(employee)
        if cached is not None:
            return cached
        account = self.accounts.get(employee)
        if account is None:
            raise KeyError(employee)
        value = account["balance"]
        self.cache.set(employee, value)
        return value

    def publish(self, employee, value):
        self.cache.set(employee, value)

    def invalidate(self, employee):
        self.cache.invalidate(employee)
