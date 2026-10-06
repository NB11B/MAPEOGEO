"""Rank decomposition of the dual linear-hypergraph form of Erdős #19."""
from __future__ import annotations
from itertools import combinations
from .erdos19_degeneracy_falsification import valid_linear_family


def rank_partition(family):
    out={}
    for e in map(frozenset,family):
        out.setdefault(len(e),[]).append(e)
    return {r:tuple(es) for r,es in sorted(out.items())}


def pair_conflicts_with_high(pair,high):
    return bool(frozenset(pair)&frozenset(high))


def high_rank_pair_budget(n:int,family):
    """For each high-rank hyperedge, count pair edges it conflicts with."""
    parts=rank_partition(family)
    pairs=parts.get(2,())
    return {h:sum(pair_conflicts_with_high(p,h) for p in pairs) for r,hs in parts.items() if r>=3 for h in hs}


def incidence_degree(n:int,family):
    deg=[0]*n
    for e in family:
        for v in e: deg[v]+=1
    return tuple(deg)


def candidate_all_subsets_up_to_rank(n:int,max_rank:int):
    return tuple(frozenset(s) for r in range(2,max_rank+1) for s in combinations(range(n),r))


def greedy_linear_families(n:int,max_rank:int):
    """Deterministic maximal families from each cyclic candidate ordering.

    This is a bounded falsification generator, not exhaustive enumeration.
    """
    cand=list(candidate_all_subsets_up_to_rank(n,max_rank))
    outs=[]
    for shift in range(max(1,len(cand))):
        order=cand[shift:]+cand[:shift]
        fam=[]
        for e in order:
            if all(len(e&f)<=1 for f in fam): fam.append(e)
        t=tuple(fam)
        if t not in outs: outs.append(t)
    return tuple(outs)
