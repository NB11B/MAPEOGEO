"""Test suite for Wave F4 Quantified Real Analysis and Proof-Bearing Dual Views."""

from __future__ import annotations

import ast
from fractions import Fraction
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
FORMAL_DIR = ROOT / "formal"
EVIDENCE_DIR = ROOT / "evidence"
DOCS_DIR = ROOT / "docs"

SOURCE_MANIFEST_PATH = FORMAL_DIR / "wave_f4_source_manifest.json"
QUANTIFIER_MANIFEST_PATH = FORMAL_DIR / "wave_f4_quantifier_manifest.json"
CLAIM_TIER_MANIFEST_PATH = FORMAL_DIR / "wave_f4_claim_tier_manifest.json"
RELATION_MANIFEST_PATH = FORMAL_DIR / "wave_f4_relation_manifest.json"
FALSIFICATION_MANIFEST_PATH = FORMAL_DIR / "wave_f4_falsification_manifest.json"
FORMAL_AUDIT_PATH = FORMAL_DIR / "wave_f4_formal_proof_audit.json"

EVIDENCE_PATH = EVIDENCE_DIR / "v0_21_wave_f4_results.json"
REPORT_PATH = DOCS_DIR / "V0_21_WAVE_F4_REPORT.md"

from mapeogeo.analysis.models import (
    AnalysisContract,
    AnalysisVerdict,
    EvidenceTier,
    QuantifierBlock,
    QuantifierSignature,
    QuantifierType,
)
from mapeogeo.analysis.exact_arithmetic import (
    ExactInterval,
    ExactRationalPolynomial,
    RationalMeshPartition,
)
from mapeogeo.analysis.quantifier_checker import QuantifierChecker
from mapeogeo.analysis.certificate_checker import CertificateChecker
from mapeogeo.analysis.eo_engine import RealAnalysisEOEngine
from mapeogeo.analysis.geo_engine import RealAnalysisGEOEngine
from mapeogeo.analysis.evaluator import RealAnalysisDualViewEvaluator
from mapeogeo.analysis.relations import RealAnalysisRelationshipChecker
from scripts.wave_f4_campaign import (
    run_falsification_suite,
    run_quantifier_and_diagonal_audit,
    run_wave_f4_campaign,
)


