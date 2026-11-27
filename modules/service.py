from . import repository as repo,stock,audit
from .auth import require,scope
from .errors import DomainError
from .validation import identifier,quantity,normalize_lines
class Service:
    def __init__(self,db,reports):
        self.db=db
        self.reports=reports
    def receipt(self,user,data):
        require(user,'central')
        with self.db.transaction() as db:
            stock.receive(db,'warehouse',identifier(data.get('sku')),quantity(data.get('quantity')))
            audit.record(db,user,'receipt',None)
        self.reports.changed('warehouse')
    def create(self,user,data):
        require(user,'clinic')
        clinic=identifier(data.get('clinic',user[2]))
        scope(user,clinic)
        ref=identifier(data.get('reference'))
        items=normalize_lines(data.get('lines'))
        with self.db.transaction() as db:
            old=repo.existing(db,clinic,ref)
            if old:
                if set(repo.lines(db,old['id']))!=set(items):
                    raise DomainError('Reference conflict',409)
                return dict(old)
            rid=repo.insert(db,clinic,ref,items)
            audit.record(db,user,'create',rid)
            return repo.get(db,rid)
    def detail(self,user,rid):
        with self.db.read() as db:
            row=repo.get(db,rid)
            scope(user,row['clinic'])
            row['lines']=repo.lines(db,rid)
            return row
    def transition(self,user,rid,action):
        require(user,'central')
        with self.db.transaction() as db:
            row=repo.get(db,rid)
            items=repo.lines(db,rid)
            if action=='approve':
                if row['status']=='approved':
                    return row
                if row['status']!='pending':
                    raise DomainError('Invalid state',409)
                for sku,q in items.items():
                    stock.reserve(db,sku,q)
                status='approved'
            elif action=='dispatch':
                if row['status']!='approved':
                    raise DomainError('Invalid state',409)
                for sku,q in items.items():
                    stock.dispatch(db,row['clinic'],sku,q)
                status='dispatched'
            elif action=='cancel':
                if row['status']=='cancelled':
                    return row
                if row['status']!='pending':
                    for sku,q in items.items():
                        stock.release(db,sku,q)
                status='cancelled'
            else:
                raise DomainError('Unknown action')
            repo.set_status(db,rid,status)
            result=repo.get(db,rid)
        with self.db.transaction() as db:
            audit.record(db,user,action,rid)
        self.reports.changed('warehouse')
        return result
