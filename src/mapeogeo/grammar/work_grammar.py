"""Work Grammar (M_6) manager, witness registration, and semantic drift auditor."""

from __future__ import annotations

from mapeogeo.grammar.coordinates import (
    CANONICAL_COORDINATES,
    KERNEL_GRAMMAR_DIMENSION,
    CanonicalCoordinate,
    WitnessCertificate,
)


class SemanticDriftError(ValueError):
    """Raised when an adapter attempts to relabel or semantically drift coordinate meanings."""


class WorkGrammar:
    """Manages the frozen 6-coordinate work grammar and witness extensions."""

    def __init__(self, base_alphabet_size: int = 58) -> None:
        self._dimension = KERNEL_GRAMMAR_DIMENSION
        self._base_alphabet_size = base_alphabet_size
        self._witnesses: dict[str, WitnessCertificate] = {}

    @property
    def dimension(self) -> int:
        """The grammar dimension d = 6 (invariant)."""
        return self._dimension

    @property
    def coordinates(self) -> tuple[CanonicalCoordinate, ...]:
        """The literal canonical coordinates."""
        return CANONICAL_COORDINATES

    @property
    def alphabet_size(self) -> int:
        """Total alphabet size: base + witness extensions (Delta a_W)."""
        return self._base_alphabet_size + len(self._witnesses)

    @property
    def delta_a_w(self) -> int:
        """Number of admitted witness extensions."""
        return len(self._witnesses)

    def register_witness(self, witness_id: str, symbol: str, role: str) -> WitnessCertificate:
        """Register a new constructive witness certificate extending coordinate W."""
        if witness_id in self._witnesses:
            return self._witnesses[witness_id]

        witness = WitnessCertificate(witness_id=witness_id, symbol=symbol, role=role)
        self._witnesses[witness_id] = witness
        return witness

    def get_witness(self, witness_id: str) -> WitnessCertificate | None:
        return self._witnesses.get(witness_id)

    def audit_coordinate_semantics(
        self, proposed_meanings: dict[str, str]
    ) -> tuple[bool, list[str]]:
        """Audit proposed coordinate descriptions to prevent semantic drift.

        Specifically forbids:
        - Relabeling Gamma as 'connection' or 'exterior derivative'
        - Relabeling Pi as arbitrary ungrounded projection
        - Relabeling sigma as generic symmetry-group coordinate
        """
        violations: list[str] = []
        forbidden_relabelings = {
            "Gamma": ["connection", "affine_connection", "levi_civita"],
            "sigma": ["symmetry_group", "gauge_group", "lie_algebra"],
            "Pi": ["generic_projection", "ambient_projection"],
        }

        for coord_name, proposed in proposed_meanings.items():
            if coord_name in forbidden_relabelings:
                for bad_term in forbidden_relabelings[coord_name]:
                    if bad_term.lower() in proposed.lower():
                        violations.append(
                            f"Semantic drift rejected on {coord_name}: "
                            f"cannot relabel literal meaning to '{proposed}' "
                            f"(matches forbidden '{bad_term}')"
                        )

        return len(violations) == 0, violations

    def enforce_strict_invariance(self) -> None:
        """Assert that grammar invariants hold."""
        if self._dimension != 6:
            raise SemanticDriftError(
                f"Grammar dimension d={self._dimension} violates invariant d=6"
            )
        if len(CANONICAL_COORDINATES) != 6:
            raise SemanticDriftError("Coordinate set length violates invariant d=6")
