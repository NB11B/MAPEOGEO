"""Unit and integration tests for MAPEOGEO v0.15.1 Confirmatory Real Analysis expansion."""

from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.import_analysis_v0_15 import (
    FORBIDDEN_PERSISTED_KEYS,
    AnalysisDeclaration,
    detect_analysis_representation_profile,
    generate_additional_analysis_declarations,
)
from scripts.analysis_intake_v0_15_1 import (
    compute_v0_15_1_metrics,
    ingest_analysis_declarations,
    ingest_v0_15_alignments,
    run_analysis_intake_v0_15_1,
    save_graph_gz,
)

ROOT = Path(__file__).resolve().parents[1]
ALIGNMENTS_PATH = ROOT / "formal" / "analysis_alignments_v0_15.json"
BASE_GRAPH_PATH = ROOT / "artifacts" / "convex_v0_14" / "mapeogeo_v0_14_graph.json.gz"
OUTPUT_DIR = ROOT / "artifacts" / "analysis_v0_15_1"


def ensure_base_graph_exists():
    """Ensure predecessor graph chain exists, reconstructing if absent."""
    if not BASE_GRAPH_PATH.exists():
        reconstruct_script = ROOT / "scripts" / "reconstruct_pipeline.py"
        res = subprocess.run(
            [sys.executable, str(reconstruct_script), "--target-stage", "v0.14"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"Failed to reconstruct base graph: {res.stderr}"
    assert BASE_GRAPH_PATH.exists()


def test_analysis_declaration_dataclass():
    """Verify AnalysisDeclaration dataclass and zero-prose serialization."""
    decl = AnalysisDeclaration(
        node_id="srcdecl:gallier:chapter:39",
        source_id="GALLIER_QUAINTANCE_2020",
        label="Gallier Chapter 39 Differential Calculus in Normed Spaces",
        decl_type="CHAPTER",
        chapter_section="Chapter 39",
        page=900,
        statement_sha256="abc123analysis",
        char_count=200,
        structural_refs=[],
        representation_profile={
            "eo_tags": ["derivative", "jacobian", "chain_rule"],
            "geo_tags": ["level_set"],
            "direct_status": "DUAL_DIRECT",
            "representation_kinds": ["abstract", "algebraic", "geometric", "computational"],
            "diversity_count": 4,
        },
    )
    d = decl.to_dict()
    assert d["node_id"] == "srcdecl:gallier:chapter:39"
    assert d["source_id"] == "GALLIER_QUAINTANCE_2020"
    for forbidden in FORBIDDEN_PERSISTED_KEYS:
        assert forbidden not in d


def test_calculus_detector_bank():
    """Verify calculus EO, GEO, and representation kind detector regex rules."""
    text_sample = (
        "The Fréchet derivative Df(x) is a bounded linear map approximating f near x. "
        "The Jacobian matrix represents Df(x) in coordinates. The Hessian matrix is symmetric by Schwarz's theorem. "
        "Critical points satisfy grad f(x*) = 0, and Newton's method algorithms compute descent steps."
    )
    title_sample = "Differential Calculus and Extrema"
    profile = detect_analysis_representation_profile(text_sample, title_sample)

    assert "derivative" in profile["eo_tags"] or "jacobian" in profile["eo_tags"]
    assert "hessian" in profile["eo_tags"] or "critical_point" in profile["eo_tags"]
    assert "algebraic" in profile["representation_kinds"]
    assert "computational" in profile["representation_kinds"]
    assert profile["diversity_count"] >= 2


def test_alignments_schema_v0_15_1():
    """Verify formal/analysis_alignments_v0_15.json schema and invariants."""
    assert ALIGNMENTS_PATH.exists()
    data = json.loads(ALIGNMENTS_PATH.read_text(encoding="utf-8"))

    canonical_objects = data.get("canonical_objects", [])
    assert len(canonical_objects) >= 85

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


def test_confirmatory_analysis_intake_pipeline(tmp_path: Path):
    """Run confirmatory analysis intake pipeline and verify output properties."""
    ensure_base_graph_exists()

    out_dir = tmp_path / "artifacts" / "analysis_v0_15_1"
    graph, metrics, summary = run_analysis_intake_v0_15_1(
        base_graph_path=BASE_GRAPH_PATH,
        alignments_path=ALIGNMENTS_PATH,
        out_dir=out_dir,
    )

    assert metrics["N_source_total"] >= 400
    assert metrics["N_canonical_total"] >= 85
    assert metrics["N_2_source_bridges"] >= 45
    assert metrics["N_3_source_bridges"] >= 30
    assert metrics["N_4_source_bridges"] >= 8
    assert metrics["D_domains_count"] >= 4
    assert metrics["representation_diversity"]["average_richness_r_bar"] >= 2.75
    assert metrics["edges_summary"]["SAME_SEMANTICS_bridges"] >= 300
    assert metrics["edges_summary"]["SCOPED_OVERLAP_bridges"] >= 20
    assert metrics["edges_summary"]["total_cross_source_bridges"] >= 400

    out_graph = out_dir / "mapeogeo_v0_15_1_graph.json.gz"
    assert out_graph.exists()

    # Verify zero-prose persistence in emitted graph
    with gzip.open(out_graph, "rt", encoding="utf-8") as f:
        saved_graph = json.load(f)
    for node in saved_graph["nodes"]:
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            assert forbidden not in node
            assert forbidden not in node.get("attributes", {})
