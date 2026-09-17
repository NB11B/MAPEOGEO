"""Unit, Discrimination, Mutation, and Relationship Verification Tests for Wave F3 Abstract Algebra & Number Theory Campaign."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from mapeogeo.algebra.evaluator import AlgebraDualViewEvaluator
from mapeogeo.algebra.groups import GroupTheoryEOEngine, GroupTheoryGEOEngine
from mapeogeo.algebra.models import (
    AlgebraContract,
    AlgebraEORealization,
    AlgebraGEORealization,
    AlgebraVerdict,
    CrossPairAuditResult,
    FalsificationMutantRecord,
    RelationshipEdgeRecord,
    RelationType,
    WaveF3AuditRecord,
)
from mapeogeo.algebra.number_theory import NumberTheoryEOEngine, NumberTheoryGEOEngine
from mapeogeo.algebra.relations import AlgebraRelationshipAuditor
from mapeogeo.algebra.rings_fields import RingFieldTheoryEOEngine, RingFieldTheoryGEOEngine
from scripts.wave_f3_campaign import (
    analyze_codomain_distinctness,
    run_cross_pair_discrimination_matrix,
    run_diagonal_audit,
    run_falsification_suite,
    run_relationship_audit,
    run_wave_f3_campaign,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST_PATH = ROOT / "formal" / "wave_f3_source_manifest.json"
CONTRACT_MANIFEST_PATH = ROOT / "formal" / "wave_f3_contract_manifest.json"
RELATION_MANIFEST_PATH = ROOT / "formal" / "wave_f3_relation_manifest.json"
FALSIFICATION_MANIFEST_PATH = ROOT / "formal" / "wave_f3_falsification_manifest.json"
EVIDENCE_PATH = ROOT / "evidence" / "v0_21_wave_f3_results.json"
REPORT_PATH = ROOT / "docs" / "V0_21_WAVE_F3_REPORT.md"


def test_wave_f3_manifest_integrity():
    # 1. Source Manifest
    assert SOURCE_MANIFEST_PATH.is_file(), f"Missing source manifest at {SOURCE_MANIFEST_PATH}"
    src_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert src_manifest["schema_version"] == "0.21"
    assert src_manifest["stage"] == "v0.21_wave_f3"
    assert len(src_manifest["corpora"]) == 2
    assert len(src_manifest["declarations"]) == 34
    for decl in src_manifest["declarations"]:
        assert len(decl["statement_sha256"]) == 64
        assert len(decl["node_id"]) > 0
        assert len(decl["raw_statement"]) > 0
        assert decl["corpus"] in ["JUDSON_ABSTRACT_ALGEBRA", "STEIN_NUMBER_THEORY"]

    # 2. Contract Manifest
    assert CONTRACT_MANIFEST_PATH.is_file(), f"Missing contract manifest at {CONTRACT_MANIFEST_PATH}"
    contract_manifest = json.loads(CONTRACT_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert contract_manifest["schema_version"] == "0.21"
    assert contract_manifest["stage"] == "v0.21_wave_f3"
    assert len(contract_manifest["target_concepts"]) == 32

    valid_contracts = {e.value for e in AlgebraContract}
    valid_verdicts = {e.value for e in AlgebraVerdict}
    valid_families = {"NUMBER_THEORY", "GROUPS", "RINGS_FIELDS"}

    for item in contract_manifest["target_concepts"]:
        assert item["contract"] in valid_contracts
        assert item["expected_verdict"] in valid_verdicts
        assert item["family"] in valid_families
        assert item["canonical_id"].startswith("canonical:")
        assert len(item["aligned_source_node_ids"]) > 0

    # 3. Relation Manifest
    assert RELATION_MANIFEST_PATH.is_file(), f"Missing relation manifest at {RELATION_MANIFEST_PATH}"
    rel_manifest = json.loads(RELATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert rel_manifest["schema_version"] == "0.21"
    assert rel_manifest["stage"] == "v0.21_wave_f3"
    assert rel_manifest["total_typed_relations"] == 14
    assert len(rel_manifest["relations"]) == 14

    valid_rel_types = {e.value for e in RelationType}
    for edge in rel_manifest["relations"]:
        assert edge["relation_type"] in valid_rel_types
        assert edge["source_canonical_id"].startswith("canonical:")
        assert edge["target_canonical_id"].startswith("canonical:")

    # 4. Falsification Manifest
    assert FALSIFICATION_MANIFEST_PATH.is_file(), f"Missing falsification manifest at {FALSIFICATION_MANIFEST_PATH}"
    fals_manifest = json.loads(FALSIFICATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert fals_manifest["schema_version"] == "0.21"
    assert fals_manifest["stage"] == "v0.21_wave_f3"
    assert fals_manifest["total_registered_mutants"] == 12
    assert len(fals_manifest["mutants"]) == 12
    for mut in fals_manifest["mutants"]:
        assert mut["expected_verdict"] == "NONCOMMUTATIVE_UNDER_CONTRACT"
        assert len(mut["mutant_id"]) > 0


def test_all_32_canonical_concepts_generate_eo_and_geo():
    contract_manifest = json.loads(CONTRACT_MANIFEST_PATH.read_text(encoding="utf-8"))
    for item in contract_manifest["target_concepts"]:
        cid = item["canonical_id"]
        family = item["family"]

        if family == "NUMBER_THEORY":
            eo = NumberTheoryEOEngine.generate(cid)
            geo = NumberTheoryGEOEngine.generate(cid)
        elif family == "GROUPS":
            eo = GroupTheoryEOEngine.generate(cid)
            geo = GroupTheoryGEOEngine.generate(cid)
        elif family == "RINGS_FIELDS":
            eo = RingFieldTheoryEOEngine.generate(cid)
            geo = RingFieldTheoryGEOEngine.generate(cid)
        else:
            pytest.fail(f"Unknown family: {family}")

        assert isinstance(eo, AlgebraEORealization)
        assert isinstance(geo, AlgebraGEORealization)
        assert len(eo.compute_hash()) == 64
        assert len(geo.compute_hash()) == 64
        assert eo.canonical_id == cid
        assert geo.canonical_id == cid


def test_wave_f3_campaign_execution_and_verdicts():
    results = run_wave_f3_campaign()

    assert results["total_canonical_concepts_audited"] == 32
    assert results["scientific_status"] == "EVIDENCE_PARTIAL"
    assert "32 of 32 abstract algebra and number theory concepts commute" in results["exact_claim_boundary"]
    assert "14 of 14 typed mathematical relationship edges commute" in results["exact_claim_boundary"]
    assert results["verdict_breakdown"][AlgebraVerdict.IMPLEMENTATION_ERROR.value] == 0
    assert results["verdict_breakdown"][AlgebraVerdict.NONCOMMUTATIVE_UNDER_CONTRACT.value] == 0
    assert results["verdict_breakdown"][AlgebraVerdict.VERIFIED_BOUNDED_CONTRACT_COMMUTATION.value] == 32
    assert results["commutation_rate_pct"] == "100.00%"

    # Family breakdown
    fam = results["family_breakdown"]
    assert fam["NUMBER_THEORY"]["total"] == 8
    assert fam["NUMBER_THEORY"]["verified_commutation"] == 8
    assert fam["GROUPS"]["total"] == 12
    assert fam["GROUPS"]["verified_commutation"] == 12
    assert fam["RINGS_FIELDS"]["total"] == 12
    assert fam["RINGS_FIELDS"]["verified_commutation"] == 12


def test_redacted_content_only_commutation():
    contract_manifest = json.loads(CONTRACT_MANIFEST_PATH.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))

    diag_records, _, _ = run_diagonal_audit(contract_manifest["target_concepts"], source_manifest)

    # Test individual pair redaction directly across all 32 concepts
    assert len(diag_records) == 32
    for rec in diag_records:
        contract = rec.contract
        eo = AlgebraDualViewEvaluator.generate_eo(rec.canonical_id)
        geo = AlgebraDualViewEvaluator.generate_geo(rec.canonical_id)
        res = AlgebraDualViewEvaluator.evaluate_redacted(eo, geo, contract)
        assert res.verdict == AlgebraVerdict.VERIFIED_BOUNDED_CONTRACT_COMMUTATION
        assert res.redacted_commutation_passed is True
        assert rec.redacted_commutation_passed is True


def test_all_14_typed_mathematical_relationships_verified():
    relation_manifest = json.loads(RELATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    relation_records, type_counts = run_relationship_audit(relation_manifest)

    assert len(relation_records) == 14
    assert sum(1 for r in relation_records if r.commutation_verified) == 14

    assert type_counts["CONSTRUCTION"] == 4
    assert type_counts["IMPLICATION"] == 2
    assert type_counts["SPECIALIZATION"] == 1
    assert type_counts["ISOMORPHISM"] == 3
    assert type_counts["PARTITION"] == 1
    assert type_counts["DECOMPOSITION"] == 1
    assert type_counts["QUOTIENT"] == 2

    for edge_res in relation_records:
        assert edge_res.commutation_verified is True
        assert len(edge_res.relationship_witness) > 0


def test_full_32x32_cross_pair_discrimination_matrix():
    contract_manifest = json.loads(CONTRACT_MANIFEST_PATH.read_text(encoding="utf-8"))
    matrix_results = run_cross_pair_discrimination_matrix(contract_manifest["target_concepts"])

    assert matrix_results["total_matrix_pairs"] == 1024
    assert matrix_results["diagonal_pairs"] == 32
    assert matrix_results["off_diagonal_pairs"] == 992
    assert matrix_results["off_diagonal_rejections"] == 992
    assert matrix_results["off_diagonal_false_positives"] == 0
    assert matrix_results["off_diagonal_rejection_rate_pct"] == "100.00%"


def test_multi_class_mutant_killing_suite():
    fals_manifest = json.loads(FALSIFICATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    mutant_results = run_falsification_suite(fals_manifest)

    assert mutant_results["total_mutants_tested"] == 12
    assert mutant_results["mutants_killed"] == 12
    assert mutant_results["mutant_kill_rate_pct"] == "100.00%"

    for m in mutant_results["mutant_records"]:
        assert m["mutant_killed"] is True
        assert m["verdict"] == AlgebraVerdict.NONCOMMUTATIVE_UNDER_CONTRACT.value


def test_source_hash_and_dependency_bindings():
    src_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    contract_manifest = json.loads(CONTRACT_MANIFEST_PATH.read_text(encoding="utf-8"))

    source_decls = {d["node_id"]: d["statement_sha256"] for d in src_manifest["declarations"]}

    for item in contract_manifest["target_concepts"]:
        for sid in item["aligned_source_node_ids"]:
            assert sid in source_decls, f"Source node {sid} not found in source manifest"
            sha = source_decls[sid]
            assert len(sha) == 64


def test_semantic_codomain_non_degeneracy():
    results = run_wave_f3_campaign()
    codomain_res = results["codomain_distinctness"]

    assert codomain_res["commutative_concepts_evaluated"] == 32
    assert codomain_res["unique_eo_semantic_digests"] == 32
    assert codomain_res["unique_geo_semantic_digests"] == 32
    assert codomain_res["is_semantically_injective"] is True
    assert codomain_res["zero_cross_concept_semantic_collisions"] is True
    assert codomain_res["codomain_entropy_bits"] == 5.0


def test_wave_f3_evidence_and_report_files_exist_and_consistent():
    assert EVIDENCE_PATH.is_file(), f"Missing evidence at {EVIDENCE_PATH}"
    assert REPORT_PATH.is_file(), f"Missing report at {REPORT_PATH}"

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert evidence["stage"] == "v0.21_wave_f3"
    assert evidence["scientific_status"] == "EVIDENCE_PARTIAL"
    assert evidence["total_canonical_concepts_audited"] == 32
    assert evidence["total_typed_relationships_audited"] == 14
    assert len(evidence["evidence_sha256"]) == 64
    assert "32 / 32" in report
    assert "14 / 14" in report
    assert "VERIFIED_BOUNDED_CONTRACT_COMMUTATION" in report
    assert "Cross-Pair Discrimination" in report


def test_engine_ast_and_import_decoupling():
    """Verify that EO and GEO realization engines do not import or reference each other."""
    import ast

    algebra_dir = ROOT / "mapeogeo" / "algebra"

    for py_file in [algebra_dir / "number_theory.py", algebra_dir / "groups.py", algebra_dir / "rings_fields.py"]:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

        # Find EO and GEO classes
        eo_class = next((c for name, c in classes.items() if "EOEngine" in name), None)
        geo_class = next((c for name, c in classes.items() if "GEOEngine" in name), None)

        assert eo_class is not None, f"Missing EOEngine in {py_file.name}"
        assert geo_class is not None, f"Missing GEOEngine in {py_file.name}"

        # Check AST nodes inside EOEngine for GEO references
        eo_code = ast.unparse(eo_class)
        assert geo_class.name not in eo_code, f"{eo_class.name} contains reference to {geo_class.name}"

        # Check AST nodes inside GEOEngine for EO references
        geo_code = ast.unparse(geo_class)
        assert eo_class.name not in geo_code, f"{geo_class.name} contains reference to {eo_class.name}"


def test_fixture_diversity_guarantees():
    """Verify explicit non-trivial algebraic and geometric fixture diversity across all families."""
    # 1. Groups: cyclic (Z6), Klein-4 (V4), non-abelian S3, S4, A4, D4
    v4 = GroupTheoryEOEngine.generate("canonical:groups:group_axioms")
    assert v4.algebraic_payload["is_abelian"] is True
    assert v4.algebraic_payload["exponent"] == 2
    assert v4.algebraic_payload["order"] == 4

    s3_sub = GroupTheoryEOEngine.generate("canonical:groups:subgroups")
    assert s3_sub.algebraic_payload["group_order"] == 6
    assert s3_sub.algebraic_payload["subgroups_count"] == 6

    s4_a4 = GroupTheoryEOEngine.generate("canonical:groups:symmetric_and_alternating_groups")
    assert s4_a4.algebraic_payload["symmetric_order"] == 24
    assert s4_a4.algebraic_payload["alternating_order"] == 12

    d4 = GroupTheoryEOEngine.generate("canonical:groups:group_actions_and_orbit_stabilizer")
    assert d4.algebraic_payload["group_order"] == 8

    # 2. Rings: Z4 (nilpotents), Z6 (zero-divisors), F5 (prime field)
    z4 = RingFieldTheoryEOEngine.generate("canonical:rings_fields:ring_axioms")
    assert z4.algebraic_payload["characteristic"] == 4

    z6 = RingFieldTheoryEOEngine.generate("canonical:rings_fields:units_and_zero_divisors")
    assert z6.algebraic_payload["units"] == [1, 5]
    assert z6.algebraic_payload["zero_divisors"] == [2, 3, 4]

    f5 = RingFieldTheoryEOEngine.generate("canonical:rings_fields:integral_domains")
    assert f5.algebraic_payload["zero_divisors_count"] == 0
    assert f5.algebraic_payload["is_domain"] is True

    # 3. Field extensions: irreducible x^2+1 over F3 yielding GF(9)
    gf9 = RingFieldTheoryEOEngine.generate("canonical:rings_fields:irreducibility_and_quotients")
    assert gf9.algebraic_payload["is_irreducible"] is True
    assert gf9.algebraic_payload["quotient_order"] == 9
    assert gf9.algebraic_payload["quotient_is_field"] is True

