from time import sleep


class Conflict(Exception):
    pass


class BudgetService:
    def __init__(self, db, accounts, ledger, audit, balances, idempotency,
                 locks, processing_delay=0.025):
        self.db = db
        self.accounts = accounts
        self.ledger = ledger
        self.audit = audit
        self.balances = balances
        self.idempotency = idempotency
        self.locks = locks
        self.processing_delay = processing_delay

    def claim(self, employee, amount, reference, key=None):
        previous = self.idempotency.lookup(employee, key)
        if previous is not None:
            return previous
        current = self.balances.get(employee)
        if current < amount:
            raise Conflict("insufficient balance")
        remaining = current - amount
        sleep(self.processing_delay)
        self.audit.record(employee, reference, amount)
        with self.db.transaction() as conn:
            self.accounts.set_balance(conn, employee, remaining)
            self.balances.publish(employee, remaining)
            self.ledger.append(conn, employee, "claim", reference, -amount)
        result = {"employee": employee, "reference": reference,
                  "amount": amount, "balance": remaining}
        self.idempotency.remember(employee, key, result)
        return result

    def topup(self, employee, amount, reference):
        if self.accounts.get(employee) is None:
            raise KeyError(employee)
        with self.db.transaction() as conn:
            self.accounts.adjust(conn, employee, amount)
            self.ledger.append(conn, employee, "topup", reference, amount)
        return {"employee": employee, "reference": reference, "amount": amount}

    def reverse(self, employee, reference):
        claim = self.ledger.claim(reference)
        if claim is None or claim["employee"] != employee:
            raise Conflict("claim not found")
        if self.ledger.reversed(employee, reference):
            raise Conflict("already reversed")
        amount = -claim["delta"]
        with self.db.transaction() as conn:
            self.accounts.adjust(conn, employee, amount)
            self.ledger.append(conn, employee, "reversal", reference, amount)
        self.balances.invalidate(employee)
        return {"employee": employee, "reference": reference, "amount": amount}

    def transfer(self, source, target, amount, reference):
        if source == target:
            raise ValueError("accounts must be different")
        with self.locks.pair(source, target):
            current = self.accounts.get(source)
            if current is None or self.accounts.get(target) is None:
                raise KeyError("account not found")
            if current["balance"] < amount:
                raise Conflict("insufficient balance")
            with self.db.transaction() as conn:
                self.accounts.adjust(conn, source, -amount)
                self.accounts.adjust(conn, target, amount)
                self.ledger.append(conn, source, "transfer_out", reference, -amount)
                self.ledger.append(conn, target, "transfer_in", reference, amount)
            self.balances.invalidate(source)
            self.balances.invalidate(target)
        return {"source": source, "target": target, "reference": reference,
                "amount": amount}
