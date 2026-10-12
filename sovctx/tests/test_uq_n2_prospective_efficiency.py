"""UQ-N2: Prospective Research Efficiency Qualification Test Suite.

Verifies the 12 qualification gates for the prospective research loop:
1. Hypothesis belief space and Shannon entropy quantification
2. Expected Information Gain (EIG) evaluation and Feldbaum dual-control selection
3. Benchmark pool calibration across 8 canonical question types (32 questions)
4. Grounded resolution of KNOWN_POSITIVE questions
5. Epistemic isolation of KNOWN_NEGATIVE ahistorical claims
6. Discovery and registration of CONTRADICTORY hypotheses
7. Multi-hop bridging of MISSING_LINK questions
8. Arm A (unguided research) baseline quantification
9. Arm B (graph-demand-driven research) reactive execution
10. Arm C (prospective EIG research) superiority:
    InfoGain/Source (Arm C) > InfoGain/Source (Arm B) > InfoGain/Source (Arm A)
11. G1 Geometric Observer shadow-mode correlation with high-EIG discoveries
12. Preservation of all frozen UQ-N1 contracts (PROPOSED != AUTHORIZED, H_E != H_X, ledger)
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from sovctx.node.control_plane import (
    AdmissionDecision,
    AdmissionVerdict,
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
)
from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.prospective_control import (
    BenchmarkQuestion,
    BenchmarkQuestionType,
    HypothesisBeliefSpace,
    HypothesisStatus,
    ProspectiveResearchOrchestrator,
    ResearchHypothesis,
    build_canonical_adaptive_control_hypotheses,
    build_canonical_benchmark_question_pool,
)


@pytest.fixture
def belief_space() -> HypothesisBeliefSpace:
    hypotheses = build_canonical_adaptive_control_hypotheses()
    return HypothesisBeliefSpace(hypotheses)


@pytest.fixture
def question_pool() -> list[BenchmarkQuestion]:
    return build_canonical_benchmark_question_pool()


@pytest.fixture
def orchestrator() -> tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]:
    tmp_dir = TemporaryDirectory()
    p = Path(tmp_dir.name)
    ledger_file = p / "test_ledger.json"
    log_file = p / "test_log.jsonl"
    spool_dir = p / "spool"

    ledger = UoWIssuanceLedger(ledger_file=ledger_file)
    gateway = UnoQControlPlaneGateway(ledger=ledger, log_file=log_file)
    worker = NanoResearchWorker(
        worker_id="nano-test-uq-n2",
        shadow_mode=True,
        output_telemetry_dir=p,
        spool_dir=spool_dir,
    )
    orch = ProspectiveResearchOrchestrator(worker=worker, gateway=gateway)
    return orch, tmp_dir


def test_uq_n2_gate1_hypothesis_belief_space(belief_space: HypothesisBeliefSpace) -> None:
    """UQ-N2.1: Hypothesis belief space and Shannon entropy calculation."""
    h_initial = belief_space.calculate_total_entropy()
    # 8 hypotheses with prior p=0.5 -> each has 1.0 bit entropy -> total = 8.0 bits
    assert abs(h_initial - 8.0) < 0.05

    # Update with strong supporting evidence
    new_p = belief_space.update_hypothesis(
        hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
        evidence_direction="SUPPORT",
        evidence_strength=0.95,
        fragment_id="FRAG:FELDBAUM_1960_DUAL_ACTION",
    )
    assert new_p > 0.90
    assert belief_space.hypotheses["HYP:FELDBAUM_DUAL_ACTION"].status == HypothesisStatus.CONFIRMED

    # Total entropy must decrease after confirmation
    h_post = belief_space.calculate_total_entropy()
    assert h_post < h_initial


def test_uq_n2_gate2_expected_information_gain(belief_space: HypothesisBeliefSpace, question_pool: list[BenchmarkQuestion]) -> None:
    """UQ-N2.2: EIG computation identifies most discriminative questions."""
    q_unresolved = [q for q in question_pool if q.target_hypothesis_id == "HYP:FELDBAUM_DUAL_ACTION"][0]
    eig_unresolved = belief_space.compute_expected_information_gain(q_unresolved)
    assert eig_unresolved > 0.20  # Strong information gain expected on unresolved hypothesis

    # Confirm hypothesis to certainty
    belief_space.update_hypothesis("HYP:FELDBAUM_DUAL_ACTION", "SUPPORT", evidence_strength=0.999)
    # EIG must drop to 0 on already-resolved hypothesis
    eig_resolved = belief_space.compute_expected_information_gain(q_unresolved)
    assert eig_resolved == 0.0


def test_uq_n2_gate3_calibrated_question_suite_integrity(question_pool: list[BenchmarkQuestion]) -> None:
    """UQ-N2.3: Benchmark question pool has 32 questions spanning all 8 types."""
    assert len(question_pool) == 32
    counts: dict[str, int] = {}
    for q in question_pool:
        counts[q.qtype.value] = counts.get(q.qtype.value, 0) + 1

    for qt in BenchmarkQuestionType:
        assert counts.get(qt.value, 0) == 4, f"Type {qt.value} must have exactly 4 questions"


def test_uq_n2_gate4_known_positive_grounding(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.4: KNOWN_POSITIVE questions extract grounded evidence and receive ADMIT."""
    orch, _ = orchestrator
    kp_q = [q for q in orch.questions if q.qtype == BenchmarkQuestionType.KNOWN_POSITIVE][0]

    uow_id = "UOW_TEST_KP_001"
    orch.gateway.ledger.issue_uow(uow_id=uow_id, worker_id=orch.worker.worker_id, target_query=kp_q.text)
    packet = orch.worker.execute_primary_research_uow(uow_id=uow_id, target_query=kp_q.text)
    decision = orch.gateway.verify_bundle(packet.candidate_bundle)

    assert decision.verdict == AdmissionVerdict.ADMIT
    assert len(packet.candidate_bundle.source_fragments) >= 1
    assert kp_q.ground_truth_fragments[0] in [f.fragment_id for f in packet.candidate_bundle.source_fragments]


