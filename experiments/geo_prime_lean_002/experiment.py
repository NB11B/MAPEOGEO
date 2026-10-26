"""Finite independent oracle and interaction-derived prime reconstruction."""
import json,math
def interaction(a,b):
    return ((a+b)**2-a*a-b*b)//2
def recursive(a,b):
    result=0
    for _ in range(b):result+=a
    return result
def observed_coefficient():
    samples=[(a,b,(a+b)**2-a*a-b*b) for a in range(1,4) for b in range(1,4)]
    coefficients={s//(a*b) for a,b,s in samples}
    if len(coefficients)!=1:raise ValueError("nonconstant interaction")
    return coefficients.pop()
def derived_primes(limit=200):
    return [n for n in range(2,limit+1)
            if not any(interaction(a,b)==n for a in range(2,n) for b in range(2,n//a+1))]
def oracle(n):
    return n>1 and all(n%d for d in range(2,math.isqrt(n)+1))
def run():
    values=[(a,b) for a in range(21) for b in range(21)]
    primes=derived_primes()
    return dict(coefficient=observed_coefficient(),tested_pairs=len(values),
      operator_errors=sum(interaction(a,b)!=recursive(a,b) for a,b in values),
      prime_count=len(primes),prime_errors=sum((n in primes)!=oracle(n) for n in range(2,201)),
      mutated_coefficient_rejected=any(((a+b)**2-a*a-b*b)//3!=a*b for a,b in values),
      zero_cases_pass=all(interaction(0,n)==0 for n in range(21)))
if __name__=="__main__":print(json.dumps(run(),indent=2))
