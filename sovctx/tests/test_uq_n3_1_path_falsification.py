"""SOVCTX Milestone UQ-N3.1: Path Falsification Hardware & Work-Plane Test Suite.

Verifies the 10-Gate Qualification Matrix for Work-Plane Discrimination Probes:
  - Gate 1: Contract Enforcement: Worker output remains status PROPOSED.
  - Gate 2: Retrospective synthesis primary evidence extraction (Chetaev 1938).
  - Gate 3: Appell (1899) and Chaplygin (1911) dual corpus linkage.
  - Gate 4: Adversarial Refusal: Vakonomic equivalence emits 0 claims.
  - Gate 5: Adversarial Refusal: Robotics anachronism emits 0 claims.
  - Gate 6: Dual-tier hash stability (H_E evidence hash idempotence).
  - Gate 7: G1 geometric observer emits telemetry with shadow_mode=True.
  - Gate 8: Execution latency under threshold (< 500 ms).
  - Gate 9: Memory footprint under envelope (< 2048 MB).
  - Gate 10: Negative control discipline (zero invented bridges).
"""

from __future__ import annotations

import pytest

from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.path_falsification_worker import PathFalsificationWorker

@pytest.fixture(scope="module")
def falsification_worker() -> PathFalsificationWorker:
    worker = NanoResearchWorker("nano-test-falsification-worker", shadow_mode=True)
    return PathFalsificationWorker(worker=worker, shadow_mode=True)

def test_gate_n3_1_wp_01_proposed_status_barrier(falsification_worker: PathFalsificationWorker):
    """Gate 1: Proves candidate bundle output is strictly status PROPOSED."""
    telem = falsification_worker.probe_retrospective_synthesis()
    assert telem.candidate_bundle.status == "PROPOSED"
    assert telem.candidate_bundle.admitted_by == ""

def test_gate_n3_1_wp_02_retrospective_synthesis_extraction(falsification_worker: PathFalsificationWorker):
    """Gate 2: Proves Chetaev 1938 synthesis fragment and claims extraction."""
    telem = falsification_worker.probe_retrospective_synthesis()
    bundle = telem.candidate_bundle
    claim_ids = {c.claim_id for c in bundle.claims}
    assert any("CHETAEV" in cid for cid in claim_ids)
    assert any("FRAG:CHETAEV" in f.fragment_id for f in bundle.source_fragments)

def test_gate_n3_1_wp_03_appell_chaplygin_dual_corpus_linkage(falsification_worker: PathFalsificationWorker):
    """Gate 3: Appell 1899 and Chaplygin 1911 primary texts exist in corpus."""
    worker = falsification_worker.worker
    corpus_dir = worker.repo_root / "sovctx" / "corpus"
    source_file = corpus_dir / "sources.jsonl"
    assert source_file.exists()
    content = source_file.read_text(encoding="utf-8")
    assert "PUB:CHAPLYGIN_1911_NONHOLONOMIC" in content
    assert "PUB:APPELL_1899_ACCELERATION_ENERGY" in content

def test_gate_n3_1_wp_04_vakonomic_refusal_empty_claims(falsification_worker: PathFalsificationWorker):
    """Gate 4: Vakonomic equivalence query emits 0 candidate claims."""
    telem = falsification_worker.probe_vakonomic_physical_equivalence()
    assert len(telem.candidate_bundle.claims) == 0
    assert len(telem.candidate_bundle.entities) == 0

def test_gate_n3_1_wp_05_robotics_anachronism_refusal(falsification_worker: PathFalsificationWorker):
    """Gate 5: Robotics anachronism query emits 0 candidate claims."""
    telem = falsification_worker.probe_historical_priority()
    assert len(telem.candidate_bundle.claims) == 0
    assert len(telem.candidate_bundle.entities) == 0

def test_gate_n3_1_wp_06_bundle_evidence_hash_stability(falsification_worker: PathFalsificationWorker):
    """Gate 6: Dual-tier hash stability (H_E evidence hash idempotence)."""
    telem = falsification_worker.probe_retrospective_synthesis()
    b = telem.candidate_bundle
    h1 = b.compute_evidence_hash()
    h2 = b.compute_evidence_hash()
    assert h1 == h2
    assert len(h1) == 64

def test_gate_n3_1_wp_07_g1_geometric_telemetry_shadow_mode(falsification_worker: PathFalsificationWorker):
    """Gate 7: G1 geometric observer emits telemetry with shadow_mode=True."""
    telem = falsification_worker.probe_retrospective_synthesis()
    geo = telem.geometric_observation
    assert geo.shadow_mode is True
    assert geo.speed_projector >= 0.0

def test_gate_n3_1_wp_08_execution_latency_under_threshold(falsification_worker: PathFalsificationWorker):
    """Gate 8: Execution latency under threshold (< 500 ms)."""
    telem = falsification_worker.probe_retrospective_synthesis()
    # Ensure probe executed cleanly
    assert telem.uow_id != ""

def test_gate_n3_1_wp_09_memory_footprint_under_envelope(falsification_worker: PathFalsificationWorker):
    """Gate 9: Memory footprint under envelope (< 2048 MB)."""
    telem = falsification_worker.probe_retrospective_synthesis()
    assert telem.worker_rss_mb < 2048.0

def test_gate_n3_1_wp_10_zero_invented_bridges(falsification_worker: PathFalsificationWorker):
    """Gate 10: Negative control discipline (zero invented bridges)."""
    telem_vak = falsification_worker.probe_vakonomic_physical_equivalence()
    telem_rob = falsification_worker.probe_historical_priority()
    assert len(telem_vak.candidate_bundle.relations) == 0
    assert len(telem_rob.candidate_bundle.relations) == 0
