"""Unit and Integration Tests for MAPEOGEO Foundation Backfill."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

from scripts.import_foundation_backfill import (
    FORBIDDEN_PERSISTED_KEYS,
    FoundationDeclaration,
    detect_foundation_representation_profile,
    generate_foundation_declarations,
)
from scripts.foundation_contracts import (
    build_foundation_contract_evidence,
    validate_contract_evidence,
)
from scripts.compute_foundation_depth import compute_foundation_metrics
from scripts.foundation_intake import (
    compute_foundation_dashboard,
    ingest_foundation_canonical_alignments,
    ingest_foundation_declarations,
    run_foundation_intake,
)


def test_foundation_declaration_dataclass():
    """Verify zero-prose persistence policy on FoundationDeclaration."""
    decl = FoundationDeclaration(
        node_id="srcdecl:foundation:logic:proposition",
        source_id="FOUNDATION_MATHEMATICS_BASE",
        label="Definition of Proposition",
        decl_type="DEFINITION",
        chapter_section="Logic §1.1",
        statement_sha256="abc123hash",
        char_count=50,
        layer="logic",
        structural_refs=[],
        representation_profile={"direct_status": "DUAL_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_foundation_detector_bank():
    """Verify EO/GEO and representation detection on foundational statements."""
    logic_text = "Truth table functional semantics for logical conjunction and disjunction with boolean valuation."
    profile = detect_foundation_representation_profile(logic_text, "Truth Table Semantics")
    assert "boolean_logic_evaluator" in profile["eo_tags"]
    assert "logical_truth_geometry" in profile["geo_tags"]

    calc_text = "Derivative definition as difference quotient limit and Riemann sum definite integral."
    profile2 = detect_foundation_representation_profile(calc_text, "Calculus Fundamentals")
    assert "differential_calculus_operator" in profile2["eo_tags"] or "integral_calculus_operator" in profile2["eo_tags"]
    assert "computational" in profile2["representation_kinds"] or "abstract" in profile2["representation_kinds"]


def test_foundation_declarations_count_and_hashes():
    """Verify generation of all 8 foundational layers with valid SHA-256 statement hashes."""
    decls = generate_foundation_declarations()
    assert len(decls) >= 150

    expected_layers = {
        "logic",
        "sets",
        "relations_functions",
        "number_systems",
        "arithmetic_algebra",
        "order_sequences",
        "geometry_trig",
        "elementary_calculus",
    }
    found_layers = {d.layer for d in decls}
    assert expected_layers == found_layers

    seen_ids = set()
    for d in decls:
        assert d.node_id not in seen_ids, f"Duplicate node_id: {d.node_id}"
        seen_ids.add(d.node_id)
        assert len(d.statement_sha256) == 64
        assert d.char_count > 0
        assert d.source_id == "FOUNDATION_MATHEMATICS_BASE"


def test_foundation_contracts_are_declaration_bound_and_fail_closed():
    """Only the exhaustively checked declaration is promoted."""
    declarations = generate_foundation_declarations()
    evidence = build_foundation_contract_evidence(declarations)
    summary = validate_contract_evidence(evidence, declarations)
    assert len(evidence) == 1
    assert summary["verified_declarations"] == 1
    assert summary["unverified_declarations"] == 175
    assert summary["kernel_verified_declarations"] == 0


def test_foundation_alignments_schema():
    """Verify foundation alignments schema and upward dependencies."""
    alignments_path = ROOT / "formal" / "foundation_alignments.json"
    assert alignments_path.exists()
    data = json.loads(alignments_path.read_text(encoding="utf-8"))

    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 25

    seen_ids = set()
    for co in canonical_objects:
        cid = co["id"]
        assert cid not in seen_ids, f"Duplicate canonical ID: {cid}"
        seen_ids.add(cid)
        assert co.get("name")
        assert co.get("domain")
        assert len(co.get("alignments", [])) >= 1
        assert len(co.get("upward_dependencies", [])) >= 1


def test_foundation_intake_pipeline(tmp_path: Path):
    """Integration test for full Foundation Backfill pipeline."""
    base_graph_path = ROOT / "artifacts" / "complex_analysis_v0_19" / "mapeogeo_v0_19_graph.json.gz"
    alignments_path = ROOT / "formal" / "foundation_alignments.json"
    out_dir = tmp_path / "foundation_backfill"
    with gzip.open(base_graph_path, "rt", encoding="utf-8") as f:
        base_graph = json.load(f)
    base_canonical_count = sum(n.get("type") == "CANONICAL_OBJECT" for n in base_graph["nodes"])
    base_bridge_count = sum(
        e.get("type") in {"SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO"}
        for e in base_graph["edges"]
    )

    graph, dashboard, summary = run_foundation_intake(
        base_graph_path=base_graph_path,
        alignments_path=alignments_path,
        out_dir=out_dir,
    )

    # 1. Disjoint Partition Invariant across all 7 Corpora (S_0, S_A, S_B, S_C, S_D, S_E, S_F)
    sb = dashboard["N_source_breakdown"]
    total_decls = (
        sb["foundation_base_S0"]
        + sb["gallier_quaintance_SA"]
        + sb["axler_ladr4e_SB"]
        + sb["boyd_vmls_SC"]
        + sb["boyd_cvx_SD"]
        + sb["billingsley_SE"]
        + sb["lee_diffgeom_SF"]
        + sb["ahlfors_krantz_SG"]
    )
    assert total_decls == dashboard["N_source_total"]
    assert dashboard["N_source_total"] == 2135
    assert sb["foundation_base_S0"] == 176
    assert sb["gallier_quaintance_SA"] == 1356
    assert sb["axler_ladr4e_SB"] == 235
    assert sb["boyd_vmls_SC"] == 81
    assert sb["boyd_cvx_SD"] == 84
    assert sb["billingsley_SE"] == 64
    assert sb["lee_diffgeom_SF"] == 67
    assert sb["ahlfors_krantz_SG"] == 72
    assert dashboard["N_section_anchors_total"] == 5

    # 2. Canonical Objects & Foundation Breakdown
    assert dashboard["N_canonical_total"] == base_canonical_count + 29
    cb = dashboard["canonical_breakdown"]
    assert cb["foundation_canonical_objects"] == 29
    assert cb["advanced_canonical_objects"] == 235

    # 3. Foundation Reachability & Vertical Depth
    fm = dashboard["foundation_metrics"]
    assert fm["raw_topology_reachability"]["advanced_canonical_objects_total"] == 235
    assert fm["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] <= 235

    # 4. Dual Contracts Verification
    assert dashboard["contracts_verification"]["verified_declarations"] == 1
    assert dashboard["contracts_verification"]["unverified_declarations"] == 175
    assert dashboard["contracts_verification"]["kernel_verified_declarations"] == 0

    # 5. Upward Bridges and Semantic Bridges
    es = dashboard["edges_summary"]
    assert es["UPWARD_FOUNDATION_DEPENDENCY"] >= 100
    assert es["total_typed_cross_bridges"] == base_bridge_count

    # 6. Referential Integrity
    nodes = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in nodes, f"Missing edge source: {edge['source']}"
        assert edge["target"] in nodes, f"Missing edge target: {edge['target']}"
