import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

from database import Database
from repositories import Accounts, Ledger, Audit
from services.cache import TTLCache, Balances
from services.idempotency import Idempotency
from services.locking import AccountLocks
from services.budget import BudgetService, Conflict


def create_app(path=None, processing_delay=0.025, lock_pause=0.02):
    app = Flask(__name__)
    db = Database(path or os.getenv("BUDGET_DB") or
                  Path(__file__).with_name("budget.sqlite3"))
    accounts, ledger, audit = Accounts(db), Ledger(db), Audit(db)
    balances = Balances(accounts, TTLCache(60))
    service = BudgetService(db, accounts, ledger, audit, balances,
                            Idempotency(TTLCache(300)),
                            AccountLocks(pause=lock_pause), processing_delay)
    app.extensions["budget"] = service

    def body():
        value = request.get_json(silent=True)
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def field(data, name):
        value = data.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(name + " required")
        return value.strip()

    def amount(data):
        value = data.get("amount")
        if type(value) is not int or not 0 < value <= 1000000000:
            raise ValueError("amount must be a positive integer")
        return value

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(KeyError)
    def not_found(error):
        return jsonify(error="account not found"), 404

    @app.errorhandler(Conflict)
    @app.errorhandler(sqlite3.IntegrityError)
    def conflict(error):
        return jsonify(error=str(error)), 409

    @app.errorhandler(TimeoutError)
    def busy(error):
        return jsonify(error=str(error)), 503

    @app.get("/api/accounts/<employee>")
    def balance(employee):
        return jsonify(employee=employee, balance=balances.get(employee))

    @app.post("/api/claims")
    def claim():
        data = body()
        return jsonify(service.claim(
            field(data, "employee"), amount(data), field(data, "reference"),
            request.headers.get("Idempotency-Key"),
        ))

    @app.post("/api/topups")
    def topup():
        data = body()
        return jsonify(service.topup(
            field(data, "employee"), amount(data), field(data, "reference")
        ))

    @app.post("/api/reversals")
    def reversal():
        data = body()
        return jsonify(service.reverse(
            field(data, "employee"), field(data, "reference")
        ))

    @app.post("/api/transfers")
    def transfer():
        data = body()
        return jsonify(service.transfer(
            field(data, "source"), field(data, "target"),
            amount(data), field(data, "reference")
        ))

    @app.get("/api/ledger/<employee>")
    def movements(employee):
        if accounts.get(employee) is None:
            raise KeyError(employee)
        return jsonify(ledger.list(employee))

    @app.get("/api/audit")
    def events():
        return jsonify(audit.list())

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, threaded=True)
