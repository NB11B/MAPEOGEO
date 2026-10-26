"""Exact Pell recurrence with independent finite-domain completeness and prime checks."""
import json
from math import isqrt,gcd
def is_prime(n):
    return n>=2 and all(n%d for d in range(2,isqrt(n)+1))
def next_triangle(n,c):
    return 3*n+2*c+1,4*n+3*c+2
def generate(limit=200000):
    n,c=3,5;rows=[]
    while n<limit:
        rows.append({"base":n,"height":n+1,"hypotenuse":c,"prime":is_prime(c),
                     "perfect_square":isqrt(c)**2==c})
        n,c=next_triangle(n,c)
    return rows
def brute(limit):
    found=[]
    for n in range(1,limit):
        h=n*n+(n+1)*(n+1);c=isqrt(h)
        if c*c==h:found.append((n,c))
    return found
def run(limit=200000):
    rows=generate(limit)
    return {"limit":limit,"rows":rows,"number_of_candidates":len(rows),
            "prime_count":sum(x["prime"] for x in rows),
            "composite_count":sum(not x["prime"] for x in rows),
            "exact_brute_agreement":[(x["base"],x["hypotenuse"]) for x in rows]==brute(limit),
            "all_primitive":all(gcd(x["base"],x["height"])==1 for x in rows),
            "all_pell":all((2*x["base"]+1)**2-2*x["hypotenuse"]**2==-1 for x in rows),
            "square_filter_false_accepts":sum(not x["prime"] and not x["perfect_square"] for x in rows)}
if __name__=="__main__":print(json.dumps(run(),indent=2))
