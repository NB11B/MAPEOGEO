"""Family-level/asymptotic proof-state machinery.

Finite observations never certify eventual asymptotic bounds.  Certification
requires an explicit eventual-bound witness/certificate supplied by a proof
backend or trusted theorem adapter.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Callable, Iterable, Sequence


@dataclass(frozen=True)
class GrowthSample:
    n: int
    value: float
    reference: float
    log_ratio: float


@dataclass(frozen=True)
class EventualBoundCertificate:
    direction: str  # "lower" or "upper"
    constant: float
    threshold_n: int
    theorem_id: str

    def __post_init__(self):
        if self.direction not in {"lower","upper"}:
            raise ValueError("direction must be lower or upper")
        if self.constant <= 0 or self.threshold_n < 0 or not self.theorem_id:
            raise ValueError("invalid eventual-bound certificate")


@dataclass(frozen=True)
class AsymptoticDecision:
    state: str
    samples: tuple[GrowthSample,...]
    certificate: EventualBoundCertificate | None
    reason: str


def normalize_growth(observations: Iterable[tuple[int,float]], reference: Callable[[int],float]) -> tuple[GrowthSample,...]:
    out=[]
    for n,value in observations:
        ref=float(reference(n))
        if n <= 0 or value <= 0 or ref <= 0:
            raise ValueError("normalization requires positive n, value, and reference")
        out.append(GrowthSample(int(n),float(value),ref,math.log(float(value)/ref)))
    return tuple(out)


def eventual_lower_bound(
    observations: Iterable[tuple[int,float]],
    reference: Callable[[int],float],
    *,
    certificate: EventualBoundCertificate | None = None,
) -> AsymptoticDecision:
    samples=normalize_growth(observations,reference)
    if certificate is not None:
        if certificate.direction != "lower":
            raise ValueError("lower-bound work requires lower certificate")
        return AsymptoticDecision("CERTIFIED",samples,certificate,"explicit eventual lower-bound certificate supplied")
    if samples:
        return AsymptoticDecision("FINITE_EVIDENCE",samples,None,"finite normalized trajectory cannot certify an eventual lower bound")
    return AsymptoticDecision("UNDERDETERMINED",samples,None,"no finite evidence or eventual certificate")


def erdos89_reference(n:int)->float:
    if n <= 1:
        raise ValueError("n must exceed 1")
    return n/math.sqrt(math.log(n))


def erdos60_reference(n:int)->float:
    if n <= 0:
        raise ValueError("n must be positive")
    return math.sqrt(n)
