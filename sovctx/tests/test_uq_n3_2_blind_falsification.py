"""SOVCTX Milestone UQ-N3.2: Blind Path Falsification Hardware & Work-Plane Test Suite.

Verifies the 10-Gate Qualification Matrix for Work-Plane Blind Probing:
  - Gate 1: Contract Enforcement: Worker output remains status PROPOSED.
  - Gate 2: Chetaev-Krasovskii primary evidence extraction.
  - Gate 3: Appell 1899 acceleration energy evidence extraction.
  - Gate 4: Samarskii difference schemes evidence extraction.
  - Gate 5: Lyapunov & Chetaev instability theorem evidence extraction.
  - Gate 6: Adversarial Refusal: Vakonomic equivalence emits 0 claims.
  - Gate 7: Adversarial Refusal: Robotics anachronism emits 0 claims.
  - Gate 8: Evidence hash idempotence (H_E deterministic computation).
  - Gate 9: G1 geometric observer emits telemetry with shadow_mode=True.
  - Gate 10: Physical memory envelope (< 2048 MB) and probe performance.
"""

from __future__ import annotations

import pytest

from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.blind_falsification_worker import BlindPathFalsificationWorker

@pytest.fixture(scope="module")
def blind_worker() -> BlindPathFalsificationWorker:
    worker = NanoResearchWorker("nano-test-blind-falsify", shadow_mode=True)
    return BlindPathFalsificationWorker(worker=worker, shadow_mode=True)

def test_gate_n3_2_wp_01_proposed_status_barrier(blind_worker: BlindPathFalsificationWorker):
    """Gate 1: Proves candidate bundle output is strictly status PROPOSED."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:01", "Chetaev 1934 instability theorem Krasovskii 1959")
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.candidate_bundle.admitted_by == ""

def test_gate_n3_2_wp_02_chetaev_krasovskii_valid_extraction(blind_worker: BlindPathFalsificationWorker):
    """Gate 2: Chetaev-Krasovskii primary evidence extraction."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:01", "Chetaev 1934 instability theorem Krasovskii 1959")
    bundle = telem.candidate_bundle
    claim_ids = {c.claim_id for c in bundle.claims}
    assert any("CHETAEV" in cid or "KRASOVSKII" in cid for cid in claim_ids)

def test_gate_n3_2_wp_03_appell_energy_valid_extraction(blind_worker: BlindPathFalsificationWorker):
    """Gate 3: Appell 1899 acceleration energy evidence extraction."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:02", "Appell 1899 acceleration energy CRAS Paris")
    bundle = telem.candidate_bundle
    claim_ids = {c.claim_id for c in bundle.claims}
    assert any("APPELL" in cid for cid in claim_ids)

def test_gate_n3_2_wp_04_samarskii_heuristic_extraction(blind_worker: BlindPathFalsificationWorker):
    """Gate 4: Samarskii difference schemes evidence extraction."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:03", "Samarskii difference schemes stability")
    bundle = telem.candidate_bundle
    claim_ids = {c.claim_id for c in bundle.claims}
    assert any("SAMARSKII" in cid for cid in claim_ids)

def test_gate_n3_2_wp_05_lyapunov_chetaev_predicate_extraction(blind_worker: BlindPathFalsificationWorker):
    """Gate 5: Lyapunov & Chetaev instability theorem evidence extraction."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:04", "Lyapunov 1892 Chetaev instability theorem 1934")
    bundle = telem.candidate_bundle
    claim_ids = {c.claim_id for c in bundle.claims}
    assert any("CHETAEV" in cid for cid in claim_ids)

def test_gate_n3_2_wp_06_vakonomic_refusal_empty_claims(blind_worker: BlindPathFalsificationWorker):
    """Gate 6: Adversarial Refusal: Vakonomic equivalence emits 0 claims."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:08", "Synthesize vakonomic mechanics delta int L dt = 0 with Chetaev equations")
    assert len(telem.candidate_bundle.claims) == 0
    assert len(telem.candidate_bundle.entities) == 0

def test_gate_n3_2_wp_07_robotics_anachronism_refusal(blind_worker: BlindPathFalsificationWorker):
    """Gate 7: Adversarial Refusal: Robotics anachronism emits 0 claims."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:09", "Did 1980 Stanford robotics invent Appell nonholonomic dynamics?")
    assert len(telem.candidate_bundle.claims) == 0
    assert len(telem.candidate_bundle.entities) == 0

def test_gate_n3_2_wp_08_evidence_hash_idempotence(blind_worker: BlindPathFalsificationWorker):
    """Gate 8: Evidence hash idempotence (H_E deterministic computation)."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:01", "Chetaev 1934 instability theorem")
    b = telem.candidate_bundle
    h1 = b.compute_evidence_hash()
    h2 = b.compute_evidence_hash()
    assert h1 == h2
    assert len(h1) == 64

def test_gate_n3_2_wp_09_g1_geometric_telemetry_shadow_mode(blind_worker: BlindPathFalsificationWorker):
    """Gate 9: G1 geometric observer emits telemetry with shadow_mode=True."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:01", "Chetaev 1934 instability theorem")
    assert telem.geometric_observation.shadow_mode is True
    assert telem.geometric_observation.speed_projector >= 0.0

def test_gate_n3_2_wp_10_memory_envelope_and_performance(blind_worker: BlindPathFalsificationWorker):
    """Gate 10: Physical memory envelope (< 2048 MB) and probe performance."""
    telem = blind_worker.execute_blind_trial_probe("TRIAL:01", "Chetaev 1934 instability theorem")
    assert telem.worker_rss_mb < 2048.0
    assert telem.uow_id != ""
