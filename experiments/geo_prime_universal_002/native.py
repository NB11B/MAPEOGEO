"""Native PSMSL matrix representation of directed cycle-step geometry."""
from pathlib import Path
import sys
VENDOR=Path(__file__).resolve().parents[2]/"ngc_geometry_lab"/"ngc_geometry_lab"/"_vendor"/"mapeogeo"
sys.path.insert(0,str(VENDOR))
from mapeogeo.psmsl_operator_algebra_v1 import matmul,information_semantics
from mapeogeo.psmsl_operator_basis_v1 import discover_linear_operator_basis
from math import isqrt
def shift(n,k):
    if n<2 or not 1<=k<n:raise ValueError("invalid step")
    return tuple(tuple(float(j==(i+k)%n) for j in range(n)) for i in range(n))
def cycles(n,k):
    shift(n,k)
    unseen=set(range(n));out=[]
    while unseen:
        start=min(unseen);seen=[start];unseen.remove(start);cur=(start+k)%n
        while cur!=start:
            if cur not in unseen:raise ValueError("inconsistent relation")
            unseen.remove(cur);seen.append(cur);cur=(cur+k)%n
        out.append(seen)
    return out
def geometry(n):
    if n<2:return {"prime":False,"witness":None}
    for k in range(1,n):
        cc=cycles(n,k)
        if len(cc)>1:return {"prime":False,"witness":{"step":k,"lengths":[len(v) for v in cc]}}
    return {"prime":True,"witness":None}
def native_audit(n,k):
    A=shift(n,k);B=shift(n,n-k)
    ident=tuple(tuple(float(i==j) for j in range(n)) for i in range(n))
    return {"inverse":matmul(A,B)==ident,"invertible":information_semantics(A).invertible,
      "rank":discover_linear_operator_basis((A,B)).rank,
      "lengths":[len(c) for c in cycles(n,k)]}
def reference(n):return n>=2 and all(n%d for d in range(2,isqrt(n)+1))
def run(limit=100):
    return {"limit":limit,"mismatches":[n for n in range(1,limit+1) if geometry(n)["prime"]!=reference(n)],
      "prime_count":sum(geometry(n)["prime"] for n in range(1,limit+1)),"n9_step3":native_audit(9,3)}
if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2))
