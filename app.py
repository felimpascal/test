from flask import Flask, jsonify
from modules.db import Database
from modules.routes import register
from modules.errors import DomainError
def create_app(path='demo.sqlite3'):
    app=Flask(__name__)
    db=Database(path)
    db.initialize()
    register(app,db)
    @app.errorhandler(DomainError)
    def domain_error(e):
        return jsonify(error=str(e)),e.status
    return app
if __name__=='__main__':
    create_app().run()
