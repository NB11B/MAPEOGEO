"""Replacement/factorization route for mixed-rank Erdős #19 incidence families."""
from __future__ import annotations
from itertools import product
from .erdos19_edge_coloring_route import round_robin_edge_coloring_complete_graph
from .erdos19_rank_decomposition import rank_partition


def admissible_replacement_colors(n,high_edge,base_coloring):
    """Colors whose base K_n incidence at every vertex of h is internal to h or absent."""
    h=frozenset(high_edge);ok=[]
    for c in range(n):
        good=True
        for v in h:
            incident=[e for e,col in base_coloring.items() if col==c and v in e]
            if incident and not all(e<=h for e in incident):
                good=False;break
        if good:ok.append(c)
    return tuple(ok)


def replacement_coloring(n,family):
    parts=rank_partition(family)
    pairs=set(parts.get(2,()))
    high=tuple(e for r,es in parts.items() if r>=3 for e in es)
    base=round_robin_edge_coloring_complete_graph(n)
    choices=[admissible_replacement_colors(n,h,base) for h in high]
    if any(not c for c in choices):return None
    for colors in product(*choices):
        hc=dict(zip(high,colors))
        if any(h&k and hc[h]==hc[k] for i,h in enumerate(high) for k in high[i+1:]):
            continue
        result={e:base[e] for e in pairs}
        result.update(hc)
        return result
    return None

def relabeled_base_coloring(n,perm):
    base=round_robin_edge_coloring_complete_graph(n)
    return {frozenset((perm[a],perm[b])):c for e,c in base.items() for a,b in [tuple(e)]}


def replacement_coloring_over_relabelings(n,family):
    from itertools import permutations
    parts=rank_partition(family)
    pairs=set(parts.get(2,()))
    high=tuple(e for r,es in parts.items() if r>=3 for e in es)
    for perm in permutations(range(n)):
        base=relabeled_base_coloring(n,perm)
        choices=[admissible_replacement_colors(n,h,base) for h in high]
        if any(not c for c in choices):continue
        for colors in product(*choices):
            hc=dict(zip(high,colors))
            if any(h&k and hc[h]==hc[k] for i,h in enumerate(high) for k in high[i+1:]):continue
            result={e:base[e] for e in pairs};result.update(hc)
            return result
    return None
