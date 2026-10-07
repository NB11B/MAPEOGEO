"""Prospective Planner Component (P).

Predicts capability gain and structural successor deficiency prior to acquisition:
    P(G_t, M) -> (\\widehat{\\Delta A}_t, \\widehat{D}_{t+1})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mapeogeo.kernel.deficiency import DeficiencyExtractor, WorkRequirement

if TYPE_CHECKING:
    from mapeogeo.kernel.machinery import MachineryCandidate
    from mapeogeo.kernel.state import KnowledgeState


@dataclass(frozen=True)
class ProspectivePlan:
    """Prospective plan evaluating a machinery candidate before commitment."""

    candidate_id: str
    predicted_delta_a: float
    predicted_next_deficiency: float
    cost: float
    unlocked_weight: float
    simulated_next_signatures: frozenset[str]


class ProspectivePlanner:
    """Predicts capability gain and next limiting deficiency."""

    def __init__(self) -> None:
        self.extractor = DeficiencyExtractor()

    def plan_candidate(
        self,
        requirements: list[WorkRequirement],
        state: KnowledgeState,
        candidate: MachineryCandidate,
    ) -> ProspectivePlan:
        """Simulate candidate acquisition and predict capability gain and remaining deficiency."""
        cand_sigs = frozenset(candidate.provided_signatures)
        sim_sigs = state.signatures | cand_sigs

        # Simulated successor state
        sim_state = state.clone()
        object.__setattr__(sim_state, "signatures", sim_sigs)

        # Extract current vs simulated deficiencies
        curr_def = self.extractor.extract_deficiencies(requirements, state)
        sim_def = self.extractor.extract_deficiencies(requirements, sim_state)

        # Compute direct unlocked requirement weight
        unlocked_weight = 0.0
        for rec in curr_def.records:
            if not rec.is_covered:
                missing_set = set(rec.missing)
                if missing_set.issubset(cand_sigs):
                    unlocked_weight += rec.weight

        # Predict Delta A: if already known, gain is minimal
        if cand_sigs.issubset(state.signatures):
            predicted_delta_a = 0.5
        else:
            predicted_delta_a = round(unlocked_weight * 0.12 + len(candidate.nodes) * 1.0, 2)

        return ProspectivePlan(
            candidate_id=candidate.candidate_id,
            predicted_delta_a=predicted_delta_a,
            predicted_next_deficiency=sim_def.total_deficient_severity,
            cost=candidate.cost,
            unlocked_weight=round(unlocked_weight, 4),
            simulated_next_signatures=sim_sigs,
        )
