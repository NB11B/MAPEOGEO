"""Independent bounded CNF exact-counting oracles; NOT an ETH implementation."""
from functools import lru_cache
from itertools import product

def validate(n, clauses):
    if n < 0:
        raise ValueError("negative variable count")
    cs = tuple(tuple(int(x) for x in clause) for clause in clauses)
    if any(l == 0 or abs(l) > n for clause in cs for l in clause):
        raise ValueError("literal outside 1..n")
    return cs

def brute_count(n, clauses):
    cs = validate(n, clauses)
    return sum(all(any((a[abs(l)-1] if l > 0 else not a[abs(l)-1])
                       for l in clause) for clause in cs)
               for a in product((False, True), repeat=n))

def dpll_count(n, clauses):
    cs = validate(n, clauses)
    @lru_cache(None)
    def rec(formula, remaining):
        if not formula:
            return 1 << len(remaining)
        if () in formula:
            return 0
        frequencies = {abs(l) for clause in formula for l in clause}
        v = max(frequencies, key=lambda x: sum(x == abs(l) for c in formula for l in c))
        def branch(value):
            lit = v if value else -v
            reduced = tuple(tuple(l for l in c if l != -lit)
                            for c in formula if lit not in c)
            return rec(reduced, tuple(x for x in remaining if x != v))
        return branch(False) + branch(True)
    return rec(cs, tuple(range(1, n+1)))

def run_tests():
    import random
    rng = random.Random(20261026)
    cases = [(0,()), (1,()), (1,((1,),)), (1,((1,),(-1,))),
             (3,((1,-1),)), (4,((1,2),(-1,3),(-3,4)))]
    for n in range(1, 11):
        for _ in range(45):
            cs = tuple(tuple(rng.choice((-1,1))*rng.randint(1,n)
                             for __ in range(rng.randint(0,3)))
                       for ___ in range(rng.randrange(0,17)))
            cases.append((n,cs))
    for index,(n,cs) in enumerate(cases):
        a,b = brute_count(n,cs),dpll_count(n,cs)
        assert a == b, (index,n,cs,a,b)
        assert (a > 0) == (b > 0)
    print(f"PASS {len(cases)}/{len(cases)} exact-count cross-checks")

if __name__ == "__main__":
    run_tests()
