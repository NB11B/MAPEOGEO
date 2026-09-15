"""Unit and integration tests for MAPEOGEO v0.14 Convex Analysis and Optimization expansion."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import pytest

from scripts.import_cvx_v0_14 import (
    FORBIDDEN_PERSISTED_KEYS,
    CvxDeclaration,
    detect_cvx_representation_profile,
    generate_mock_cvx_declarations,
    get_cvx_declarations,
)
from scripts.convex_intake_v0_14 import (
    compute_v0_14_metrics,
    ingest_cvx_declarations,
    ingest_quad_source_alignments,
    run_convex_intake,
    save_graph_gz,
)

ROOT = Path(__file__).resolve().parents[1]
ALIGNMENTS_PATH = ROOT / "formal" / "convex_alignments_v0_14.json"
BASE_GRAPH_PATH = ROOT / "artifacts" / "tri_source_v0_13" / "mapeogeo_v0_13_graph.json.gz"
OUTPUT_DIR = ROOT / "artifacts" / "convex_v0_14"


def test_cvx_declaration_dataclass():
    """Verify CvxDeclaration dataclass and zero-prose serialization."""
    decl = CvxDeclaration(
        node_id="srcdecl:cvx:section:2_1",
        source_id="BOYD_VANDENBERGHE_CVX_2004",
        label="Convex Optimization 2.1 Affine and convex sets",
        decl_type="SECTION",
        chapter_section="Chapter 2",
        page=21,
        statement_sha256="abc123hash",
        char_count=150,
        structural_refs=["2.2"],
        representation_profile={
            "eo_tags": ["convex_combination"],
            "geo_tags": ["hyperplane", "convex_set"],
            "direct_status": "DUAL_DIRECT",
            "representation_kinds": ["abstract", "geometric"],
            "diversity_count": 2,
        },
    )
    d = decl.to_dict()
    assert d["node_id"] == "srcdecl:cvx:section:2_1"
    assert d["source_id"] == "BOYD_VANDENBERGHE_CVX_2004"
    assert d["page"] == 21
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_detector_bank():
    """Verify EO, GEO, and representation kind detector regex rules."""
    text_sample = (
        "An affine set is a set containing the line through any two distinct points in the set. "
        "A convex set contains the line segment between any two points. A hyperplane is an affine subspace."
    )
    title_sample = "Affine and convex sets"
    profile = detect_cvx_representation_profile(text_sample, title_sample)

    assert "affine_combination" in profile["eo_tags"] or "convex_combination" in profile["eo_tags"]
    assert "hyperplane" in profile["geo_tags"] or "convex_set" in profile["geo_tags"]
    assert profile["direct_status"] == "DUAL_DIRECT"
    assert "geometric" in profile["representation_kinds"] or "abstract" in profile["representation_kinds"]
    assert profile["diversity_count"] >= 1


def test_mock_cvx_declarations():
    """Verify deterministic mock generator provides at least 35 rich declarations."""
    mock_decls = generate_mock_cvx_declarations()
    assert len(mock_decls) >= 35

    chap_names = {d.chapter_section for d in mock_decls}
    assert "Chapter 2" in chap_names
    assert "Chapter 3" in chap_names
    assert "Chapter 4" in chap_names
    assert "Chapter 5" in chap_names
    assert "Chapter 6" in chap_names
    assert "Chapter 8" in chap_names

    for d in mock_decls:
        assert d.node_id.startswith("srcdecl:cvx:section:")
        assert d.statement_sha256
        assert d.char_count > 0
        assert d.representation_profile["diversity_count"] >= 1


def test_alignments_schema():
    """Verify formal/convex_alignments_v0_14.json schema and invariants."""
    assert ALIGNMENTS_PATH.exists()
    data = json.loads(ALIGNMENTS_PATH.read_text(encoding="utf-8"))

    assert data.get("stage") == "v0.14"
    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 60

    valid_corpora = {"GALLIER", "AXLER", "VMLS", "CVX"}
    valid_rep_kinds = {"abstract", "algebraic", "geometric", "computational", "formal", "applied"}

    for co in canonical_objects:
        assert "id" in co
        assert "name" in co
        assert "domain" in co
        rep_kinds = co.get("representation_kinds", [])
        assert len(rep_kinds) >= 1
        for rk in rep_kinds:
            assert rk in valid_rep_kinds

        alignments = co.get("alignments", [])
        assert len(alignments) >= 1
        for al in alignments:
            assert al["corpus"] in valid_corpora
            assert "source" in al


def test_convex_intake_mock_pipeline(tmp_path: Path):
    """Run intake pipeline on mock declarations and verify output properties."""
    out_dir = tmp_path / "artifacts" / "convex_v0_14"
    graph, metrics, summary = run_convex_intake(
        base_graph_path=BASE_GRAPH_PATH,
        alignments_path=ALIGNMENTS_PATH,
        out_dir=out_dir,
        use_mock=True,
    )

    assert metrics["N_source_total"] >= 350
    assert metrics["source_breakdown"]["S_D_cvx"] >= 35
    assert metrics["N_canonical_total"] >= 60
    assert metrics["N_2_source_bridges"] >= 40
    assert metrics["N_3_source_bridges"] >= 20
    assert metrics["N_4_source_bridges"] >= 8
    assert metrics["D_domains_count"] >= 3
    assert metrics["representation_diversity"]["average_richness_r_bar"] >= 2.5
    assert metrics["edges_summary"]["SAME_SEMANTICS_bridges"] >= 200

    out_graph = out_dir / "mapeogeo_v0_14_graph.json.gz"
    assert out_graph.exists()

    # Verify zero-prose persistence in emitted graph
    with gzip.open(out_graph, "rt", encoding="utf-8") as f:
        saved_graph = json.load(f)
    for node in saved_graph["nodes"]:
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            assert forbidden not in node
            assert forbidden not in node.get("attributes", {})
