"""Principal Reproduction Test: Closed-Loop Software Acquisition Campaign.

Verifies:
1. Full 50-requirement Software Engineering Campaign across 5 sectors:
   - Distributed Systems (Raft)
   - Cryptography & Security (HMAC)
   - Reactive Streaming (Event Bus)
   - Traffic Shaping (Token Rate Limiter)
   - Resilience & Fault Tolerance (Circuit Breaker)
2. Exact deficiency severity evolution:
   1086.91 -> 766.15 -> 509.11 -> 303.91 -> 158.76 -> 0.00
3. Exact machinery acquisition sequence:
   Raft -> HMAC -> Event Bus -> Rate Limiter -> Circuit Breaker -> REFUSE
4. Deficiency conservation law Delta D = 0 on every state transition.
5. Monotone marginal utility collapse after acquisition.
6. Terminal rational refusal stopping rule at round 6 (top J < tau_J = 1.5).
7. Partial satisfaction and redundant dependency controls.
"""

from __future__ import annotations

import math

from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.deficiency import DeficiencyExtractor, WorkRequirement
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import (
    DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    StateTransitionEngine,
)
from tests.fixtures.software.benchmark_corpus import get_software_requirements_corpus
from tests.fixtures.software.candidate_machinery import (
    get_candidate_software_machinery,
    to_machinery_candidates,
)


