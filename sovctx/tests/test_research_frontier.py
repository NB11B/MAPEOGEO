"""Unit and Integration Tests for the SOVCTX Autonomous Research Frontier.

Verifies:
1. Registration of all 9 Canonical Thread Families (T1 through T9) with negative bounds.
2. RESEARCH_QUESTION object and Priority scoring formula (P = N + B + E + I + G - D).
3. Open-Question Ledger operations, corroboration, and contradiction handling.
4. Institutional transport channels distinction (citation vs personnel vs institutional vs structural).
5. Autonomous evidence-driven branching engine (spawning T10+).
6. Thread saturation detector (Delta new relations -> 0).
7. 50/30/20 Attention Allocation (Spines / Bridges / Anomalies).
8. Cross-thread bridge matrix (T2xT3, T4xT6, T5xT3, T1xT8, etc.).
9. Discovery-oriented reporting format.
"""

from __future__ import annotations

import pytest

from sovctx.node.research_question import (
    AutonomousBranchingEngine,
    BranchingTrigger,
    CANONICAL_THREAD_FAMILIES,
    InstitutionalChannelType,
    OpenQuestionLedger,
    PriorityComponents,
    QuestionStatus,
    ResearchQuestion,
    ThreadFamily,
    ThreadSaturationDetector,
)
from sovctx.node.research_frontier import (
    CANONICAL_CROSS_THREAD_BRIDGES,
    CrossThreadBridge,
    DiscoveryReport,
    FrontierCycleAllocation,
    ResearchFrontierCoordinator,
)


# ---------------------------------------------------------------------------
# 1. Canonical Thread Families T1 - T9
# ---------------------------------------------------------------------------

def test_canonical_thread_families_registration() -> None:
    assert len(CANONICAL_THREAD_FAMILIES) == 9
    expected_ids = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]
    for tid in expected_ids:
        assert tid in CANONICAL_THREAD_FAMILIES
        tf = CANONICAL_THREAD_FAMILIES[tid]
        assert tf.thread_id == tid
        assert tf.name != ""
        assert tf.starting_region != ""
        assert len(tf.follow_targets) > 0
        assert len(tf.negative_presumptions) > 0

    # Verify specific negative presumptions
    t1 = CANONICAL_THREAD_FAMILIES["T1"]
    assert any("Leibniz directly caused" in p for p in t1.negative_presumptions)

    t2 = CANONICAL_THREAD_FAMILIES["T2"]
    assert any("aerospace was the inevitable endpoint" in p for p in t2.negative_presumptions)

    t3 = CANONICAL_THREAD_FAMILIES["T3"]
    assert any("radar/geophysics are the only applications" in p for p in t3.negative_presumptions)

    t4 = CANONICAL_THREAD_FAMILIES["T4"]
    assert any("plasma is the only descendant" in p for p in t4.negative_presumptions)

    t5 = CANONICAL_THREAD_FAMILIES["T5"]
    assert any("computing is the principal destination" in p for p in t5.negative_presumptions)

    t6 = CANONICAL_THREAD_FAMILIES["T6"]
    assert any("ancestors of modern AI" in p for p in t6.negative_presumptions)

    t7 = CANONICAL_THREAD_FAMILIES["T7"]
    assert any("intellectual lineage follows institutional lineage" in p for p in t7.negative_presumptions)

    t8 = CANONICAL_THREAD_FAMILIES["T8"]
    assert any("English translation preserves the historical concept" in p for p in t8.negative_presumptions)

    t9 = CANONICAL_THREAD_FAMILIES["T9"]
    assert any("pure discovery reserve" in p for p in t9.negative_presumptions)


# ---------------------------------------------------------------------------
# 2. Priority Scoring Formula: P = N + B + E + I + G - D
# ---------------------------------------------------------------------------

def test_priority_scoring_formula() -> None:
    comp = PriorityComponents(
        novelty=0.8,
        bridge_potential=0.7,
        evidentiary_quality=0.8,
        corroboration_potential=0.6,
        historical_gap_value=0.9,
        duplication_penalty=0.1,
    )
    # 0.8 + 0.7 + 0.8 + 0.6 + 0.9 - 0.1 = 3.7000
    assert comp.total_score == 3.7000

    # Test high duplication penalty reducing score
    comp_dup = PriorityComponents(
        novelty=0.2,
        bridge_potential=0.1,
        evidentiary_quality=0.5,
        corroboration_potential=0.2,
        historical_gap_value=0.1,
        duplication_penalty=0.9,
    )
    # 0.2 + 0.1 + 0.5 + 0.2 + 0.1 - 0.9 = 0.2000
    assert comp_dup.total_score == 0.2000

    # Test non-negative clipping
    comp_zero = PriorityComponents(
        novelty=0.1,
        bridge_potential=0.0,
        evidentiary_quality=0.1,
        corroboration_potential=0.0,
        historical_gap_value=0.0,
        duplication_penalty=1.0,
    )
    assert comp_zero.total_score == 0.0


