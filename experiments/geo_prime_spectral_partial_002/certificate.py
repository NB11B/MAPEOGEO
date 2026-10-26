"""Exact observation certificate; independent exhaustive enumeration through n=6."""
from itertools import permutations
from math import factorial

def cycle_type(p):
    remaining=set(range(len(p))); lengths=[]
    while remaining:
        start=min(remaining); x=start; length=0
        while x in remaining:
            remaining.remove(x); length+=1; x=p[x]
        if x!=start:raise ValueError('nonpermutation')
        lengths.append(length)
    return tuple(sorted(lengths))

def certificate(n,edges):
    if n<2:return {'status':'refuse','reason':'small_n'}
    mapping={}; targets=set()
    for a,b in edges:
        if not (0<=a<n and 0<=b<n):return {'status':'refuse','reason':'vertex_range'}
        if a in mapping and mapping[a]!=b:return {'status':'refuse','reason':'conflict'}
        if b in targets and mapping.get(a)!=b:return {'status':'refuse','reason':'noninjective'}
        mapping[a]=b;targets.add(b)
    missing=n-len(mapping)
    return {'status':'identified' if missing<=1 else 'ambiguous','missing':missing,
            'completions':factorial(missing), 'spectrum_identified':missing<=1}

def exhaustive(max_n=6):
    checked=0;errors=[]
    for n in range(2,max_n+1):
        seen=set()
        for p in permutations(range(n)):
            for mask in range(1<<n):
                edges=tuple((i,p[i]) for i in range(n) if mask>>i&1)
                if edges in seen:continue
                seen.add(edges)
                r=certificate(n,edges)
                completions=[q for q in permutations(range(n)) if all(q[a]==b for a,b in edges)]
                spectrum_unique=len({cycle_type(q) for q in completions})==1
                checked+=1
                if len(completions)!=r['completions'] or spectrum_unique!=r['spectrum_identified']:
                    errors.append((n,edges))
    return checked,errors
if __name__=='__main__':print(exhaustive())
