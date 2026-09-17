"""Unit, Falsification, and Anti-Circularity Tests for Wave F2 & F2.1 EO/GEO Commutation Audit."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from mapeogeo.dual_view.eo_engine import EOEngine
from mapeogeo.dual_view.evaluator import DualViewEvaluator
from mapeogeo.dual_view.geo_engine import GEOEngine
from mapeogeo.dual_view.models import (
    CommutationVerdict,
    EORealization,
    EquivalenceContract,
    GEORealization,
)
from scripts.wave_f2_commutation_campaign import (
    analyze_codomain_distinctness,
    run_commutation_campaign,
    run_cross_pair_discrimination_matrix,
    run_mutant_killing_suite,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "formal" / "wave_f2_commutation_manifest.json"
EVIDENCE_PATH = ROOT / "evidence" / "v0_21_wave_f2_commutation_results.json"
REPORT_PATH = ROOT / "docs" / "V0_21_WAVE_F2_COMMUTATION_REPORT.md"
OPEN_LOGIC_PATH = ROOT / "formal" / "open_logic_manifest_v0_21.json"
OPEN_SET_PATH = ROOT / "formal" / "open_set_theory_manifest_v0_21.json"
LEVIN_PATH = ROOT / "formal" / "levin_discrete_manifest_v0_21.json"


def test_wave_f2_manifest_integrity():
    assert MANIFEST_PATH.is_file(), f"Missing manifest at {MANIFEST_PATH}"
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "0.21"
    assert manifest["stage"] == "v0.21_wave_f2"
    assert manifest["total_canonical_concepts"] == 32
    assert len(manifest["target_concepts"]) == 32

    valid_contracts = {e.value for e in EquivalenceContract}
    valid_verdicts = {e.value for e in CommutationVerdict}

    for item in manifest["target_concepts"]:
        assert item["contract"] in valid_contracts
        assert item["expected_verdict"] in valid_verdicts
        assert item["canonical_id"].startswith("canonical:")
        assert "aligned_source_node_ids" in item
        assert "aligned_statement_sha256s" in item
        assert len(item["aligned_source_node_ids"]) > 0
        assert len(item["aligned_statement_sha256s"]) > 0


def test_all_32_canonical_concepts_generate_eo_and_geo():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for item in manifest["target_concepts"]:
        cid = item["canonical_id"]
        eo = EOEngine.generate(cid)
        geo = GEOEngine.generate(cid)

        assert isinstance(eo, EORealization)
        assert isinstance(geo, GEORealization)
        assert len(eo.compute_hash()) == 64
        assert len(geo.compute_hash()) == 64
        assert eo.canonical_id == cid
        assert geo.canonical_id == cid


def test_commutation_campaign_execution_and_verdicts():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    results = run_commutation_campaign(manifest)

    assert results["total_canonical_concepts_audited"] == 32
    assert results["scientific_status"] == "EVIDENCE_PARTIAL"
    assert "27 of 32 concepts commute" in results["exact_claim_boundary"]
    assert results["verdict_breakdown"][CommutationVerdict.IMPLEMENTATION_ERROR.value] == 0
    assert results["verdict_breakdown"][CommutationVerdict.NONCOMMUTATIVE_UNDER_CONTRACT.value] == 0
    assert results["verdict_breakdown"][CommutationVerdict.VERIFIED_BOUNDED_CONTRACT_COMMUTATION.value] == 27
    assert results["verdict_breakdown"][CommutationVerdict.OUTSIDE_CURRENT_EXECUTABLE_SCOPE.value] == 4
    assert results["verdict_breakdown"][CommutationVerdict.PARTIAL_ONE_SIDED_REALIZATION.value] == 1
    assert results["commutation_rate"] == 0.8438

    # Verify per-concept expected verdicts match exactly
    for record in results["commutation_records"]:
        matching_manifest = next(c for c in manifest["target_concepts"] if c["canonical_id"] == record["canonical_id"])
        assert record["verdict"] == matching_manifest["expected_verdict"]
        assert len(record["bound_source_hashes"]) == len(matching_manifest["aligned_statement_sha256s"])


def test_full_32x32_cross_pair_discrimination_matrix():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    matrix_results = run_cross_pair_discrimination_matrix(manifest["target_concepts"])

    assert matrix_results["total_matrix_pairs"] == 1024
    assert matrix_results["diagonal_pairs"] == 32
    assert matrix_results["off_diagonal_pairs"] == 992
    assert matrix_results["off_diagonal_rejections"] == 992
    assert matrix_results["off_diagonal_false_positives"] == 0
    assert matrix_results["off_diagonal_rejection_rate"] == 1.0


def test_multi_class_mutant_killing_suite():
    mutant_results = run_mutant_killing_suite()

    assert mutant_results["total_mutants_tested"] == 6
    assert mutant_results["mutants_killed"] == 6
    assert mutant_results["mutant_kill_rate"] == 1.0

    classes = {m["mutation_class"] for m in mutant_results["mutant_audit_records"]}
    assert len(classes) == 6
    for m in mutant_results["mutant_audit_records"]:
        assert m["mutant_rejected"] is True
        assert m["verdict"] == CommutationVerdict.NONCOMMUTATIVE_UNDER_CONTRACT.value


def test_source_hash_and_dependency_bindings():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    # Collect all declaration hashes from source manifests
    source_decls: dict[str, str] = {}
    for p in [OPEN_LOGIC_PATH, OPEN_SET_PATH, LEVIN_PATH]:
        data = json.loads(p.read_text(encoding="utf-8"))
        for d in data.get("declarations", []):
            source_decls[d["node_id"]] = d["statement_sha256"]

    for item in manifest["target_concepts"]:
        for sid, sha in zip(item["aligned_source_node_ids"], item["aligned_statement_sha256s"]):
            assert sid in source_decls, f"Source node {sid} not found in source manifests"
            assert source_decls[sid] == sha, f"Hash mismatch for {sid}: expected {source_decls[sid]}, got {sha}"
            assert len(sha) == 64


def test_semantic_codomain_non_degeneracy():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    results = run_commutation_campaign(manifest)
    codomain_res = results["codomain_distinctness"]

    assert codomain_res["commutative_concepts_evaluated"] == 27
    assert codomain_res["unique_eo_semantic_digests"] == 27
    assert codomain_res["unique_geo_semantic_digests"] == 27
    assert codomain_res["is_semantically_injective"] is True
    assert codomain_res["zero_cross_concept_semantic_collisions"] is True


def test_commutation_evidence_and_report_files_exist_and_consistent():
    assert EVIDENCE_PATH.is_file(), f"Missing evidence at {EVIDENCE_PATH}"
    assert REPORT_PATH.is_file(), f"Missing report at {REPORT_PATH}"

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert evidence["stage"] == "v0.21_wave_f2"
    assert evidence["scientific_status"] == "EVIDENCE_PARTIAL"
    assert "27 / 32" in report
    assert "VERIFIED_BOUNDED_CONTRACT_COMMUTATION" in report
    assert "Anti-Circularity and Discrimination Matrix" in report
    assert len(evidence["evidence_sha256"]) == 64
