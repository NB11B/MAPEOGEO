"""Exact witnessed reduced-class predicate for the documented n=13 EFL frontier."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .erdos19_frontier13_v5 import verify_linear_space


@dataclass(frozen=True)
class Reduced13Witness:
    core_indices:tuple[int,...]


@dataclass(frozen=True)
class Reduced13Membership:
    member:bool
    reason:str
    digest:str


def line_intersects(a,b): return bool(frozenset(a)&frozenset(b))


def verify_reduced13(lines,witness:Reduced13Witness,*,m_min=33,m_max=54):
    lines=tuple(map(frozenset,lines));m=len(lines)
    payload={"lines":[sorted(e) for e in lines],"core":list(witness.core_indices),"range":[m_min,m_max]}
    digest=hashlib.sha256(json.dumps(payload,separators=(",",":"),sort_keys=True).encode()).hexdigest()
    if not (m_min<=m<=m_max):return Reduced13Membership(False,"LINE_COUNT_OUTSIDE_FRONTIER",digest)
    if not verify_linear_space(13,lines):return Reduced13Membership(False,"NOT_13_POINT_LINEAR_SPACE",digest)
    core=tuple(witness.core_indices)
    if len(set(core))!=len(core) or any(i<0 or i>=m for i in core):
        return Reduced13Membership(False,"INVALID_CORE_INDICES",digest)
    cs=set(core)
    if any(len(e)>=3 and i not in cs for i,e in enumerate(lines)):
        return Reduced13Membership(False,"CORE_OMITS_LARGE_LINE",digest)
    for i in core:
        degree=sum(1 for j in core if j!=i and line_intersects(lines[i],lines[j]))
        if degree<13:return Reduced13Membership(False,"CORE_MIN_DEGREE_BELOW_13",digest)
    return Reduced13Membership(True,"MEMBER",digest)
