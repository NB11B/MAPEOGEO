"""Sound partial-state feasibility bounds for the witnessed n=13 reduced class."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Feasibility:
    feasible:bool
    reason:str

def comb_pairs(e):
    e=sorted(e)
    for i,a in enumerate(e):
        for b in e[i+1:]:
            yield a,b

def used_pairs(lines):
    s=set()
    for e in lines:
        for a,b in comb_pairs(e):
            p=(a,b)
            if p in s:return None
            s.add(p)
    return s

def partial_feasible13(lines,*,m_min=33,m_max=54):
    lines=tuple(map(frozenset,lines))
    if any(any(v<0 or v>=13 for v in e) or len(e)<2 for e in lines):
        return Feasibility(False,"INVALID_LINE")
    if len(lines)>m_max:return Feasibility(False,"TOO_MANY_LINES")
    pairs=used_pairs(lines)
    if pairs is None:return Feasibility(False,"PAIR_REUSED")
    remaining=78-len(pairs)
    if len(lines)+remaining<m_min:
        return Feasibility(False,"CANNOT_REACH_MIN_LINE_COUNT")
    return Feasibility(True,"POSSIBLE")
