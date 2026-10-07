"""Physical Domain Ontology and Epistemic Abstractions.

Defines domain primitives for empirical physics within the UoW architecture:
- PhysicalObjective: target physical task / inverse problem / conservation audit.
- MeasuredObservation: empirical measurement data y = P(X) from physical sensors.
- EpistemicStatus: explicit progression from raw observation to measurement support:
      OBSERVED -> INFERRED -> MODEL_CONSISTENT -> FALSIFICATION_SURVIVED -> MEASUREMENT_SUPPORTED
- PhysicalHypothesis: proposed physical model with explicit epistemic status.
- PhysicalConstraint: conservation and dimensional laws governing physical work.
- PhysicalMachinery: candidate machinery node representing physical capability.
- PhysicalCertificate: certificate from the 5-gate physical boundary C_phys.

Governing rule:
    Mathematical admissibility != physical establishment.
    Effect observed != source identified.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EpistemicStatus(StrEnum):
    """Explicit epistemological state of a physical claim or hypothesis.

    INVARIANT:
        Transitions must be explicit. No transition may happen implicitly.
        Effect observed does NOT imply source identified.
    """

    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    MODEL_CONSISTENT = "MODEL_CONSISTENT"
    FALSIFICATION_SURVIVED = "FALSIFICATION_SURVIVED"
    MEASUREMENT_SUPPORTED = "MEASUREMENT_SUPPORTED"


class PhysicalCertificationVerdict(StrEnum):
    """Formal verdict of physical certification evaluation."""

    THEORETICALLY_ADMISSIBLE = "THEORETICALLY_ADMISSIBLE"
    MODEL_CONSISTENT = "MODEL_CONSISTENT"
    INSUFFICIENT_MEASUREMENT = "INSUFFICIENT_MEASUREMENT"
    FALSIFIED = "FALSIFIED"
    MEASUREMENT_SUPPORTED = "MEASUREMENT_SUPPORTED"


@dataclass(frozen=True)
class PhysicalConstraint:
    """Formal conservation or dimensional constraint governing physical work."""

    constraint_id: str
    name: str
    law_type: str  # e.g. "CONSERVATION_ENERGY", "CONSERVATION_MOMENTUM", "GAUSS_LAW"
    tolerance: float = 1e-6
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.constraint_id:
            raise ValueError("constraint_id must be non-empty")
        if self.tolerance < 0:
            raise ValueError("tolerance must be non-negative")


@dataclass(frozen=True)
class MeasuredObservation:
    """Concrete empirical observation y = P(X) acquired from physical sensors.

    Represents raw measurement data before any model inference or source assignment.
    """

    observation_id: str
    sensor_id: str
    projection_matrix: tuple[tuple[float, ...], ...]
    values: tuple[float, ...]
    timestamp: float = 0.0
    noise_variance: float = 0.0
    units: str = "dimensionless"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id must be non-empty")
        if len(self.projection_matrix) != len(self.values):
            raise ValueError("Projection matrix row count must match values length")

    @property
    def dimension(self) -> int:
        return len(self.values)

    @property
    def latent_dimension(self) -> int:
        return len(self.projection_matrix[0]) if self.projection_matrix else 0

    @property
    def digest(self) -> str:
        """Deterministic cryptographic digest of measurement data."""
        hasher = hashlib.sha256()
        hasher.update(self.sensor_id.encode())
        hasher.update(str(self.values).encode())
        hasher.update(str(self.projection_matrix).encode())
        return hasher.hexdigest()


@dataclass(frozen=True)
class PhysicalObjective:
    """Target physical goal, inverse problem, or capability requirement."""

    objective_id: str
    title: str
    domain: str  # e.g. "Electrodynamics", "Fluid Dynamics", "Acoustics", "Wave Mechanics"
    required_signatures: tuple[str, ...]
    conservation_laws: tuple[PhysicalConstraint, ...] = ()
    difficulty: float = 1.0
    structural_distance: float = 1.0
    novelty: float = 1.0
    depth: float = 1.0
    base_ability_pct: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective_id:
            raise ValueError("objective_id must be non-empty")
        if not self.required_signatures:
            raise ValueError("required_signatures must be non-empty")

    @property
    def weight(self) -> float:
        """Intrinsic objective weight."""
        return round(
            self.difficulty * self.structural_distance * self.novelty * self.depth,
            3,
        )


@dataclass(frozen=True)
class PhysicalHypothesis:
    """Proposed physical model relating latent state to observations."""

    hypothesis_id: str
    model_name: str
    latent_state: tuple[float, ...]
    epistemic_status: EpistemicStatus = EpistemicStatus.INFERRED
    is_source_identified: bool = False
    null_space_dimension: int = 0
    residual_norm: float = 0.0
    parameters: Mapping[str, float] = field(default_factory=dict)
    free_parameters_count: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id must be non-empty")
        # Invariant: If null space dimension > 0, source CANNOT be identified
        if self.null_space_dimension > 0 and self.is_source_identified:
            raise ValueError(
                "Source identification forbidden when null space dimension > 0 "
                "(observational equivalence implies ambiguous source identity)"
            )


@dataclass(frozen=True)
class PhysicalMachinery:
    """A physical machinery candidate capable of resolving physical deficiencies."""

    machinery_id: str
    name: str
    provided_signatures: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    witness_id: str | None = None
    cost: float = 10.0
    conserved_quantities: tuple[str, ...] = ()
    dimensional_units: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PhysicalCertificate:
    """Audit certificate issued by the 5-gate Physical Certification Boundary."""

    certificate_id: str
    verdict: PhysicalCertificationVerdict
    is_certified: bool
    gates_passed: tuple[str, ...]
    falsifications_checked: tuple[str, ...]
    residual_error: float
    epistemic_status: EpistemicStatus
    is_source_identified: bool
    failure_reason: str | None = None
    timestamp: float = 0.0
