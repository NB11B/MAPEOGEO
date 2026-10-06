"""Production backend contracts: fast proposers, small trusted verification boundary."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
@dataclass(frozen=True)
class CanonicalResult:
    digest:str; backend:str; proof_artifact:str|None; verified:bool
@dataclass(frozen=True)
class ColoringResult:
    status:str; colors:tuple[int,...]|None; backend:str; proof_artifact:str|None; verified:bool
class CanonicalBackend(Protocol):
    def canonicalize(self,n:int,lines)->CanonicalResult: ...
class ColoringBackend(Protocol):
    def solve(self,n:int,lines)->ColoringResult: ...
def accept_canonical(r): return r.verified and len(r.digest)==64
def accept_coloring(r):
    if not r.verified:return False
    if r.status=="SAT":return r.colors is not None
    if r.status=="UNSAT":return bool(r.proof_artifact)
    return False
