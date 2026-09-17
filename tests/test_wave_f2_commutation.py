"""Unit and Falsification Tests for Wave F2 EO/GEO Commutation Audit."""

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
from scripts.wave_f2_commutation_campaign import run_commutation_campaign

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "formal" / "wave_f2_commutation_manifest.json"
EVIDENCE_PATH = ROOT / "evidence" / "v0_21_wave_f2_commutation_results.json"
REPORT_PATH = ROOT / "docs" / "V0_21_WAVE_F2_COMMUTATION_REPORT.md"


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
    assert results["verdict_breakdown"][CommutationVerdict.IMPLEMENTATION_ERROR.value] == 0
    assert results["verdict_breakdown"][CommutationVerdict.REJECTED.value] == 0
    assert results["verdict_breakdown"][CommutationVerdict.VERIFIED_COMMUTATIVE.value] == 27
    assert results["verdict_breakdown"][CommutationVerdict.UNSUPPORTED.value] == 4
    assert results["verdict_breakdown"][CommutationVerdict.WOUNDED.value] == 1
    assert results["commutation_rate"] == 0.8438

    # Verify per-concept expected verdicts match exactly
    for record in results["commutation_records"]:
        matching_manifest = next(c for c in manifest["target_concepts"] if c["canonical_id"] == record["canonical_id"])
        assert record["verdict"] == matching_manifest["expected_verdict"]


def test_commutation_falsification_on_mutated_eo_payload():
    cid = "canonical:logic:propositional_syntax_and_semantics"
    eo_nominal = EOEngine.generate(cid)
    geo_nominal = GEOEngine.generate(cid)

    # Mutate truth table vector in EO payload
    mutated_payload = dict(eo_nominal.algebraic_payload)
    mutated_payload["truth_table_vector"] = [1, 0, 1, 1]  # broke tautology
    eo_mutated = EORealization(
        canonical_id=cid,
        representation_type=eo_nominal.representation_type,
        algebraic_payload=mutated_payload,
        structural_signature="EO:MUTATED",
    )

    record = DualViewEvaluator.audit_commutation(
        name="Mutated Propositional",
        domain="Logic & Proof Theory",
        eo=eo_mutated,
        geo=geo_nominal,
        contract=EquivalenceContract.EXACT_MATCH,
    )

    assert record.verdict == CommutationVerdict.REJECTED
    assert record.delta_metric > 0.0
    assert "truth_vector" in record.witness["discrepancies"]


def test_commutation_falsification_on_mutated_geo_payload():
    cid = "canonical:discrete:planarity_and_eulers_formula"
    eo_nominal = EOEngine.generate(cid)
    geo_nominal = GEOEngine.generate(cid)

    # Mutate faces count in GEO payload
    mutated_payload = dict(geo_nominal.geometric_payload)
    mutated_payload["faces_F"] = 99  # breaks Euler formula V - E + F = 2
    geo_mutated = GEORealization(
        canonical_id=cid,
        representation_type=geo_nominal.representation_type,
        geometric_payload=mutated_payload,
        structural_signature="GEO:MUTATED",
    )

    record = DualViewEvaluator.audit_commutation(
        name="Mutated Planar Graph",
        domain="Discrete Mathematics & Combinatorics",
        eo=eo_nominal,
        geo=geo_mutated,
        contract=EquivalenceContract.HOMOLOGY_EQUIVALENCE,
    )

    assert record.verdict == CommutationVerdict.REJECTED
    assert record.delta_metric > 0.0
    assert "faces_count" in record.witness["discrepancies"]


def test_commutation_evidence_and_report_files_exist_and_consistent():
    assert EVIDENCE_PATH.is_file(), f"Missing evidence at {EVIDENCE_PATH}"
    assert REPORT_PATH.is_file(), f"Missing report at {REPORT_PATH}"

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert evidence["stage"] == "v0.21_wave_f2"
    assert "27 / 32" in report
    assert "VERIFIED_COMMUTATIVE" in report
    assert len(evidence["evidence_sha256"]) == 64
