"""Unit tests for MAPEOGEO v0.12 Cross-Source Mathematics Expansion."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.import_axler_v0_12 import (
    DEFAULT_CACHE_PATH,
    FORBIDDEN_PERSISTED_KEYS,
    AxlerDeclaration,
    detect_representation_profile,
    generate_mock_axler_declarations,
    get_axler_declarations,
    parse_declarations_from_pdf,
)
from scripts.cross_source_intake_v0_12 import (
    compute_expansion_metrics,
    ingest_axler_declarations,
    ingest_canonical_alignments,
    save_graph_gz,
    validate_against_preregistration,
)
from tests.validate_cross_source_v0_12 import validate_artifacts

ROOT = Path(__file__).resolve().parents[1]


def test_detector_bank_eo_only():
    profile = detect_representation_profile(
        text="A linear map T from V to W has a null space and range.",
        title="linear map properties",
    )
    assert "linear_map" in profile["eo_tags"]
    assert "null_space" in profile["eo_tags"]
    assert "range" in profile["eo_tags"]
    assert len(profile["geo_tags"]) == 0
    assert profile["direct_status"] == "EO_ONLY_DIRECT"


def test_detector_bank_geo_only():
    profile = detect_representation_profile(
        text="An inner product defines a norm and orthogonality between vectors.",
        title="orthogonal properties",
    )
    assert len(profile["eo_tags"]) == 0
    assert "orthogonal" in profile["geo_tags"]
    assert "norm" in profile["geo_tags"]
    assert "inner_product" in profile["geo_tags"]
    assert profile["direct_status"] == "GEO_ONLY_DIRECT"


def test_detector_bank_dual_direct():
    profile = detect_representation_profile(
        text="An orthogonal projection is a linear map onto a subspace along its orthogonal complement.",
        title="orthogonal projection",
    )
    assert "linear_map" in profile["eo_tags"] or "subspace" in profile["eo_tags"]
    assert "projection" in profile["geo_tags"] or "orthogonal" in profile["geo_tags"]
    assert profile["direct_status"] == "DUAL_DIRECT"


def test_zero_prose_invariant():
    decl = AxlerDeclaration(
        node_id="srcdecl:axler:theorem:1_45",
        source_id="AXLER_LADR4E_2026_08_16",
        label="Axler 1.45 Theorem condition for a direct sum",
        decl_type="THEOREM",
        chapter_section="1C",
        page=37,
        statement_sha256="abc123hash",
        char_count=120,
        structural_refs=["1.41"],
        representation_profile={"eo_tags": ["direct_sum"], "geo_tags": [], "direct_status": "EO_ONLY_DIRECT"},
    )
    d = decl.to_dict()
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_mock_axler_declarations():
    decls = generate_mock_axler_declarations()
    assert len(decls) >= 30
    node_ids = {d.node_id for d in decls}
    assert "srcdecl:axler:definition:1_20" in node_ids
    assert "srcdecl:axler:theorem:3_21" in node_ids
    assert "srcdecl:axler:theorem:6_32" in node_ids
    assert "srcdecl:axler:theorem:7_29" in node_ids


def test_pdf_extraction_if_available():
    if not DEFAULT_CACHE_PATH.exists():
        pytest.skip("LADR4e.pdf not present locally")
    decls = parse_declarations_from_pdf(DEFAULT_CACHE_PATH)
    assert len(decls) >= 30
    node_ids = {d.node_id for d in decls}
    assert "srcdecl:axler:definition:1_20" in node_ids
    assert "srcdecl:axler:theorem:3_21" in node_ids
    assert "srcdecl:axler:theorem:6_32" in node_ids
    assert "srcdecl:axler:theorem:7_29" in node_ids


def test_cross_source_alignments_schema():
    align_path = ROOT / "formal" / "cross_source_alignments_v0_12.json"
    assert align_path.exists()
    data = json.loads(align_path.read_text(encoding="utf-8"))
    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 25

    for co in canonical_objects:
        assert "id" in co and co["id"].startswith("canonical:linear_algebra:")
        assert "name" in co
        assert "alignments" in co
        assert len(co["alignments"]) >= 1


def test_cross_source_intake_pipeline(tmp_path: Path):
    from scripts.cross_source_intake_v0_12 import load_json_or_gz
    base_graph_path = ROOT / "data" / "mapeogeo_v0_11_graph.json.gz"
    if not base_graph_path.exists():
        base_graph_path = ROOT / "artifacts" / "source_v0_6" / "mapeogeo_independent_graph.json"
    if not base_graph_path.exists():
        base_graph_path = ROOT / "artifacts" / "test_v06" / "mapeogeo_independent_graph.json"
    assert base_graph_path.exists(), "Gallier base graph missing"
    graph = load_json_or_gz(base_graph_path)
    decls = get_axler_declarations()

    # Ingest Axler
    graph = ingest_axler_declarations(graph, decls)
    axler_nodes = [n for n in graph["nodes"] if n["id"].startswith("srcdecl:axler:")]
    assert len(axler_nodes) == len(decls)

    # Ingest Canonical Alignments
    align_path = ROOT / "formal" / "cross_source_alignments_v0_12.json"
    align_data = json.loads(align_path.read_text(encoding="utf-8"))
    graph, summary = ingest_canonical_alignments(graph, align_data)

    assert summary["aligned_canonical_objects"] >= 15

    # Compute metrics
    metrics = compute_expansion_metrics(graph, summary)
    dashboard = metrics["primary_dashboard"]
    assert dashboard["N_source"] >= 30
    assert dashboard["N_canonical"] >= 25
    assert dashboard["N_cross_source"] >= 15
    assert dashboard["N_EO"] > 0
    assert dashboard["N_GEO"] > 0
    assert dashboard["D_domains"] == ["Linear Algebra"]

    # Validate against preregistration
    prereg_path = ROOT / "evidence" / "v0_12_preregistration.json"
    eval_result = validate_against_preregistration(metrics, prereg_path)
    assert eval_result["engine_validity"] == "VALID"
    assert eval_result["scientific_result"] == "PASS"

    # Save and test validator
    graph_out = tmp_path / "mapeogeo_v0_12_graph.json.gz"
    save_graph_gz(graph, graph_out)

    align_out = tmp_path / "cross_source_alignments.json"
    align_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    metrics_out = tmp_path / "expansion_metrics.json"
    metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    results_out = tmp_path / "scientific_results.json"
    results_out.write_text(json.dumps({
        "stage": "v0.12",
        "evaluation": eval_result,
        "primary_dashboard": dashboard,
        "coverage_metrics": metrics["coverage_metrics"],
    }, indent=2), encoding="utf-8")

    success, errors = validate_artifacts(tmp_path, prereg_path)
    assert success, f"Validation failed with errors: {errors}"
