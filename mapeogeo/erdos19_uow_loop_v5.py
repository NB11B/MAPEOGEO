"""Continuous UoW research loop for Erdős #19 residual list coloring.

Searches high-rank colorings for the strongest residual local list slack and
reports counterexamples to candidate sufficient inequalities.
"""
from __future__ import annotations
from itertools import product
from .erdos19_rank_decomposition import rank_partition
from .erdos19_residual_list_coloring import proper_hyperedge_coloring,residual_pair_lists,solve_list_edge_coloring


def pair_degrees(family):
    pairs=rank_partition(family).get(2,())
    d={}
    for e in pairs:
        for v in e:d[v]=d.get(v,0)+1
    return d


def residual_metrics(n,family,high_coloring):
    lists=residual_pair_lists(n,family,high_coloring)
    deg=pair_degrees(family)
    rows=[]
    for e,L in lists.items():
        u,v=tuple(e)
        rows.append({
            "edge":e,"list_size":len(L),
            "max_degree":max(deg.get(u,0),deg.get(v,0)),
            "degree_sum_minus_one":deg.get(u,0)+deg.get(v,0)-1,
            "slack_max_plus_one":len(L)-(max(deg.get(u,0),deg.get(v,0))+1),
        })
    return tuple(rows)


def best_high_coloring(n,family):
    parts=rank_partition(family)
    high=tuple(e for r,es in parts.items() if r>=3 for e in es)
    if not high:return {}, residual_metrics(n,family,{})
    best=None
    for colors in product(range(n),repeat=len(high)):
        hc=proper_hyperedge_coloring(high,n,colors)
        if hc is None:continue
        rows=residual_metrics(n,family,hc)
        min_slack=min((r["slack_max_plus_one"] for r in rows),default=n)
        score=(min_slack,sum(r["list_size"] for r in rows))
        if best is None or score>best[0]:best=(score,hc,rows)
    return (best[1],best[2]) if best else (None,())


def candidate_bound_holds(n,family):
    hc,rows=best_high_coloring(n,family)
    return hc is not None and all(r["slack_max_plus_one"]>=0 for r in rows)


def residual_is_colorable(n,family):
    hc,_=best_high_coloring(n,family)
    if hc is None:return False
    return solve_list_edge_coloring(n,residual_pair_lists(n,family,hc)) is not None

def global_delta_bound_holds(n,family):
    hc,rows=best_high_coloring(n,family)
    if hc is None:return False
    deg=pair_degrees(family)
    delta=max(deg.values(),default=0)
    return all(r["list_size"]>=delta for r in rows)
