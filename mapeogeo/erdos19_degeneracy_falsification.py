"""Falsification search for the candidate Erdős #19 degeneracy bridge.

Dual shared-incidence model:
- each shared vertex is a subset I(v) of clique indices with |I(v)| >= 2;
- linearity requires |I(u) ∩ I(v)| <= 1 for distinct shared vertices;
- conflict adjacency is nonempty intersection.

The candidate bridge is degeneracy(conflict graph) < n.
"""
from __future__ import annotations
from itertools import combinations


def valid_linear_family(family):
    fam=tuple(frozenset(s) for s in family)
    return all(len(s)>=2 for s in fam) and all(len(a&b)<=1 for a,b in combinations(fam,2))


def conflict_adjacency(family):
    fam=tuple(frozenset(s) for s in family)
    return {i:{j for j,b in enumerate(fam) if i!=j and fam[i]&b} for i in range(len(fam))}


def degeneracy(family):
    adj={v:set(ns) for v,ns in conflict_adjacency(family).items()}
    d=0
    while adj:
        v=min(adj,key=lambda x:(len(adj[x]),x))
        d=max(d,len(adj[v]))
        for u in adj.pop(v):
            if u in adj: adj[u].discard(v)
    return d


def pair_only_family(n:int):
    return tuple(frozenset(p) for p in combinations(range(n),2))


def falsify_pair_family(n:int):
    fam=pair_only_family(n)
    assert valid_linear_family(fam)
    return {"n":n,"shared_vertices":len(fam),"degeneracy":degeneracy(fam),"bridge_holds":degeneracy(fam)<n}