def test_research_question_serialization() -> None:
    q = ResearchQuestion(
        question_id="RQ:T3:0041",
        thread_id="T3",
        originating_evidence="Tikhonov (1943) DAN SSSR",
        question_text="Where else was conditional stabilization of an inverse problem used before 1970?",
        relation_under_test="INVERT -> CONSTRAIN -> STABILIZE",
        known_endpoints=["Tikhonov", "Zelkin"],
        unknown_endpoint=True,
        temporal_window="1940-1970",
        priority_components=PriorityComponents(
            novelty=0.9, bridge_potential=0.8, evidentiary_quality=0.9,
            corroboration_potential=0.7, historical_gap_value=0.9, duplication_penalty=0.0
        ),
        target_channel=InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER,
    )
    assert q.priority == 4.2000
    d = q.to_dict()
    assert d["question_id"] == "RQ:T3:0041"
    assert d["status"] == "OPEN"
    assert d["target_channel"] == "DOCUMENTED_CITATION_TRANSFER"

    rebuilt = ResearchQuestion.from_dict(d)
    assert rebuilt.question_id == q.question_id
    assert rebuilt.priority == q.priority
    assert rebuilt.status == QuestionStatus.OPEN
    assert rebuilt.target_channel == InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER


# ---------------------------------------------------------------------------
# 3. Open-Question Ledger Operations
# ---------------------------------------------------------------------------

def test_open_question_ledger_lifecycle() -> None:
    ledger = OpenQuestionLedger()

    q1 = ResearchQuestion(
        question_id="RQ:T2:0001",
        thread_id="T2",
        originating_evidence="Lyapunov 1892",
        question_text="How did stability move into regulation?",
        relation_under_test="STABILIZE -> CONTROL",
        known_endpoints=["Lyapunov", "Pontryagin"],
        priority_components=PriorityComponents(novelty=0.7, bridge_potential=0.9),
    )
    ledger.add_question(q1)

    assert ledger.get_question("RQ:T2:0001") is not None
    assert len(ledger.get_by_thread("T2")) == 1

    # Record corroboration
    ledger.record_corroboration("RQ:T2:0001", "SRC:KRASOVSKII_1959")
    q_corrob = ledger.get_question("RQ:T2:0001")
    assert "SRC:KRASOVSKII_1959" in q_corrob.independent_support

    # Resolve question
    resolved = ledger.resolve_question(
        qid="RQ:T2:0001",
        resolved_endpoint="Krasovskii",
        summary="Krasovskii (1959) established Lyapunov functions with feedback control.",
        support_source="SRC:KRASOVSKII_1959",
    )
    assert resolved is True
    assert ledger.get_question("RQ:T2:0001").status == QuestionStatus.RESOLVED

    # Record contradiction on a new question
    q2 = ResearchQuestion(
        question_id="RQ:T9:0002",
        thread_id="T9",
        originating_evidence="Anomalous text",
        question_text="Did engineering technique predate formulation?",
        relation_under_test="PREDATE -> CLAIM",
        known_endpoints=["RadarLab"],
    )
    ledger.add_question(q2)
    ledger.record_contradiction("RQ:T9:0002", "Archival document confirms 1951 date contradicts 1958 theory.")
    assert ledger.get_question("RQ:T9:0002").status == QuestionStatus.CONTRADICTED


# ---------------------------------------------------------------------------
# 4. Autonomous Evidence-Driven Branching Engine
# ---------------------------------------------------------------------------

def test_autonomous_branching_engine() -> None:
    ledger = OpenQuestionLedger()
    engine = AutonomousBranchingEngine(ledger)

    # Trigger branching for new recurring relation
    new_thread = engine.evaluate_branching(
        trigger=BranchingTrigger.NEW_RECURRING_RELATION,
        label="State Estimation",
        starting_region="Radar -> Navigation -> Meteorology",
        follow_targets=["OBSERVE", "FILTER", "ESTIMATE_STATE", "CORRECT"],
        rationale="Encountered OBSERVE -> FILTER -> ESTIMATE_STATE -> CORRECT recurring across 3 independent domains.",
    )

    assert new_thread.thread_id.startswith("T10_")
    assert "STATE_ESTIMATION" in new_thread.thread_id
    assert new_thread.is_dynamically_spawned is True
    assert new_thread.spawn_trigger == "NEW_RECURRING_RELATION"
    assert new_thread.thread_id in ledger.threads


