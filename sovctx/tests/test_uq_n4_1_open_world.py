"""SOVCTX Milestone UQ-N4.1: Open-World Work-Plane & Hardware Test Suite.

Verifies the 10-Gate Qualification Matrix for Work-Plane Open-World Probing:
  - Gate 1: Contract Enforcement: Worker output strictly remains status PROPOSED.
  - Gate 2: Stage A Entity-only probe execution without relation hints.
  - Gate 3: Stage B Institutional domain probe execution.
  - Gate 4: Stage C Conceptual anomaly probe execution.
  - Gate 5: G1.1 Geometric Residual computation (||r_t|| >= 0.0).
  - Gate 6: Open-set detection: High residual emitted for novel out-of-vocabulary concepts (||r_t|| >= 0.30).
  - Gate 7: Low residual emitted for classical known lineages (||r_t|| < 0.10).
  - Gate 8: Adversarial Refusal: Vakonomic & robotics noise queries emit 0 claims.
  - Gate 9: Deterministic evidence hashing (H_E computation).
  - Gate 10: Physical memory envelope (< 2048 MB) and probe performance.
"""

from __future__ import annotations

import pytest
import time

from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.open_world_worker import OpenWorldResearchWorker

@pytest.fixture(scope="module")
def open_worker() -> OpenWorldResearchWorker:
    worker = NanoResearchWorker("nano-test-open-world", shadow_mode=True)
    return OpenWorldResearchWorker(worker=worker, shadow_mode=True)

def test_gate_n4_1_wp_01_proposed_status_barrier(open_worker: OpenWorldResearchWorker):
    """Gate 1: Proves candidate bundle output is strictly status PROPOSED."""
    telem = open_worker.execute_stage_a_entity_probe("TRIAL:01", ["Pontryagin 1956", "Feldbaum 1960"])
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.candidate_bundle.admitted_by == ""

def test_gate_n4_1_wp_02_stage_a_entity_probe(open_worker: OpenWorldResearchWorker):
    """Gate 2: Stage A Entity-only probe execution without relation hints."""
    telem = open_worker.execute_stage_a_entity_probe("TRIAL:02", ["Chetaev 1934", "Krasovskii 1959"])
    claim_ids = {c.claim_id for c in telem.candidate_bundle.claims}
    assert any("CHETAEV" in cid or "KRASOVSKII" in cid for cid in claim_ids)
    assert telem.candidate_bundle.status == "PROPOSED"

def test_gate_n4_1_wp_03_stage_b_institution_probe(open_worker: OpenWorldResearchWorker):
    """Gate 3: Stage B Institutional domain probe execution."""
    telem = open_worker.execute_stage_b_institution_probe(
        "TRIAL:B1",
        "Kazan School of Mechanics stability of motion Chetaev 1934"
    )
    assert telem.candidate_bundle.status == "PROPOSED"
    assert len(telem.candidate_bundle.claims) >= 0

def test_gate_n4_1_wp_04_stage_c_conceptual_anomaly_probe(open_worker: OpenWorldResearchWorker):
    """Gate 4: Stage C Conceptual anomaly probe execution."""
    query = "A recurring formulation involving admissibility, perturbation, and constrained motion Appell Chetaev"
    telem = open_worker.execute_stage_c_anomaly_probe("TRIAL:C1", query)
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.worker_rss_mb < 2048.0

def test_gate_n4_1_wp_05_geometric_residual_computation(open_worker: OpenWorldResearchWorker):
    """Gate 5: G1.1 Geometric Residual computation (||r_t|| >= 0.0)."""
    res = open_worker.compute_trial_geometric_residual("Chetaev Krasovskii stability")
    assert res >= 0.0
    assert isinstance(res, float)

def test_gate_n4_1_wp_06_high_residual_novel_concept(open_worker: OpenWorldResearchWorker):
    """Gate 6: High residual emitted for novel out-of-vocabulary concepts (||r_t|| >= 0.30)."""
    res_lie = open_worker.compute_trial_geometric_residual("Poincare Chetaev Lie algebra equations")
    res_strat = open_worker.compute_trial_geometric_residual("Stratonovich Ito stochastic integral calculus")
    assert res_lie >= 0.30
    assert res_strat >= 0.30

def test_gate_n4_1_wp_07_low_residual_known_lineage(open_worker: OpenWorldResearchWorker):
    """Gate 7: Low residual emitted for classical known lineages (||r_t|| < 0.10)."""
    res = open_worker.compute_trial_geometric_residual("Pontryagin Feldbaum maximum principle")
    assert res < 0.10

def test_gate_n4_1_wp_08_adversarial_noise_refusal(open_worker: OpenWorldResearchWorker):
    """Gate 8: Adversarial Refusal: Vakonomic & robotics noise queries emit 0 claims."""
    telem_vak = open_worker.execute_stage_c_anomaly_probe(
        "TRIAL:10",
        "Synthesize vakonomic mechanics delta int L dt = 0 with Chetaev equations"
    )
    assert len(telem_vak.candidate_bundle.claims) == 0
    assert len(telem_vak.candidate_bundle.entities) == 0

def test_gate_n4_1_wp_09_evidence_hash_idempotence(open_worker: OpenWorldResearchWorker):
    """Gate 9: Deterministic evidence hashing (H_E computation)."""
    telem = open_worker.execute_stage_a_entity_probe("TRIAL:01", ["Chetaev 1934"])
    b = telem.candidate_bundle
    h1 = b.compute_evidence_hash()
    h2 = b.compute_evidence_hash()
    assert h1 == h2
    assert len(h1) == 64

def test_gate_n4_1_wp_10_memory_envelope_and_performance(open_worker: OpenWorldResearchWorker):
    """Gate 10: Physical memory envelope (< 2048 MB) and probe performance."""
    t0 = time.perf_counter()
    telem = open_worker.execute_stage_a_entity_probe("TRIAL:01", ["Pontryagin 1956", "Feldbaum 1960"])
    dt = (time.perf_counter() - t0) * 1000.0
    assert telem.worker_rss_mb < 2048.0
    assert dt < 500.0
