"""Erdos open-problem machinery triage.

This module does not claim to solve open problems.  It classifies a frozen
problem-catalog row into present router capability overlap and a fail-closed
next action.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

UNRESOLVED_STATES={"open","open (Lean)","verifiable","falsifiable","decidable"}

FAMILY_TAGS={
 "graph":{"graph theory","chromatic number","cycles","turan number","hypergraphs"},
 "geometry":{"geometry","distances","convex"},
 "analysis":{"analysis","polynomials"},
 "number_theory":{"number theory","primes","divisors","factorials","irrationality","unit fractions","sidon sets","additive combinatorics","additive basis","arithmetic progressions","powerful","binomial coefficients"},
 "combinatorics":{"ramsey theory","combinatorics","set theory"},
}
EXECUTABLE_FAMILIES={"graph","geometry","analysis"}


@dataclass(frozen=True)
class ErdosTriage:
    number: str
    state: str
    families: tuple[str,...]
    outcome: str
    reason: str


def classify(number:str,state:str,tags:Iterable[str]) -> ErdosTriage:
    tags=set(tags)
    fam=tuple(sorted(name for name,needles in FAMILY_TAGS.items() if tags & needles))
    if state not in UNRESOLVED_STATES:
        return ErdosTriage(number,state,fam,"EXCLUDE","not unresolved under frozen campaign policy")
    overlap=sorted(set(fam)&EXECUTABLE_FAMILIES)
    if overlap:
        return ErdosTriage(number,state,fam,"INSPECT_STATEMENT","capability overlap: "+",".join(overlap))
    return ErdosTriage(number,state,fam,"IMPLEMENT_OR_CERTIFY","no present executable family covers statement metadata")
