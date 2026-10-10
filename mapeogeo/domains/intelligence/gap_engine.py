r"""Prioritized Intelligence Requirement (PIR) & Gap Qualification Engine.

Scans the organizational functional matrix and graph relationships to detect:
1. Unevidenced functional matrix cells (M_ij without grounding).
2. Epistemic state gaps (UNRESOLVED, CONFLICTING, REFUTED).
3. Taxonomy of intelligence gaps:
   - FACT_GAP -> O (Observe: acquire source evidence)
   - SOURCE_APPLICABILITY_GAP -> C (Compare: verify domain relevance)
   - INTERPRETATION_GAP -> K (Classify: formalize interpretation)
   - COVERAGE_GAP -> C (Compare: assess coverage limits)
   - OPERATION_DEFINITION_GAP -> F (Form: formalize operational contract)
   - CUSTODY_TRANSFER_GAP -> O/D (Observe/Dispatch: track physical custody)
   - AUTHORIZATION_GAP -> K/S (Classify/Secure: verify authority instrument)
4. Compiles formal platform deficiencies D = R \setminus G.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from mapeogeo.domains.intelligence.functions import (
    ALL_FUNCTIONS,
    FunctionalEdge,
    FunctionalMatrix,
    OrganizationalFunction,
)
from mapeogeo.domains.intelligence.grammar_mapping import (
    INTELLIGENCE_GAP_TO_OPERATOR,
    map_intelligence_deficiency,
)
from mapeogeo.domains.intelligence.ontology import (
    EpistemicState,
    IntelligenceGapKind,
    IntelligenceRequirement,
)


@dataclass(frozen=True)
class PrioritizedIntelligenceRequirement:
    """A prioritized intelligence requirement (PIR) generated from identified functional gaps."""
    pir_id: str
    priority: int  # 1 (Critical) to 5 (Routine)
    target_function: OrganizationalFunction
    target_entity: str
    gap_kind: IntelligenceGapKind
    required_operator: str  # One of O, E, K, C, F, D, S
    collection_directive: str
    epistemic_state: EpistemicState
    rationale: str

    def to_deficiency(self) -> Dict[str, Any]:
        r"""Projects PIR into standard platform deficiency D = R \setminus G."""
        return {
            "deficiency_id": f"def:{self.pir_id}",
            "target_subject": self.target_entity,
            "required_operator": self.required_operator,
            "gap_kind": self.gap_kind.value,
            "priority": self.priority,
            "is_unresolved": self.epistemic_state != EpistemicState.SUPPORTED,
            "resolution_directive": self.collection_directive,
        }


class IntelligenceGapEngine:
    """Detects, scores, and prioritizes intelligence gaps across organizational functional matrices."""

    def __init__(self, matrix: Optional[FunctionalMatrix] = None) -> None:
        self.matrix = matrix or FunctionalMatrix()

    def set_matrix(self, matrix: FunctionalMatrix) -> None:
        self.matrix = matrix

    def detect_matrix_gaps(self) -> List[PrioritizedIntelligenceRequirement]:
        """Scans the 49 cells of M_F for unevidenced or conflicting relationships."""
        pirs: List[PrioritizedIntelligenceRequirement] = []
        counter = 1

        # 1. Unevidenced functional matrix cells
        unevidenced = self.matrix.unevidenced_cells()
        for src, tgt in unevidenced:
            # Governance, Force, and Intelligence boundary gaps are high priority
            if src in (OrganizationalFunction.GOVERNANCE, OrganizationalFunction.FORCE, OrganizationalFunction.INTELLIGENCE):
                prio = 1
            else:
                prio = 3

            pir_id = f"PIR-GAP-{counter:03d}"
            counter += 1
            pirs.append(
                PrioritizedIntelligenceRequirement(
                    pir_id=pir_id,
                    priority=prio,
                    target_function=tgt,
                    target_entity=f"cell:{src.value}->{tgt.value}",
                    gap_kind=IntelligenceGapKind.FACT_GAP,
                    required_operator=INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.FACT_GAP],
                    collection_directive=f"Task collection assets to observe interactions between {src.value} and {tgt.value}",
                    epistemic_state=EpistemicState.UNRESOLVED,
                    rationale=f"Zero verified evidence found for cross-functional interface M({src.value}, {tgt.value})",
                )
            )

        # 2. Conflicting and unresolved edges
        for edge in self.matrix.edges:
            state = getattr(edge, "epistemic_state", "supported").lower()
            if state in ("conflicting", "hypothesis", "unresolved"):
                pir_id = f"PIR-GAP-{counter:03d}"
                counter += 1
                kind = IntelligenceGapKind.SOURCE_APPLICABILITY_GAP if state == "conflicting" else IntelligenceGapKind.FACT_GAP
                pirs.append(
                    PrioritizedIntelligenceRequirement(
                        pir_id=pir_id,
                        priority=2,
                        target_function=edge.target_function,
                        target_entity=f"edge:{edge.edge_id}",
                        gap_kind=kind,
                        required_operator=INTELLIGENCE_GAP_TO_OPERATOR[kind],
                        collection_directive=f"Seek multi-source corroboration to resolve {state} state on edge {edge.edge_id}",
                        epistemic_state=EpistemicState.CONFLICTING if state == "conflicting" else EpistemicState.UNRESOLVED,
                        rationale=f"Edge {edge.edge_id} between {edge.actor} and {edge.target_actor} has uncertain status: {state}",
                    )
                )

        return sorted(pirs, key=lambda p: p.priority)

    def compile_deficiency_queue(self) -> List[Dict[str, Any]]:
        """Compiles all detected gaps into a platform-executable deficiency queue."""
        pirs = self.detect_matrix_gaps()
        return [p.to_deficiency() for p in pirs]
