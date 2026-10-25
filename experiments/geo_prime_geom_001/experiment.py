"""Consecutive-leg right triangles: exact geometry and prime counterexamples."""
import math,json
def is_prime(n):
    return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))
def consecutive_triangles(limit=200000):
    rows=[]
    for n in range(1,limit):
        c2=n*n+(n+1)**2;c=math.isqrt(c2)
        if c*c==c2:
            rows.append(dict(base=n,height=n+1,hypotenuse=c,prime=is_prime(c),
              hypotenuse_square=math.isqrt(c)**2==c,primitive=math.gcd(n,n+1)==1,
              pell=(2*n+1)**2-2*c*c==-1))
    return rows
def run():
    rows=consecutive_triangles()
    return dict(search_limit_exclusive=200000,integer_triangles=len(rows),
        prime_hypotenuses=sum(r["prime"] for r in rows),
        composite_hypotenuses=sum(not r["prime"] for r in rows),
        all_primitive=all(r["primitive"] for r in rows),
        all_negative_pell=all(r["pell"] for r in rows),cases=rows)
if __name__=="__main__":print(json.dumps(run(),indent=2))
