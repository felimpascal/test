from flask import Flask, request, jsonify
from modules.inventory import Inventory

def create_app(database='inventory.sqlite3'):
    app = Flask(__name__)
    inventory = Inventory(database)
    @app.post('/items')
    def create_item():
        data = request.get_json()
        inventory.create(data['sku'], data['name'])
        return jsonify(ok=True), 201
    @app.post('/movements')
    def movement():
        data = request.get_json()
        try:
            inventory.move(data['sku'], data['kind'], int(data['quantity']), data['reference'])
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        return jsonify(ok=True), 201
    @app.get('/report')
    def report():
        return jsonify(inventory.report())
    return app

if __name__ == '__main__':
    create_app().run()
