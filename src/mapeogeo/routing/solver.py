"""Goal Solver with Work Decomposition and Terminal State Adjudication.

Consumes the Wave-4 kernel (KnowledgeState, DeficiencyExtractor) and Router.
The GoalSolver decomposes:
    Q -> {q_1, ..., q_m}
asks kernel for deficiencies, and asks routing for admissible candidate paths.
It does NOT itself decide that an unsatisfied goal is satisfied.

Terminal States:
    SATISFIED
    PARTIALLY_SATISFIED
    UNREACHABLE
    BLOCKED_RESOURCE
    BLOCKED_AUTHORITY
    BLOCKED_INVARIANT
    AMBIGUOUS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mapeogeo.kernel.deficiency import DeficiencyExtractor, WorkRequirement
from mapeogeo.routing.contracts import ResourceRequirement
from mapeogeo.routing.goal import Goal
from mapeogeo.routing.route import Route
from mapeogeo.routing.router import Router

if TYPE_CHECKING:
    from mapeogeo.kernel.state import KnowledgeState


@dataclass(frozen=True)
class GoalSolution:
    """Outcome of goal solving and work route decomposition."""

    goal_id: str
    status: str
    # Valid statuses: SATISFIED, PARTIALLY_SATISFIED, UNREACHABLE,
    # BLOCKED_RESOURCE, BLOCKED_AUTHORITY, BLOCKED_INVARIANT, AMBIGUOUS
    reason: str
    resolved_subgoals: tuple[str, ...]
    unresolved_subgoals: tuple[str, ...]
    selected_routes: tuple[Route, ...]
    total_cost: float
    total_resources: ResourceRequirement
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_satisfied(self) -> bool:
        return self.status == "SATISFIED"


class GoalSolver:
    """Consolidates goal decomposition, kernel deficiency extraction, and route selection."""

    def __init__(self, router: Router) -> None:
        self.router = router
        self.extractor = DeficiencyExtractor()

    def solve(
        self,
        goal: Goal,
        state: KnowledgeState,
    ) -> GoalSolution:
        """Solve a formal goal against certified state G_t and registered work routes."""
        # 1. Decompose goal Q -> {q_1, ..., q_m} as WorkRequirements
        subgoals = goal.target_signatures
        requirements = [
            WorkRequirement(
                req_id=f"req-{goal.goal_id}-{sig}",
                required_signatures=(sig,),
                weight=1.0,
            )
            for sig in subgoals
        ]

        # 2. Extract deficiencies via Wave-4 kernel DeficiencyExtractor
        deficiencies = self.extractor.extract_deficiencies(requirements, state)

        # 3. For each subgoal, evaluate reachability and routing
        resolved: list[str] = []
        unresolved: list[str] = []
        selected_routes: list[Route] = []
        total_res = ResourceRequirement()
        total_cost = 0.0

        blocked_statuses: set[str] = set()
        block_reasons: list[str] = []
        has_ambiguity = False

        for sig in subgoals:
            # Check routing candidates
            candidates = self.router.find_routes(
                target=sig,
                available_capabilities=set(state.signatures),
                budget=goal.budget,
                granted_roles=goal.authority_roles,
                granted_scopes=goal.authority_scopes,
                has_audit_receipt=goal.has_audit_receipt,
                prohibited_invariants=goal.prohibited_invariants,
                tolerance=goal.allowed_tolerance,
            )

            # Filter candidates excluding explicitly prohibited contracts
            filtered_candidates = [
                c
                for c in candidates
                if not any(x.contract_id in goal.excluded_contracts for x in c.route.contracts)
            ]

            admissible = [c for c in filtered_candidates if c.is_admissible]

            if admissible:
                # Ambiguity: multiple top routes with identical cost and disjoint contracts
                if len(admissible) > 1:
                    top_0 = admissible[0].route
                    top_1 = admissible[1].route
                    if (
                        top_0.total_cost == top_1.total_cost
                        and top_0.total_error == top_1.total_error
                        and set(top_0.contracts) != set(top_1.contracts)
                        and goal.metadata.get("detect_ambiguity", False)
                    ):
                        has_ambiguity = True

                chosen = admissible[0].route
                resolved.append(sig)
                selected_routes.append(chosen)
                total_cost += chosen.total_cost
                total_res = total_res.combine(chosen.total_resources)
            else:
                unresolved.append(sig)
                if filtered_candidates:
                    top_cand = filtered_candidates[0]
                    blocked_statuses.add(top_cand.status)
                    block_reasons.extend(top_cand.rejection_reasons)
                else:
                    blocked_statuses.add("UNREACHABLE")

        # 4. Adjudicate terminal status
        if has_ambiguity:
            status = "AMBIGUOUS"
            reason = "Multiple conflicting routes with identical metrics exist for sub-goals"
        elif len(unresolved) == 0:
            # Check combined budget
            if total_cost > goal.budget.max_cost or not total_res.fits_in(goal.budget):
                status = "BLOCKED_RESOURCE"
                reason = "Aggregate routes exceed total goal resource/cost budget"
            else:
                status = "SATISFIED"
                reason = "All goal target signatures resolved by certified admissible routes"
        elif len(resolved) > 0:
            status = "PARTIALLY_SATISFIED"
            reason = (
                f"Partially resolved {len(resolved)}/{len(subgoals)} subgoals; "
                f"unresolved: {sorted(unresolved)}"
            )
        elif "BLOCKED_AUTHORITY" in blocked_statuses:
            status = "BLOCKED_AUTHORITY"
            reason = f"Blocked by authority credentials: {'; '.join(block_reasons[:2])}"
        elif "BLOCKED_RESOURCE" in blocked_statuses:
            status = "BLOCKED_RESOURCE"
            reason = f"Blocked by resource budget: {'; '.join(block_reasons[:2])}"
        elif "BLOCKED_INVARIANT" in blocked_statuses:
            status = "BLOCKED_INVARIANT"
            reason = f"Blocked by prohibited invariants: {'; '.join(block_reasons[:2])}"
        else:
            status = "UNREACHABLE"
            reason = f"No admissible routes found for subgoals: {sorted(unresolved)}"

        return GoalSolution(
            goal_id=goal.goal_id,
            status=status,
            reason=reason,
            resolved_subgoals=tuple(resolved),
            unresolved_subgoals=tuple(unresolved),
            selected_routes=tuple(selected_routes),
            total_cost=round(total_cost, 4),
            total_resources=total_res,
            metadata={"deficiencies": deficiencies},
        )
