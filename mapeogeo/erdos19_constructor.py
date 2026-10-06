"""Bounded constructor synthesis for the shared-vertex coloring obligation in Erdős #19.

This is a finite CSP constructor/search.  Success on bounded instances is not a
universal proof of the Erdős-Faber-Lovász theorem.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Hashable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class EFLInstance:
    n: int
    cliques: tuple[frozenset[Hashable],...]

    def __post_init__(self):
        if self.n < 0 or len(self.cliques) != self.n:
            raise ValueError("expected exactly n cliques")
        if any(len(c) != self.n for c in self.cliques):
            raise ValueError("each clique must have n vertices")
        for i in range(self.n):
            for j in range(i):
                if len(self.cliques[i] & self.cliques[j]) > 1:
                    raise ValueError("cliques must intersect in at most one vertex")


def shared_vertices(inst:EFLInstance)->tuple[Hashable,...]:
    counts={}
    for c in inst.cliques:
        for v in c:
            counts[v]=counts.get(v,0)+1
    return tuple(sorted((v for v,k in counts.items() if k>=2),key=repr))


def valid_shared_coloring(inst:EFLInstance,coloring:Mapping[Hashable,int])->bool:
    shared=set(shared_vertices(inst))
    if set(coloring)!=shared:
        return False
    if any(not (0<=c<inst.n) for c in coloring.values()):
        return False
    for clique in inst.cliques:
        vals=[coloring[v] for v in clique if v in shared]
        if len(vals)!=len(set(vals)):
            return False
    return True


def synthesize_shared_coloring(inst:EFLInstance)->dict[Hashable,int]|None:
    vertices=shared_vertices(inst)
    incident={v:[i for i,c in enumerate(inst.cliques) if v in c] for v in vertices}
    # Most constrained first: high incidence, then deterministic repr.
    order=sorted(vertices,key=lambda v:(-len(incident[v]),repr(v)))
    assigned={}
    used=[set() for _ in range(inst.n)]

    def dfs(k:int)->bool:
        if k==len(order):
            return True
        v=order[k]
        forbidden=set().union(*(used[i] for i in incident[v])) if incident[v] else set()
        for color in range(inst.n):
            if color in forbidden:
                continue
            assigned[v]=color
            for i in incident[v]: used[i].add(color)
            if dfs(k+1): return True
            for i in incident[v]: used[i].remove(color)
            del assigned[v]
        return False

    return dict(assigned) if dfs(0) else None
