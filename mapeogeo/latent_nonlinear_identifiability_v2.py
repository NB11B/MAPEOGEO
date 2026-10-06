"""Nonlinear local identifiability via finite-difference Jacobian rank."""
from __future__ import annotations
from .latent_generator_v1 import linear_inverse

def jacobian(f,x,eps=1e-6):
    x=list(map(float,x));base=tuple(f(tuple(x)));J=[]
    cols=[]
    for j in range(len(x)):
        xp=x[:];xm=x[:];xp[j]+=eps;xm[j]-=eps
        fp=tuple(f(tuple(xp)));fm=tuple(f(tuple(xm)))
        cols.append(tuple((fp[i]-fm[i])/(2*eps) for i in range(len(base))))
    return tuple(tuple(cols[j][i] for j in range(len(x))) for i in range(len(base)))

def local_identifiability(f,x):
    J=jacobian(f,x)
    # Zero observation gives rank/nullspace without requiring a state solve.
    r=linear_inverse(J,tuple(0.0 for _ in J))
    return J,r.identifiable_rank,r.null_basis
