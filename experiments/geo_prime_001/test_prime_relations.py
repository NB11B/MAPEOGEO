"""GEO-PRIME-001: relational-state/operator-order primality experiment.

No prime flags are supplied to the relational construction. A separate
trial-division oracle is used only after construction for independent scoring.
"""
from __future__ import annotations
import json
import math
import unittest

def is_prime_oracle(n: int) -> bool:
    return n >= 2 and not any(n % a == 0 for a in range(2,math.isqrt(n)+1))

def enumerate_relations(limit: int, ascending: bool = True):
    """Single-pass construction: factor edges require earlier registered vertices."""
    if limit < 2: raise ValueError("limit must be at least two")
    order = range(2,limit+1) if ascending else range(limit,1,-1)
    seen=set()
    state={}
    for x in order:
        pairs=[(a,x//a) for a in range(2,math.isqrt(x)+1)
               if x % a == 0 and a in seen and x//a in seen]
        state[x]=pairs
        seen.add(x)
    return state

def close_relations(limit: int):
    """Order-independent finite closure; factors must be < x and > 1."""
    return {x:[(a,x//a) for a in range(2,math.isqrt(x)+1)
               if x%a==0] for x in range(2,limit+1)}

def run(limit=1000):
    asc=enumerate_relations(limit,True)
    desc=enumerate_relations(limit,False)
    closed=close_relations(limit)
    candidate_values=[2]+[2*n+1 for n in range(1,(limit-1)//2+1)]
    scoring=lambda relations:sum((not bool(relations[x]))!=is_prime_oracle(x) for x in range(2,limit+1))
    witnesses={str(n):closed[n][:3] for n in range(2,22)}
    return {"limit":limit,"candidate_count":len(candidate_values),
            "odd_candidate_count":len(candidate_values)-1,
            "prime_count_from_ascending":sum(not bool(asc[n]) for n in candidate_values),
            "ascending_errors":scoring(asc),
            "descending_one_pass_errors":scoring(desc),
            "closed_errors":scoring(closed),
            "descending_false_prime_count":sum(not desc[n] and not is_prime_oracle(n) for n in range(2,limit+1)),
            "first_relation_witnesses":witnesses,
            "interpretation":"Primality is invariant under complete closure; knowledge of witnesses depends on event order."}

class Tests(unittest.TestCase):
    def test_ascending(self):self.assertEqual(run()["ascending_errors"],0)
    def test_closure(self):self.assertEqual(run()["closed_errors"],0)
    def test_generator(self):self.assertEqual(run()["candidate_count"],500)
    def test_prime_count(self):self.assertEqual(run()["prime_count_from_ascending"],168)
    def test_order(self):self.assertEqual(run()["descending_one_pass_errors"],831)
    def test_small_domain(self):self.assertEqual(run(20)["closed_errors"],0)
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):enumerate_relations(1)

if __name__=="__main__":
    print(json.dumps(run(),indent=2))
    unittest.main(argv=[""],exit=False)
