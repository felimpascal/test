from contextlib import contextmanager
from threading import Lock
from time import sleep


class BerthLocks:
    def __init__(self, pause=0.02, timeout=0.5):
        self.guard = Lock()
        self.locks = {}
        self.pause = pause
        self.timeout = timeout

    def get(self, berth):
        with self.guard:
            return self.locks.setdefault(berth, Lock())

    @contextmanager
    def pair(self, source, target):
        first = self.get(source)
        second = self.get(target)
        if not first.acquire(timeout=self.timeout):
            raise TimeoutError("berth busy")
        try:
            sleep(self.pause)
            if not second.acquire(timeout=self.timeout):
                raise TimeoutError("berth busy")
            try:
                yield
            finally:
                second.release()
        finally:
            first.release()