def test_software_closed_loop_acquisition_trajectory() -> None:
    """Execute the canonical 6-round software acquisition campaign."""
    grammar = WorkGrammar(base_alphabet_size=58)
    engine = StateTransitionEngine(
        grammar=grammar,
        refusal_threshold=DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    )
    extractor = DeficiencyExtractor()

    # 1. Load canonical N = 50 software requirements corpus
    sw_reqs = get_software_requirements_corpus()
    assert len(sw_reqs) == 50

    requirements: list[WorkRequirement] = [
        WorkRequirement(
            req_id=req.requirement_id,
            required_signatures=req.required_signatures,
            weight=req.weight,
        )
        for req in sw_reqs
    ]

    state_0 = KnowledgeState.initial()
    dist_0 = extractor.extract_deficiencies(requirements, state_0)
    assert math.isclose(dist_0.total_deficient_severity, 1086.91, abs_tol=1e-2)

    # 2. Register software witness certificates in work grammar
    sw_packages = get_candidate_software_machinery()
    for pkg in sw_packages:
        if pkg.witness_id and pkg.witness_symbol:
            grammar.register_witness(pkg.witness_id, pkg.witness_symbol, pkg.name)

    candidate_pool = to_machinery_candidates(sw_packages)

    selected_trajectory: list[str] = []
    utility_trajectory: list[float] = []

    # --- ROUND 1: RAFT ACQUISITION ---
    outcome_1 = engine.step(requirements, state_0, candidate_pool)
    assert outcome_1.decision == "TRANSITION"
    assert outcome_1.champion is not None
    assert outcome_1.champion.candidate_id == "LIB_RAFT_CONSENSUS"
    assert outcome_1.is_learning_event is True
    assert outcome_1.conservation_report is not None
    assert outcome_1.conservation_report["is_conserved"] is True
    assert math.isclose(outcome_1.conservation_report["d_resolved"], 320.76, abs_tol=1e-2)
    state_1 = outcome_1.next_state
    selected_trajectory.append(outcome_1.champion.candidate_id)
    utility_trajectory.append(outcome_1.champion.cost_efficiency_j)

    dist_1 = extractor.extract_deficiencies(requirements, state_1)
    assert math.isclose(dist_1.total_deficient_severity, 766.15, abs_tol=1e-2)
    assert dist_1.covered_requirements == 10

    # --- ROUND 2: HMAC ACQUISITION ---
    outcome_2 = engine.step(requirements, state_1, candidate_pool)
    assert outcome_2.decision == "TRANSITION"
    assert outcome_2.champion is not None
    assert outcome_2.champion.candidate_id == "LIB_SEC_HMAC_AUTH"
    assert outcome_2.is_learning_event is True
    assert outcome_2.conservation_report is not None
    assert outcome_2.conservation_report["is_conserved"] is True
    assert math.isclose(outcome_2.conservation_report["d_resolved"], 257.04, abs_tol=1e-2)
    state_2 = outcome_2.next_state
    selected_trajectory.append(outcome_2.champion.candidate_id)
    utility_trajectory.append(outcome_2.champion.cost_efficiency_j)

    dist_2 = extractor.extract_deficiencies(requirements, state_2)
    assert math.isclose(dist_2.total_deficient_severity, 509.11, abs_tol=1e-2)
    assert dist_2.covered_requirements == 20

    # --- ROUND 3: EVENT BUS ACQUISITION ---
    outcome_3 = engine.step(requirements, state_2, candidate_pool)
    assert outcome_3.decision == "TRANSITION"
    assert outcome_3.champion is not None
    assert outcome_3.champion.candidate_id == "LIB_ASYNC_EVENT_STREAM"
    assert outcome_3.is_learning_event is True
    assert outcome_3.conservation_report is not None
    assert outcome_3.conservation_report["is_conserved"] is True
    assert math.isclose(outcome_3.conservation_report["d_resolved"], 205.20, abs_tol=1e-2)
    state_3 = outcome_3.next_state
    selected_trajectory.append(outcome_3.champion.candidate_id)
    utility_trajectory.append(outcome_3.champion.cost_efficiency_j)

    dist_3 = extractor.extract_deficiencies(requirements, state_3)
    assert math.isclose(dist_3.total_deficient_severity, 303.91, abs_tol=1e-2)
    assert dist_3.covered_requirements == 30

    # --- ROUND 4: RATE LIMITER ACQUISITION ---
    outcome_4 = engine.step(requirements, state_3, candidate_pool)
    assert outcome_4.decision == "TRANSITION"
    assert outcome_4.champion is not None
    assert outcome_4.champion.candidate_id == "LIB_TOKEN_RATE_LIMITER"
    assert outcome_4.is_learning_event is True
    assert outcome_4.conservation_report is not None
    assert outcome_4.conservation_report["is_conserved"] is True
    assert math.isclose(outcome_4.conservation_report["d_resolved"], 145.15, abs_tol=1e-2)
    state_4 = outcome_4.next_state
    selected_trajectory.append(outcome_4.champion.candidate_id)
    utility_trajectory.append(outcome_4.champion.cost_efficiency_j)

    dist_4 = extractor.extract_deficiencies(requirements, state_4)
    assert math.isclose(dist_4.total_deficient_severity, 158.76, abs_tol=1e-2)
    assert dist_4.covered_requirements == 40

    # --- ROUND 5: CIRCUIT BREAKER ACQUISITION ---
    outcome_5 = engine.step(requirements, state_4, candidate_pool)
    assert outcome_5.decision == "TRANSITION"
    assert outcome_5.champion is not None
    assert outcome_5.champion.candidate_id == "LIB_CIRCUIT_BREAKER"
    assert outcome_5.is_learning_event is True
    assert outcome_5.conservation_report is not None
    assert outcome_5.conservation_report["is_conserved"] is True
    assert math.isclose(outcome_5.conservation_report["d_resolved"], 158.76, abs_tol=1e-2)
    state_5 = outcome_5.next_state
    selected_trajectory.append(outcome_5.champion.candidate_id)
    utility_trajectory.append(outcome_5.champion.cost_efficiency_j)

    dist_5 = extractor.extract_deficiencies(requirements, state_5)
    assert math.isclose(dist_5.total_deficient_severity, 0.0, abs_tol=1e-2)
    assert dist_5.covered_requirements == 50

    # --- ROUND 6: RATIONAL REFUSAL ---
    outcome_6 = engine.step(requirements, state_5, candidate_pool)
    assert outcome_6.decision == "REFUSE"
    assert outcome_6.verdict == "NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE"
    assert outcome_6.champion is not None
    assert outcome_6.champion.cost_efficiency_j < DEFAULT_REFUSAL_THRESHOLD_TAU_J

    # Invariant checks:
    # 1. Trajectory sequence
    expected_seq = [
        "LIB_RAFT_CONSENSUS",
        "LIB_SEC_HMAC_AUTH",
        "LIB_ASYNC_EVENT_STREAM",
        "LIB_TOKEN_RATE_LIMITER",
        "LIB_CIRCUIT_BREAKER",
    ]
    assert selected_trajectory == expected_seq

    # 2. Marginal utility decay across rounds
    assert utility_trajectory[0] > utility_trajectory[1]  # Raft > HMAC
    assert utility_trajectory[1] > utility_trajectory[2]  # HMAC > Event Bus
    assert utility_trajectory[2] > utility_trajectory[3]  # Event Bus > Rate Limiter
    assert utility_trajectory[3] > utility_trajectory[4]  # Rate Limiter > Circuit Breaker
    assert utility_trajectory[4] > outcome_6.champion.cost_efficiency_j


