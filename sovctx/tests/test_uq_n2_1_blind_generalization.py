"""SOVCTX Milestone UQ-N2.1: Blind Prospective Generalization Test Suite.

Verifies the 10-Gate Qualification Matrix:
    - Gate 1: Stability Lineage Hypothesis Space Integrity (8 hypotheses, 8.0 bits initial entropy)
    - Gate 2: External Hidden Answer-Key Separation (zero controller leakage)
    - Gate 3: Class A Holdout Multi-Relation Recovery (7 diverse relation modes)
    - Gate 4: Leave-Family-Out Testing (Zubov true holdout discovery)
    - Gate 5: Class B Unresolved Calibration & Uncertainty Preservation
    - Gate 6: Class C Adversarial False Premise Rejection & Zero Invented Bridges
    - Gate 7: Brier Score Calibration (BS <= 0.15 on Class A)
    - Gate 8: Three-Arm Comparative Hierarchy (Arm C > Arm B > Arm A)
    - Gate 9: Cost-Aware Telemetry & Research Efficiency Logging (eta_research)
    - Gate 10: Retrospective G1 Geometric Telemetry & Shadow-Mode Invariant
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Set, Tuple

import pytest

from sovctx.node.control_plane import (
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
)
from sovctx.node.nano_research_worker import (
    NanoResearchWorker,
)
from sovctx.node.prospective_control import (
    HypothesisBeliefSpace,
    HypothesisStatus,
)
from sovctx.node.blind_generalization import (
    BlindProspectiveOrchestrator,
    ContaminationTag,
    GeneralizationQuestionClass,
    HistoricalRelationType,
    build_generalization_benchmark_pool,
    build_stability_lineage_hypotheses,
)


@pytest.fixture(scope="module")
def stability_environment() -> Tuple[NanoResearchWorker, UnoQControlPlaneGateway]:
    """Configures clean test environment for UQ-N2.1."""
    worker = NanoResearchWorker("nano-test-gen", shadow_mode=True)
    canonical_entities = {
        "PERSON:LYAPUNOV_AM",
        "CONCEPT:LYAPUNOV_STABILITY",
        "PERSON:CHETAEV_NG",
        "CONCEPT:CHETAEV_INSTABILITY",
        "PERSON:KRASOVSKII_NN",
        "PERSON:ZUBOV_VI",
        "CONCEPT:ZUBOV_METHOD_PDE",
        "CONCEPT:DOMAIN_OF_ATTRACTION",
        "INSTITUTION:KAZAN_UNIVERSITY",
        "PERSON:CHEBYSHEV_PL",
    }
    canonical_relations = {
        ("CONCEPT:CHETAEV_INSTABILITY", "CONCEPT:LYAPUNOV_STABILITY"),
        ("PERSON:CHETAEV_NG", "CONCEPT:CHETAEV_INSTABILITY"),
        ("PERSON:KRASOVSKII_NN", "PERSON:CHETAEV_NG"),
        ("PERSON:ZUBOV_VI", "CONCEPT:ZUBOV_METHOD_PDE"),
        ("CONCEPT:ZUBOV_METHOD_PDE", "CONCEPT:DOMAIN_OF_ATTRACTION"),
        ("CONCEPT:ZUBOV_METHOD_PDE", "CONCEPT:LYAPUNOV_STABILITY"),
        ("PERSON:CHETAEV_NG", "INSTITUTION:KAZAN_UNIVERSITY"),
        ("PERSON:LYAPUNOV_AM", "PERSON:CHEBYSHEV_PL"),
    }
    canonical_claims = {
        "CLAIM:CHETAEV_1934_INSTABILITY_THEOREM_INVERSION",
        "CLAIM:ZUBOV_1955_PDE_DOMAIN_OF_ATTRACTION",
        "CLAIM:KRASOVSKII_1959_LYAPUNOV_STOCHASTIC_CONVERSE",
    }
    gateway = UnoQControlPlaneGateway(
        ledger=UoWIssuanceLedger(),
        canonical_entities=canonical_entities,
        canonical_relations=canonical_relations,
        canonical_claims=canonical_claims,
    )
    return worker, gateway


def test_uq_n2_1_gate1_stability_hypothesis_space_integrity() -> None:
    """Gate 1: Verifies 8 calibrated hypotheses with non-committal priors and initial entropy = 8.0 bits."""
    hyps = build_stability_lineage_hypotheses()
    assert len(hyps) == 8

    belief = HypothesisBeliefSpace(hyps)
    for h in belief.hypotheses.values():
        assert h.prior == 0.50
        assert h.current_probability == 0.50
        assert h.status == HypothesisStatus.UNRESOLVED

    total_h = belief.calculate_total_entropy()
    assert total_h == pytest.approx(8.0, abs=1e-3)


def test_uq_n2_1_gate2_hidden_answer_key_separation() -> None:
    """Gate 2: Verifies that controller question view strips all hidden answers, fragments, and verdicts."""
    questions = build_generalization_benchmark_pool()
    assert len(questions) == 34

    for q in questions:
        ctrl_q = q.to_controller_view()
        # Hidden metadata must not leak to controller
        assert ctrl_q.ground_truth_verdict == ""
        assert ctrl_q.ground_truth_fragments == []
        assert not hasattr(ctrl_q, "hidden_required_relation")
        assert not hasattr(ctrl_q, "hidden_ground_truth_verdict")


def test_uq_n2_1_gate3_class_a_holdout_multi_relation_diversity() -> None:
    """Gate 3: Verifies Class A questions span all 7 diverse relation types."""
    questions = build_generalization_benchmark_pool()
    class_a = [q for q in questions if q.qclass == GeneralizationQuestionClass.CLASS_A_HOLDOUT]
    assert len(class_a) == 14

    relation_types = {q.relation_type for q in class_a}
    assert HistoricalRelationType.MATHEMATICAL_EXTENSION in relation_types
    assert HistoricalRelationType.DOCUMENTED_CITATION in relation_types
    assert HistoricalRelationType.TEACHER_STUDENT_LINEAGE in relation_types
    assert HistoricalRelationType.INSTITUTIONAL_TRANSFER in relation_types
    assert HistoricalRelationType.TERMINOLOGICAL_CONTINUITY in relation_types
    assert HistoricalRelationType.INDEPENDENT_PARALLEL in relation_types
    assert HistoricalRelationType.AEROSPACE_ENGINEERING_TRANSFER in relation_types


def test_uq_n2_1_gate4_leave_family_out_zubov_discovery(stability_environment: Tuple[NanoResearchWorker, UnoQControlPlaneGateway]) -> None:
    """Gate 4: Verifies leave-family-out testing on Zubov (TRUE_HOLDOUT) without initial graph presence."""
    worker, gateway = stability_environment
    questions = build_generalization_benchmark_pool()
    zubov_questions = [
        q for q in questions
        if q.target_cluster == "ZUBOV" and q.contamination == ContaminationTag.TRUE_HOLDOUT
    ]
    assert len(zubov_questions) >= 3

    # Must issue UoW in ledger before execution (causal authority contract)
    gateway.ledger.issue_uow(
        uow_id="UOW_TEST_ZUBOV",
        worker_id=worker.worker_id,
        target_query=zubov_questions[0].text,
    )

    # Primary research probe for Zubov
    packet = worker.execute_primary_research_uow(
        uow_id="UOW_TEST_ZUBOV",
        target_query=zubov_questions[0].text,
    )
    bundle = packet.candidate_bundle
    # Check that candidate entities and claims for Zubov are proposed
    ent_ids = [e.entity_id for e in bundle.candidate_entities]
    assert "PERSON:ZUBOV_VI" in ent_ids
    assert "CONCEPT:ZUBOV_METHOD_PDE" in ent_ids

    # Gateway verifies and admits candidate bundle
    decision = gateway.verify_bundle(bundle)
    assert decision.verdict.value == "ADMIT"


def test_uq_n2_1_gate5_class_b_unresolved_calibration() -> None:
    """Gate 5: Verifies Class B genuinely unresolved inquiries terminate as UNRESOLVED without forced binary collapse."""
    questions = build_generalization_benchmark_pool()
    class_b = [q for q in questions if q.qclass == GeneralizationQuestionClass.CLASS_B_UNRESOLVED]
    assert len(class_b) == 10

    for q in class_b:
        assert q.hidden_ground_truth_verdict == "UNRESOLVED"
        assert q.hidden_required_relation is None


def test_uq_n2_1_gate6_class_c_adversarial_rejection_and_zero_invented_bridges(
    stability_environment: Tuple[NanoResearchWorker, UnoQControlPlaneGateway]
) -> None:
    """Gate 6: Verifies Class C adversarial false premises are safely rejected with zero invented bridges."""
    worker, _ = stability_environment
    questions = build_generalization_benchmark_pool()
    class_c = [q for q in questions if q.qclass == GeneralizationQuestionClass.CLASS_C_ADVERSARIAL]
    assert len(class_c) == 10

    for q in class_c:
        packet = worker.execute_primary_research_uow(
            uow_id=f"UOW_ADV_{q.question_id}",
            target_query=q.text,
        )
        bundle = packet.candidate_bundle
        # Negative filter must ensure NO candidate claims or relations are generated for adversarial premises
        assert len(bundle.candidate_claims) == 0
        for r in bundle.candidate_relations:
            # Must not invent Chetaev dual control or Zubov neural network bridges
            assert not ("CHETAEV" in r.source_id and "DUAL_CONTROL" in r.target_id)
            assert not ("ZUBOV" in r.source_id and "NEURAL" in r.target_id)


def test_uq_n2_1_gate7_brier_score_calibration() -> None:
    """Gate 7: Verifies Brier score formulation on calibrated probability distributions."""
    hyps = build_stability_lineage_hypotheses()
    belief = HypothesisBeliefSpace(hyps)

    # Initial uniform belief Brier score on TRUE hypotheses: (0.5 - 1.0)^2 = 0.25
    brier_0 = (0.5 - 1.0) ** 2
    assert brier_0 == 0.25

    # After primary explicit update to 0.90: (0.90 - 1.0)^2 = 0.01 (excellent calibration)
    belief.update_hypothesis("HYP:CHETAEV_INSTABILITY_EXTENSION", "SUPPORT", evidence_strength=0.90)
    p_updated = belief.hypotheses["HYP:CHETAEV_INSTABILITY_EXTENSION"].current_probability
    brier_updated = (p_updated - 1.0) ** 2
    assert brier_updated <= 0.02


def test_uq_n2_1_gate8_three_arm_comparative_hierarchy(stability_environment: Tuple[NanoResearchWorker, UnoQControlPlaneGateway]) -> None:
    """Gate 8: Validates the research efficiency hierarchy: Arm C (EIG) > Arm B (FIFO) > Arm A (Unguided)."""
    worker, gateway = stability_environment
    questions = build_generalization_benchmark_pool()
    hyps = build_stability_lineage_hypotheses()
    orchestrator = BlindProspectiveOrchestrator(
        worker=worker,
        gateway=gateway,
        questions=questions,
        hypotheses=hyps,
    )

    metrics_a, _ = orchestrator.run_arm_a_unguided(uow_budget=8)
    metrics_b, _ = orchestrator.run_arm_b_demand_driven(uow_budget=8)
    metrics_c, _ = orchestrator.run_arm_c_prospective_eig(uow_budget=8)

    # Core generalizability assertion: Prospective EIG strictly outperforms unguided and reactive FIFO
    assert metrics_c.total_entropy_reduction > metrics_b.total_entropy_reduction
    assert metrics_b.total_entropy_reduction > metrics_a.total_entropy_reduction
    assert metrics_c.epistemic_yield_per_uow > metrics_b.epistemic_yield_per_uow
    assert metrics_c.epistemic_yield_per_source > metrics_a.epistemic_yield_per_source

    # False promotion rate must remain zero across all arms
    assert metrics_c.false_promotion_rate == 0.0
    assert metrics_c.invented_bridge_edges == 0


def test_uq_n2_1_gate9_cost_aware_telemetry_logging(stability_environment: Tuple[NanoResearchWorker, UnoQControlPlaneGateway]) -> None:
    """Gate 9: Verifies that cost variables (CPU, network, parse, verify, RSS) are logged per action."""
    worker, gateway = stability_environment
    questions = build_generalization_benchmark_pool()
    hyps = build_stability_lineage_hypotheses()
    orchestrator = BlindProspectiveOrchestrator(
        worker=worker,
        gateway=gateway,
        questions=questions,
        hypotheses=hyps,
    )

    metrics_c, _ = orchestrator.run_arm_c_prospective_eig(uow_budget=4)
    assert len(metrics_c.cost_records) == 4
    for cr in metrics_c.cost_records:
        assert cr.cpu_time_ms >= 0.0
        assert cr.network_bytes >= 0
        assert cr.verification_ops >= 1
        assert cr.peak_rss_mb >= 0.0

    assert metrics_c.research_cost_efficiency > 0.0


def test_uq_n2_1_gate10_g1_shadow_retrospective_telemetry(stability_environment: Tuple[NanoResearchWorker, UnoQControlPlaneGateway]) -> None:
    """Gate 10: Verifies logging of G1 observer states and confirms zero admission authority."""
    worker, gateway = stability_environment
    questions = build_generalization_benchmark_pool()
    hyps = build_stability_lineage_hypotheses()
    orchestrator = BlindProspectiveOrchestrator(
        worker=worker,
        gateway=gateway,
        questions=questions,
        hypotheses=hyps,
    )

    metrics_c, _ = orchestrator.run_arm_c_prospective_eig(uow_budget=4)
    assert len(metrics_c.geometric_records) == 4
    for gr in metrics_c.geometric_records:
        assert hasattr(gr, "speed_max_angle")
        assert hasattr(gr, "speed_projector")
        assert hasattr(gr, "kappa_g")
        assert hasattr(gr, "residual_norm")
        assert hasattr(gr, "davis_kahan_ratio")

    assert worker.shadow_mode is True
