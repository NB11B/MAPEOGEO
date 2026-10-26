"""Prime angular-wheel recurrence and rotational spectral invariance."""
from math import gcd
import cmath
def wheel(n):
    return tuple(int(gcd(x,n)==1) for x in range(n))
def extend(w,p):
    n=len(w)*p
    return tuple(w[x%len(w)]*int(x%p!=0) for x in range(n))
def count_removed(w,p):
    tiled=w*p
    out=extend(w,p)
    return sum(tiled)-sum(out)
def dft(w,k):
    n=len(w)
    return sum(v*cmath.exp(-2j*cmath.pi*k*i/n) for i,v in enumerate(w))
def campaign():
    entries=[]
    for n,p in [(30,7),(210,11)]:
        w=wheel(n);actual=wheel(n*p);pred=extend(w,p)
        entries.append({'from':n,'new_prime':p,'to':n*p,
                        'reconstructed':pred==actual,
                        'old_repeated':sum(w)*p,
                        'survivors':sum(actual),
                        'removed':count_removed(w,p)})
    rotations={}
    for n in (30,210):
        w=wheel(n)
        rotations[n]=max(abs(abs(dft(w,k))-abs(dft(w[-3:]+w[:-3],k))) for k in range(n))
    return {'transitions':entries,'rotation_magnitude_residual':rotations}
if __name__=='__main__':
    print(campaign())
