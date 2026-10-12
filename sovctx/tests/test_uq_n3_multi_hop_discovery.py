"""SOVCTX Milestone UQ-N3: Multi-Hop Frontier Discovery Hardware & Work-Plane Test Suite.

Verifies the 10-Gate Qualification Matrix on the Jetson Nano Work Plane:
  - Gate 1: Architectural Barrier: PROPOSED != AUTHORIZED output status.
  - Gate 2: Hop 1: Chaplygin 1911 & Appell 1899 Primary Evidence Acquisition.
  - Gate 3: Hop 2: Chetaev 1938 Gauss Principle & Virtual Displacement Conditions.
  - Gate 4: Hop 3: Appell-Chetaev Equations of Motion Synthesis.
  - Gate 5: Hop 4: Rumyantsev 1966 Non-Holonomic Lyapunov Stability Discovery.
  - Gate 6: Full 4-Hop Continuous Derivation Lineage Traversal.
  - Gate 7: Candidate Bundle Content Hash & Evidence Hash Stability.
  - Gate 8: Adversarial Refusal & Zero False Promotions (Vakonomic Mechanics, 1980s Robotics).
  - Gate 9: G1 Geometric Observer Telemetry & Shadow-Mode Invariant.
  - Gate 10: Physical Memory Footprint (< 2048 MB) and Execution Latency.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import pytest

from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.multi_hop_frontier import MultiHopFrontierOrchestrator

@pytest.fixture(scope="module")
def frontier_orchestrator() -> MultiHopFrontierOrchestrator:
    worker = NanoResearchWorker("nano-test-n3-worker", shadow_mode=True)
    return MultiHopFrontierOrchestrator(worker=worker, shadow_mode=True)

def test_gate_n3_wp_01_proposed_not_authorized_contract(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 1: Worker must strictly output status=PROPOSED with zero executive authority."""
    h1 = frontier_orchestrator.execute_hop1_chaplygin_appell()
    assert h1.bundle.status == "PROPOSED"
    assert h1.bundle.canonical_commit_hash == ""
    assert h1.bundle.admitted_by == ""

def test_gate_n3_wp_02_hop1_chaplygin_appell_acquisition(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 2: Hop 1 primary evidence extraction for Chaplygin and Appell."""
    h1 = frontier_orchestrator.execute_hop1_chaplygin_appell()
    bundle = h1.bundle
    
    entity_ids = {e.entity_id for e in bundle.entities}
    assert "PERSON:CHAPLYGIN_SA" in entity_ids or "PERSON:APPELL_P" in entity_ids
    assert "CONCEPT:NONHOLONOMIC_CONSTRAINTS" in entity_ids or "CONCEPT:ACCELERATION_ENERGY" in entity_ids
    assert len(bundle.claims) >= 1
    assert any("CHAPLYGIN" in c.claim_id or "APPELL" in c.claim_id for c in bundle.claims)

def test_gate_n3_wp_03_hop2_chetaev_virtual_displacement(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 3: Hop 2 Chetaev 1938 Gauss principle and virtual displacement condition."""
    h2 = frontier_orchestrator.execute_hop2_chetaev_conditions()
    bundle = h2.bundle

    entity_ids = {e.entity_id for e in bundle.entities}
    assert "CONCEPT:CHETAEV_CONDITIONS" in entity_ids or "CONCEPT:GAUSS_PRINCIPLE" in entity_ids
    assert len(bundle.claims) >= 1
    assert any("CHETAEV" in c.claim_id for c in bundle.claims)

def test_gate_n3_wp_04_hop3_appell_chetaev_equations(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 4: Hop 3 Appell-Chetaev equations of motion synthesis."""
    h3 = frontier_orchestrator.execute_hop3_appell_chetaev_synthesis()
    bundle = h3.bundle

    entity_ids = {e.entity_id for e in bundle.entities}
    assert "CONCEPT:APPELL_CHETAEV_EQUATIONS" in entity_ids
    assert len(bundle.claims) >= 1
    assert any("CHETAEV" in c.claim_id for c in bundle.claims)
    assert len(h3.parent_uow_ids) >= 1

def test_gate_n3_wp_05_hop4_rumyantsev_nonholonomic_lyapunov(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 5: Hop 4 Rumyantsev 1966 non-holonomic Lyapunov stability discovery."""
    h4 = frontier_orchestrator.execute_hop4_rumyantsev_stability()
    bundle = h4.bundle

    entity_ids = {e.entity_id for e in bundle.entities}
    assert "PERSON:RUMYANTSEV_VV" in entity_ids or "CONCEPT:NONHOLONOMIC_LYAPUNOV_STABILITY" in entity_ids
    assert len(bundle.claims) >= 1
    assert any("RUMYANTSEV" in c.claim_id for c in bundle.claims)

def test_gate_n3_wp_06_complete_multi_hop_traversal_closure(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 6: Full 4-hop continuous derivation lineage traversal."""
    report = frontier_orchestrator.run_full_lineage_discovery()
    assert report["success"] is True
    assert report["hops_executed"] == 4
    assert len(report["hop_results"]) == 4

def test_gate_n3_wp_07_candidate_bundle_hash_stability(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 7: Deterministic SHA-256 hash computation."""
    h1 = frontier_orchestrator.execute_hop1_chaplygin_appell()
    b1 = h1.bundle
    hash1 = b1.compute_evidence_hash()
    hash2 = b1.compute_evidence_hash()
    assert hash1 == hash2
    assert len(hash1) == 64

def test_gate_n3_wp_08_adversarial_vakonomic_refusal(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 8: Adversarial queries must be rejected with 0 claims emitted."""
    adv1 = frontier_orchestrator.execute_adversarial_distractor_query(
        "Synthesize vakonomic mechanics delta int L dt = 0 with Chetaev non-holonomic equations"
    )
    assert len(adv1.bundle.claims) == 0
    assert len(adv1.bundle.entities) == 0

    adv2 = frontier_orchestrator.execute_adversarial_distractor_query(
        "Did 1980 Stanford robotics invent Appell nonholonomic dynamics?"
    )
    assert len(adv2.bundle.claims) == 0

def test_gate_n3_wp_09_g1_geometric_telemetry_shadow_mode(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 9: G1 geometric observer emits telemetry with shadow_mode=True."""
    h1 = frontier_orchestrator.execute_hop1_chaplygin_appell()
    geo = h1.telemetry.geometric_observation
    assert geo.shadow_mode is True
    assert geo.speed_projector >= 0.0
    assert geo.spectral_gap >= 0.0

def test_gate_n3_wp_10_memory_envelope_and_performance(frontier_orchestrator: MultiHopFrontierOrchestrator):
    """Gate 10: Jetson Nano memory footprint < 2048 MB and fast execution."""
    h1 = frontier_orchestrator.execute_hop1_chaplygin_appell()
    rss = h1.telemetry.worker_rss_mb
    assert rss < 2048.0
    assert h1.execution_time_ms < 1000.0
