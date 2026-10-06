"""High-rank-first decomposition into residual list edge coloring for Erdős #19."""
from __future__ import annotations
from itertools import product
from .erdos19_rank_decomposition import rank_partition


def proper_hyperedge_coloring(edges,n,colors):
    assigned={}
    for e,c in zip(edges,colors):
        if not 0<=c<n: return None
        if any(c==assigned[f] and e&f for f in assigned): return None
        assigned[e]=c
    return assigned


def residual_pair_lists(n,family,high_coloring):
    parts=rank_partition(family)
    pairs=parts.get(2,())
    forbidden=[set() for _ in range(n)]
    for e,c in high_coloring.items():
        for v in e: forbidden[v].add(c)
    return {e:tuple(c for c in range(n) if c not in forbidden[next(iter(e))] and c not in forbidden[next(iter(e-{next(iter(e))}))]) for e in pairs}


def solve_list_edge_coloring(n,pair_lists):
    edges=sorted(pair_lists,key=lambda e:(len(pair_lists[e]),repr(e)))
    assigned={};used=[set() for _ in range(n)]
    def dfs(k):
        if k==len(edges): return True
        e=edges[k];u,v=tuple(e)
        for c in pair_lists[e]:
            if c in used[u] or c in used[v]: continue
            assigned[e]=c;used[u].add(c);used[v].add(c)
            if dfs(k+1): return True
            used[u].remove(c);used[v].remove(c);del assigned[e]
        return False
    return dict(assigned) if dfs(0) else None


def decompose_color(n,family,*,exhaustive_high=True):
    parts=rank_partition(family)
    high=tuple(e for r,es in parts.items() if r>=3 for e in es)
    if not high:
        high_assignments=[()]
    elif exhaustive_high:
        high_assignments=product(range(n),repeat=len(high))
    else:
        high_assignments=[tuple(range(len(high)))]
    for colors in high_assignments:
        hc=proper_hyperedge_coloring(high,n,colors)
        if hc is None: continue
        lists=residual_pair_lists(n,family,hc)
        pc=solve_list_edge_coloring(n,lists)
        if pc is not None:
            return {**hc,**pc}
    return None


def verify_coloring(n,family,coloring):
    fam=tuple(map(frozenset,family))
    if coloring is None or set(coloring)!=set(fam): return False
    if any(not 0<=c<n for c in coloring.values()): return False
    for i,e in enumerate(fam):
        for f in fam[i+1:]:
            if e&f and coloring[e]==coloring[f]: return False
    return True
