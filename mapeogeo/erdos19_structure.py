"""Structural view of the Erdős #19 shared-coloring CSP."""
from __future__ import annotations
from collections import defaultdict
from .erdos19_constructor import EFLInstance,shared_vertices


def conflict_graph(inst:EFLInstance):
    """Return adjacency among shared vertices that occur in a common clique."""
    vs=shared_vertices(inst)
    adj={v:set() for v in vs}
    shared=set(vs)
    for c in inst.cliques:
        s=[v for v in c if v in shared]
        for i,u in enumerate(s):
            for v in s[i+1:]:
                adj[u].add(v);adj[v].add(u)
    return {v:frozenset(n) for v,n in adj.items()}


def greedy_degeneracy_order(inst:EFLInstance):
    """Smallest-last order and degeneracy of the shared-vertex conflict graph."""
    adj={v:set(ns) for v,ns in conflict_graph(inst).items()}
    order=[];deg=0
    while adj:
        v=min(adj,key=lambda x:(len(adj[x]),repr(x)))
        deg=max(deg,len(adj[v]))
        ns=adj.pop(v)
        for u in ns:
            if u in adj: adj[u].discard(v)
        order.append(v)
    return tuple(order),deg


def degeneracy_coloring(inst:EFLInstance):
    order,deg=greedy_degeneracy_order(inst)
    if deg>=inst.n:
        return None,deg
    adj=conflict_graph(inst);color={}
    for v in reversed(order):
        used={color[u] for u in adj[v] if u in color}
        color[v]=next(c for c in range(inst.n) if c not in used)
    return color,deg
