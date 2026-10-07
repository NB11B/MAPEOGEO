"""Latent generators, observations, and observable relational signatures.

Enforces:
    observed quantity != inferred generator
Preserves status='unknown' without forcing premature identity.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from mapeogeo.psmsl.algebra import Matrix, Vector, eye, matmul


@dataclass(frozen=True)
class Observation:
    """An empirical observation record consisting of measured numeric values.

    Represents raw observed values, strictly distinct from inferred generator sources.
    """

    observation_id: str
    values: Vector
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id must be non-empty")
        if not self.values:
            raise ValueError("Observation values must be non-empty")


@dataclass(frozen=True)
class ObservableSignature:
    """Multi-sample or multi-step trajectory signature across observations."""

    signature_id: str
    observations: tuple[Observation, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.signature_id:
            raise ValueError("signature_id must be non-empty")

    @classmethod
    def build_trajectory_matrix(
        cls, system_matrix: Matrix, observation_matrix: Matrix, steps: int
    ) -> Matrix:
        """Construct multi-step observability matrix O = [C; CA; CA^2; ... ; CA^(steps-1)]."""
        n = len(system_matrix)
        power = eye(n)
        rows: list[Vector] = []
        for _ in range(steps):
            ca = matmul(observation_matrix, power)
            rows.extend(ca)
            power = matmul(power, system_matrix)
        return tuple(rows)


@dataclass(frozen=True)
class LatentGenerator:
    """Inferred state generator producing observable consequences.

    Must preserve status='unknown' when source identity or state cannot be uniquely bounded.
    Fail-closed invariant: nullity > 0 strictly prohibits status='identified'.
    """

    generator_id: str
    status: str = "unknown"
    estimated_state: Vector | None = None
    nullity: int = 0
    evidence_observations: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.generator_id:
            raise ValueError("generator_id must be non-empty")

        valid_statuses = {"unknown", "candidate", "provisional", "identified"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'; must be one of {sorted(valid_statuses)}"
            )

        # Fail-closed invariant: Cannot claim identified status with positive nullity
        if self.status == "identified" and self.nullity > 0:
            raise ValueError(
                f"Fail-closed invariant violation: generator '{self.generator_id}' has positive "
                f"nullity ({self.nullity}); cannot be marked 'identified'"
            )

        if self.status == "identified" and self.estimated_state is None:
            raise ValueError("Identified generator must have an estimated_state")
