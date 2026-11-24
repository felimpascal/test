from time import sleep


class Conflict(Exception):
    pass


class YardService:
    def __init__(self, db, berths, movements, log, gauge, memo, locks, delay=0.025):
        self.db = db
        self.berths = berths
        self.movements = movements
        self.log = log
        self.gauge = gauge
        self.memo = memo
        self.locks = locks
        self.delay = delay

    def reserve(self, berth, metres, reference, key=None):
        previous = self.memo.lookup(berth, key)
        if previous is not None:
            return previous
        current = self.gauge.get(berth)
        if current < metres:
            raise Conflict("not enough free metres")
        remaining = current - metres
        sleep(self.delay)
        self.log.record(berth, reference, metres)
        with self.db.transaction() as conn:
            self.berths.set_free(conn, berth, remaining)
            self.gauge.publish(berth, remaining)
            self.movements.append(conn, berth, "reserve", reference, -metres)
        result = {
            "berth": berth,
            "reference": reference,
            "metres": metres,
            "free": remaining,
        }
        self.memo.remember(berth, key, result)
        return result

    def replenish(self, berth, metres, reference):
        if self.berths.get(berth) is None:
            raise KeyError(berth)
        with self.db.transaction() as conn:
            self.berths.adjust(conn, berth, metres)
            self.movements.append(conn, berth, "replenish", reference, metres)
        return {"berth": berth, "reference": reference, "metres": metres}

    def release(self, berth, reference):
        row = self.movements.reservation(reference)
        if row is None or row["berth"] != berth:
            raise Conflict("reservation not found")
        if self.movements.released(berth, reference):
            raise Conflict("already released")
        metres = -row["delta"]
        with self.db.transaction() as conn:
            self.berths.adjust(conn, berth, metres)
            self.movements.append(conn, berth, "release", reference, metres)
        self.gauge.invalidate(berth)
        return {"berth": berth, "reference": reference, "metres": metres}

    def shift(self, source, target, metres, reference):
        if source == target:
            raise ValueError("berths must be different")
        with self.locks.pair(source, target):
            current = self.berths.get(source)
            if current is None or self.berths.get(target) is None:
                raise KeyError("berth not found")
            if current["free"] < metres:
                raise Conflict("not enough free metres")
            with self.db.transaction() as conn:
                self.berths.adjust(conn, source, -metres)
                self.berths.adjust(conn, target, metres)
                self.movements.append(conn, source, "shift_out", reference, -metres)
                self.movements.append(conn, target, "shift_in", reference, metres)
            self.gauge.invalidate(source)
            self.gauge.invalidate(target)
        return {
            "source": source,
            "target": target,
            "reference": reference,
            "metres": metres,
        }
