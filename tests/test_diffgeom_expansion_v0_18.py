"""Unit and Integration Tests for MAPEOGEO v0.18 Differential Geometry, Lie Groups & Smooth Manifolds Expansion."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

from scripts.import_diffgeom_v0_18 import (
    FORBIDDEN_PERSISTED_KEYS,
    DiffGeomDeclaration,
    detect_diffgeom_representation_profile,
    generate_diffgeom_declarations,
)
from scripts.diffgeom_intake_v0_18 import (
    compute_v0_18_dashboard_metrics,
    ingest_diffgeom_declarations,
    ingest_v0_18_canonical_alignments,
    run_diffgeom_intake_v0_18,
)


def test_diffgeom_declaration_dataclass():
    """Verify zero-prose persistence policy on DiffGeomDeclaration."""
    decl = DiffGeomDeclaration(
        node_id="srcdecl:diffgeom:def:smooth_manifold",
        source_id="LEE_SMOOTH_MANIFOLDS_2013",
        label="Definition of Smooth Manifold",
        decl_type="DEFINITION",
        chapter_section="Chapter 1",
        page=14,
        statement_sha256="abc123hash",
        char_count=50,
        structural_refs=[],
        representation_profile={"direct_status": "DUAL_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_diffgeom_detector_bank():
    """Verify EO/GEO and representation detection on differential geometry statements."""
    stokes_text = "Generalized Stokes' Theorem for integration of differential forms on manifolds with boundary."
    profile = detect_diffgeom_representation_profile(stokes_text, "Stokes Theorem")
    assert "stokes_integral_operator" in profile["eo_tags"] or "exterior_derivative_operator" in profile["eo_tags"]
    assert "abstract" in profile["representation_kinds"] or "geometric" in profile["representation_kinds"]

    lie_text = "Lie group G and its Lie algebra of left-invariant vector fields with Lie bracket [X, Y]."
    profile2 = detect_diffgeom_representation_profile(lie_text, "Lie Group Definition")
    assert "lie_group_geometry" in profile2["geo_tags"] or "tangent_bundle_geometry" in profile2["geo_tags"]
    assert "algebraic" in profile2["representation_kinds"] or "abstract" in profile2["representation_kinds"]


def test_alignments_schema_v0_18():
    """Verify cross-source alignments schema and 6-source semantic statuses."""
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_18.json"
    assert alignments_path.exists()
    data = json.loads(alignments_path.read_text(encoding="utf-8"))

    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 180

    valid_statuses = {
        "CROSS_SOURCE_SAME",
        "CROSS_SOURCE_SCOPED_OVERLAP",
        "CROSS_SOURCE_RELATED_NOT_SAME",
        "UNRESOLVED",
    }
    valid_corpora = {"GALLIER", "AXLER", "VMLS", "CVX", "BILLINGSLEY", "LEE"}

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
            assert al["status"] in valid_statuses
            assert al["corpus"] in valid_corpora


def test_diffgeom_intake_pipeline(tmp_path: Path):
    """Integration test for full v0.18 expansion."""
    base_graph_path = ROOT / "artifacts" / "measure_v0_17" / "mapeogeo_v0_17_graph.json.gz"
    if not base_graph_path.exists():
        import subprocess, sys
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "reconstruct_pipeline.py"), "--target-stage", "v0.17"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_18.json"
    out_dir = tmp_path / "diffgeom_v0_18"

    graph, dashboard, summary = run_diffgeom_intake_v0_18(
        base_graph_path=base_graph_path,
        alignments_path=alignments_path,
        out_dir=out_dir,
    )

    # 1. Disjoint Partition Invariant across 6 Sources
    sb = dashboard["N_source_breakdown"]
    total_decls = (
        sb["gallier_quaintance_SA"]
        + sb["axler_ladr4e_SB"]
        + sb["boyd_vmls_SC"]
        + sb["boyd_cvx_SD"]
        + sb["billingsley_SE"]
        + sb["lee_diffgeom_SF"]
    )
    assert total_decls == dashboard["N_source_total"]
    assert dashboard["N_source_total"] == 1891
    assert sb["gallier_quaintance_SA"] == 1360
    assert sb["axler_ladr4e_SB"] == 235
    assert sb["boyd_vmls_SC"] == 81
    assert sb["boyd_cvx_SD"] == 84
    assert sb["billingsley_SE"] == 64
    assert sb["lee_diffgeom_SF"] == 67
    assert dashboard["N_section_anchors_total"] == 5

    # 2. Canonical Objects & Multi-Source Convergence
    assert dashboard["N_canonical_total"] >= 200
    msc = dashboard["multi_source_convergence"]
    assert msc["two_source_canonical_objects"] >= 125
    assert msc["three_source_canonical_objects"] >= 65
    assert msc["four_source_canonical_objects"] >= 30
    assert msc["five_source_canonical_objects"] >= 8
    assert msc["six_source_canonical_objects"] >= 1

    # 3. Distinct Domains (7 domains)
    assert dashboard["domains_count"] == 7
    assert "Differential Geometry & Lie Groups" in dashboard["domains_list"]
    assert "Measure Theory & Probability" in dashboard["domains_list"]
    assert "Topology & Metric Spaces" in dashboard["domains_list"]

    # 4. Representation Richness
    assert dashboard["representation_diversity"]["average_richness_r_bar"] >= 3.0

    # 5. Semantic Bridges
    es = dashboard["edges_summary"]
    assert es["SAME_SEMANTICS"] >= 500
    assert es["SCOPED_OVERLAP"] >= 300
    assert es["total_typed_cross_bridges"] >= 850

    # 6. Referential Integrity
    nodes = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in nodes, f"Missing edge source: {edge['source']}"
        assert edge["target"] in nodes, f"Missing edge target: {edge['target']}"
