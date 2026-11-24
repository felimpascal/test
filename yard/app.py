import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

from database import Database
from repositories import Berths, Movements, SuccessLog
from services.gauge import FreeMetres, TTLCache
from services.locks import BerthLocks
from services.memo import Memo
from services.yard import Conflict, YardService


def create_app(path=None, delay=0.025, lock_pause=0.02):
    app = Flask(__name__)
    db = Database(path or os.getenv("QUAY_DB") or Path(__file__).with_name("quay.sqlite3"))
    berths, movements, log = Berths(db), Movements(db), SuccessLog(db)
    gauge = FreeMetres(berths, TTLCache(60))
    service = YardService(
        db, berths, movements, log, gauge,
        Memo(TTLCache(300)),
        BerthLocks(pause=lock_pause),
        delay,
    )
    app.extensions["yard"] = service

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

    def metres(data):
        value = data.get("metres")
        if type(value) is not int or not 0 < value <= 1000000000:
            raise ValueError("metres must be a positive integer")
        return value

    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(KeyError)
    def not_found(error):
        return jsonify(error="berth not found"), 404

    @app.errorhandler(Conflict)
    @app.errorhandler(sqlite3.IntegrityError)
    def conflict(error):
        return jsonify(error=str(error)), 409

    @app.errorhandler(TimeoutError)
    def busy(error):
        return jsonify(error=str(error)), 503

    @app.get("/api/berths/<berth>")
    def free(berth):
        return jsonify(berth=berth, free=gauge.get(berth))

    @app.post("/api/reserves")
    def reserve():
        data = body()
        return jsonify(service.reserve(
            field(data, "berth"), metres(data), field(data, "reference"),
            request.headers.get("Idempotency-Key"),
        ))

    @app.post("/api/replenish")
    def replenish():
        data = body()
        return jsonify(service.replenish(
            field(data, "berth"), metres(data), field(data, "reference"),
        ))

    @app.post("/api/releases")
    def release():
        data = body()
        return jsonify(service.release(field(data, "berth"), field(data, "reference")))

    @app.post("/api/shifts")
    def shift():
        data = body()
        return jsonify(service.shift(
            field(data, "source"), field(data, "target"),
            metres(data), field(data, "reference"),
        ))

    @app.get("/api/movements/<berth>")
    def movements_for(berth):
        if berths.get(berth) is None:
            raise KeyError(berth)
        return jsonify(movements.list(berth))

    @app.get("/api/log")
    def events():
        return jsonify(log.list())

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, threaded=True)
