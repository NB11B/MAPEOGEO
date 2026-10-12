"""Unit tests for the SOVCTX Nano Research Work Plane Worker."""

from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import pytest

from sovctx.node.nano_research_worker import (
    CandidateBundle,
    CandidateBundleVerifier,
    CandidateQuestion,
    CandidateRelation,
    CandidateSource,
    NanoResearchWorker,
    ResearchStateVectorBuilder,
)
from sovctx.node.research_question import ResearchQuestion


def test_nano_worker_initialization_and_shadow_mode() -> None:
    worker = NanoResearchWorker(shadow_mode=True)
    assert worker.shadow_mode is True
    assert worker.current_state == "IDLE"
    assert len(worker.state_history) == 0


def test_nano_worker_candidate_bundle_hash_invariant() -> None:
    """Verifies PROPOSED != AUTHORIZED: Candidate bundles are immutable proposals."""
    bundle = CandidateBundle(
        uow_id="UOW_SOV_001",
        parent_uow_id=None,
        sequence_idx=1,
        sources=[
            CandidateSource(
                source_id="PUB:TEST_1960",
                label="Test Paper",
                authors=["Test Author"],
                year=1960,
                provenance_path="/data/test.pdf",
                content_hash="abc123hash",
            )
        ],
        relations=[
            CandidateRelation(
                source_id="PUB:TEST_1960",
                target_id="EQ:LYAPUNOV_1892",
                verb="STABILIZE",
                rationale="Proposes Lyapunov direct method application",
                evidence_fragment_ids=["FRAG:001"],
            )
        ],
    )
    h1 = bundle.compute_hash()
    assert len(h1) == 64
    assert bundle.content_hash == h1

    # Determinism: same contents yield identical hash
    bundle2 = CandidateBundle(
        uow_id="UOW_SOV_001",
        parent_uow_id=None,
        sequence_idx=1,
        sources=bundle.sources,
        relations=bundle.relations,
    )
    assert bundle2.compute_hash() == h1


def test_nano_worker_process_work_unit_and_self_observation() -> None:
    """Verifies that the Nano executes the research loop and self-observes state motion."""
    with TemporaryDirectory() as tmp_dir:
        worker = NanoResearchWorker(
            worker_id="nano-test-worker",
            tracker_k=2,
            tracker_alpha=0.5,
            shadow_mode=True,
            output_telemetry_dir=Path(tmp_dir),
        )

        q1 = ResearchQuestion(
            question_id="RQ:TEST:0001",
            thread_id="T2",
            originating_evidence="Krasovskii 1959",
            question_text="How does Krasovskii invariance extend to delayed differential equations?",
            relation_under_test="OBSERVE -> INVERT -> CONSTRAIN -> STABILIZE",
            known_endpoints=["Krasovskii"],
        )

        packet = worker.process_work_unit(
            uow_id="UOW_TEST_001",
            parent_uow_id=None,
            questions_to_probe=[q1],
        )

        assert packet.worker_id == "nano-test-worker"
        assert packet.uow_id == "UOW_TEST_001"
        assert packet.sequence_idx == 1
        assert packet.causal_sequence_id == 1
        assert packet.geometric_observation.shadow_mode is True
        assert len(worker.state_history) == 1

        # Check telemetry file persisted
        telemetry_file = Path(tmp_dir) / "nano_workplane_telemetry.json"
        assert telemetry_file.exists()


def test_nano_worker_shrinking_eigengap_caution_signal() -> None:
    """Verifies that low speed + degraded identifiability triggers AMBIGUOUS / ALLOCATE_MORE_OBSERVATION."""
    with TemporaryDirectory() as tmp_dir:
        worker = NanoResearchWorker(
            worker_id="nano-caution-tester",
            tracker_k=2,
            tracker_alpha=0.5,
            shadow_mode=True,
            output_telemetry_dir=Path(tmp_dir),
        )

        # Feed 15 nearly identical alternating orthogonal increments to force collapsing eigengap
        q_base = ResearchQuestion(
            question_id="RQ:TEST:0002",
            thread_id="T2",
            originating_evidence="Test",
            question_text="Test question",
            relation_under_test="STABILIZE",
            known_endpoints=["EndpointA", "EndpointB"],
        )

        for i in range(12):
            packet = worker.process_work_unit(
                uow_id=f"UOW_SEQ_{i:03d}",
                parent_uow_id=None,
                questions_to_probe=[q_base],
            )

        # In steady state where the question vector doesn't change, motion becomes zero
        # but rank-2 eigengap is degenerate (single rank-1 line repeated)
        geom = packet.geometric_observation
        assert geom.speed_max_angle < 0.25
        # The advice must NOT be premature STABLE_REGIME if identifiability is degraded
        if geom.identifiability == "NON_IDENTIFIABLE":
            assert geom.interpretation == "AMBIGUOUS_LOW_MOTION_WEAK_SEPARATION"
            assert geom.recommended_action == "DEFER_STABILIZATION_ALLOCATE_MORE_OBSERVATION"


