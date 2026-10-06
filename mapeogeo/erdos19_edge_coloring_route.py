"""Surviving structural route after degeneracy falsification for Erdős #19."""
from __future__ import annotations
from itertools import combinations
from .erdos19_degeneracy_falsification import pair_only_family


def round_robin_edge_coloring_complete_graph(n:int):
    """Construct an edge coloring of K_n with n colors (not necessarily optimal).

    For odd n, standard round-robin uses n colors.
    For even n, it uses n-1 colors, embedded in n available colors.
    """
    vertices=list(range(n))
    dummy=None
    if n%2==1:
        dummy=n
        vertices.append(dummy)
    m=len(vertices)
    fixed=vertices[-1]
    ring=vertices[:-1]
    coloring={}
    rounds=m-1
    for color in range(rounds):
        pairs=[]
        pairs.append((fixed,ring[0]))
        for i in range(1,m//2):
            pairs.append((ring[i],ring[-i]))
        for a,b in pairs:
            if a!=dummy and b!=dummy:
                coloring[frozenset((a,b))]=color
        ring=[ring[0]]+[ring[-1]]+ring[1:-1]
    return coloring


def verify_pair_family_coloring(n:int,coloring)->bool:
    fam=pair_only_family(n)
    if set(coloring)!=set(fam):
        return False
    if any(not (0<=c<n) for c in coloring.values()):
        return False
    for clique in range(n):
        colors=[coloring[e] for e in fam if clique in e]
        if len(colors)!=len(set(colors)):
            return False
    return True
