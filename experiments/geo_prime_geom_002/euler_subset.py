"""Euler product for the finite subset of primes found as Pell hypotenuses."""
from math import prod
from experiment import generate
def closure(primes,cap):
    states={1}
    for p in primes:
        new=set()
        for n in states:
            m=n
            while m<=cap:
                new.add(m)
                m*=p
        states=new
    return states
def run(cap=20000):
    primes=[v["hypotenuse"] for v in generate() if v["prime"]]
    states=closure(primes,cap)
    total=prod(1/(1-1/p**2) for p in primes)
    removed=prod(1/(1-1/p**2) for p in primes if p!=5)
    return {"primes":primes,
            "prime_reciprocal_square_sum":sum(1/p**2 for p in primes),
            "subset_euler_product":total,"restricted_semigroup_count":len(states),
            "restricted_sum":sum(1/n**2 for n in states),
            "excluded_five_product_ratio":removed/total,
            "predicted_ratio":1-1/25,
            "contains_two":2 in states}
if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2))
