"""Intelligence Domain Ontology and Semantic Vocabulary.

Defines operational roles, intelligence gap taxonomy, and epistemic states
for network intelligence analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class OperationalRole(str, Enum):
    """Canonical operational roles within intelligence collection and analysis."""
    COLLECTOR = "collector"
    ANALYST = "analyst"
    OPERATOR = "operator"
    CONTROLLER = "controller"
    OBSERVER = "observer"


class IntelligenceGapKind(str, Enum):
    """Taxonomy of intelligence deficiencies."""
    FACT_GAP = "fact_gap"
    SOURCE_APPLICABILITY_GAP = "source_applicability_gap"
    INTERPRETATION_GAP = "interpretation_gap"
    COVERAGE_GAP = "coverage_gap"
    OPERATION_DEFINITION_GAP = "operation_definition_gap"
    CUSTODY_TRANSFER_GAP = "custody_transfer_gap"
    AUTHORIZATION_GAP = "authorization_gap"


class EpistemicState(str, Enum):
    """Epistemic certainty states preserving incomplete and conflicting intelligence."""
    SUPPORTED = "supported"
    UNRESOLVED = "unresolved"
    CONFLICTING = "conflicting"
    REFUTED = "refuted"


@dataclass(frozen=True)
class IntelligenceRequirement:
    """A formal intelligence requirement / question."""
    requirement_id: str
    topic: str
    target_functions: List[str]
    priority: int = 1
    epistemic_state: EpistemicState = EpistemicState.UNRESOLVED
    gap_kind: Optional[IntelligenceGapKind] = None
    corroboration_sources: List[str] = field(default_factory=list)
