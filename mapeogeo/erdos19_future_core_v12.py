"""Sound future-core feasibility bounds for partial n=13 linear spaces."""
from __future__ import annotations
from dataclasses import dataclass
from .erdos19_partial_feasibility_v11 import used_pairs

@dataclass(frozen=True)
class CoreFutureBound:
    feasible:bool
    reason:str
    max_possible_core_degree:tuple[int,...]

def future_core_bounds(lines,core_indices):
    lines=tuple(map(frozenset,lines));core=tuple(core_indices)
    used=used_pairs(lines)
    if used is None:return CoreFutureBound(False,"PAIR_REUSED",())
    uncovered={tuple(sorted((a,b))) for a in range(13) for b in range(a+1,13)}-set(used)
    bounds=[]
    for i in core:
        if i<0 or i>=len(lines):return CoreFutureBound(False,"INVALID_CORE_INDEX",())
        e=lines[i]
        current=sum(1 for j in core if j!=i and e&lines[j])
        # Every future line intersecting e must consume at least one uncovered
        # pair (v,w) with v in e. Distinct future lines consume disjoint pairs.
        incident_pairs=sum(1 for p in uncovered if p[0] in e or p[1] in e)
        # Also cannot exceed final other-line count 53.
        bounds.append(min(53,current+incident_pairs))
    if any(b<13 for b in bounds):
        return CoreFutureBound(False,"CORE_VERTEX_CANNOT_REACH_DEGREE_13",tuple(bounds))
    return CoreFutureBound(True,"POSSIBLE",tuple(bounds))
