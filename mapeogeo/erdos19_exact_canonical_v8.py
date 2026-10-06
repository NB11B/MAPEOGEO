"""Bounded individualization-refinement canonical labeling fallback."""
from __future__ import annotations
import hashlib,json


def _refine(adj,colors):
    colors=list(colors)
    while True:
        keys=[]
        for v,ns in enumerate(adj):
            counts={}
            for u in ns:counts[colors[u]]=counts.get(colors[u],0)+1
            keys.append((colors[v],tuple(sorted(counts.items()))))
        uniq={k:i for i,k in enumerate(sorted(set(keys),key=repr))}
        nxt=[uniq[k] for k in keys]
        if nxt==colors:return tuple(colors)
        colors=nxt


def incidence_graph(n,lines):
    lines=tuple(frozenset(e) for e in lines);N=n+len(lines)
    adj=[set() for _ in range(N)]
    for i,e in enumerate(lines):
        lv=n+i
        for v in e:adj[v].add(lv);adj[lv].add(v)
    sizes=sorted(set(map(len,lines)));sc={s:i+1 for i,s in enumerate(sizes)}
    colors=[0]*n+[sc[len(e)] for e in lines]
    return tuple(frozenset(x) for x in adj),tuple(colors)


def exact_canonical_digest(n,lines,max_states=200000):
    adj,initial=incidence_graph(n,lines);best=None;states=0
    def rec(colors):
        nonlocal best,states
        states+=1
        if states>max_states:raise RuntimeError("CANONICAL_STATE_LIMIT")
        colors=_refine(adj,colors)
        cells={}
        for v,c in enumerate(colors):cells.setdefault(c,[]).append(v)
        cell=next((vs for _,vs in sorted(cells.items()) if len(vs)>1),None)
        if cell is None:
            order=sorted(range(len(adj)),key=lambda v:colors[v])
            pos={v:i for i,v in enumerate(order)}
            code=tuple(sorted((min(pos[v],pos[u]),max(pos[v],pos[u])) for v in range(len(adj)) for u in adj[v] if v<u))
            if best is None or code<best:best=code
            return
        fresh=max(colors)+1
        for v in cell:
            c=list(colors);c[v]=fresh;rec(tuple(c))
    rec(initial)
    payload=json.dumps(best,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest(),states
