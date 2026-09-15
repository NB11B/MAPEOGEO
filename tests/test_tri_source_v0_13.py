"""Unit tests for MAPEOGEO v0.13 Tri-Source Mathematics Expansion."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.import_vmls_v0_13 import (
    DEFAULT_CACHE_PATH as DEFAULT_VMLS_PDF,
    FORBIDDEN_PERSISTED_KEYS,
    VmlsDeclaration,
    detect_vmls_representation_profile,
    generate_mock_vmls_declarations,
    get_vmls_declarations,
    parse_vmls_declarations_from_pdf,
)
from scripts.blinded_alignment_benchmark_v0_13 import run_blinded_benchmark
from scripts.tri_source_intake_v0_13 import (
    compute_tri_source_metrics,
    ingest_tri_source_alignments,
    ingest_vmls_declarations,
    save_graph_gz,
    validate_against_tri_source_preregistration,
)
from tests.validate_tri_source_v0_13 import validate_tri_source_artifacts

ROOT = Path(__file__).resolve().parents[1]


def test_vmls_detector_bank():
    profile = detect_vmls_representation_profile(
        text="The least squares problem minimizes the Euclidean norm squared ||Ax - b||^2.",
        title="Least squares problem",
    )
    assert "least_squares" in profile["eo_tags"]
    assert "norm" in profile["geo_tags"]
    assert profile["direct_status"] == "DUAL_DIRECT"


def test_vmls_zero_prose_invariant():
    decl = VmlsDeclaration(
        node_id="srcdecl:vmls:section:12_1",
        source_id="BOYD_VANDENBERGHE_VMLS_2018",
        label="VMLS 12.1 Least squares problem",
        decl_type="SECTION",
        chapter_section="Chapter 12",
        page=243,
        statement_sha256="abc123vmls",
        char_count=500,
        structural_refs=["11.1"],
        representation_profile={"eo_tags": ["least_squares"], "geo_tags": ["norm"], "direct_status": "DUAL_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_vmls_mock_declarations():
    decls = generate_mock_vmls_declarations()
    assert len(decls) >= 30
    node_ids = {d.node_id for d in decls}
    assert "srcdecl:vmls:section:1_1" in node_ids
    assert "srcdecl:vmls:section:5_4" in node_ids
    assert "srcdecl:vmls:section:12_1" in node_ids


def test_vmls_pdf_extraction_if_available():
    if not DEFAULT_VMLS_PDF.exists():
        pytest.skip("vmls.pdf not present locally")
    decls = parse_vmls_declarations_from_pdf(DEFAULT_VMLS_PDF)
    assert len(decls) >= 30
    node_ids = {d.node_id for d in decls}
    assert "srcdecl:vmls:section:1_1" in node_ids
    assert "srcdecl:vmls:section:5_4" in node_ids
    assert "srcdecl:vmls:section:12_1" in node_ids


def test_tri_source_alignments_schema():
    align_path = ROOT / "formal" / "tri_source_alignments_v0_13.json"
    assert align_path.exists()
    data = json.loads(align_path.read_text(encoding="utf-8"))
    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 35

    three_source_count = 0
    domains = set()

    for co in canonical_objects:
        assert "id" in co
        assert "name" in co
        assert "alignments" in co
        domains.add(co.get("domain", ""))
        corpora = {al["corpus"] for al in co.get("alignments", [])}
        if {"GALLIER", "AXLER", "VMLS"}.issubset(corpora):
            three_source_count += 1

    assert three_source_count >= 10
    assert len(domains) >= 2


def test_blinded_alignment_benchmark_execution(tmp_path: Path):
    align_path = ROOT / "formal" / "tri_source_alignments_v0_13.json"
    prereg_path = ROOT / "evidence" / "v0_13_preregistration.json"
    summary = run_blinded_benchmark(align_path, prereg_path, tmp_path)

    assert summary["holdout_count"] > 0
    assert "top_1_accuracy" in summary["metrics"]
    assert "top_3_recall" in summary["metrics"]
    assert "unresolved_rate" in summary["metrics"]
    assert summary["evaluation"]["status"] == "PASS"


def test_tri_source_intake_pipeline(tmp_path: Path):
    graph = {"nodes": [], "edges": []}
    mock_decls = generate_mock_vmls_declarations()

    # Ingest VMLS
    graph = ingest_vmls_declarations(graph, mock_decls)
    vmls_nodes = [n for n in graph["nodes"] if n["id"].startswith("srcdecl:vmls:")]
    assert len(vmls_nodes) == len(mock_decls)

    # Ingest Tri-Source Alignments
    align_path = ROOT / "formal" / "tri_source_alignments_v0_13.json"
    align_data = json.loads(align_path.read_text(encoding="utf-8"))
    graph, summary = ingest_tri_source_alignments(graph, align_data)

    assert summary["two_source_canonical_objects"] >= 25
    assert summary["three_source_canonical_objects"] >= 10

    # Compute metrics
    metrics = compute_tri_source_metrics(graph, summary)
    dashboard = metrics["primary_dashboard"]
    assert dashboard["N_source"] >= 30
    assert dashboard["N_canonical"] >= 35
    assert dashboard["N_2_source"] >= 25
    assert dashboard["N_3_source"] >= 10
    assert dashboard["D_domains_count"] >= 2

    # Benchmark
    prereg_path = ROOT / "evidence" / "v0_13_preregistration.json"
    bench_results = run_blinded_benchmark(align_path, prereg_path, tmp_path)

    # Validate against preregistration
    eval_result = validate_against_tri_source_preregistration(metrics, prereg_path)
    assert eval_result["engine_validity"] == "VALID"
    assert eval_result["scientific_result"] == "PASS"

    # Save and test validator
    graph_out = tmp_path / "mapeogeo_v0_13_graph.json.gz"
    save_graph_gz(graph, graph_out)

    align_out = tmp_path / "tri_source_alignments.json"
    align_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    metrics_out = tmp_path / "expansion_metrics.json"
    metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    results_out = tmp_path / "scientific_results.json"
    results_out.write_text(json.dumps({
        "stage": "v0.13",
        "evaluation": eval_result,
        "primary_dashboard": dashboard,
        "coverage_metrics": metrics["coverage_metrics"],
        "blinded_benchmark_summary": bench_results["metrics"],
    }, indent=2), encoding="utf-8")

    success, errors = validate_tri_source_artifacts(tmp_path, prereg_path)
    assert success, f"Validation failed with errors: {errors}"
