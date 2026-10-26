"""GEO-BSL-001: finite spectral invariant discovery and falsification."""
from __future__ import annotations
import argparse
import json
import math
import numpy as np

def cycle_adjacency(n):
    if n < 3: raise ValueError("cycle requires >=3 vertices")
    a=np.zeros((n,n),dtype=float)
    for i in range(n): a[i,(i+1)%n]=a[(i+1)%n,i]=1
    return a

def path_adjacency(n):
    if n < 2: raise ValueError("path requires >=2 vertices")
    a=np.zeros((n,n),dtype=float)
    for i in range(n-1): a[i,i+1]=a[i+1,i]=1
    return a

def laplacian(a):
    if a.ndim != 2 or a.shape[0]!=a.shape[1] or not np.allclose(a,a.T) or np.any(a<0) or not np.allclose(np.diag(a),0):
        raise ValueError("invalid adjacency")
    return np.diag(a.sum(axis=1))-a

def topology(a):
    n=len(a)
    if not np.all(np.isclose(a,0)|np.isclose(a,1)): return "weighted_or_invalid"
    seen={0}; stack=[0]
    while stack:
        i=stack.pop()
        for j in np.flatnonzero(a[i]>0):
            if int(j) not in seen: seen.add(int(j)); stack.append(int(j))
    if len(seen)!=n: return "disconnected"
    degrees=a.sum(axis=1)
    if n>=3 and np.all(degrees==2): return "cycle"
    if n>=2 and np.count_nonzero(degrees==1)==2 and np.count_nonzero(degrees==2)==n-2: return "path"
    return "other"

def inverse_trace(a):
    eigenvalues=np.linalg.eigvalsh(laplacian(a))
    return float(np.sum(1/eigenvalues[eigenvalues>1e-9]))

def fit_cycle_invariant(sizes=(5,7,9,12,16,21)):
    x=np.array([[n*n,1] for n in sizes],dtype=float)
    y=np.array([inverse_trace(cycle_adjacency(n)) for n in sizes])
    a,b=np.linalg.lstsq(x,y,rcond=None)[0]
    return float(a),float(b)

def accepts(a,coeff,tolerance=1e-7):
    return topology(a)=="cycle" and abs(inverse_trace(a)-(coeff[0]*len(a)**2+coeff[1]))<tolerance

def run():
    training=(5,7,9,12,16,21)
    holdout=(6,8,11,14,18,25,32,48)
    coeff=fit_cycle_invariant(training)
    errors=[abs(inverse_trace(cycle_adjacency(n))-(coeff[0]*n*n+coeff[1])) for n in holdout]
    rng=np.random.default_rng(20261025)
    permutations=all(accepts(cycle_adjacency(n)[np.ix_(p,p)],coeff) for n in holdout for p in [rng.permutation(n)])
    broken=cycle_adjacency(16); broken[0,1]=broken[1,0]=0
    weighted=cycle_adjacency(16); weighted[0,1]=weighted[1,0]=2
    disconnected=np.zeros((16,16))
    disconnected[:8,:8]=cycle_adjacency(8); disconnected[8:,8:]=cycle_adjacency(8)
    partial=sum(1/(k*k) for k in range(1,10001))
    return dict(training_sizes=list(training),holdout_sizes=list(holdout),
        fitted_a=coeff[0],fitted_b=coeff[1],max_holdout_absolute_error=max(errors),
        permuted_holdout_pass=permutations,broken_cycle_rejected=not accepts(broken,coeff),
        path_rejected=not accepts(path_adjacency(16),coeff),
        weighted_cycle_rejected=not accepts(weighted,coeff),
        disconnected_cycles_rejected=not accepts(disconnected,coeff),
        basel_partial_10000=partial,basel_reference=math.pi**2/6,
        basel_error=abs(partial-math.pi**2/6),
        stage="finite spectral identity verified; MAPEOGEO operator integration pending")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output")
    args=parser.parse_args()
    payload=json.dumps(run(),indent=2,sort_keys=True)
    if args.output:
        with open(args.output,"w",encoding="utf-8") as f: f.write(payload+"\n")
    print(payload)

if __name__=="__main__": main()
