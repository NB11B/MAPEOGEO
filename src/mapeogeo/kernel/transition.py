"""State Transition and Admission Engine (A).

Executes atomic transition G_t -> G_{t+1} or triggers the formal refusal state:
    \\max_M J_t(M) < \\tau_J ==> REFUSE (NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE)

Enforces:
    1. Prospective planning and utility ranking.
    2. 4-gate fail-closed certification before admission.
    3. Mandatory verification of deficiency conservation on admitted transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.certification import CertificationBoundary, CertificationResult
from mapeogeo.kernel.deficiency import DeficiencyExtractor
from mapeogeo.kernel.reach import is_learning_event
from mapeogeo.kernel.utility import UtilityEstimate, UtilityModel

if TYPE_CHECKING:
    from mapeogeo.kernel.deficiency import WorkRequirement
    from mapeogeo.kernel.machinery import MachineryCandidate
    from mapeogeo.kernel.state import KnowledgeState

DEFAULT_REFUSAL_THRESHOLD_TAU_J: float = 1.5


@dataclass(frozen=True)
class TransitionOutcome:
    """Outcome of state transition evaluation."""

    decision: str  # "TRANSITION", "REFUSE", "REJECT"
    verdict: str
    reason: str
    next_state: KnowledgeState
    champion: UtilityEstimate | None = None
    certification: CertificationResult | None = None
    conservation_report: dict[str, Any] | None = None
    is_learning_event: bool = False


class StateTransitionEngine:
    """Orchestrates atomic state transitions or triggers rational refusal."""

    def __init__(
        self,
        grammar: WorkGrammar | None = None,
        refusal_threshold: float = DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    ) -> None:
        self.grammar = grammar or WorkGrammar()
        self.certifier = CertificationBoundary(self.grammar)
        self.utility_model = UtilityModel()
        self.extractor = DeficiencyExtractor()
        self.refusal_threshold = refusal_threshold

    def step(
        self,
        requirements: list[WorkRequirement],
        current_state: KnowledgeState,
        candidate_pool: list[MachineryCandidate],
    ) -> TransitionOutcome:
        """Execute one step of the closed-loop prospective acquisition cycle."""
        # 1. Extract initial deficiencies D_t
        initial_def = self.extractor.extract_deficiencies(requirements, current_state)

        # 2. Evaluate and rank candidate pool by prospective utility J_t(M)
        rankings = self.utility_model.rank_candidates(requirements, current_state, candidate_pool)
        if not rankings:
            return TransitionOutcome(
                decision="REFUSE",
                verdict="NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE",
                reason="Candidate pool is empty",
                next_state=current_state,
            )

        champion_estimate = rankings[0]
        # Candidate machinery corresponding to champion
        champion_candidate = next(
            c for c in candidate_pool if c.candidate_id == champion_estimate.candidate_id
        )

        # 3. Refusal rule: max_M J_t(M) < tau_J
        if champion_estimate.cost_efficiency_j < self.refusal_threshold:
            return TransitionOutcome(
                decision="REFUSE",
                verdict="NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE",
                reason=(
                    f"Top efficiency J = {champion_estimate.cost_efficiency_j} < "
                    f"\\tau_J = {self.refusal_threshold}"
                ),
                champion=champion_estimate,
                next_state=current_state,
            )

        # 4. Fail-closed 4-gate certification
        cert = self.certifier.certify_candidate(champion_candidate, current_state)
        if not cert.is_certified:
            return TransitionOutcome(
                decision="REJECT",
                verdict="CERTIFICATION_FAILURE",
                reason=cert.failure_reason or "Certification rejected",
                champion=champion_estimate,
                certification=cert,
                next_state=current_state,
            )

        # 5. Atomic state transition G_{t+1} = G_t U {M^*}
        new_ability = current_state.cumulative_ability + champion_estimate.predicted_delta_a
        next_state = current_state.transition(
            new_signatures=champion_candidate.provided_signatures,
            new_nodes=champion_candidate.nodes,
            new_witnesses=set(champion_candidate.witness_ids),
            new_ability=new_ability,
        )

        # 6. Verify deficiency conservation: D_t = D_res U D_red U D_unc U D_exp
        next_def = self.extractor.extract_deficiencies(requirements, next_state)
        conservation_report = self.extractor.verify_conservation(initial_def, next_def)

        # 7. Check if learning event occurred: Reach(G_{t+1}) supersets Reach(G_t)
        learning = is_learning_event(current_state.signatures, next_state.signatures)

        return TransitionOutcome(
            decision="TRANSITION",
            verdict="CAPABILITY_ACQUIRED",
            reason=f"Acquired machinery package '{champion_candidate.candidate_id}'",
            champion=champion_estimate,
            certification=cert,
            next_state=next_state,
            conservation_report=conservation_report,
            is_learning_event=learning,
        )
