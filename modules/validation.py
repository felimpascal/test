from .errors import DomainError
def identifier(value):
    if not isinstance(value,str) or not value.strip():
        raise DomainError('Invalid identifier')
    return value.strip().lower()
def quantity(value):
    if type(value) is not int or value<=0:
        raise DomainError('Invalid quantity')
    return value
def normalize_lines(lines):
    if not isinstance(lines,list) or not lines:
        raise DomainError('Missing lines')
    result={}
    for line in lines:
        sku=identifier(line.get('sku'))
        result[sku]=result.get(sku,0)+quantity(line.get('quantity'))
    return result
