"""Enumerate permutation spectra compatible with partial operator observations."""
from itertools import permutations
from math import lcm

def cycle_type(p):
    unseen=set(range(len(p))); cycles=[]
    while unseen:
        x=start=next(iter(unseen));length=0
        while x in unseen:
            unseen.remove(x);length+=1;x=p[x]
        assert x==start
        cycles.append(length)
    return tuple(sorted(cycles))

def spectral_profile(p):
    cycles=cycle_type(p);order=1
    for c in cycles:order=lcm(order,c)
    return cycles,order

def infer(n,edges,max_n=8):
    if n<2 or n>max_n:return {"status":"refuse","reason":"outside_enumeration_bound"}
    given={}
    for a,b in edges:
        if not (0<=a<n and 0<=b<n):return {"status":"refuse","reason":"invalid_vertex"}
        if a in given and given[a]!=b:return {"status":"refuse","reason":"contradictory_edge"}
        given[a]=b
    if len(set(given.values()))!=len(given):return {"status":"refuse","reason":"not_injective"}
    completions=[p for p in permutations(range(n)) if all(p[a]==b for a,b in given.items())]
    if not completions:return {"status":"refuse","reason":"no_completion"}
    types=sorted(set(cycle_type(p) for p in completions))
    orders=sorted(set(spectral_profile(p)[1] for p in completions))
    return {"status":"identified" if len(types)==1 else "ambiguous",
            "completions":len(completions),"cycle_types":types,
            "possible_orders":orders,
            "full_orbit_certain":all(t==(n,) for t in types),
            "full_orbit_possible":any(t==(n,) for t in types)}
