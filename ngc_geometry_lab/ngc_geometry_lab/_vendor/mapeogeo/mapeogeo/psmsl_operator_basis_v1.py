"""PSMSL operator-basis discovery for finite matrix operator sets."""
from __future__ import annotations
from dataclasses import dataclass
from .psmsl_operator_algebra_v1 import rank

def flatten(A):return tuple(float(x) for row in A for x in row)

@dataclass(frozen=True)
class OperatorBasis:
    basis_indices:tuple[int,...]
    rank:int
    redundant_indices:tuple[int,...]

def discover_linear_operator_basis(operators,tol=1e-10):
    if not operators:return OperatorBasis((),0,())
    vecs=[flatten(A) for A in operators]
    chosen=[];current=[]
    r0=0
    for i,v in enumerate(vecs):
        candidate=current+[v]
        # vectors are rows; rank detects span growth.
        r=rank(tuple(candidate),tol)
        if r>r0:
            chosen.append(i);current=candidate;r0=r
    redundant=tuple(i for i in range(len(operators)) if i not in chosen)
    return OperatorBasis(tuple(chosen),r0,redundant)