def test_partial_composite_requirement_satisfaction() -> None:
    """Verify that machinery satisfying only a subset of composite signatures does not clear req."""
    extractor = DeficiencyExtractor()
    req = WorkRequirement(
        req_id="REQ-COMPOSITE",
        required_signatures=("SIG_AUTH", "SIG_ENCRYPT"),
        weight=20.0,
    )

    state_0 = KnowledgeState.initial()
    dist_0 = extractor.extract_deficiencies([req], state_0)
    assert dist_0.total_deficient_severity == 20.0
    assert dist_0.covered_requirements == 0

    # Partial machinery providing only SIG_AUTH
    state_partial = KnowledgeState(
        t=1,
        signatures=frozenset({"SIG_AUTH"}),
        certified_nodes=(
            MachineryNode("node:auth", ("SIG_AUTH",), dependencies=(), witness_id=None),
        ),
        witness_ids=frozenset(),
        cumulative_ability=10.0,
        state_hash="h_part",
    )
    dist_partial = extractor.extract_deficiencies([req], state_partial)
    assert dist_partial.covered_requirements == 0  # Still incomplete
    assert dist_partial.total_deficient_severity == 20.0


def test_redundant_dependency_zero_reach_expansion() -> None:
    """Verify that acquiring an already satisfied capability yields zero deficiency resolution."""
    grammar = WorkGrammar(base_alphabet_size=58)
    engine = StateTransitionEngine(
        grammar=grammar,
        refusal_threshold=DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    )

    req = WorkRequirement(
        req_id="REQ-SIMPLE",
        required_signatures=("SIG_A",),
        weight=20.0,
    )
    cand_a = MachineryCandidate(
        candidate_id="CAND_A",
        provided_signatures=("SIG_A",),
        cost=2.0,
        nodes=(MachineryNode("node:a", ("SIG_A",), dependencies=(), witness_id=None),),
    )

    state_0 = KnowledgeState.initial()
    outcome_1 = engine.step([req], state_0, [cand_a])
    assert outcome_1.decision == "TRANSITION"
    assert outcome_1.conservation_report is not None
    assert outcome_1.conservation_report["d_resolved"] == 20.0

    state_1 = outcome_1.next_state
    # Redundant candidate offering SIG_A again
    cand_dup = MachineryCandidate(
        candidate_id="CAND_A_DUP",
        provided_signatures=("SIG_A",),
        cost=2.0,
        nodes=(MachineryNode("node:a_dup", ("SIG_A",), dependencies=(), witness_id=None),),
    )
    outcome_2 = engine.step([req], state_1, [cand_dup])
    assert outcome_2.decision == "REFUSE"
    assert outcome_2.verdict == "NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE"
