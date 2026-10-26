"""Discover prime generators from successor, addition and repeated addition."""
from dataclasses import dataclass
import math,json
@dataclass
class Result:
    limit:int
    successors:int
    addition_edges:int
    multiplication_edges:int
    generators:list
    complete:bool
    unique_factorizations:bool
    direct_sum:float
    prime_product:float
    ablations:dict
def discover(limit=120):
    if limit<2:raise ValueError('limit must >=2')
    successor={n:n+1 for n in range(limit)}
    add={}
    for a in range(limit+1):
        z=a
        for b in range(limit+1-a):
            add[(a,b)]=z
            if b<limit-a:z=successor[z]
    mul={}
    for a in range(1,limit+1):
        z=0
        for b in range(1,limit//a+1):
            z=add[(z,a)]
            mul[(a,b)]=z
    witness={n:[] for n in range(2,limit+1)}
    for (a,b),v in mul.items():
        if a>1 and b>1:witness[v].append((a,b))
    generators=[n for n in range(2,limit+1) if not witness[n]]
    memo={1:{()}}
    def factor(n):
        if n not in memo:
            if n in generators:memo[n]={(n,)}
            else:
                combos=set()
                for a,b in witness[n]:
                    for fa in factor(a):
                        for fb in factor(b):combos.add(tuple(sorted(fa+fb)))
                memo[n]=combos
        return memo[n]
    forms={n:factor(n) for n in range(1,limit+1)}
    product=math.prod(1/(1-1/p**2) for p in generators)
    ablations={}
    for p in generators[:5]:
        kept=[n for n in range(1,limit+1) if p not in next(iter(forms[n]))]
        ablations[str(p)]={'retained_count':len(kept),'ratio':1-1/p**2}
    return Result(limit,len(successor),len(add),len(mul),generators,
                  all(len(forms[n])>=1 for n in forms),
                  all(len(forms[n])==1 for n in forms),
                  sum(1/n**2 for n in range(1,limit+1)),product,ablations)
if __name__=='__main__':print(json.dumps(discover().__dict__,indent=2))
