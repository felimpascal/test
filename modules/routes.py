from flask import request,jsonify
from .auth import actor,scope
from .validation import identifier
from .errors import DomainError
from .report import Reports
from .service import Service
from . import repository as repo
def body():
    data=request.get_json(silent=True)
    if not isinstance(data,dict):
        raise DomainError('Expected object')
    return data
def register(app,db):
    reports=Reports(db)
    service=Service(db,reports)
    @app.post('/receipts')
    def receipt():
        service.receipt(actor(),body())
        return jsonify(ok=True),201
    @app.post('/requests')
    def create():
        return jsonify(service.create(actor(),body())),201
    @app.get('/requests/<int:rid>')
    def detail(rid):
        return jsonify(service.detail(actor(),rid))
    @app.post('/requests/<int:rid>/<action>')
    def transition(rid,action):
        return jsonify(service.transition(actor(),rid,action))
    @app.get('/requests')
    def listing():
        user=actor()
        clinic=request.args.get('clinic',user[2] if user[1]=='clinic' else None)
        if clinic:
            clinic=identifier(clinic)
            scope(user,clinic)
        try:
            cursor=int(request.args.get('cursor',0))
            limit=max(1,min(100,int(request.args.get('limit',20))))
        except ValueError:
            raise DomainError('Invalid pagination')
        with db.read() as conn:
            return jsonify(repo.page(conn,clinic,request.args.get('status'),cursor,limit))
    @app.get('/report')
    def report():
        user=actor()
        location=request.args.get('location',user[2] if user[1]=='clinic' else None)
        if location:
            location=identifier(location)
            scope(user,location)
        return jsonify(reports.get(location))
