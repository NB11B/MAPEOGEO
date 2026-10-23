"""PSMSL operator algebra: information and ordering semantics."""
from __future__ import annotations
from dataclasses import dataclass
import math

Matrix=tuple[tuple[float,...],...]

def matmul(A:Matrix,B:Matrix)->Matrix:
    if not A or not B or len(A[0])!=len(B):raise ValueError("shape mismatch")
    return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))) for i in range(len(A)))
def matsub(A,B):
    return tuple(tuple(A[i][j]-B[i][j] for j in range(len(A[0]))) for i in range(len(A)))
def frobenius(A):return math.sqrt(sum(x*x for r in A for x in r))
def rank(A,tol=1e-10):
    M=[list(map(float,r)) for r in A];m=len(M);n=len(M[0]) if M else 0;r=0
    for c in range(n):
        p=next((i for i in range(r,m) if abs(M[i][c])>tol),None)
        if p is None:continue
        M[r],M[p]=M[p],M[r];q=M[r][c];M[r]=[x/q for x in M[r]]
        for i in range(m):
            if i!=r:
                q=M[i][c]
                if abs(q)>tol:M[i]=[M[i][j]-q*M[r][j] for j in range(n)]
        r+=1
    return r
def commutator(A,B):return matsub(matmul(A,B),matmul(B,A))

@dataclass(frozen=True)
class InformationSemantics:
    input_dim:int;output_dim:int;rank:int;nullity:int
    injective:bool;surjective:bool;invertible:bool;information_loss:bool

@dataclass(frozen=True)
class OrderingSemantics:
    commutator_norm:float;commutes:bool;reorder_safe:bool;parallel_candidate:bool

def information_semantics(A,tol=1e-10):
    m=len(A);n=len(A[0]) if A else 0;r=rank(A,tol)
    return InformationSemantics(n,m,r,n-r,r==n,r==m,m==n==r,r<n)

def ordering_semantics(A,B,tol=1e-10):
    C=commutator(A,B);norm=frobenius(C);ok=norm<=tol
    return OrderingSemantics(norm,ok,ok,ok)

def fuse(A,B):return matmul(B,A)
