"""Surviving structural route after degeneracy falsification for Erdős #19."""
from __future__ import annotations
from .erdos19_degeneracy_falsification import pair_only_family


def round_robin_edge_coloring_complete_graph(n:int):
    """Construct a proper edge coloring of K_n using at most n colors.

    Circle method: add a dummy vertex when n is odd, then rotate all but one
    fixed position.  Each round is a matching and receives one color.
    """
    if n < 2:
        return {}
    vertices=list(range(n))
    dummy=None
    if n % 2 == 1:
        dummy=n
        vertices.append(dummy)
    m=len(vertices)
    arr=vertices[:]
    coloring={}
    for color in range(m-1):
        for i in range(m//2):
            a,b=arr[i],arr[m-1-i]
            if a!=dummy and b!=dummy:
                coloring[frozenset((a,b))]=color
        # Keep arr[0] fixed; rotate the remaining positions.
        arr=[arr[0],arr[-1],*arr[1:-1]]
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
