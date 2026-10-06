"""Erdős #60/#89 qualification adapters for the asymptotic family layer."""
from __future__ import annotations
from dataclasses import dataclass
from .asymptotic_family import erdos60_reference,erdos89_reference,eventual_lower_bound


@dataclass(frozen=True)
class FrontierResult:
    problem: str
    state: str
    missing_bridge: str


def qualify_erdos89(observations):
    d=eventual_lower_bound(observations,erdos89_reference)
    return FrontierResult("89",d.state,"Lean eventual lower-bound theorem n/sqrt(log n) = O(minimalDistinctDistances)")


def qualify_erdos60(observations):
    d=eventual_lower_bound(observations,erdos60_reference)
    return FrontierResult("60",d.state,"uniform eventual C4-count lower bound c*sqrt(n) above extremal threshold")
