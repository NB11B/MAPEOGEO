"""Trajectory observability for latent generators."""
from __future__ import annotations
from dataclasses import dataclass
from .latent_generator_v1 import linear_inverse


def matmul(A,B):
    return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))) for i in range(len(A)))
def eye(n): return tuple(tuple(1.0 if i==j else 0.0 for j in range(n)) for i in range(n))
def stack_observations(Ps,ys):
    P=[];y=[]
    for Pi,yi in zip(Ps,ys):
        P.extend(tuple(map(float,row)) for row in Pi);y.extend(map(float,yi))
    return tuple(P),tuple(y)
def trajectory_inverse(Ps,ys):
    P,y=stack_observations(Ps,ys)
    return linear_inverse(P,y)
def observability_matrix(A,C,steps=None):
    n=len(A);steps=n if steps is None else steps
    power=eye(n);rows=[]
    for _ in range(steps):
        CA=matmul(C,power);rows.extend(CA);power=matmul(power,A)
    return tuple(rows)
def dynamic_initial_state_inverse(A,C,ys):
    O=observability_matrix(A,C,len(ys))
    y=tuple(v for sample in ys for v in sample)
    return linear_inverse(O,y)
