"""Bounded exact-cover inference of hidden permutation actions from unlabelled transition pairs.
No operator identities supplied. Returns candidate families, never arbitrary 'best' group.
"""
from itertools import permutations, combinations
from collections import Counter

def observations(family):
    return Counter((src, p[src]) for p in family for src in range(len(p)))

def reconstruct(rows, max_n=4):
    if not rows:
        return {"status":"refuse", "reason":"empty"}
    n=max(max(a,b) for a,b in rows)+1
    if n<2 or n>max_n or any(a<0 or b<0 for a,b in rows):
        return {"status":"refuse", "reason":"outside_bound"}
    counts=Counter(rows)
    if len(rows)!=n*n or any(counts[(a,b)]!=1 for a in range(n) for b in range(n)):
        return {"status":"refuse", "reason":"insufficient_or_conflicting"}
    perms=list(permutations(range(n)))
    full=[]
    def compose(a,b):return tuple(a[b[x]] for x in range(n))
    for inds in combinations(range(len(perms)),n):
        fam=tuple(perms[i] for i in inds)
        if observations(fam)!=counts:continue
        fs=set(fam)
        if tuple(range(n)) not in fs:continue
        if any(compose(a,b) not in fs for a in fam for b in fam):continue
        full.append(fam)
    if not full:return {"status":"refuse","reason":"no_closed_completion"}
    def order(p):
        x=tuple(range(n))
        for i in range(1,n+1):
            x=compose(p,x)
            if x==tuple(range(n)):return i
        raise AssertionError
    signatures=sorted({tuple(sorted(order(p) for p in f)) for f in full})
    return {"status":"ambiguous" if len(signatures)>1 else "structurally_identified",
            "n":n,"labelled_completions":len(full),"signatures":signatures}
if __name__=='__main__':
    print(reconstruct([(a,b) for a in range(4) for b in range(4)]))
