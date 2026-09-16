"""Unit and Integration Tests for MAPEOGEO v0.17 Measure Theory, Integration & Probability Expansion."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

from scripts.import_billingsley_v0_17 import (
    FORBIDDEN_PERSISTED_KEYS,
    BillingsleyDeclaration,
    detect_measure_representation_profile,
    generate_billingsley_declarations,
)
from scripts.measure_intake_v0_17 import (
    compute_v0_17_dashboard,
    ingest_billingsley_declarations,
    ingest_v0_17_alignments,
    run_measure_intake_v0_17,
)


def test_billingsley_declaration_dataclass():
    """Verify zero-prose persistence policy on BillingsleyDeclaration."""
    decl = BillingsleyDeclaration(
        node_id="srcdecl:billingsley:def:field_sigma_field",
        source_id="BILLINGSLEY_PROB_MEASURE_1995",
        label="Definition of Sigma-Field",
        decl_type="DEFINITION",
        chapter_section="Section 2",
        page=19,
        statement_sha256="abc123hash",
        char_count=50,
        structural_refs=[],
        representation_profile={"direct_status": "DUAL_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_measure_detector_bank():
    """Verify EO/GEO and representation detection on measure theory text."""
    integral_text = "Lebesgue integral of non-negative measurable functions with monotone convergence theorem."
    profile = detect_measure_representation_profile(integral_text, "Lebesgue Integral Definition")
    assert "lebesgue_integral" in profile["eo_tags"] or "monotone_convergence" in profile["eo_tags"]
    assert "abstract" in profile["representation_kinds"]

    prob_text = "Probability space (Omega, F, P) with random variables and sigma-algebra of events."
    profile2 = detect_measure_representation_profile(prob_text, "Probability Space Definition")
    assert "sigma_algebra" in profile2["geo_tags"] or "measure_space" in profile2["geo_tags"]
    assert "abstract" in profile2["representation_kinds"] or "applied" in profile2["representation_kinds"]


def test_alignments_schema_v0_17():
    """Verify cross-source alignments schema and 5-source semantic statuses."""
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_17.json"
    assert alignments_path.exists()
    data = json.loads(alignments_path.read_text(encoding="utf-8"))

    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 150

    valid_statuses = {
        "CROSS_SOURCE_SAME",
        "CROSS_SOURCE_SCOPED_OVERLAP",
        "CROSS_SOURCE_RELATED_NOT_SAME",
        "UNRESOLVED",
    }
    valid_corpora = {"GALLIER", "AXLER", "VMLS", "CVX", "BILLINGSLEY"}

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


def test_measure_intake_pipeline(tmp_path: Path):
    """Integration test for full v0.17 expansion."""
    base_graph_path = ROOT / "artifacts" / "topology_v0_16" / "mapeogeo_v0_16_graph.json.gz"
    if not base_graph_path.exists():
        import subprocess, sys
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "reconstruct_pipeline.py"), "--target-stage", "v0.16"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    alignments_path = ROOT / "formal" / "cross_source_alignments_v0_17.json"
    out_dir = tmp_path / "measure_v0_17"

    graph, dashboard, summary = run_measure_intake_v0_17(
        base_graph_path=base_graph_path,
        alignments_path=alignments_path,
        out_dir=out_dir,
    )

    # 1. Disjoint Partition Invariant across 5 Sources
    sb = dashboard["source_breakdown"]
    total_decls = sb["S_A_gallier"] + sb["S_B_axler"] + sb["S_C_vmls"] + sb["S_D_cvx"] + sb["S_E_billingsley"]
    assert total_decls == dashboard["N_source_total"]
    assert dashboard["N_source_total"] == 1824
    assert sb["S_A_gallier"] == 1360
    assert sb["S_B_axler"] == 235
    assert sb["S_C_vmls"] == 81
    assert sb["S_D_cvx"] == 84
    assert sb["S_E_billingsley"] == 64
    assert dashboard["N_section_anchors_total"] == 5

    # 2. Canonical Objects & Multi-Source Convergence
    assert dashboard["N_canonical_total"] >= 170
    assert dashboard["N_2_source_bridges"] >= 100
    assert dashboard["N_3_source_bridges"] >= 50
    assert dashboard["N_4_source_bridges"] >= 25
    assert dashboard["N_5_source_bridges"] >= 5

    # 3. Distinct Domains (6 domains)
    assert dashboard["D_domains_count"] == 6
    assert "Measure Theory & Probability" in dashboard["domains_list"]
    assert "Topology & Metric Spaces" in dashboard["domains_list"]

    # 4. Representation Richness
    assert dashboard["representation_diversity"]["average_richness_r_bar"] >= 3.0

    # 5. Semantic Bridges
    es = dashboard["edges_summary"]
    assert es["SAME_SEMANTICS_bridges"] >= 450
    assert es["SCOPED_OVERLAP_bridges"] >= 250
    assert es["total_cross_source_bridges"] >= 750

    # 6. Referential Integrity
    nodes = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in nodes, f"Missing edge source: {edge['source']}"
        assert edge["target"] in nodes, f"Missing edge target: {edge['target']}"
