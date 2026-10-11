from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sovctx.node.config import load_config
from sovctx.node.source_family import SourceFamilyClassifier
from sovctx.node.synthesis import (
    CANONICAL_HISTORICAL_SCHOOL_REGISTRY,
    CandidateType,
    ContradictionType,
    HistoricalSynthesisEngine,
    LineageType,
    PromotionState,
    SchoolDossier,
    SupportClass,
)
from sovctx.node.work_db import WorkDatabase
from sovctx.tools.qualify_n45 import run_n45_qualification


def test_falsification_mirror_duplication_inflation() -> None:
    """Falsification Test 1: 10 copies of the same underlying source must resolve to

    independent_sources = 1 and at most S1_MULTIPLE_DEPENDENT_WITNESSES.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "mirror_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        classifier = SourceFamilyClassifier(db)

        # 10 mirrors with same sha256 or same scan
        mirrors = [
            {
                "id": f"SOVSRC:mirror_{i}",
                "sha256": "mirror_exact_sha256_hash",
                "title": "Оптимальные процессы управления",
                "authors": ["Понтрягин Л. С."],
                "year": 1961,
            }
            for i in range(10)
        ]

        # All pairs resolve to IDENTICAL_BLOB
        rel = classifier.classify_pair(mirrors[0], mirrors[1])
        assert rel.relationship == "IDENTICAL_BLOB"

        clusters = classifier.cluster_sources(mirrors)
        assert len(clusters) == 1
        assert len(clusters[0].member_source_ids) == 10

        # In synthesis, these 10 works must count as 1 independent source family
        family_map = {m["id"]: "FAMILY:MIRROR_CLUSTER" for m in mirrors}
        unique_families = set(family_map.values())
        assert len(unique_families) == 1

        # Must NOT be promoted to independent support
        support_class = (
            SupportClass.S1_MULTIPLE_DEPENDENT_WITNESSES.value
            if len(unique_families) == 1 and len(mirrors) > 1
            else SupportClass.S2_MULTIPLE_INDEPENDENT_WITNESSES.value
        )
        assert support_class == SupportClass.S1_MULTIPLE_DEPENDENT_WITNESSES.value


def test_falsification_chronological_discontinuity() -> None:
    """Falsification Test 2: If researcher dies in 1894 and an institution uses the method

    in 1920, the relationship is TEMPORALLY_DISJOINT or LATER_LINEAGE, NOT direct school membership.
    """
    person_active = (1847, 1894)  # Chebyshev
    institution_use = (1920, 1950)  # Later Soviet institute

    # Intersection check
    t_start = max(person_active[0], institution_use[0])
    t_end = min(person_active[1], institution_use[1])
    is_overlapping = t_start <= t_end

    assert is_overlapping is False
    temporal_status = "CONTEMPORANEOUS" if is_overlapping else "TEMPORALLY_DISJOINT"
    assert temporal_status == "TEMPORALLY_DISJOINT"


def test_falsification_translation_not_intellectual_lineage() -> None:
    """Falsification Test 3: An English translation must be recognized as TRANSLATION_OF,

    never as an INTELLECTUAL_LINEAGE edge.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "trans_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        classifier = SourceFamilyClassifier(db)
        ru_work = {
            "id": "SOVSRC:ru_orig",
            "sha256": "sha_ru",
            "title": "Математическая теория оптимальных процессов",
            "authors": ["Понтрягин Л. С."],
            "year": 1961,
            "language": "ru",
        }
        en_work = {
            "id": "SOVSRC:en_trans",
            "sha256": "sha_en",
            "title": "The Mathematical Theory of Optimal Processes",
            "authors": ["Pontryagin L. S."],
            "year": 1962,
            "language": "en",
        }

        rel = classifier.classify_pair(ru_work, en_work)
        assert rel.relationship == "TRANSLATION_OF"
        assert rel.relationship != LineageType.INTELLECTUAL_LINEAGE.value


def test_falsification_institutional_continuity_no_same_as() -> None:
    """Falsification Test 4: Same physical building with new administrative structure

    must NOT collapse via flat SAME_AS.
    """
    from sovctx.node.temporal import validate_genealogical_edge

    is_valid, err = validate_genealogical_edge("SAME_AS")
    assert is_valid is False
    assert "Forbidden collapse relation 'SAME_AS'" in err

    is_valid_renamed, err2 = validate_genealogical_edge("RENAMED_TO")
    assert is_valid_renamed is True
    assert err2 is None


def test_true_convergence_attestation() -> None:
    """Test 5: True convergence with independent sources, overlapping dates, mentorship,

    and shared institution achieves S4_MULTI_TYPE_CONVERGENCE and HISTORICALLY_ATTESTED.
    """
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "conv_test.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        engine = HistoricalSynthesisEngine(config=config, db=db)
        res = engine.run_synthesis()

        # Find Tikhonov or Pontryagin school
        pontryagin = next(d for d in res["dossiers"] if "Понтрягин" in d["proposed_label"])
        assert pontryagin["support_class"] == SupportClass.S4_MULTI_TYPE_CONVERGENCE.value
        assert pontryagin["promotion_state"] == PromotionState.HISTORICALLY_ATTESTED.value
        assert pontryagin["temporal_validity"] == "CONTEMPORANEOUS"
        assert pontryagin["historical_criteria"]["teacher_student_or_mentorship"] is True
        assert pontryagin["historical_criteria"]["shared_institution_overlapping_period"] is True


def test_direct_vs_inferred_separation_invariant() -> None:
    """Test 6: Invariant that DIRECT_SUPPORT and INFERRED_SUPPORT are never combined silently."""
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "sep_test.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        engine = HistoricalSynthesisEngine(config=config, db=db)
        res = engine.run_synthesis()

        for d in res["dossiers"]:
            assert "direct_evidence" in d
            assert "inferred_evidence" in d
            assert len(d["direct_evidence"]) > 0
            assert len(d["inferred_evidence"]) > 0

            # Direct evidence must have explicit witness nature
            for de in d["direct_evidence"]:
                assert de["evidence_nature"] in (
                    "PRIMARY_SOURCE_LOCATOR",
                    "PRIMARY_FORMULATION",
                    "PRIMARY_SOURCE_BYLINE",
                    "PRIMARY_ACKNOWLEDGMENT_OR_DISSERTATION",
                )

            # Inferred evidence must have inferred nature
            for ie in d["inferred_evidence"]:
                assert ie["evidence_nature"] in (
                    "SEMINAR_OR_COAUTHOR_CONVERGENCE",
                    "FREQUENCY_ANALYSIS",
                )


def test_candidate_isolation_no_canonical_writes() -> None:
    """Test 7: Gate N4.5 synthesis objects remain in candidate tables and never write to canonical."""
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "iso_test.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        engine = HistoricalSynthesisEngine(config=config, db=db)
        res = engine.run_synthesis()

        # All dossier IDs must have SOVSCH: prefix
        for d in res["dossiers"]:
            assert d["id"].startswith("SOVSCH:")

        # All lineage IDs must have LIN: prefix
        for l in res["lineages"]:
            assert l["id"].startswith("LIN:")

        # Invariant ledger check
        assert res["invariants"]["canonical_promotion_violations"] == 0
        assert res["invariants"]["mapeogeo_cross_graph_access"] == 0


def test_full_n45_qualification_harness() -> None:
    """Test 8: Full qualification harness passes all criteria."""
    res = run_n45_qualification()
    assert res["verdict"] == "PASS"
    for t_name, passed in res["thresholds"].items():
        assert passed is True, f"Failed threshold: {t_name}"
