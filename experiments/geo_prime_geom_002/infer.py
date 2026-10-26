"""Infer affine recurrence from consecutive triangles without supplied coefficients."""
from fractions import Fraction
from experiment import generate

def solve(A,b):
    rows=[[Fraction(v) for v in x]+[Fraction(y)] for x,y in zip(A,b)]
    n=len(rows)
    for i in range(n):
        p=next((k for k in range(i,n) if rows[k][i]),None)
        if p is None:raise ValueError("nonidentifiable coefficients")
        rows[i],rows[p]=rows[p],rows[i]
        d=rows[i][i];rows[i]=[v/d for v in rows[i]]
        for k in range(n):
            if i!=k:
                d=rows[k][i];rows[k]=[a-d*v for a,v in zip(rows[k],rows[i])]
    return tuple(r[-1] for r in rows)

def discover():
    rows=generate()
    x=[[r["base"],r["hypotenuse"],1] for r in rows[:-1]]
    y=[[r["base"],r["hypotenuse"]] for r in rows[1:]]
    coeff=tuple(solve(x[:3],[v[j] for v in y[:3]]) for j in (0,1))
    predict=lambda row:tuple(sum(a*b for a,b in zip(c,row)) for c in coeff)
    if not all(predict(a)==tuple(b) for a,b in zip(x,y)):
        raise ValueError("failed withheld recurrence transitions")
    return coeff,len(x)-3
if __name__=="__main__":print(discover())
