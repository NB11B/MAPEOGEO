"""Qualified finite permutation-group gamma invariant."""
from fractions import Fraction
from itertools import permutations
from math import isqrt

def compose(a,b): return tuple(a[b[i]] for i in range(len(a)))
def group_order(p):
    n=len(p);e=tuple(range(n));q=e
    for t in range(1,10000):
        q=compose(p,q)
        if q==e:return t
    raise ValueError('permutation order exceeds bound')
def spf(n):
    if n<2:raise ValueError('order must be >=2')
    for d in range(2,isqrt(n)+1):
        if n%d==0:return d
    return n

def gamma(operators):
    if not operators: return {'status':'refuse','reason':'empty'}
    ops=tuple(tuple(p) for p in operators)
    n=len(ops[0]);m=len(ops)
    if m<2 or n<1 or any(len(p)!=n or sorted(p)!=list(range(n)) for p in ops):
        return {'status':'refuse','reason':'invalid_permutations_or_order'}
    e=tuple(range(n));family=set(ops)
    if len(family)!=m or e not in family:
        return {'status':'refuse','reason':'duplicated_or_missing_identity'}
    if any(compose(a,b) not in family for a in ops for b in ops):
        return {'status':'refuse','reason':'not_closed'}
    orders=tuple(sorted(group_order(p) for p in ops))
    actual=Fraction(min(o for o in orders if o>1),m)
    expected=Fraction(spf(m),m)
    return {'status':'qualified','size':m,'gamma':str(actual),
            'order_signature':orders,'prime_order':actual==1,
            'spf_reference':str(expected),'consistent':actual==expected}

def cyclic(n):return tuple(tuple((x+k)%n for x in range(n)) for k in range(n))
def klein():return tuple(tuple(x^k for x in range(4)) for k in range(4))
def symmetric3():return tuple(permutations(range(3)))
def dihedral4():
    return tuple(tuple((k+x)%4 for x in range(4)) for k in range(4))+tuple(tuple((k-x)%4 for x in range(4)) for k in range(4))
if __name__=='__main__':
    import json
    print(json.dumps({name:gamma(g) for name,g in [('C5',cyclic(5)),('C9',cyclic(9)),('C12',cyclic(12)),('V4',klein()),('S3',symmetric3()),('D4',dihedral4())]},indent=2))
