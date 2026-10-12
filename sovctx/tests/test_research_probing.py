"""Unit tests for Research Probing and Autonomous Shakedown Engine."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sovctx.node.research_frontier import ResearchFrontierCoordinator
from sovctx.node.research_probing import (
    CorpusGraphIndex,
    EpochCheckpoint,
    ProbeOutcome,
    ResearchProber,
    ResearchShakedownSupervisor,
)
from sovctx.node.research_question import (
    InstitutionalChannelType,
    OpenQuestionLedger,
    PriorityComponents,
    QuestionStatus,
    ResearchQuestion,
)


def test_corpus_graph_index() -> None:
    # Test loading and indexing
    index = CorpusGraphIndex()
    assert len(index.nodes) > 0
    assert len(index.edges) > 0

    # Keyword search test
    hits = index.search_keyword("gelfand")
    assert len(hits) >= 1
    hit_ids = [h["id"] for h in hits]
    assert any("GELFAND" in hid for hid in hit_ids)


def test_research_prober_xbridge_resolution() -> None:
    index = CorpusGraphIndex()
    prober = ResearchProber(index)

    q = ResearchQuestion(
        question_id="RQ:XBRIDGE:T2_T3:0001",
        thread_id="T2",
        originating_evidence="Pontryagin & Tikhonov",
        question_text="Can Pontryagin's maximum principle be unified with Tikhonov regularization in ill-posed dynamic optimization?",
        relation_under_test="OBSERVE -> INVERT -> CONSTRAIN -> REGULARIZE -> CONTROL",
        known_endpoints=["Pontryagin", "Tikhonov", "Krasovskii", "Lavrentiev"],
        metadata={"bridge_id": "XBRIDGE:T2_T3"},
        target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
    )

    outcome = prober.probe(q)
    assert outcome.status == QuestionStatus.RESOLVED
    assert outcome.resolved_endpoint is not None
    assert "Krasovskii" in outcome.resolved_endpoint
    assert len(outcome.new_relations_found) >= 1
    assert len(outcome.descendant_questions) == 1
    assert outcome.descendant_questions[0].generation == 1
    assert outcome.descendant_questions[0].metadata.get("parent_question_id") == "RQ:XBRIDGE:T2_T3:0001"


def test_research_prober_anomaly_contradiction() -> None:
    index = CorpusGraphIndex()
    prober = ResearchProber(index)

    q = ResearchQuestion(
        question_id="RQ:T9:0003",
        thread_id="T9",
        originating_evidence="Radar claim",
        question_text="Did early radar manual predating formulation originate secret theory?",
        relation_under_test="PREDATE -> CLAIM",
        known_endpoints=["RadarLab"],
    )

    outcome = prober.probe(q)
    assert outcome.status == QuestionStatus.CONTRADICTED
    assert len(outcome.contradictions) >= 1


def test_research_shakedown_supervisor_lifecycle() -> None:
    with TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        coord = ResearchFrontierCoordinator()

        supervisor = ResearchShakedownSupervisor(
            coordinator=coord,
            duration_seconds=2,
            epoch_duration_seconds=1,
            pace_seconds=0.01,
            output_dir=out_path,
        )

        receipt = supervisor.run_campaign()
        assert receipt["verdict"] == "PASS"
        assert receipt["epochs_completed"] >= 1
        assert receipt["total_probes"] >= 1

        # Verify artifacts were written to disk
        live_file = out_path / "research_shakedown_live.json"
        assert live_file.exists()
        live_data = json.loads(live_file.read_text(encoding="utf-8"))
        assert live_data["status"] == "COMPLETED"

        receipt_file = out_path / "final" / "research_shakedown_receipt.json"
        assert receipt_file.exists()

        checkpoints = list((out_path / "checkpoints").glob("epoch_*.json"))
        assert len(checkpoints) >= 1


def test_research_prober_bcig_xgraph_resolution() -> None:
    index = CorpusGraphIndex()
    prober = ResearchProber(index)
    coord = ResearchFrontierCoordinator()

    bcig_qs = [
        q for q in coord.ledger.questions.values()
        if "BCIG_XGRAPH" in q.question_id
    ]
    assert len(bcig_qs) == 4, f"Expected 4 BCIG_XGRAPH questions, found {len(bcig_qs)}"

    for q in bcig_qs:
        outcome = prober.probe(q)
        assert outcome.status == QuestionStatus.RESOLVED, f"Question {q.question_id} did not resolve: {outcome.status}"
        assert outcome.resolved_endpoint is not None
        assert outcome.resolution_summary is not None
        assert len(outcome.corroborating_sources) >= 3
        assert len(outcome.new_relations_found) >= 1

        # Strict check: all corroborating sources must exist in the canonical index!
        for src_id in outcome.corroborating_sources:
            assert src_id in index.node_by_id, f"Corroborating source {src_id} not in corpus graph index!"