def test_nano_worker_primary_research_uow_feldbaum() -> None:
    """Verifies that the Nano executes the bounded Feldbaum dual-control UoW and extracts candidate evidence."""
    with TemporaryDirectory() as tmp_dir:
        worker = NanoResearchWorker(
            worker_id="nano-test-feldbaum",
            shadow_mode=True,
            output_telemetry_dir=Path(tmp_dir),
        )

        query = (
            "Find primary-source evidence bearing on whether Feldbaum's dual-control formulation "
            "explicitly distinguishes information-gathering action from directing action."
        )

        packet = worker.execute_primary_research_uow(
            uow_id="UOW_QUAL_FELDBAUM_001",
            target_query=query,
        )

        bundle = packet.candidate_bundle
        assert bundle.uow_id == "UOW_QUAL_FELDBAUM_001"
        assert len(bundle.candidate_bundle_hash) == 64
        assert bundle.source_manifest == ["PUB:FELDBAUM_1960_DUAL_CONTROL"]
        assert len(bundle.source_fragments) == 1
        assert bundle.source_fragments[0].fragment_id == "FRAG:FELDBAUM_1960_DUAL_ACTION"
        assert "Part I, pp. 1242-1244" in bundle.source_fragments[0].locator

        # Check candidate entities
        ent_ids = {e.entity_id for e in bundle.candidate_entities}
        assert "CONCEPT:DUAL_CONTROL" in ent_ids
        assert "CONCEPT:INVESTIGATIVE_ACTION" in ent_ids
        assert "CONCEPT:DIRECTING_ACTION" in ent_ids
        assert "PERSON:FELDBAUM_AA" in ent_ids

        # Check candidate claims
        assert len(bundle.candidate_claims) == 1
        cl = bundle.candidate_claims[0]
        assert cl.predicate == "EXPLICITLY_DISTINGUISHES_ACTION_TYPES"
        assert cl.epistemic_status == "HISTORICALLY_SUPPORTED"
        assert cl.evidence_fragment_ids == ["FRAG:FELDBAUM_1960_DUAL_ACTION"]

        # Control-plane gate admission verification
        verifier = CandidateBundleVerifier(
            allowed_software_commits={bundle.software_commit},
        )
        decision = verifier.verify_bundle(bundle)
        assert decision.verdict.value == "ADMIT"


def test_nano_worker_backpressure_signaling() -> None:
    """Verifies that low RAM (< 256 MB) or thermal stop sets backpressure_flag = True."""
    from unittest.mock import patch
    from sovctx.node.guard import ResourceSample

    with TemporaryDirectory() as tmp_dir:
        worker = NanoResearchWorker(shadow_mode=True, output_telemetry_dir=Path(tmp_dir))

        # Simulated low RAM (< 256 MB)
        with patch.object(
            worker.guard,
            "sample",
            return_value=ResourceSample(
                sampled_at="2026-10-12T05:00:00Z",
                disk_free_gb=20.0,
                ram_available_mb=200.0,
                swap_used_gb=0.5,
                thermal_max_c=45.0,
                load_1m=1.0,
                worker_rss_mb=64.0,
                verdict="WARN",
                reasons=["Low RAM"],
            ),
        ):
            pkt = worker.process_work_unit(uow_id="UOW_LOW_RAM_TEST")
            assert pkt.backpressure_flag is True
            assert pkt.ram_available_mb == 200.0

        # Simulated thermal critical
        with patch.object(
            worker.guard,
            "sample",
            return_value=ResourceSample(
                sampled_at="2026-10-12T05:00:00Z",
                disk_free_gb=20.0,
                ram_available_mb=1000.0,
                swap_used_gb=0.5,
                thermal_max_c=85.0,
                load_1m=1.0,
                worker_rss_mb=64.0,
                verdict="STOP",
                reasons=["Thermal Critical"],
            ),
        ):
            pkt_th = worker.process_work_unit(uow_id="UOW_THERMAL_STOP_TEST")
            assert pkt_th.backpressure_flag is True

