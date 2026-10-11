from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sovctx.node.benchmarks import (
    BENCHMARK_CORPUS,
    evaluate_citation_benchmark,
    evaluate_entity_benchmark,
)
from sovctx.node.config import load_config
from sovctx.node.drift_monitor import DriftMonitor, EpistemicInstabilityPause
from sovctx.node.expansion import ExpansionCoordinator
from sovctx.node.provenance import AcquisitionCausalityRecord, ProvenanceTracker
from sovctx.node.research_school import ResearchSchoolDetector
from sovctx.node.source_family import (
    FAMILY_RELATIONSHIPS,
    SourceFamilyClassifier,
    WorkFamilyCluster,
)
from sovctx.node.work_db import WorkDatabase
from sovctx.tools.qualify_n4 import run_n4_qualification


def test_provenance_tracker_causality() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "prov_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        tracker = ProvenanceTracker(db)

        # Seed source (Gen 0)
        tracker.record_causality(
            AcquisitionCausalityRecord(
                source_id="SOVSRC:seed1",
                generation=0,
                nomination_id=None,
                frontier_id=None,
                origin_source_id=None,
                origin_passage_id=None,
                frontier_type=None,
                reason="Seed document",
                resolution_state="SEED_GROUNDED",
                parent_path=["SOVSRC:seed1"],
            )
        )

        # Child source (Gen 1)
        tracker.record_causality(
            AcquisitionCausalityRecord(
                source_id="SOVSRC:child1",
                generation=1,
                nomination_id="NOM:123",
                frontier_id="FRONTIER:456",
                origin_source_id="SOVSRC:seed1",
                origin_passage_id="PASSAGE:789",
                frontier_type="CITATION",
                reason="Cited in seed1",
                resolution_state="EXACT_MATCH",
                parent_path=["SOVSRC:seed1", "SOVSRC:child1"],
            )
        )

        audit = tracker.audit_causality(["SOVSRC:seed1", "SOVSRC:child1"])
        assert audit["is_valid"] is True
        assert audit["orphaned_count"] == 0
        assert audit["valid_chains_count"] == 2

        # Check export
        out_jsonl = Path(td) / "provenance.jsonl"
        tracker.export_provenance_paths(out_jsonl)
        assert out_jsonl.exists()
        lines = out_jsonl.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2


def test_source_family_classification() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "fam_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        classifier = SourceFamilyClassifier(db)

        # Identical hash
        s1 = {"id": "S1", "sha256": "abc123", "title": "Оптимальные процессы", "authors": ["Понтрягин Л.С."], "year": 1961, "language": "ru"}
        s2 = {"id": "S2", "sha256": "abc123", "title": "Оптимальные процессы", "authors": ["Понтрягин Л.С."], "year": 1961, "language": "ru"}
        rel1 = classifier.classify_pair(s1, s2)
        assert rel1.relationship == "IDENTICAL_BLOB"

        # Same work, different edition
        s3 = {"id": "S3", "sha256": "def456", "title": "Оптимальные процессы", "authors": ["Понтрягин Л.С."], "year": 1969, "language": "ru"}
        rel2 = classifier.classify_pair(s1, s3)
        assert rel2.relationship == "SAME_WORK"

        # Translation
        s4 = {"id": "S4", "sha256": "ghi789", "title": "The Mathematical Theory of Optimal Processes", "authors": ["Pontryagin L.S."], "year": 1962, "language": "en"}
        rel3 = classifier.classify_pair(s1, s4)
        assert rel3.relationship == "TRANSLATION_OF"

        # Clustering
        sources = [s1, s2, s3, s4]
        clusters = classifier.cluster_sources(sources)
        assert len(clusters) >= 1


def test_drift_monitor_and_epistemic_pause() -> None:
    monitor = DriftMonitor()

    # Normal generation
    m1 = monitor.evaluate_generation(
        generation=1,
        total_nominations=20,
        duplicate_nominations=1,
        total_frontier_items=40,
        unresolved_frontier_items=2,
        terminology_nominations=10,
        generic_rejected_terms=0,
        canonical_promotions_attempted=0,
        orphaned_sources_detected=0,
    )
    assert len(m1.epistemic_violations) == 0

    # Invariant breach: attempt canonical promotion must raise EpistemicInstabilityPause
    with pytest.raises(EpistemicInstabilityPause) as exc_info:
        monitor.evaluate_generation(
            generation=2,
            total_nominations=30,
            duplicate_nominations=2,
            total_frontier_items=50,
            unresolved_frontier_items=3,
            terminology_nominations=15,
            generic_rejected_terms=0,
            canonical_promotions_attempted=1,  # VIOLATION
            orphaned_sources_detected=0,
        )
    assert "EPISTEMIC_PAUSE" in str(exc_info.value)


def test_benchmarks_quality() -> None:
    # 10 benchmark documents
    assert len(BENCHMARK_CORPUS) == 10

    # Citation benchmark
    cb = evaluate_citation_benchmark()
    assert cb["citation_precision"] >= 0.95
    assert cb["citation_recall"] >= 0.80
    assert cb["total_ground_truth_citations"] > 30

    # Entity benchmark
    eb = evaluate_entity_benchmark()
    assert eb["entity_routing_precision"] >= 0.95
    assert eb["entity_recall"] >= 0.80
    assert eb["total_ground_truth_entities"] > 60


def test_research_school_detector() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "school_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        detector = ResearchSchoolDetector(db)

        # Mock sources containing Steklov and Gorky school key figures
        sources = [
            {"id": "S1", "authors": ["Понтрягин Л.С.", "Болтянский В.Г."], "title": "Принцип максимума", "generation": 1},
            {"id": "S2", "authors": ["Гамкрелидзе Р.В.", "Мищенко Е.Ф."], "title": "Дифференциальные игры", "generation": 2},
            {"id": "S3", "authors": ["Андронов А.А.", "Понтрягин Л.С."], "title": "Грубые системы", "generation": 0},
            {"id": "S4", "authors": ["Марков А.А."], "title": "Цепи Маркова", "generation": 1},
            {"id": "S5", "authors": ["Тихонов А.Н."], "title": "Регуляризация", "generation": 1},
        ]

        candidates = detector.detect_candidates(sources)
        assert len(candidates) >= 2
        for c in candidates:
            assert c.id.startswith("SOVSCH:")  # Candidate prefix
            assert len(c.supporting_sources) >= 1
            assert len(c.subgraph["edges"]) >= 1


def test_expansion_coordinator_bounded_execution() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "coord_test.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        coord = ExpansionCoordinator(config=config, db=db)
        res = coord.run_expansion()

        assert len(res["generations"]) == 4  # Gen 0, 1, 2, 3
        # Check ceilings
        assert res["generations"][0]["sources_admitted"] <= 5
        assert res["generations"][1]["sources_admitted"] <= 20
        assert res["generations"][2]["sources_admitted"] <= 40
        assert res["generations"][3]["sources_admitted"] <= 80

        # Export dossier
        out_dir = Path(td) / "evidence"
        exported = coord.export_dossier(res, out_dir)

        expected_keys = [
            "generation_0",
            "generation_1",
            "generation_2",
            "generation_3",
            "provenance_paths",
            "frontier_health",
            "duplicate_families",
            "unresolved_register",
            "receipt",
            "report",
        ]
        for ek in expected_keys:
            assert ek in exported
            assert exported[ek].exists()


def test_full_n4_qualification_harness() -> None:
    res = run_n4_qualification()
    assert res["verdict"] == "PASS"
    t = res["thresholds"]
    for k, v in t.items():
        assert v is True, f"Threshold failed: {k}"
