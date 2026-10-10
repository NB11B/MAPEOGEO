r"""Operational Grammar Mapping for Intelligence Profile.

Maps intelligence domain operations and deficiencies directly to the frozen
platform 7-operator grammar basis \Sigma_W = {O, E, K, C, F, D, S}.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from mapeogeo.domains.intelligence.ontology import IntelligenceGapKind


# Operational grammar mapping: IntelligenceGapKind -> Operator in \Sigma_W
INTELLIGENCE_GAP_TO_OPERATOR: Dict[IntelligenceGapKind, str] = {
    IntelligenceGapKind.FACT_GAP: "O",                    # Observe: Inquire/acquire raw source evidence
    IntelligenceGapKind.SOURCE_APPLICABILITY_GAP: "C",    # Compare: Evaluate relevance/coverage against domain criteria
    IntelligenceGapKind.INTERPRETATION_GAP: "K",          # Classify: Assign formal intelligence type / category
    IntelligenceGapKind.COVERAGE_GAP: "C",                # Compare: Assess coverage boundaries against requirements
    IntelligenceGapKind.OPERATION_DEFINITION_GAP: "F",    # Form: Formalize operational contract specification
    IntelligenceGapKind.CUSTODY_TRANSFER_GAP: "O",        # Observe: Acquire custody transfer receipt / telemetry
    IntelligenceGapKind.AUTHORIZATION_GAP: "K",           # Classify: Classify and verify authorization instrument
}


def map_intelligence_deficiency(
    gap_kind: IntelligenceGapKind,
    target_subject: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    r"""Projects an intelligence gap into a platform deficiency D = R \setminus G."""
    op = INTELLIGENCE_GAP_TO_OPERATOR.get(gap_kind, "O")
    return {
        "target_subject": target_subject,
        "required_operator": op,
        "gap_kind": gap_kind.value,
        "is_unresolved": True,
        "context": context or {},
    }
