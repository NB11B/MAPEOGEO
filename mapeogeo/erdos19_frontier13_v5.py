"""Public n=13,m=33 EFL frontier witness from the 2026 Erdős #19 audit."""
from __future__ import annotations

LINES_33=tuple(map(frozenset,[
 (0,1),(0,3),(0,4),(0,5),(0,6),(0,8),(0,9),(0,12),(1,10),(4,5),(6,11),(8,10),
 (0,2,10),(0,7,11),(1,2,6),(1,3,4),(1,5,11),(1,7,12),(1,8,9),(2,3,7),
 (2,4,12),(2,5,9),(2,8,11),(3,5,10),(3,6,8),(4,6,9),(4,7,8),(4,10,11),
 (5,6,7),(5,8,12),(6,10,12),(7,9,10),(3,9,11,12),
]))


def verify_linear_space(n,lines):
    pairs={}
    for idx,e in enumerate(lines):
        for a in e:
            if not 0<=a<n:return False
        for a in e:
            for b in e:
                if a<b:
                    if (a,b) in pairs:return False
                    pairs[(a,b)]=idx
    return len(pairs)==n*(n-1)//2


def exact_edge_coloring(n,lines):
    lines=tuple(lines)
    conflicts=[set() for _ in lines]
    for i,e in enumerate(lines):
        for j in range(i):
            if e&lines[j]:conflicts[i].add(j);conflicts[j].add(i)
    order=sorted(range(len(lines)),key=lambda i:(-len(conflicts[i]),-len(lines[i]),i))
    color={};used=[set() for _ in range(n)]
    def dfs(k):
        if k==len(order):return True
        i=order[k];e=lines[i]
        forbidden=set().union(*(used[v] for v in e))
        for c in range(n):
            if c in forbidden:continue
            color[i]=c
            for v in e:used[v].add(c)
            if dfs(k+1):return True
            for v in e:used[v].remove(c)
            del color[i]
        return False
    return tuple(color[i] for i in range(len(lines))) if dfs(0) else None


def verify_edge_coloring(n,lines,colors):
    if colors is None or len(colors)!=len(lines):return False
    for i,e in enumerate(lines):
        if not 0<=colors[i]<n:return False
        for j in range(i):
            if e&lines[j] and colors[i]==colors[j]:return False
    return True
