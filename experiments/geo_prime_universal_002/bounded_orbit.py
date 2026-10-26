"""Bounded operational orbit test, no gcd or primality feature in classifier."""
from native import shift
def bounded_reach(n,k):
    A=shift(n,k)
    visited=set();position=0
    for _ in range(n):
        visited.add(position)
        position=next(j for j,v in enumerate(A[position]) if v==1)
    return len(visited)==n, len(visited), position
def run(limit=80):
    mismatch=[]
    for n in range(2,limit+1):
        for k in range(1,n):
            full,visited,end=bounded_reach(n,k)
            from native import cycles
            expected=len(cycles(n,k))==1
            if full!=expected or end!=0:mismatch.append((n,k,visited,end))
    return {"limit":limit,"checked_steps":sum(n-1 for n in range(2,limit+1)),
            "mismatches":mismatch,"nine_step_three":bounded_reach(9,3),
            "seventeen_step_four":bounded_reach(17,4)}
if __name__=="__main__":
 import json
 print(json.dumps(run(),indent=2))