# ---------------------------------------------------------------------------
# 5. Thread Saturation Detector
# ---------------------------------------------------------------------------

def test_thread_saturation_detector() -> None:
    # 1. Below acquisition threshold (< 20)
    state_short = ThreadSaturationDetector.evaluate_thread_saturation(
        thread_id="T3",
        recent_acquisitions=10,
        duplicate_relations=9,
        new_relations=1,
    )
    assert state_short.is_saturated is False
    assert "CONTINUE_SAMPLING" in state_short.recommendation

    # 2. Saturated: 100 acquisitions, 98 duplicates, 2 new relations (2% < 5%)
    state_sat = ThreadSaturationDetector.evaluate_thread_saturation(
        thread_id="T3",
        recent_acquisitions=100,
        duplicate_relations=98,
        new_relations=2,
    )
    assert state_sat.is_saturated is True
    assert state_sat.new_relation_ratio == 0.0200
    assert "SATURATED" in state_sat.recommendation

    # 3. Productive: 50 acquisitions, 35 duplicates, 15 new relations (30% > 5%)
    state_prod = ThreadSaturationDetector.evaluate_thread_saturation(
        thread_id="T2",
        recent_acquisitions=50,
        duplicate_relations=35,
        new_relations=15,
    )
    assert state_prod.is_saturated is False
    assert state_prod.new_relation_ratio == 0.3000
    assert "ACTIVE_DISCOVERY" in state_prod.recommendation


# ---------------------------------------------------------------------------
# 6. Attention Allocation Engine (50 / 30 / 20 Budget)
# ---------------------------------------------------------------------------

def test_attention_allocation_50_30_20() -> None:
    coord = ResearchFrontierCoordinator()

    # Total 10 slots
    alloc_10 = coord.allocate_cycle(total_slots=10)
    assert alloc_10.spines_quota == 5     # 50%
    assert alloc_10.bridges_quota == 3    # 30%
    assert alloc_10.anomalies_quota == 2  # 20%

    # Verify selected candidates belong to the right thread families
    for q in alloc_10.selected_spines:
        assert q.thread_id in ("T1", "T2", "T3", "T4", "T5", "T6")

    for q in alloc_10.selected_anomalies:
        assert q.thread_id == "T9" or q.thread_id.startswith("T10_")


# ---------------------------------------------------------------------------
# 7. Cross-Thread Bridge Matrix
# ---------------------------------------------------------------------------

def test_cross_thread_bridge_matrix() -> None:
    bridges = CANONICAL_CROSS_THREAD_BRIDGES
    assert len(bridges) >= 6

    # Verify presence of core intersections
    bridge_ids = [b.bridge_id for b in bridges]
    assert "XBRIDGE:T2_T3" in bridge_ids  # Stability x Inversion
    assert "XBRIDGE:T4_T6" in bridge_ids  # Collective x Cybernetics
    assert "XBRIDGE:T5_T3" in bridge_ids  # Approximation x Inversion
    assert "XBRIDGE:T1_T8" in bridge_ids  # Relational Ancestry x Terminology


# ---------------------------------------------------------------------------
# 8. Discovery-Oriented Reporting
# ---------------------------------------------------------------------------

def test_discovery_oriented_reporting() -> None:
    coord = ResearchFrontierCoordinator()
    report = coord.generate_discovery_report(
        new_relations=[
            {
                "relation": "STABILIZE -> REGULATE",
                "endpoints": "Lyapunov -> Krasovskii",
                "source": "Krasovskii (1959)",
            }
        ],
        new_threads=[
            {
                "thread_id": "T10_STATE_ESTIMATION",
                "name": "State Estimation in Dynamic Inverse Systems",
                "trigger": "NEW_RECURRING_RELATION",
                "rationale": "Recurring cross-domain motif in radar and navigation.",
            }
        ],
        saturated_threads=[
            {
                "thread_id": "T3",
                "recommendation": "SATURATED: 95% duplicate relations. Rebalancing to cross-thread bridges.",
            }
        ],
    )

    md = report.to_markdown()
    assert "# SOVCTX Autonomous Research Frontier Report" in md
    assert "New Relationships Discovered" in md
    assert "STABILIZE -> REGULATE" in md
    assert "T10_STATE_ESTIMATION" in md
    assert "SATURATED" in md
    assert "Relational duality" in md
    assert "Binary East-West split" in md
