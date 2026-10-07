"""Utility Model Component (U).

Evaluates cost-efficiency and prospective acquisition utility:
    J_t(M) = \\widehat{\\Delta A}_t(M) / Cost(M)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mapeogeo.kernel.planning import ProspectivePlan, ProspectivePlanner

if TYPE_CHECKING:
    from mapeogeo.kernel.deficiency import WorkRequirement
    from mapeogeo.kernel.machinery import MachineryCandidate
    from mapeogeo.kernel.state import KnowledgeState


@dataclass(frozen=True)
class UtilityEstimate:
    """Evaluated utility and cost-efficiency for a candidate M."""

    candidate_id: str
    predicted_delta_a: float
    cost: float
    cost_efficiency_j: float
    plan: ProspectivePlan


class UtilityModel:
    """Evaluates prospective utility and ranks candidate machinery packages."""

    def __init__(self) -> None:
        self.planner = ProspectivePlanner()

    def evaluate_candidate(
        self,
        requirements: list[WorkRequirement],
        state: KnowledgeState,
        candidate: MachineryCandidate,
    ) -> UtilityEstimate:
        """Compute prospective utility J_t(M) = \\widehat{\\Delta A}_t(M) / Cost(M)."""
        plan = self.planner.plan_candidate(requirements, state, candidate)
        j_val = round(plan.predicted_delta_a / max(0.1, plan.cost), 4)

        return UtilityEstimate(
            candidate_id=candidate.candidate_id,
            predicted_delta_a=plan.predicted_delta_a,
            cost=plan.cost,
            cost_efficiency_j=j_val,
            plan=plan,
        )

    def rank_candidates(
        self,
        requirements: list[WorkRequirement],
        state: KnowledgeState,
        candidates: list[MachineryCandidate],
    ) -> list[UtilityEstimate]:
        """Rank all candidates by cost-efficiency J_t descending."""
        estimates = [self.evaluate_candidate(requirements, state, c) for c in candidates]
        return sorted(estimates, key=lambda e: e.cost_efficiency_j, reverse=True)
