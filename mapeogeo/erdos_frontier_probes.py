"""Finite witness probes for selected open Erdős problems.

These are search/verification tools, never proof upgrades for the asymptotic or
infinite statements.
"""
from __future__ import annotations
from itertools import combinations
import math


def distinct_distance_count(points) -> int:
    vals=set()
    for a,b in combinations(points,2):
        vals.add(sum((float(x)-float(y))**2 for x,y in zip(a,b)))
    return len(vals)


def collinear_triple_3d(points):
    for i,j,k in combinations(range(len(points)),3):
        a,b,c=points[i],points[j],points[k]
        u=[b[t]-a[t] for t in range(3)]
        v=[c[t]-a[t] for t in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        if cross==(0,0,0):
            return (i,j,k)
    return None


def greedy_sidon(n_terms:int) -> tuple[int,...]:
    if n_terms<1:
        return ()
    seq=[1]
    sums={2}
    candidate=2
    while len(seq)<n_terms:
        new_sums=[candidate+a for a in seq]+[2*candidate]
        if len(new_sums)==len(set(new_sums)) and not any(s in sums for s in new_sums):
            seq.append(candidate)
            sums.update(new_sums)
        candidate+=1
    return tuple(seq)


def sidon_verified(seq) -> bool:
    seen=set()
    for i,a in enumerate(seq):
        for b in seq[i:]:
            s=a+b
            if s in seen:
                return False
            seen.add(s)
    return True