def test_wave_f4_manifest_integrity():
    """Verify all 5 sealed manifests exist, are valid JSON, and have expected counts."""
    for p in [
        SOURCE_MANIFEST_PATH,
        QUANTIFIER_MANIFEST_PATH,
        CLAIM_TIER_MANIFEST_PATH,
        RELATION_MANIFEST_PATH,
        FALSIFICATION_MANIFEST_PATH,
        FORMAL_AUDIT_PATH,
    ]:
        assert p.is_file(), f"Missing manifest or audit at {p}"

    src = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    quant = json.loads(QUANTIFIER_MANIFEST_PATH.read_text(encoding="utf-8"))
    tier = json.loads(CLAIM_TIER_MANIFEST_PATH.read_text(encoding="utf-8"))
    rel = json.loads(RELATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    fals = json.loads(FALSIFICATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    audit = json.loads(FORMAL_AUDIT_PATH.read_text(encoding="utf-8"))

    assert src["total_source_declarations"] == 32
    assert quant["total_quantifier_contracts"] == 32
    assert tier["total_canonical_concepts"] == 32
    assert rel["total_typed_relations"] == 20
    assert fals["total_registered_mutants"] == 20
    assert audit["total_formal_general_theorems"] == 14

    assert len(src["corpora"]) == 3
    corpus_ids = {c["corpus_id"] for c in src["corpora"]}
    assert "LEBL_BASIC_ANALYSIS_1" in corpus_ids
    assert "TRENCH_REAL_ANALYSIS" in corpus_ids
    assert "REASBOOK_LEAN_FORMALIZATION" in corpus_ids


def test_all_32_canonical_concepts_generate_eo_and_geo():
    """Verify all 32 concepts generate deterministic EO and GEO realizations."""
    tier_manifest = json.loads(CLAIM_TIER_MANIFEST_PATH.read_text(encoding="utf-8"))

    for item in tier_manifest["claims"]:
        cid = item["canonical_id"]
        eo = RealAnalysisDualViewEvaluator.generate_eo(cid)
        geo = RealAnalysisDualViewEvaluator.generate_geo(cid)

        assert eo.canonical_id == cid
        assert geo.canonical_id == cid
        assert len(eo.algebraic_payload) > 0
        assert len(geo.geometric_payload) > 0
        assert len(eo.compute_hash()) == 64
        assert len(geo.compute_hash()) == 64


def test_quantifier_signatures_and_dependency_checker():
    """Verify machine-checked quantifier dependency validation."""
    quant_manifest = json.loads(QUANTIFIER_MANIFEST_PATH.read_text(encoding="utf-8"))

    for q in quant_manifest["contracts"]:
        cid = q["canonical_id"]
        q_blocks = [
            QuantifierBlock(
                type=QuantifierType(b["type"]),
                var=b["var"],
                domain=b["domain"],
                depends_on=b.get("depends_on", []),
            )
            for b in q["ordered_quantifiers"]
        ]
        q_sig = QuantifierSignature(
            canonical_id=cid,
            blocks=q_blocks,
            hypotheses=q["hypotheses"],
            conclusion=q["conclusion"],
            permitted_dependencies=q["permitted_witness_dependencies"],
            forbidden_dependencies=q["forbidden_dependencies"],
        )
        valid, msg = QuantifierChecker.validate_dependency_graph(q_sig)
        assert valid is True, f"Quantifier graph validation failed for {cid}: {msg}"

    # Verify that forbidden variable leakage in uniform continuity is caught
    def bad_modulus(eps, x):
        return eps * x

    valid, msg = QuantifierChecker.check_witness_dependencies(
        bad_modulus, permitted_params=["eps"], forbidden_params=["x", "y"]
    )
    assert valid is False
    assert "forbidden variable" in msg


def test_exact_rational_arithmetic_and_float_rejection():
    """Verify exact interval and polynomial arithmetic with Fraction and strict float rejection."""
    # 1. Exact interval arithmetic
    iv1 = ExactInterval(Fraction(1, 3), Fraction(1, 2))
    iv2 = ExactInterval(Fraction(1, 4), Fraction(1, 2))
    iv_sum = iv1 + iv2
    assert iv_sum.a == Fraction(7, 12)
    assert iv_sum.b == Fraction(1, 1)

    # 2. Strict float rejection
    with pytest.raises(TypeError, match="Floating-point value"):
        ExactInterval(0.1, 0.5)

    with pytest.raises(TypeError, match="Floating-point value"):
        iv1.contains_point(0.4)

    # 3. Exact polynomial Taylor expansion
    poly = ExactRationalPolynomial([1, 2, 3])  # 1 + 2x + 3x^2
    t1 = poly.taylor_polynomial(1, 1)          # at x0=1: P(1)=6, P'(1)=8 -> 6 + 8(x-1) = -2 + 8x
    assert t1.eval(1) == 6
    assert t1.derivative().eval(1) == 8

    # 4. Rational partition
    part = RationalMeshPartition.uniform(0, 1, 10)
    assert part.mesh_width == Fraction(1, 10)
    gap = part.darboux_gap(poly)
    assert isinstance(gap, Fraction)
    assert gap > 0


def test_claim_tier_assignments_and_non_promotion():
    """Verify proper tier assignments and guard against improper promotion."""
    tier_manifest = json.loads(CLAIM_TIER_MANIFEST_PATH.read_text(encoding="utf-8"))

    tiers_count = tier_manifest["tier_breakdown"]
    assert tiers_count["FORMAL_GENERAL"] == 14
    assert tiers_count["CHECKED_SYMBOLIC_FAMILY"] == 10
    assert tiers_count["EXACT_BOUNDED_INSTANCE"] == 8
    assert tiers_count.get("NUMERICAL_PROBE_ONLY", 0) == 0

    # Verify improper promotion rejection
    cert_valid, tier, msg = CertificateChecker.verify_claim_tier(
        "canonical:diff_integration:pointwise_vs_uniform_convergence",
        EvidenceTier.FORMAL_GENERAL,
        {"sample_grid_points": 100},
    )
    assert cert_valid is False
    assert tier == EvidenceTier.OUTSIDE_CURRENT_SCOPE


def test_redacted_content_only_commutation():
    """Verify dual-view commutation across all 32 concepts without concept metadata."""
    tier_manifest = json.loads(CLAIM_TIER_MANIFEST_PATH.read_text(encoding="utf-8"))

    for item in tier_manifest["claims"]:
        cid = item["canonical_id"]
        eo = RealAnalysisDualViewEvaluator.generate_eo(cid)
        geo = RealAnalysisDualViewEvaluator.generate_geo(cid)
        res = RealAnalysisDualViewEvaluator.evaluate_redacted(
            eo, geo, AnalysisContract.QUANTIFIED_DUAL_VIEW_COMMUTATION
        )
        assert res.verdict == AnalysisVerdict.VERIFIED_QUANTIFIED_COMMUTATION
        assert res.redacted_commutation_passed is True
        assert res.delta_metric == 0.0


def test_all_20_typed_mathematical_relationships_verified():
    """Verify all 20 typed relationship edges produce checked witnesses."""
    relation_manifest = json.loads(RELATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    records, type_counts = RealAnalysisRelationshipChecker.evaluate_all_relationships(relation_manifest)

    assert len(records) == 20
    assert sum(1 for r in records if r.commutation_verified) == 20

    rel_ids = {r.relation_id for r in records}
    assert "REL:F4:10_LIPSCHITZ_TO_UNIFORM" in rel_ids
    assert "REL:F4:11_CONNECTED_TO_IVT" in rel_ids
    assert "REL:F4:13_EXTREME_AND_FERMAT_TO_ROLLE" in rel_ids
    assert "REL:F4:17_UNIFORM_CONT_TO_RIEMANN_INT" in rel_ids
    assert "REL:F4:18_CONTINUITY_AND_INTEGRAL_TO_FTC1" in rel_ids

    for rec in records:
        assert rec.commutation_verified is True
        assert len(rec.relationship_witness) > 0
        assert rec.relationship_witness["transformation_verified"] is True


def test_full_32x32_cross_pair_discrimination_matrix():
    """Verify 100% rejection rate on 992 off-diagonal pairs in discrimination matrix."""
    tier_manifest = json.loads(CLAIM_TIER_MANIFEST_PATH.read_text(encoding="utf-8"))
    matrix_res = RealAnalysisDualViewEvaluator.run_cross_pair_matrix(tier_manifest["claims"])

    assert matrix_res["total_matrix_pairs"] == 1024
    assert matrix_res["diagonal_pairs"] == 32
    assert matrix_res["off_diagonal_pairs"] == 992
    assert matrix_res["off_diagonal_rejections"] == 992
    assert matrix_res["off_diagonal_false_positives"] == 0
    assert matrix_res["off_diagonal_rejection_rate_pct"] == "100.00%"


def test_multi_class_mutant_killing_suite():
    """Verify all 20 pre-registered mutants are killed (100% kill rate)."""
    fals_manifest = json.loads(FALSIFICATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    mutant_res = run_falsification_suite(fals_manifest)

    assert mutant_res["total_mutants_tested"] == 20
    assert mutant_res["mutants_killed"] == 20
    assert mutant_res["mutant_kill_rate_pct"] == "100.00%"

    for m in mutant_res["mutant_records"]:
        assert m["mutant_killed"] is True
        assert m["verdict"] == AnalysisVerdict.NONCOMMUTATIVE_UNDER_CONTRACT.value


def test_engine_ast_and_import_decoupling():
    """Verify that EO and GEO realization engines do not import or reference each other."""
    eo_file = ROOT / "mapeogeo" / "analysis" / "eo_engine.py"
    geo_file = ROOT / "mapeogeo" / "analysis" / "geo_engine.py"

    eo_code = eo_file.read_text(encoding="utf-8")
    geo_code = geo_file.read_text(encoding="utf-8")

    assert "geo_engine" not in eo_code
    assert "RealAnalysisGEOEngine" not in eo_code

    assert "eo_engine" not in geo_code
    assert "RealAnalysisEOEngine" not in geo_code

    # AST structural check
    eo_tree = ast.parse(eo_code)
    geo_tree = ast.parse(geo_code)

    eo_imports = [n.names[0].name for n in ast.walk(eo_tree) if isinstance(n, ast.Import)]
    geo_imports = [n.names[0].name for n in ast.walk(geo_tree) if isinstance(n, ast.Import)]

    for imp in eo_imports:
        assert "geo" not in imp
    for imp in geo_imports:
        assert "eo" not in imp


def test_semantic_codomain_non_degeneracy():
    """Verify 32 unique semantic state digests with entropy 5.0 bits."""
    tier_manifest = json.loads(CLAIM_TIER_MANIFEST_PATH.read_text(encoding="utf-8"))
    codomain_res = RealAnalysisDualViewEvaluator.compute_codomain_entropy(tier_manifest["claims"])

    assert codomain_res["commutative_concepts_evaluated"] == 32
    assert codomain_res["unique_eo_semantic_digests"] == 32
    assert codomain_res["unique_geo_semantic_digests"] == 32
    assert codomain_res["is_semantically_injective"] is True
    assert codomain_res["zero_cross_concept_semantic_collisions"] is True
    assert codomain_res["codomain_entropy_bits"] == 5.0


def test_lean_formal_alignment_and_audit():
    """Verify that Lean formal source files exist and formal audit passes with zero sorry."""
    lean_lib = ROOT / "MAPEOGEOFormal" / "WaveF4.lean"
    lean_formal = ROOT / "formal" / "lean" / "wave_f4" / "WaveF4.lean"

    assert lean_lib.is_file(), f"Missing {lean_lib}"
    assert lean_formal.is_file(), f"Missing {lean_formal}"

    lib_text = lean_lib.read_text(encoding="utf-8")
    assert "theorem OrderedField" in lib_text
    assert "theorem HeineBorel" in lib_text
    assert "theorem RollesTheorem" in lib_text
    assert "theorem MeanValueTheorem" in lib_text
    assert "theorem FundamentalTheoremCalculus" in lib_text

    assert "sorry" not in lib_text
    assert "admit" not in lib_text

    audit = json.loads(FORMAL_AUDIT_PATH.read_text(encoding="utf-8"))
    assert audit["total_formal_general_theorems"] == 14
    for record in audit["audit_records"]:
        assert record["has_sorry"] is False
        assert record["has_admit"] is False
        assert record["has_sorryAx"] is False
        assert record["has_custom_axioms"] is False
        assert record["status"] == "VERIFIED_FORMAL_GENERAL"


def test_wave_f4_evidence_and_report_files_exist_and_consistent():
    """Verify that evidence and report files exist and reflect authoritative results."""
    assert EVIDENCE_PATH.is_file(), f"Missing evidence at {EVIDENCE_PATH}"
    assert REPORT_PATH.is_file(), f"Missing report at {REPORT_PATH}"

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert evidence["stage"] == "v0.21_wave_f4"
    assert evidence["scientific_status"] == "EVIDENCE_PARTIAL"
    assert evidence["total_canonical_concepts_audited"] == 32
    assert evidence["total_typed_relationships_audited"] == 20
    assert len(evidence["evidence_sha256"]) == 64

    assert "32 / 32" in report
    assert "20 / 20" in report
    assert "FORMAL_GENERAL" in report
    assert "CHECKED_SYMBOLIC_FAMILY" in report
    assert "EXACT_BOUNDED_INSTANCE" in report
    assert "0 remained probe-only" in report
