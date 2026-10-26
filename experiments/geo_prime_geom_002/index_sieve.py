"""Structural filter: composite odd Pell indices produce composite hypotenuses."""
from math import isqrt
from experiment import generate,is_prime

def pell(n):
    if n<0:raise ValueError("negative Pell index")
    a,b=0,1
    for _ in range(n):a,b=b,2*b+a
    return a

def odd_factor(k):
    if k<3 or k%2==0:raise ValueError("odd index >=3 required")
    return next((d for d in range(3,isqrt(k)+1,2) if k%d==0),None)

def run(max_index=101):
    tested=list(range(3,max_index+1,2))
    forced=[];undetermined=[]
    for k in tested:
        d=odd_factor(k)
        if d:
            if pell(k)%pell(d)!=0:raise AssertionError("Pell divisibility failed")
            forced.append((k,d,pell(d),pell(k)//pell(d)))
        else:undetermined.append(k)
    geometry=generate()
    return {"max_odd_index":max_index,"odd_indices_tested":len(tested),
        "forced_composite":len(forced),"unresolved_indices":len(undetermined),
        "all_sieve_witnesses_nontrivial":all(a>1 and b>1 for _,_,a,b in forced),
        "geometry_alignment":all(pell(2*i+3)==r["hypotenuse"] for i,r in enumerate(geometry)),
        "prime_index_composite_counterexample":{"index":7,"hypotenuse":pell(7),"prime":is_prime(pell(7))},
        "first_witnesses":forced[:8]}
if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2))
