"""Opaque, complete permutation-family qualification; no factor features."""
import random, math, json
def compose(a,b): return tuple(a[b[i]] for i in range(len(a)))
def identity(n): return tuple(range(n))
def conjugate(operators,labels):
    n=len(labels); inv=[0]*n
    for i,j in enumerate(labels): inv[j]=i
    return tuple(tuple(labels[p[inv[v]]] for v in range(n)) for p in operators)
def cyclic_family(n,seed=0):
    if n<2: raise ValueError("at least two vertices")
    labels=list(range(n));random.Random(seed).shuffle(labels)
    ops=tuple(tuple((i+k)%n for i in range(n)) for k in range(n))
    return conjugate(ops,labels),labels
def orbit_lengths(perm):
    n=len(perm)
    if sorted(perm)!=list(range(n)):raise ValueError("not permutation")
    unseen=set(range(n));sizes=[]
    while unseen:
        x=min(unseen);start=x;size=0
        while x in unseen:
            unseen.remove(x);size+=1;x=perm[x]
        if x!=start:raise ValueError("broken cycle")
        sizes.append(size)
    return tuple(sorted(sizes))
def qualify(operators):
    if not operators or not operators[0]:return {"status":"refuse","reason":"empty"}
    n=len(operators[0]);ops=tuple(tuple(p) for p in operators)
    if n<2 or any(len(p)!=n or sorted(p)!=list(range(n)) for p in ops):
        return {"status":"refuse","reason":"invalid_permutation"}
    if len(set(ops))!=n or len(ops)!=n or identity(n) not in ops:
        return {"status":"refuse","reason":"incomplete_or_duplicated_family"}
    family=set(ops)
    if any(compose(a,b) not in family for a in ops for b in ops):
        return {"status":"refuse","reason":"not_closed"}
    lengths=[orbit_lengths(p) for p in ops if p!=identity(n)]
    full=sum(c==(n,) for c in lengths)
    if full==0:return {"status":"refuse","reason":"not_cyclic"}
    return {"status":"qualified","n":n,"prime":full==n-1,
       "full_orbit_operators":full,"nonidentity_operators":n-1,
       "composite_witness":next((c for c in lengths if c!=(n,)),None)}
def oracle(n):return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))
def campaign(limit=35):
    mismatch=[]
    for n in range(2,limit+1):
        ops,_=cyclic_family(n)
        r=qualify(ops)
        if r["status"]!="qualified" or r["prime"]!=oracle(n):mismatch.append(n)
    ops,_=cyclic_family(9)
    p=list(range(9));random.Random(9001).shuffle(p)
    alt=(identity(4),(1,0,3,2),(2,3,0,1),(3,2,1,0))
    return {"tested_n":limit-1,"mismatches":mismatch,"n9":qualify(ops),
      "relabel_invariant":qualify(ops)==qualify(conjugate(ops,p)),
      "missing_family_refused":qualify(ops[:-1])["status"]=="refuse",
      "duplicate_refused":qualify(ops[:-1]+(ops[0],))["status"]=="refuse",
      "noncyclic_group_refused":qualify(alt)["status"]=="refuse",
      "single_full_cycle_refused":qualify((tuple((i+1)%9 for i in range(9)),))["status"]=="refuse"}
if __name__=="__main__":print(json.dumps(campaign(),indent=2))
