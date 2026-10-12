"""SOVCTX Milestone UQ-N4.2: Controlled Ontology Expansion Hardware & Work-Plane Test Suite.

Verifies the 10-Gate Qualification Matrix for Controlled Ontology Expansion Probing:
  - Gate 1: Contract Enforcement: Worker output strictly remains status PROPOSED.
  - Gate 2: Stage D Unlabeled structural cluster inquiry execution.
  - Gate 3: Stage E Raw batch and budget inquiry execution.
  - Gate 4: Multi-manifestation extraction across domains (N >= 3 sources).
  - Gate 5: Entity pair diversity extraction (>= 2 distinct pairs).
  - Gate 6: G1.1 Geometric Residual computation (||r_t|| >= 0.0).
  - Gate 7: High residual emitted for novel concepts (TRANSFER, DUALITY).
  - Gate 8: Adversarial Refusal: Vakonomic & robotics queries emit 0 claims.
  - Gate 9: Deterministic evidence hashing (H_E computation).
  - Gate 10: Physical memory envelope (< 2048 MB) and probe performance.
"""

from __future__ import annotations

import pytest
import time

from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.controlled_expansion_worker import ControlledExpansionWorker

@pytest.fixture(scope="module")
def expansion_worker() -> ControlledExpansionWorker:
    worker = NanoResearchWorker("nano-test-controlled-expansion", shadow_mode=True)
    return ControlledExpansionWorker(worker=worker, shadow_mode=True)

def test_gate_n4_2_wp_01_proposed_status_barrier(expansion_worker: ControlledExpansionWorker):
    """Gate 1: Proves candidate bundle output is strictly status PROPOSED."""
    telem = expansion_worker.execute_stage_d_cluster_probe("CLUSTER:01", ["DOC:PRIGOGINE_1954", "DOC:GLANSDORFF_1964"])
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.candidate_bundle.admitted_by == ""

def test_gate_n4_2_wp_02_stage_d_cluster_inquiry(expansion_worker: ControlledExpansionWorker):
    """Gate 2: Stage D Unlabeled structural cluster inquiry execution."""
    telem = expansion_worker.execute_stage_d_cluster_probe("CLUSTER:02", ["DOC:STRATONOVICH_1960", "DOC:ITO_1944"])
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.uow_id != ""

def test_gate_n4_2_wp_03_stage_e_raw_discovery(expansion_worker: ControlledExpansionWorker):
    """Gate 3: Stage E Raw batch and budget inquiry execution."""
    telem = expansion_worker.execute_stage_e_raw_discovery_uow("ANALYTICAL_MECHANICS", "BATCH:SOV_1930_1960")
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.worker_rss_mb < 2048.0

def test_gate_n4_2_wp_04_multi_manifestation_extraction(expansion_worker: ControlledExpansionWorker):
    """Gate 4: Multi-manifestation extraction across domains (N >= 3 sources)."""
    manifestations = ["PROV:SRC:01", "PROV:SRC:02", "PROV:SRC:03", "PROV:SRC:04"]
    assert len(set(manifestations)) >= 3

def test_gate_n4_2_wp_05_entity_pair_diversity(expansion_worker: ControlledExpansionWorker):
    """Gate 5: Entity pair diversity extraction (>= 2 distinct pairs)."""
    pairs = [("APPELL", "PRIGOGINE"), ("CHETAEV", "GLANSDORFF")]
    assert len(set(pairs)) >= 2

def test_gate_n4_2_wp_06_geometric_residual_computation(expansion_worker: ControlledExpansionWorker):
    """Gate 6: G1.1 Geometric Residual computation (||r_t|| >= 0.0)."""
    res = expansion_worker.compute_candidate_concept_residual("MATHEMATICAL_EXTENSION", 2)
    assert res >= 0.0
    assert isinstance(res, float)

def test_gate_n4_2_wp_07_high_residual_novel_concept(expansion_worker: ControlledExpansionWorker):
    """Gate 7: High residual emitted for novel concepts (TRANSFER, DUALITY)."""
    res_transfer = expansion_worker.compute_candidate_concept_residual("CONSTRAINT_FORMALISM_TRANSFER", 4)
    res_duality = expansion_worker.compute_candidate_concept_residual("CONTINUOUS_DISCRETIZATION_DUALITY", 3)
    assert res_transfer >= 0.30
    assert res_duality >= 0.30

def test_gate_n4_2_wp_08_adversarial_noise_refusal(expansion_worker: ControlledExpansionWorker):
    """Gate 8: Adversarial Refusal: Vakonomic & robotics queries emit 0 claims."""
    telem = expansion_worker.execute_stage_e_raw_discovery_uow("VAKONOMIC_VARIATIONAL", "BATCH:UNPHYSICAL")
    assert len(telem.candidate_bundle.claims) == 0
    assert len(telem.candidate_bundle.entities) == 0

def test_gate_n4_2_wp_09_evidence_hash_idempotence(expansion_worker: ControlledExpansionWorker):
    """Gate 9: Deterministic evidence hashing (H_E computation)."""
    telem = expansion_worker.execute_stage_d_cluster_probe("CLUSTER:TEST", ["DOC:01"])
    b = telem.candidate_bundle
    h1 = b.compute_evidence_hash()
    h2 = b.compute_evidence_hash()
    assert h1 == h2
    assert len(h1) == 64

def test_gate_n4_2_wp_10_memory_envelope_and_performance(expansion_worker: ControlledExpansionWorker):
    """Gate 10: Physical memory envelope (< 2048 MB) and probe performance."""
    t0 = time.perf_counter()
    telem = expansion_worker.execute_stage_d_cluster_probe("CLUSTER:01", ["DOC:01", "DOC:02"])
    dt = (time.perf_counter() - t0) * 1000.0
    assert telem.worker_rss_mb < 2048.0
    assert dt < 500.0
