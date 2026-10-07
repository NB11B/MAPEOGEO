"""Literal Frozen Grammar Mapping and Compliance Auditor for Physics.

Enforces:
    w -> (Delta, I, W, sigma, Pi, Gamma, circ)
using the literal frozen Wave-4 coordinate algebra.

Physical meanings of literal coordinates:
    Delta: Difference / variation / defect / dissipation / perturbation
    I:     Invariant / conservation law / balance equation / constant of motion
    W:     Sensor witness / empirical certificate / measurement receipt
    sigma: Spacetime structure / symmetry / boundary condition / topology
    Pi:    Observation projection / sensor measurement / slice / restriction
    Gamma: Generator / time evolution / dynamical flow / transition rule
    circ:  Composition of physical operations / sequential evolution

Audits every factoring into:
- EXACT_FACTOR: exact 6D coordinate decomposition using registered sensor witnesses.
- WITNESS_EXTENSION: clean extension of registered witness catalog without dimension change.
- COMPOSITION: composite operations over base coordinates.
- SEMANTIC_DRIFT: unauthorized semantic drift or forbidden relabeling.
- NEW_COORDINATE_REQUIRED: invalid attempt to break the 6D coordinate algebra.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from mapeogeo.grammar.coordinates import CanonicalCoordinate
from mapeogeo.grammar.work_grammar import WorkGrammar


class FactoringClassification(StrEnum):
    """Classification of physical work factoring against frozen 6D grammar."""

    EXACT_FACTOR = "EXACT_FACTOR"
    WITNESS_EXTENSION = "WITNESS_EXTENSION"
    COMPOSITION = "COMPOSITION"
    SEMANTIC_DRIFT = "SEMANTIC_DRIFT"
    NEW_COORDINATE_REQUIRED = "NEW_COORDINATE_REQUIRED"


@dataclass(frozen=True)
class FactoringAuditRecord:
    """Audit result for a physical grammar factoring."""

    work_id: str
    classification: FactoringClassification
    coordinates_used: tuple[str, ...]
    witness_id: str | None
    is_compliant: bool
    drift_detected: bool
    details: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


class PhysicalGrammarFactorer:
    """Factorer and compliance auditor for physical work expressions."""

    def __init__(self, grammar: WorkGrammar | None = None) -> None:
        self.grammar = grammar or WorkGrammar(base_alphabet_size=58)

    def factor_physical_work(
        self,
        work_id: str,
        expression: str,
        witness_id: str | None = None,
        witness_symbol: str | None = None,
        witness_role: str | None = None,
    ) -> FactoringAuditRecord:
        """Factor physical work expression against literal frozen 6D coordinates."""
        # 1. Check for attempted illegal dimension expansion beyond d=6
        if re.search(
            r"\b(DIMENSION_7|COORD_7|EXTENDED_DIMENSION|AFFINE_SPACE_7)\b", expression, re.I
        ):
            return FactoringAuditRecord(
                work_id=work_id,
                classification=FactoringClassification.NEW_COORDINATE_REQUIRED,
                coordinates_used=(),
                witness_id=witness_id,
                is_compliant=False,
                drift_detected=True,
                details="Expression attempted illegal coordinate dimension expansion beyond d=6",
            )

        # 2. Detect semantic drift (e.g. forbidden relabelings)
        forbidden_terms = {
            "Gamma": ["connection", "affine_connection", "levi_civita"],
            "sigma": ["gauge_group", "lie_algebra"],
            "Pi": ["arbitrary_projection", "unprojected_ambient"],
        }
        for coord_name, bad_terms in forbidden_terms.items():
            for term in bad_terms:
                if term in expression.lower():
                    return FactoringAuditRecord(
                        work_id=work_id,
                        classification=FactoringClassification.SEMANTIC_DRIFT,
                        coordinates_used=(),
                        witness_id=witness_id,
                        is_compliant=False,
                        drift_detected=True,
                        details=(
                            f"Semantic drift detected on {coord_name}: forbidden term '{term}' "
                            f"attempts to redefine literal coordinate meaning"
                        ),
                    )

        # 3. Identify coordinates referenced in expression
        coords_found: list[str] = []
        for coord in CanonicalCoordinate:
            if coord.value in expression or coord.name in expression:
                coords_found.append(coord.value)

        # 4. Handle witness registration
        classification = FactoringClassification.EXACT_FACTOR
        witness_registered = False

        if witness_id is not None:
            existing_witness = self.grammar.get_witness(witness_id)
            if existing_witness is None:
                if witness_symbol and witness_role:
                    self.grammar.register_witness(witness_id, witness_symbol, witness_role)
                    witness_registered = True
                    classification = FactoringClassification.WITNESS_EXTENSION
                else:
                    return FactoringAuditRecord(
                        work_id=work_id,
                        classification=FactoringClassification.SEMANTIC_DRIFT,
                        coordinates_used=tuple(coords_found),
                        witness_id=witness_id,
                        is_compliant=False,
                        drift_detected=True,
                        details=f"Unregistered witness ID '{witness_id}' without valid declaration",
                    )
            else:
                classification = FactoringClassification.EXACT_FACTOR

        if "\u2218" in expression or "\\circ" in expression or "circ" in expression:
            if not witness_registered:
                classification = FactoringClassification.COMPOSITION

        return FactoringAuditRecord(
            work_id=work_id,
            classification=classification,
            coordinates_used=tuple(coords_found),
            witness_id=witness_id,
            is_compliant=True,
            drift_detected=False,
            details=f"Factored successfully under 6D algebra: {classification.value}",
        )
