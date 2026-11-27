from flask import request
from .errors import DomainError
USERS={'central':('central','warehouse'),'north':('clinic','north'),'south':('clinic','south'),'auditor':('audit',None)}
def actor():
    token=request.headers.get('Authorization','').removeprefix('Bearer ')
    if token not in USERS:
        raise DomainError('Forbidden',403)
    role,clinic=USERS[token]
    return token,role,clinic
def require(user,*roles):
    if user[1] not in roles:
        raise DomainError('Forbidden',403)
def scope(user,clinic):
    if user[1]=='clinic' and user[2]!=clinic:
        raise DomainError('Forbidden',403)
