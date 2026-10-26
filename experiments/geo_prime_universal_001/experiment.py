"""Geometric characterization by cyclic step orbits and Pascal divisibility."""
from math import comb,isqrt
import json
def orbit_length(n,step):
    if n<2 or not 1<=step<n:raise ValueError("invalid n or step")
    seen=set();x=0
    while x not in seen:
        seen.add(x);x=(x+step)%n
    assert x==0
    return len(seen)
def cyclic_prime(n):
    return n>=2 and all(orbit_length(n,k)==n for k in range(1,n))
def pascal_prime(n):
    return n>=2 and all(comb(n,k)%n==0 for k in range(1,n))
def reference_prime(n):
    return n>=2 and all(n%d for d in range(2,isqrt(n)+1))
def witness(n):
    if n<2:return None
    for k in range(1,n):
        size=orbit_length(n,k)
        if size<n:return {"step":k,"orbit":size,"missing":n-size}
    return None
def run(limit=300):
    primes=[n for n in range(2,limit+1) if reference_prime(n)]
    a=[n for n in range(1,limit+1) if cyclic_prime(n)!=reference_prime(n)]
    b=[n for n in range(1,limit+1) if pascal_prime(n)!=reference_prime(n)]
    return {"limit":limit,"prime_count":len(primes),"cycle_mismatches":a,"pascal_mismatches":b,
      "examples":{str(n):{"prime":cyclic_prime(n),"witness":witness(n)} for n in (2,3,4,5,9,15,17,25,29)}}
if __name__=="__main__":print(json.dumps(run(),indent=2))
