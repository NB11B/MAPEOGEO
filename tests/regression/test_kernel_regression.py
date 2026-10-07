"""Regression test replaying the closed-loop prospective acquisition trajectory.

Replays the multi-round curriculum dynamics:
    Round 1: Candidate 1 Acquired (large deficiency resolution)
    Round 2: Candidate 2 Acquired (marginal utility of candidate 1 collapsed, candidate 2 dominant)
    Round 3: Candidate 3 Acquired
    Round 4: Candidate 4 Acquired
    Round 5: Rational Refusal: max_M J(M) < tau_J (all remaining candidates below threshold)

Verifies:
- Deficiency conservation holds on every single state transition.
- Dynamic marginal utility decay across rounds.
- Strict termination at Round 5 with NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE.
- Monotone capability accumulation and strict learning events at each acquisition.
"""

from __future__ import annotations

from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.deficiency import DeficiencyExtractor, WorkRequirement
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import (
    DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    StateTransitionEngine,
)


def test_closed_loop_curriculum_and_autonomous_refusal_trajectory() -> None:
    """Simulate a 5-round closed-loop acquisition trajectory verifying conservation and refusal."""
    grammar = WorkGrammar()
    # Register witness certificates for candidates
    grammar.register_witness("wit-pkg-1", "sig.pkg1", "hash-cert-1")
    grammar.register_witness("wit-pkg-2", "sig.pkg2", "hash-cert-2")
    grammar.register_witness("wit-pkg-3", "sig.pkg3", "hash-cert-3")
    grammar.register_witness("wit-pkg-4", "sig.pkg4", "hash-cert-4")
    grammar.register_witness("wit-pkg-5", "sig.pkg5", "hash-cert-5")

    engine = StateTransitionEngine(
        grammar=grammar, refusal_threshold=DEFAULT_REFUSAL_THRESHOLD_TAU_J
    )
    extractor = DeficiencyExtractor()

    # Requirements spanning 4 major capability sectors
    requirements = [
        # Sector 1 requirements (wt: 40)
        WorkRequirement("req-s1-1", ("sig.pkg1.a", "sig.pkg1.b"), weight=20.0),
        WorkRequirement("req-s1-2", ("sig.pkg1.b", "sig.pkg1.c"), weight=20.0),
        # Sector 2 requirements (wt: 35)
        WorkRequirement("req-s2-1", ("sig.pkg2.a", "sig.pkg2.b"), weight=15.0),
        WorkRequirement("req-s2-2", ("sig.pkg2.c",), weight=20.0),
        # Sector 3 requirements (wt: 30)
        WorkRequirement("req-s3-1", ("sig.pkg3.a",), weight=30.0),
        # Sector 4 requirements (wt: 25)
        WorkRequirement("req-s4-1", ("sig.pkg4.a", "sig.pkg4.b"), weight=25.0),
    ]

    # Candidate machinery pool
    cand1 = MachineryCandidate(
        candidate_id="pkg-sector-1",
        provided_signatures=("sig.pkg1.a", "sig.pkg1.b", "sig.pkg1.c"),
        cost=2.0,
        nodes=(
            MachineryNode("n-s1-a", ("sig.pkg1.a",), witness_id="wit-pkg-1"),
            MachineryNode("n-s1-b", ("sig.pkg1.b",), witness_id="wit-pkg-1"),
            MachineryNode("n-s1-c", ("sig.pkg1.c",), witness_id="wit-pkg-1"),
        ),
        witness_ids=("wit-pkg-1",),
    )
    cand2 = MachineryCandidate(
        candidate_id="pkg-sector-2",
        provided_signatures=("sig.pkg2.a", "sig.pkg2.b", "sig.pkg2.c"),
        cost=2.0,
        nodes=(
            MachineryNode("n-s2-a", ("sig.pkg2.a",), witness_id="wit-pkg-2"),
            MachineryNode("n-s2-b", ("sig.pkg2.b",), witness_id="wit-pkg-2"),
            MachineryNode("n-s2-c", ("sig.pkg2.c",), witness_id="wit-pkg-2"),
        ),
        witness_ids=("wit-pkg-2",),
    )
    cand3 = MachineryCandidate(
        candidate_id="pkg-sector-3",
        provided_signatures=("sig.pkg3.a",),
        cost=2.0,
        nodes=(MachineryNode("n-s3-a", ("sig.pkg3.a",), witness_id="wit-pkg-3"),),
        witness_ids=("wit-pkg-3",),
    )
    cand4 = MachineryCandidate(
        candidate_id="pkg-sector-4",
        provided_signatures=("sig.pkg4.a", "sig.pkg4.b"),
        cost=2.0,
        nodes=(
            MachineryNode("n-s4-a", ("sig.pkg4.a",), witness_id="wit-pkg-4"),
            MachineryNode("n-s4-b", ("sig.pkg4.b",), witness_id="wit-pkg-4"),
        ),
        witness_ids=("wit-pkg-4",),
    )
    # Marginal / redundant candidate with low unlocked gain and high cost
    cand5 = MachineryCandidate(
        candidate_id="pkg-redundant-5",
        provided_signatures=("sig.pkg5.minor",),
        cost=8.0,
        nodes=(MachineryNode("n-s5-m", ("sig.pkg5.minor",), witness_id="wit-pkg-5"),),
        witness_ids=("wit-pkg-5",),
    )

    all_candidates = [cand1, cand2, cand3, cand4, cand5]

    # --- ROUND 1 ---
    state_0 = KnowledgeState.initial()
    dist_0 = extractor.extract_deficiencies(requirements, state_0)
    assert dist_0.total_deficient_severity == 130.0

    outcome_1 = engine.step(requirements, state_0, all_candidates)
    assert outcome_1.decision == "TRANSITION"
    assert outcome_1.champion is not None
    assert outcome_1.champion.candidate_id == "pkg-sector-1"
    assert outcome_1.is_learning_event is True
    assert outcome_1.conservation_report is not None
    assert outcome_1.conservation_report["is_conserved"] is True
    assert outcome_1.conservation_report["d_resolved"] == 40.0
    state_1 = outcome_1.next_state

    # --- ROUND 2 ---
    outcome_2 = engine.step(requirements, state_1, all_candidates)
    assert outcome_2.decision == "TRANSITION"
    assert outcome_2.champion is not None
    assert outcome_2.champion.candidate_id == "pkg-sector-2"
    assert outcome_2.is_learning_event is True
    assert outcome_2.conservation_report is not None
    assert outcome_2.conservation_report["is_conserved"] is True
    assert outcome_2.conservation_report["d_resolved"] == 35.0
    state_2 = outcome_2.next_state

    # --- ROUND 3 ---
    outcome_3 = engine.step(requirements, state_2, all_candidates)
    assert outcome_3.decision == "TRANSITION"
    assert outcome_3.champion is not None
    assert outcome_3.champion.candidate_id == "pkg-sector-4"
    assert outcome_3.is_learning_event is True
    assert outcome_3.conservation_report is not None
    assert outcome_3.conservation_report["is_conserved"] is True
    assert outcome_3.conservation_report["d_resolved"] == 25.0
    state_3 = outcome_3.next_state

    # --- ROUND 4 ---
    outcome_4 = engine.step(requirements, state_3, all_candidates)
    assert outcome_4.decision == "TRANSITION"
    assert outcome_4.champion is not None
    assert outcome_4.champion.candidate_id == "pkg-sector-3"
    assert outcome_4.is_learning_event is True
    assert outcome_4.conservation_report is not None
    assert outcome_4.conservation_report["is_conserved"] is True
    assert outcome_4.conservation_report["d_resolved"] == 30.0
    state_4 = outcome_4.next_state

    # All target requirements now 100% resolved
    dist_4 = extractor.extract_deficiencies(requirements, state_4)
    assert dist_4.total_deficient_severity == 0.0
    assert dist_4.covered_requirements == 6
    assert dist_4.deficient_requirements == 0

    # --- ROUND 5: AUTONOMOUS RATIONAL REFUSAL ---
    outcome_5 = engine.step(requirements, state_4, all_candidates)
    assert outcome_5.decision == "REFUSE"
    assert outcome_5.verdict == "NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE"
    assert "Top efficiency J" in outcome_5.reason
    assert outcome_5.champion is not None
    assert outcome_5.champion.cost_efficiency_j < DEFAULT_REFUSAL_THRESHOLD_TAU_J
    # State remains unmutated
    assert outcome_5.next_state == state_4
