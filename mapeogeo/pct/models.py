"""Shared enums and dataclasses for the PCT subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CoefficientField(str, Enum):
    GF2 = "GF2"
    Q = "Q"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID = "INVALID"
    ERROR = "ERROR"
    INCONCLUSIVE = "INCONCLUSIVE"


class EquivalenceContract(str, Enum):
    EXACT = "EXACT"
    RELABELING = "RELABELING"
    SUBDIVISION = "SUBDIVISION"
    RIGID_MOTION_2D = "RIGID_MOTION_2D"
    RIGID_MOTION_AND_SCALE_2D = "RIGID_MOTION_AND_SCALE_2D"
    HOMEOMORPHISM_CONTROL = "HOMEOMORPHISM_CONTROL"
    CHAIN_HOMOTOPY_CONTROL = "CHAIN_HOMOTOPY_CONTROL"


class Applicability(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class Simplex:
    vertices: tuple[int, ...]

    @property
    def dimension(self) -> int:
        return len(self.vertices) - 1


@dataclass(frozen=True)
class FiniteComplex:
    complex_id: str
    simplices: tuple[Simplex, ...]
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ChainMap:
    map_id: str
    source_id: str
    target_id: str
    matrices_by_degree: dict[int, object]
    construction_method: str


@dataclass(frozen=True)
class ProbeState:
    probe_id: str
    probe_family: str
    parameters: dict[str, float | int | str]
    scale: float
    observation_operator: str
    coefficient_backend: CoefficientField
    applicability_contract: str


@dataclass(frozen=True)
class VerdictRecord:
    check_id: str
    applicability: Applicability
    verdict: Verdict
    measured: object
    expected: object
    tolerance_or_exact_rule: str
    provenance: dict[str, object] = field(default_factory=dict)
