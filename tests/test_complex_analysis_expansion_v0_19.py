"""Unit and Integration Tests for MAPEOGEO v0.19 Complex Analysis, SCV & Riemann Surfaces Expansion."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

from scripts.import_complex_analysis_v0_19 import (
    FORBIDDEN_PERSISTED_KEYS,
    SOURCE_ID,
    ComplexAnalysisDeclaration,
    build_complex_declarations,
    detect_complex_representation_profile,
)
from scripts.complex_analysis_intake_v0_19 import run_v0_19_intake


def test_complex_declaration_dataclass():
    """Verify zero-prose persistence policy on ComplexAnalysisDeclaration."""
    decl = ComplexAnalysisDeclaration(
        node_id="decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:DEFINITION:2.1",
        source_id=SOURCE_ID,
        label="Definition of Holomorphic Function",
        decl_type="DEFINITION",
        chapter_section="Ahlfors Chapter 2.1",
        page=30,
        statement_sha256="abc123complexhash",
        char_count=50,
        structural_refs=[],
        representation_profile={"direct_status": "DUAL_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d, f"Forbidden key '{forbidden}' found in serialized declaration dict"


def test_complex_detector_bank():
    """Verify EO/GEO and representation detection on complex analysis statements."""
    cr_text = "Cauchy-Riemann equations partial u / partial x = partial v / partial y and partial u / partial y = -partial v / partial x"
    profile = detect_complex_representation_profile(cr_text, "Cauchy-Riemann Equations")
    assert "cauchy_riemann_operator" in profile["eo_tags"]

    res_text = "Cauchy's Residue Theorem: (1 / (2 pi i)) oint_gamma f(z) dz = sum_k Ind_gamma(zk) Res(f, zk)"
    profile2 = detect_complex_representation_profile(res_text, "Residue Theorem")
    assert "residue_calculus_operator" in profile2["eo_tags"] or "cauchy_integral_operator" in profile2["eo_tags"]

    rs_text = "A Riemann surface X is a 2-dimensional manifold equipped with a holomorphic atlas."
    profile3 = detect_complex_representation_profile(rs_text, "Riemann Surface Definition")
    assert "riemann_surface_geometry" in profile3["geo_tags"] or "conformal_mapping_geometry" in profile3["geo_tags"]


def test_complex_declarations_count_and_hashes():
    """Verify exact count, unique node IDs, and non-empty hashes for all 72 Source G declarations."""
    decls = build_complex_declarations()
    assert len(decls) == 72, f"Expected exactly 72 Source G declarations, got {len(decls)}"

    seen_ids = set()
    for d in decls:
        assert d.node_id not in seen_ids, f"Duplicate node_id: {d.node_id}"
        seen_ids.add(d.node_id)
        assert d.source_id == SOURCE_ID
        assert len(d.statement_sha256) == 64, f"Invalid SHA-256 hash length for {d.node_id}"
        assert d.char_count > 0
        assert d.page > 0
        assert d.chapter_section


def test_alignments_schema_v0_19():
    """Verify cross-source alignments schema and 7-source semantic statuses."""
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_19.json"
    assert alignments_path.exists()
    data = json.loads(alignments_path.read_text(encoding="utf-8"))

    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 215

    valid_statuses = {
        "CROSS_SOURCE_SAME",
        "CROSS_SOURCE_SCOPED_OVERLAP",
        "CROSS_SOURCE_RELATED_NOT_SAME",
        "UNRESOLVED",
    }
    valid_corpora = {"GALLIER", "AXLER", "VMLS", "CVX", "BILLINGSLEY", "LEE", "AHLFORS", "FOUNDATION"}

    seen_ids = set()
    for co in canonical_objects:
        cid = co["id"]
        assert cid not in seen_ids, f"Duplicate canonical ID: {cid}"
        seen_ids.add(cid)
        assert co.get("name")
        assert co.get("domain")
        alignments = co.get("alignments", [])
        assert len(alignments) >= 1
        for al in alignments:
            assert al["status"] in valid_statuses, f"Invalid status {al['status']} in {cid}"
            assert al["corpus"] in valid_corpora, f"Invalid corpus {al['corpus']} in {cid}"


def test_complex_analysis_intake_pipeline(tmp_path: Path):
    """Integration test for full v0.19 intake pipeline."""
    base_graph_path = ROOT / "artifacts" / "diffgeom_v0_18" / "mapeogeo_v0_18_graph.json.gz"
    if not base_graph_path.exists():
        import subprocess, sys
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "reconstruct_pipeline.py"), "--target-stage", "v0.18"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_19.json"
    out_dir = tmp_path / "complex_analysis_v0_19"

    dashboard = run_v0_19_intake(
        base_graph_path=base_graph_path,
        alignments_path=alignments_path,
        out_dir=out_dir,
    )

    assert dashboard["stage"] == "v0.19"
    assert dashboard["N_source_total"] == 1959
    assert dashboard["source_breakdown"]["S_G_ahlfors"] == 72
    assert dashboard["source_breakdown"]["S_A_gallier"] == 1356
    assert dashboard["source_breakdown"]["S_B_axler"] == 235
    assert dashboard["source_breakdown"]["S_C_vmls"] == 81
    assert dashboard["source_breakdown"]["S_D_cvx"] == 84
    assert dashboard["source_breakdown"]["S_E_billingsley"] == 64
    assert dashboard["source_breakdown"]["S_F_lee"] == 67
    assert dashboard["disjoint_partition_verified"] is True
    assert dashboard["N_canonical_total"] == 235
    assert dashboard["domains"]["count"] >= 8
    assert dashboard["edges_summary"]["total_cross_source_bridges"] >= 1000

    graph_out = out_dir / "mapeogeo_v0_19_graph.json.gz"
    assert graph_out.exists()
    with gzip.open(graph_out, "rt", encoding="utf-8") as f:
        saved_graph = json.load(f)
    assert len(saved_graph["nodes"]) >= 3100
    assert len(saved_graph["edges"]) >= 26000
