"""Deterministic artifact serialization, SHA-256 sealing, and MAPEOGEO graph emission."""

from __future__ import annotations

from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from shapely.geometry.base import BaseGeometry
import sympy as sp

from mapeogeo.pct.chain import (
    betti_numbers,
    boundary_matrix,
    euler_from_chains,
    euler_from_homology,
    simplices_by_degree,
)
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.maps import check_chain_map, triangle_subdivision_map
from mapeogeo.pct.models import (
    Applicability,
    ChainMap,
    CoefficientField,
    FiniteComplex,
    Simplex,
    Verdict,
    VerdictRecord,
)
from mapeogeo.pct.persistence import (
    FilteredSimplex,
    PersistencePair,
    pairing_ledger,
    persistent_pairs_gf2,
)
from mapeogeo.pct.probes import line_response_field, support_samples


FORBIDDEN_GRAPH_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}


def _pct_json_default(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, Simplex):
        return {"vertices": list(obj.vertices), "dimension": obj.dimension}
    elif isinstance(obj, FiniteComplex):
        return {
            "complex_id": obj.complex_id,
            "simplices": [
                {"vertices": list(s.vertices), "dimension": s.dimension}
                for s in obj.simplices
            ],
            "metadata": obj.metadata,
        }
    elif isinstance(obj, ChainMap):
        matrices_dict = {}
        for deg, mat in obj.matrices_by_degree.items():
            if isinstance(mat, sp.Matrix):
                matrices_dict[str(deg)] = [[int(mat[r, c]) for c in range(mat.cols)] for r in range(mat.rows)]
            else:
                matrices_dict[str(deg)] = mat
        return {
            "map_id": obj.map_id,
            "source_id": obj.source_id,
            "target_id": obj.target_id,
            "construction_method": obj.construction_method,
            "matrices_by_degree": matrices_dict,
        }
    elif isinstance(obj, VerdictRecord):
        return {
            "check_id": obj.check_id,
            "applicability": obj.applicability.value if isinstance(obj.applicability, Enum) else obj.applicability,
            "verdict": obj.verdict.value if isinstance(obj.verdict, Enum) else obj.verdict,
            "measured": obj.measured,
            "expected": obj.expected,
            "tolerance_or_exact_rule": obj.tolerance_or_exact_rule,
            "provenance": obj.provenance,
        }
    elif isinstance(obj, PersistencePair):
        return {
            "dimension": obj.dimension,
            "birth": obj.birth,
            "birth_simplex": list(obj.birth_simplex.vertices),
            "death": obj.death,
            "death_simplex": list(obj.death_simplex.vertices) if obj.death_simplex else None,
            "essential": obj.essential,
        }
    elif isinstance(obj, FilteredSimplex):
        return {"simplex": list(obj.simplex.vertices), "filtration": obj.filtration}
    elif isinstance(obj, sp.Matrix):
        return [[int(obj[r, c]) for c in range(obj.cols)] for r in range(obj.rows)]
    elif isinstance(obj, BaseGeometry):
        return {
            "geom_type": obj.geom_type,
            "area": float(obj.area),
            "length": float(obj.length),
            "is_empty": obj.is_empty,
        }
    elif isinstance(obj, set):
        return sorted(list(obj))
    elif isinstance(obj, tuple):
        return list(obj)
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def canonical_json(value: Any) -> str:
    """Serialize any value to key-sorted, 2-space indented canonical JSON with trailing newline."""
    return json.dumps(value, default=_pct_json_default, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(data: bytes) -> str:
    """Compute hex SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Compute hex SHA-256 hash of a file."""
    return sha256_bytes(path.read_bytes())


def build_graph_fragment(result: dict[str, Any]) -> dict[str, Any]:
    """Emit a valid, scoped MAPEOGEO graph fragment containing PCT executable evidence."""
    run_id = result.get("run_id", "MAPEOGEO-PCT-V0.10")
    engine_validity = result.get("engine_validity", "UNKNOWN")
    scientific_result = result.get("scientific_result", "UNKNOWN")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    # Root run node
    run_node_id = f"pct_run:{run_id}"
    nodes.append({
        "id": run_node_id,
        "type": "PCT_RUN",
        "label": f"PCT Execution {run_id}",
        "views": ["EO", "GEO"],
        "attributes": {
            "engine_validity": engine_validity,
            "scientific_result": scientific_result,
            "stage": result.get("stage", "v0.10"),
        },
    })

    # Certificate node
    cert_node_id = f"pct_cert:{run_id}"
    nodes.append({
        "id": cert_node_id,
        "type": "CERTIFICATE",
        "label": f"PCT Executable Evidence Certificate {run_id}",
        "certificate_class": "EXECUTABLE_EVIDENCE_PCT",
        "views": ["EO", "GEO"],
        "attributes": {
            "engine_validity": engine_validity,
            "scientific_result": scientific_result,
        },
    })
    edges.append({
        "id": f"edge:{run_node_id}->{cert_node_id}",
        "source": run_node_id,
        "target": cert_node_id,
        "type": "ATTESTS",
        "views": ["EO", "GEO"],
    })

    # Nodes for each scientific test
    for s_id, s_rec in result.get("scientific_tests", {}).items():
        test_node_id = f"pct_test:{s_id}"
        nodes.append({
            "id": test_node_id,
            "type": "PCT_OBSERVATION",
            "label": f"PCT Test {s_id}",
            "views": ["EO", "GEO"],
            "attributes": {
                "check_id": s_rec.check_id if hasattr(s_rec, "check_id") else s_rec.get("check_id"),
                "verdict": s_rec.verdict.value if hasattr(s_rec, "verdict") else str(s_rec.get("verdict")),
            },
        })
        edges.append({
            "id": f"edge:{run_node_id}->{test_node_id}",
            "source": run_node_id,
            "target": test_node_id,
            "type": "CONTAINS_OBSERVATION",
            "views": ["EO", "GEO"],
        })

    # Nodes for chain maps
    map_node_id = "pct_map:triangle_subdivision"
    nodes.append({
        "id": map_node_id,
        "type": "PCT_MAP",
        "label": "Triangle Barycentric Subdivision Map",
        "views": ["EO"],
        "attributes": {
            "construction": "BARYCENTRIC_SUBDIVISION_1D",
            "source": "triangle_loop",
            "target": "triangle_loop_subdivided",
        },
    })
    edges.append({
        "id": f"edge:{run_node_id}->{map_node_id}",
        "source": run_node_id,
        "target": map_node_id,
        "type": "EVALUATES_MAP",
        "views": ["EO"],
    })

    # Check for forbidden keys
    for node in nodes:
        for k in FORBIDDEN_GRAPH_KEYS:
            if k in node or k in node.get("attributes", {}):
                raise ValueError(f"Forbidden key {k} detected in graph node")

    return {
        "graph_id": "mapeogeo-pct-v0-10-fragment",
        "schema_version": "0.10",
        "required_views": ["EO", "GEO"],
        "nodes": nodes,
        "edges": edges,
    }


def write_run_artifacts(
    result: dict[str, Any],
    out_dir: Path | str,
    manifest: dict[str, Any],
) -> dict[str, str]:
    """Write all deterministic artifacts, summary, graph fragment, and hashes.json."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    (out_path / "objects").mkdir(exist_ok=True)
    (out_path / "probes").mkdir(exist_ok=True)
    (out_path / "complexes").mkdir(exist_ok=True)
    (out_path / "maps").mkdir(exist_ok=True)
    (out_path / "homology").mkdir(exist_ok=True)
    (out_path / "persistence").mkdir(exist_ok=True)
    (out_path / "geometry").mkdir(exist_ok=True)
    (out_path / "event_ledger").mkdir(exist_ok=True)
    (out_path / "reconstruction").mkdir(exist_ok=True)
    (out_path / "negative_controls").mkdir(exist_ok=True)
    (out_path / "residuals").mkdir(exist_ok=True)

    corpus = build_control_corpus()
    directions: list[float] = manifest.get("directions_radians", [k * (math.pi / 6.0) for k in range(12)])
    offsets: list[float] = manifest.get("offsets", [x / 4.0 for x in range(-16, 17)])

    # 1. manifest.json
    (out_path / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")

    # 2. validity.json
    validity_data = {
        "ENGINE_VALIDITY": result.get("engine_validity"),
        "validity_gates": result.get("validity_gates"),
    }
    (out_path / "validity.json").write_text(canonical_json(validity_data), encoding="utf-8")

    # 3. scientific_result.json
    sci_data = {
        "SCIENTIFIC_RESULT": result.get("scientific_result"),
        "scientific_tests": result.get("scientific_tests"),
        "baseline_matrix": result.get("baseline_matrix"),
        "claim_boundary": result.get("claim_boundary"),
    }
    (out_path / "scientific_result.json").write_text(canonical_json(sci_data), encoding="utf-8")

    # 4. objects/fixtures.json
    fixtures_summary: dict[str, Any] = {}
    for fid, f in corpus.items():
        fixtures_summary[fid] = {
            "fixture_id": f.fixture_id,
            "has_complex": f.complex is not None,
            "has_geometry": f.geometry is not None,
            "expected_betti": f.expected_betti,
            "expected_euler": f.expected_euler,
            "expected_area": f.expected_area,
            "expected_perimeter": f.expected_perimeter,
            "is_convex": f.is_convex,
            "applicability": f.applicability.value,
        }
    (out_path / "objects" / "fixtures.json").write_text(canonical_json(fixtures_summary), encoding="utf-8")

    # 5. probes/responses.json
    probes_data = {
        "directions": directions,
        "offsets": offsets,
        "square_support_samples": support_samples(corpus["equal_area_square"].geometry, directions),
        "triangle_support_samples": support_samples(corpus["equal_area_triangle"].geometry, directions),
        "square_line_responses": line_response_field(corpus["equal_area_square"].geometry, directions, offsets),
    }
    (out_path / "probes" / "responses.json").write_text(canonical_json(probes_data), encoding="utf-8")

    # 6. complexes/chain_data.json
    chain_data: dict[str, Any] = {}
    for fid, f in corpus.items():
        if f.complex is not None:
            deg_map = simplices_by_degree(f.complex)
            mats = {}
            for k in range(1, max(deg_map.keys()) + 1):
                bm = boundary_matrix(f.complex, k)
                mats[str(k)] = [[int(bm[r, c]) for c in range(bm.cols)] for r in range(bm.rows)]
            chain_data[fid] = {
                "dimensions": {str(k): len(simps) for k, simps in deg_map.items()},
                "boundary_matrices": mats,
                "chain_condition": result.get("validity_gates", {}).get("V1", {}).measured.get(fid, True) if hasattr(result.get("validity_gates", {}).get("V1"), "measured") else True,
            }
    (out_path / "complexes" / "chain_data.json").write_text(canonical_json(chain_data), encoding="utf-8")

    # 7. maps/chain_maps.json
    coarse = corpus["triangle_loop"].complex
    fine = corpus["triangle_loop_subdivided"].complex
    assert coarse is not None and fine is not None
    m_valid = triangle_subdivision_map(corrupt=False)
    m_corrupt = triangle_subdivision_map(corrupt=True)
    maps_data = {
        "valid_subdivision": m_valid,
        "corrupted_subdivision": m_corrupt,
    }
    (out_path / "maps" / "chain_maps.json").write_text(canonical_json(maps_data), encoding="utf-8")

    # 8. homology/betti.json
    homology_data: dict[str, Any] = {}
    for fid, f in corpus.items():
        if f.complex is not None:
            homology_data[fid] = {
                "betti_gf2": betti_numbers(f.complex, CoefficientField.GF2),
                "betti_q": betti_numbers(f.complex, CoefficientField.Q),
                "euler_chains": euler_from_chains(f.complex),
                "euler_homology": euler_from_homology(f.complex, CoefficientField.Q),
            }
    (out_path / "homology" / "betti.json").write_text(canonical_json(homology_data), encoding="utf-8")

    # 9. persistence/pairs.json
    filt_items = [
        FilteredSimplex(Simplex((0,)), 0.0),
        FilteredSimplex(Simplex((1,)), 0.0),
        FilteredSimplex(Simplex((2,)), 0.0),
        FilteredSimplex(Simplex((0, 1)), 1.0),
        FilteredSimplex(Simplex((1, 2)), 1.0),
        FilteredSimplex(Simplex((0, 2)), 1.0),
        FilteredSimplex(Simplex((0, 1, 2)), 2.0),
    ]
    pairs = persistent_pairs_gf2(filt_items)
    (out_path / "persistence" / "pairs.json").write_text(canonical_json(pairs), encoding="utf-8")

    # 10. geometry/metrics.json
    geom_data = {
        "equal_area_square": {
            "area": float(corpus["equal_area_square"].geometry.area),
            "perimeter": float(corpus["equal_area_square"].geometry.length),
        },
        "equal_area_triangle": {
            "area": float(corpus["equal_area_triangle"].geometry.area),
            "perimeter": float(corpus["equal_area_triangle"].geometry.length),
        },
        "scale_events": result.get("scale_events"),
    }
    (out_path / "geometry" / "metrics.json").write_text(canonical_json(geom_data), encoding="utf-8")

    # 11. event_ledger/events.json
    events_data = {
        "persistence_ledger": pairing_ledger(pairs),
        "scale_transitions": result.get("scale_events"),
    }
    (out_path / "event_ledger" / "events.json").write_text(canonical_json(events_data), encoding="utf-8")

    # 12. reconstruction/results.json
    (out_path / "reconstruction" / "results.json").write_text(
        canonical_json(result.get("reconstruction_results")), encoding="utf-8"
    )

    # 13. negative_controls/results.json
    (out_path / "negative_controls" / "results.json").write_text(
        canonical_json(result.get("negative_controls")), encoding="utf-8"
    )

    # 14. residuals/results.json
    res_valid = check_chain_map(coarse, fine, m_valid)
    res_corrupt = check_chain_map(coarse, fine, m_corrupt)
    residuals_data = {
        "valid_subdivision": {
            "pass": res_valid["pass"],
            "residual_nonzero_entries": res_valid["residual_nonzero_entries"],
            "nonzeros_detail": res_valid["nonzeros_detail"],
        },
        "corrupted_subdivision": {
            "pass": res_corrupt["pass"],
            "residual_nonzero_entries": res_corrupt["residual_nonzero_entries"],
            "nonzeros_detail": res_corrupt["nonzeros_detail"],
        },
    }
    (out_path / "residuals" / "results.json").write_text(
        canonical_json(residuals_data), encoding="utf-8"
    )

    # 15. pct_graph_fragment.json
    graph_fragment = build_graph_fragment(result)
    (out_path / "pct_graph_fragment.json").write_text(
        canonical_json(graph_fragment), encoding="utf-8"
    )

    # 16. summary.md
    summary_md = f"""# MAPEOGEO PCT v0.10 Run Summary

- **Run ID**: `{result.get("run_id")}`
- **Repository Commit**: `{result.get("repository_commit")}`
- **Engine Validity**: `{result.get("engine_validity")}`
- **Scientific Result**: `{result.get("scientific_result")}`

## Validity Gates (V0–V8)
| Gate | Check ID | Verdict | Rule / Tolerance |
|------|----------|---------|------------------|
"""
    for v_id in sorted(result.get("validity_gates", {}).keys()):
        g = result["validity_gates"][v_id]
        v_val = g.verdict.value if hasattr(g, "verdict") else str(g.get("verdict"))
        tol_val = g.tolerance_or_exact_rule if hasattr(g, "tolerance_or_exact_rule") else str(g.get("tolerance_or_exact_rule"))
        chk = g.check_id if hasattr(g, "check_id") else str(g.get("check_id"))
        summary_md += f"| {v_id} | `{chk}` | **{v_val}** | `{tol_val}` |\n"

    summary_md += """
## Scientific Tests (S1–S10)
| Test | Check ID | Verdict | Attribution / Result |
|------|----------|---------|----------------------|
"""
    for s_id in sorted(result.get("scientific_tests", {}).keys()):
        st = result["scientific_tests"][s_id]
        v_val = st.verdict.value if hasattr(st, "verdict") else str(st.get("verdict"))
        chk = st.check_id if hasattr(st, "check_id") else str(st.get("check_id"))
        summary_md += f"| {s_id} | `{chk}` | **{v_val}** | {st.tolerance_or_exact_rule if hasattr(st, 'tolerance_or_exact_rule') else ''} |\n"

    summary_md += f"""
## Claim Boundary
> {result.get("claim_boundary")}
"""
    (out_path / "summary.md").write_text(summary_md, encoding="utf-8")

    # 17. hashes.json (Compute SHA-256 for all generated files)
    file_hashes: dict[str, str] = {}
    for p in sorted(out_path.rglob("*")):
        if p.is_file() and p.name != "hashes.json":
            rel_name = p.relative_to(out_path).as_posix()
            file_hashes[rel_name] = sha256_file(p)

    (out_path / "hashes.json").write_text(canonical_json(file_hashes), encoding="utf-8")

    return file_hashes
