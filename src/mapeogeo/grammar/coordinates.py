"""Frozen 6-coordinate work grammar (M_6).

Enforces the literal coordinate tuple:
    (Delta, I, W, sigma, Pi, Gamma) + circ (composition)

Coordinates:
    Delta: difference / variation / defect
    I:     invariant / conservation / identity
    W:     witness / certificate / proof
    sigma: structure / topology / symmetry
    Pi:    projection / restriction / slice
    Gamma: generator / transition / rule
    circ:  algebraic composition operator

INVARIANT:
    Dimension d = 6 is strictly invariant (Delta d = 0).
    Coordinates MUST NOT be semantically drifted or relabeled.
    Extensions are strictly confined to the witness alphabet W.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class CanonicalCoordinate(StrEnum):
    """The literal six coordinates of the work grammar."""

    DELTA = "Delta"  # Difference / defect / variation
    INVARIANT = "I"  # Invariant / conservation / balance
    WITNESS = "W"  # Witness / certificate / verification
    STRUCTURE = "sigma"  # Structure / topology / symmetry
    PROJECTION = "Pi"  # Projection / restriction / slice
    GENERATOR = "Gamma"  # Generator / transition / rule


COMPOSE_OPERATOR: Final[str] = "circ"
KERNEL_GRAMMAR_DIMENSION: Final[int] = 6

CANONICAL_COORDINATES: Final[tuple[CanonicalCoordinate, ...]] = (
    CanonicalCoordinate.DELTA,
    CanonicalCoordinate.INVARIANT,
    CanonicalCoordinate.WITNESS,
    CanonicalCoordinate.STRUCTURE,
    CanonicalCoordinate.PROJECTION,
    CanonicalCoordinate.GENERATOR,
)

# Literal coordinate definitions to prevent semantic drift
COORDINATE_DEFINITIONS: Final[dict[CanonicalCoordinate, str]] = {
    CanonicalCoordinate.DELTA: "difference / variation / defect",
    CanonicalCoordinate.INVARIANT: "invariant / conservation / balance",
    CanonicalCoordinate.WITNESS: "witness / certificate / verification",
    CanonicalCoordinate.STRUCTURE: "structure / topology / symmetry",
    CanonicalCoordinate.PROJECTION: "projection / restriction / slice",
    CanonicalCoordinate.GENERATOR: "generator / transition / rule",
}


@dataclass(frozen=True)
class WitnessCertificate:
    """Declared witness extension to coordinate W."""

    witness_id: str
    symbol: str
    role: str
    coordinate_basis: CanonicalCoordinate = CanonicalCoordinate.WITNESS

    def __post_init__(self) -> None:
        if not self.witness_id:
            raise ValueError("witness_id must be non-empty")
        if self.coordinate_basis != CanonicalCoordinate.WITNESS:
            raise ValueError("Extensions are strictly confined to witness coordinate W")
