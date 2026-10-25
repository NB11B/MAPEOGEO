"""C4 versus V4 observational nonidentifiability without operator identifiers."""
from collections import Counter
import json

def cyclic_four():
    return tuple(tuple((x+k)%4 for x in range(4)) for k in range(4))

def klein_four():
    return tuple(tuple(x^k for x in range(4)) for k in range(4))

def observations(operators):
    n=len(operators)
    if n<2 or any(len(p)!=n or sorted(p)!=list(range(n)) for p in operators):
        raise ValueError("invalid permutation family")
    return Counter((i,p[i]) for p in operators for i in range(n))

def permutation_order(p):
    n=len(p);x=tuple(range(n))
    for k in range(1,n+1):
        x=tuple(p[y] for y in x)
        if x==tuple(range(n)):return k
    raise AssertionError("not a permutation")

def signature(ops):
    return tuple(sorted(permutation_order(p) for p in ops))

def qualify(rows):
    if rows==observations(cyclic_four())==observations(klein_four()):
        return {"status":"refuse","reason":"C4_V4_observational_collision",
                "alternative_signatures":[signature(cyclic_four()),signature(klein_four())]}
    return {"status":"refuse","reason":"unique_structure_not_established"}

def run():
    c,v=cyclic_four(),klein_four()
    a,b=observations(c),observations(v)
    return {"vertex_count":4,"events":sum(a.values()),
        "same_unlabeled_observations":a==b,
        "all_pairs_once":len(a)==16 and set(a.values())=={1},
        "cyclic_signature":signature(c),"klein_signature":signature(v),
        "decision":qualify(a)}
if __name__=="__main__":print(json.dumps(run(),indent=2))