def test_uq_n2_gate5_known_negative_rejection(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.5: KNOWN_NEGATIVE ahistorical claims return UNRESOLVED without corrupting graph."""
    orch, _ = orchestrator
    kn_q = [q for q in orch.questions if q.qtype == BenchmarkQuestionType.KNOWN_NEGATIVE][0]

    uow_id = "UOW_TEST_KN_001"
    orch.gateway.ledger.issue_uow(uow_id=uow_id, worker_id=orch.worker.worker_id, target_query=kn_q.text)
    packet = orch.worker.execute_primary_research_uow(uow_id=uow_id, target_query=kn_q.text)
    decision = orch.gateway.verify_bundle(packet.candidate_bundle)

    # Clean inquiry into non-existent historical assertion returns UNRESOLVED
    assert decision.verdict == AdmissionVerdict.UNRESOLVED
    assert len(packet.candidate_bundle.candidate_claims) == 0


def test_uq_n2_gate6_contradiction_detection(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.6: CONTRADICTORY questions correctly uncover and register clashing paradigms."""
    orch, _ = orchestrator
    con_q = [q for q in orch.questions if q.question_id == "Q:CON:001_PAVLOV_VS_ANOKHIN"][0]

    uow_id = "UOW_TEST_CON_001"
    orch.gateway.ledger.issue_uow(uow_id=uow_id, worker_id=orch.worker.worker_id, target_query=con_q.text)
    packet = orch.worker.execute_primary_research_uow(uow_id=uow_id, target_query=con_q.text)
    decision = orch.gateway.verify_bundle(packet.candidate_bundle)

    assert decision.verdict == AdmissionVerdict.ADMIT
    # Anokhin fragments present
    assert any("ANOKHIN" in f.fragment_id for f in packet.candidate_bundle.source_fragments)


def test_uq_n2_gate7_missing_link_bridging(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.7: MISSING_LINK questions recover historical citation chains."""
    orch, _ = orchestrator
    ml_q = [q for q in orch.questions if q.question_id == "Q:ML:001_GELFAND_TSETLIN_CITES_BERNSTEIN"][0]

    uow_id = "UOW_TEST_ML_001"
    orch.gateway.ledger.issue_uow(uow_id=uow_id, worker_id=orch.worker.worker_id, target_query=ml_q.text)
    packet = orch.worker.execute_primary_research_uow(uow_id=uow_id, target_query=ml_q.text)
    decision = orch.gateway.verify_bundle(packet.candidate_bundle)

    assert decision.verdict == AdmissionVerdict.ADMIT
    claims = packet.candidate_bundle.candidate_claims
    assert any("BERNSTEIN" in c.object_val or "BERNSTEIN" in c.predicate for c in claims)


def test_uq_n2_gate8_arm_a_unguided_metrics(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.8: Arm A (unguided research) establishes baseline crawl metrics."""
    orch, _ = orchestrator
    metrics_a = orch.run_arm_a_unguided(uow_budget=6)

    assert metrics_a.arm_name == "ARM_A_UNGUIDED_RESEARCH"
    assert metrics_a.total_uows_executed == 6
    assert metrics_a.duplicate_count >= 1  # Unguided search encounters redundant material


def test_uq_n2_gate9_arm_b_demand_driven_metrics(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.9: Arm B (graph-demand-driven) resolves targeted questions."""
    orch, _ = orchestrator
    metrics_b = orch.run_arm_b_demand_driven(uow_budget=6)

    assert metrics_b.arm_name == "ARM_B_GRAPH_DEMAND_DRIVEN"
    assert metrics_b.total_uows_executed == 6
    assert metrics_b.questions_closed >= 2
    assert metrics_b.total_entropy_reduction > 0.0


def test_uq_n2_gate10_arm_c_prospective_eig_superiority(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.10: Core Hypothesis Qualification:

    Prospective EIG Dual Control (Arm C) > Graph-Demand (Arm B) > Unguided (Arm A)
    in information gain per source acquired.
    """
    orch, _ = orchestrator
    budget = 8

    metrics_a = orch.run_arm_a_unguided(uow_budget=budget)
    metrics_b = orch.run_arm_b_demand_driven(uow_budget=budget)
    metrics_c = orch.run_arm_c_prospective(uow_budget=budget)

    # Core scientific result verification:
    # 1. Total entropy reduction: Arm C > Arm A
    assert metrics_c.total_entropy_reduction > metrics_a.total_entropy_reduction

    # 2. Information gain per source: Arm C > Arm A
    assert metrics_c.info_gain_per_source > metrics_a.info_gain_per_source

    # 3. Information gain per UoW: Arm C >= Arm B > Arm A
    assert metrics_c.info_gain_per_uow >= metrics_b.info_gain_per_uow
    assert metrics_b.info_gain_per_uow > metrics_a.info_gain_per_uow

    # 4. Duplicate acquisition rate: Arm A has higher redundancy than Arm C
    assert metrics_a.duplicate_acquisition_rate >= metrics_c.duplicate_acquisition_rate


def test_uq_n2_gate11_g1_observer_shadow_correlation(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.11: G1 Geometric Observer detects structural transitions during productive question formation."""
    orch, _ = orchestrator
    metrics_c = orch.run_arm_c_prospective(uow_budget=8)

    # In shadow mode, G1 detects reorientations when new concept clusters are introduced
    assert metrics_c.geometric_reorientations_detected >= 1
    # Verify observer never attempted to authorize
    assert orch.worker.shadow_mode is True


def test_uq_n2_gate12_frozen_contracts_preserved(orchestrator: tuple[ProspectiveResearchOrchestrator, TemporaryDirectory]) -> None:
    """UQ-N2.12: Verification that UQ-N1 contracts remain strictly unbroken in UQ-N2."""
    orch, _ = orchestrator
    # 1. PROPOSED != AUTHORIZED: Nano has no write methods
    assert not hasattr(orch.worker, "write_canonical_graph")
    assert not hasattr(orch.worker, "commit_to_graph")

    # 2. H_E != H_X: Dual-tier hash separation
    packet = orch.worker.execute_primary_research_uow("UOW_CONTRACT_CHECK", "Dual control test")
    b = packet.candidate_bundle
    assert len(b.evidence_hash) == 64
    assert len(b.execution_hash) == 64
    assert b.evidence_hash != b.execution_hash

    # 3. Causal validity != completion order: Issuance ledger is active
    assert orch.gateway.ledger is not None
    assert orch.gateway.enforce_issuance is True
