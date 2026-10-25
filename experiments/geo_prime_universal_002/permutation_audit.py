"""Permutation-invariant audit for operational cycle relation matrices."""
import random
from native import shift,cycles
from mapeogeo.psmsl_operator_algebra_v1 import matmul
def permute_matrix(A,perm):
    return tuple(tuple(A[perm[i]][perm[j]] for j in range(len(perm))) for i in range(len(perm)))
def orbit_partition(A):
    n=len(A)
    if any(sum(row)!=1 for row in A) or any(sum(A[i][j] for i in range(n))!=1 for j in range(n)):
        raise ValueError("not a permutation relation")
    mapping=[next(j for j in range(n) if A[i][j]==1) for i in range(n)]
    unseen=set(range(n));sizes=[]
    while unseen:
        v=min(unseen);start=v;length=0
        while v in unseen:
            unseen.remove(v);length+=1;v=mapping[v]
        if v!=start:raise ValueError("invalid cycle")
        sizes.append(length)
    return tuple(sorted(sizes))
def run():
    rng=random.Random(20261025)
    results=[]
    for n,k in ((9,3),(17,4),(25,5),(15,3),(29,7)):
        original=orbit_partition(shift(n,k))
        for _ in range(10):
            p=list(range(n));rng.shuffle(p)
            moved=orbit_partition(permute_matrix(shift(n,k),p))
            if original!=moved:raise AssertionError("label-dependent orbit partition")
        results.append({"vertices":n,"step":k,"orbit_lengths":original,"renamings":10})
    return results
if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2))
