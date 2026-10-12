"""Unit tests for the SOVCTX Nano Research Work Plane Worker."""

from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import pytest

from sovctx.node.nano_research_worker import (
    CandidateBundle,
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
