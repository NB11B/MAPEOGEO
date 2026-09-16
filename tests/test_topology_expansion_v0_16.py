"""Unit and Integration Tests for MAPEOGEO v0.16 Topology, Metric Spaces & Functional Structure Expansion."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

from scripts.import_topology_v0_16 import (
    FORBIDDEN_PERSISTED_KEYS,
    TopologyDeclaration,
    detect_topology_representation_profile,
    generate_supplementary_topology_declarations,
)
from scripts.topology_intake_v0_16 import (
    compute_v0_16_dashboard,
    ingest_topology_declarations,
    ingest_v0_16_alignments,
    run_topology_intake_v0_16,
)


def test_topology_declaration_dataclass():
    """Verify zero-prose persistence policy on TopologyDeclaration."""
    decl = TopologyDeclaration(
        node_id="srcdecl:cvx:appendix:A_1",
        source_id="BOYD_VANDENBERGHE_CVX_2004",
        label="CVX Appendix A.1 Norms",
        decl_type="APPENDIX",
        chapter_section="Appendix A",
        page=633,
        statement_sha256="abc123hash",
        char_count=50,
        structural_refs=[],
        representation_profile={"direct_status": "DUAL_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_topology_detector_bank():
    """Verify EO/GEO and representation detection on topology text."""
    metric_text = "Metric space (X, d) with open balls B(x, r) forming open sets in the metric topology."
    profile = detect_topology_representation_profile(metric_text, "Metric Space Definition")
    assert "metric_distance" in profile["eo_tags"]
    assert "open_set" in profile["geo_tags"] or "open_ball" in profile["geo_tags"]
    assert profile["direct_status"] == "DUAL_DIRECT"
    assert "abstract" in profile["representation_kinds"]
    assert "geometric" in profile["representation_kinds"]

    operator_text = "Bounded linear operator between Banach spaces with finite operator norm and contraction mapping."
    profile2 = detect_topology_representation_profile(operator_text, "Operator Norm Proposition")
    assert "operator_norm" in profile2["eo_tags"]
    assert "contraction_mapping" in profile2["eo_tags"]
    assert "abstract" in profile2["representation_kinds"]


def test_alignments_schema_v0_16():
    """Verify cross-source alignments schema and semantic statuses."""
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_16.json"
    assert alignments_path.exists()
    data = json.loads(alignments_path.read_text(encoding="utf-8"))

    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 130

    valid_statuses = {
        "CROSS_SOURCE_SAME",
        "CROSS_SOURCE_SCOPED_OVERLAP",
        "CROSS_SOURCE_RELATED_NOT_SAME",
        "UNRESOLVED",
    }

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
            assert al["corpus"] in {"GALLIER", "AXLER", "VMLS", "CVX"}


def test_topology_intake_pipeline(tmp_path: Path):
    """Integration test for full v0.16 expansion."""
    base_graph_path = ROOT / "artifacts" / "analysis_v0_15_2" / "mapeogeo_v0_15_2_graph.json.gz"
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_16.json"
    out_dir = tmp_path / "topology_v0_16"

    graph, dashboard, summary = run_topology_intake_v0_16(
        base_graph_path=base_graph_path,
        alignments_path=alignments_path,
        out_dir=out_dir,
    )

    # 1. Disjoint Partition Invariant
    sb = dashboard["source_breakdown"]
    total_decls = sb["S_A_gallier"] + sb["S_B_axler"] + sb["S_C_vmls"] + sb["S_D_cvx"]
    assert total_decls == dashboard["N_source_total"]
    assert dashboard["N_source_total"] >= 1760

    # 2. Canonical Objects & Convergence
    assert dashboard["N_canonical_total"] >= 130
    assert dashboard["N_2_source_bridges"] >= 80
    assert dashboard["N_3_source_bridges"] >= 40
    assert dashboard["N_4_source_bridges"] >= 20

    # 3. Distinct Domains
    assert dashboard["D_domains_count"] >= 5
    assert "Topology & Metric Spaces" in dashboard["domains_list"]

    # 4. Representation Richness
    assert dashboard["representation_diversity"]["average_richness_r_bar"] >= 3.0

    # 5. Semantic Bridges
    es = dashboard["edges_summary"]
    assert es["SAME_SEMANTICS_bridges"] >= 400
    assert es["SCOPED_OVERLAP_bridges"] >= 180
    assert es["total_cross_source_bridges"] >= 600

    # 6. Referential Integrity
    nodes = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in nodes, f"Missing edge source: {edge['source']}"
        assert edge["target"] in nodes, f"Missing edge target: {edge['target']}"
