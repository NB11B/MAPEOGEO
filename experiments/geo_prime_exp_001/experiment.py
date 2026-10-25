"""Consecutive-power prime obstruction experiment; requires sympy."""
from sympy import isprime
def F(n):
    if n<1:raise ValueError("positive n required")
    return n**(n+1)+(n+1)**n
def prime_shift_witness(n):
    q=n+2
    return q if n>=3 and isprime(q) and F(n)%q==0 else None
def mod_three_witness(n):
    return 3 if n>=7 and n%6==1 and F(n)%3==0 else None
def run(limit=50):
    return {"limit":limit,"prime_indices":[n for n in range(1,limit+1) if isprime(F(n))],
      "prime_shift_cases":[n for n in range(1,limit+1) if prime_shift_witness(n)],
      "mod_three_cases":[n for n in range(1,limit+1) if mod_three_witness(n)],
      "first_eight":[F(n) for n in range(1,9)]}
if __name__=="__main__":
 import json
 print(json.dumps(run(),indent=2))
