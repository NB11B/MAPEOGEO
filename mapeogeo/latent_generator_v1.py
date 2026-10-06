"""Latent-generator inverse/forward qualification primitives."""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class InverseResult:
    generator:tuple[float,...]
    null_basis:tuple[tuple[float,...],...]
    identifiable_rank:int
    residual:float
    source_identified:bool=False


def _rref(A,b,tol=1e-10):
    M=[list(map(float,row))+[float(y)] for row,y in zip(A,b)]
    m=len(M);n=len(A[0]) if A else 0;piv=[];r=0
    for c in range(n):
        p=next((i for i in range(r,m) if abs(M[i][c])>tol),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r]
        q=M[r][c];M[r]=[x/q for x in M[r]]
        for i in range(m):
            if i==r:continue
            q=M[i][c]
            if abs(q)>tol:M[i]=[M[i][j]-q*M[r][j] for j in range(n+1)]
        piv.append(c);r+=1
        if r==m:break
    return M,piv


def linear_inverse(P,y,tol=1e-9):
    """Minimum-free-variable-zero representative plus exact null-space basis."""
    if not P or len(P)!=len(y):raise ValueError("shape mismatch")
    n=len(P[0])
    if any(len(row)!=n for row in P):raise ValueError("ragged projection")
    M,piv=_rref(P,y,tol)
    for row in M:
        if all(abs(row[j])<=tol for j in range(n)) and abs(row[n])>tol:
            raise ValueError("inconsistent observation")
    x=[0.0]*n
    for i,c in enumerate(piv):x[c]=M[i][n]
    free=[j for j in range(n) if j not in piv];null=[]
    for f in free:
        z=[0.0]*n;z[f]=1.0
        for i,c in enumerate(piv):z[c]=-M[i][f]
        null.append(tuple(z))
    yh=[sum(P[i][j]*x[j] for j in range(n)) for i in range(len(P))]
    residual=math.sqrt(sum((yh[i]-y[i])**2 for i in range(len(y))))
    return InverseResult(tuple(x),tuple(null),len(piv),residual,False)


def forward(P,q):
    return tuple(sum(float(P[i][j])*float(q[j]) for j in range(len(q))) for i in range(len(P)))


def sinusoid_generator(amplitude,theta):
    return (amplitude*math.cos(theta),amplitude*math.sin(theta))


def radial_angular_velocity(amplitude,theta,d_amplitude,d_theta):
    r=(math.cos(theta),math.sin(theta))
    th=(-math.sin(theta),math.cos(theta))
    radial=(d_amplitude*r[0],d_amplitude*r[1])
    angular=(amplitude*d_theta*th[0],amplitude*d_theta*th[1])
    return radial,angular,(radial[0]+angular[0],radial[1]+angular[1])
