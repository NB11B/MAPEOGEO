"""Cumulative Graph Assembly & Deterministic Intake for Wave F5."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FORMAL_DIR = REPO_ROOT / "formal" / "wave_f5"
BATCHES_DIR = FORMAL_DIR / "batches"


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_wave_f5_graph(
    formal_dir: Optional[Path] = None,
    batches_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Assemble cumulative active graph for Wave F5, resolving all nodes, edges, joints, and views."""
    f_dir = formal_dir or FORMAL_DIR
    b_dir = batches_dir or (f_dir / "batches")

    nodes_by_id: Dict[str, Dict[str, Any]] = {}

    # 1. Load canonical formulations
    formulations_file = f_dir / "formulations.json"
    if formulations_file.exists():
        formulations_data = load_json(formulations_file)
        formulation_list = formulations_data.get("formulations", [])
        for form in formulation_list:
            fid = form.get("canonical_id", form.get("formulation_id"))
            if not fid:
                continue
            nodes_by_id[fid] = {
                "node_id": fid,
                "title": form.get("name", form.get("canonical_name", fid)),
                "concept_family": form.get("family_code", form.get("family", "UNCLASSIFIED")),
                "category": form.get("kind", "CANONICAL_FORMULATION"),
                "scope": form.get("scope", {}),
                "source_provenance": form.get("source_bindings", form.get("source_provenance", [])),
                "metadata": {"reconciled_from": form.get("reconciled_from", [])},
            }

    # 2. Load batch items (declarations)
    if b_dir.exists():
        for b_file in sorted(b_dir.glob("batch_*.json")):
            b_data = load_json(b_file)
            decls = b_data.get("declarations", b_data.get("items", []))
            for item in decls:
                cid = item.get("declaration_id", item.get("canonical_id"))
                if cid and cid not in nodes_by_id:
                    nodes_by_id[cid] = {
                        "node_id": cid,
                        "title": item.get("name", item.get("statement", item.get("statement_summary", cid))),
                        "concept_family": item.get("family_code", item.get("family", "UNCLASSIFIED")),
                        "category": item.get("kind", item.get("item_type", "STATEMENT")),
                        "scope": item.get("scope", item.get("scope_summary", {})),
                        "source_provenance": [{"source_ref": item.get("source_key"), "locator": item.get("locator", item.get("source_locator"))}],
                        "metadata": {"batch": b_data.get("package_code", b_data.get("batch_id"))},
                    }

    # 3. Load dependencies (edges)
    dep_file = f_dir / "dependencies.json"
    edges: List[Dict[str, Any]] = []
    if dep_file.exists():
        dep_data = load_json(dep_file)
        deps = dep_data.get("dependencies", [])
        for dep in deps:
            src = dep.get("source_id", dep.get("from_node", dep.get("from_concept", dep.get("source"))))
            tgt = dep.get("target_id", dep.get("to_node", dep.get("to_concept", dep.get("target"))))
            dep_type = dep.get("dependency_type", dep.get("type", "PREREQUISITE_FOR"))
            # In Wave F5, add edge if both nodes or if target is known
            if src in nodes_by_id and tgt in nodes_by_id:
                edges.append({
                    "source": src,
                    "target": tgt,
                    "type": dep_type,
                    "description": dep.get("description", ""),
                })
            elif src in nodes_by_id:
                # If target is a historical baseline node outside F5, record as external dependency
                edges.append({
                    "source": src,
                    "target": tgt,
                    "type": dep_type,
                    "external": True,
                })

    # 4. Load joints (relations)
    rel_file = f_dir / "relations.json"
    joints: List[Dict[str, Any]] = []
    if rel_file.exists():
        rel_data = load_json(rel_file)
        raw_joints = rel_data.get("joints", [])
        for j in raw_joints:
            # Check feet resolution
            feet_resolved = all(foot.get("node_id") in nodes_by_id for foot in j.get("feet", []))
            if feet_resolved:
                joints.append(j)

    # 5. Load visual descriptors
    vis_file = f_dir / "visualizations.json"
    visualizations: List[Dict[str, Any]] = []
    if vis_file.exists():
        vis_data = load_json(vis_file)
        visualizations = vis_data.get("views", [])

    return {
        "schema_version": "0.22",
        "description": "Cumulative active graph for Wave F5 functional analysis, operator theory, and ODE flows.",
        "nodes": list(nodes_by_id.values()),
        "edges": edges,
        "joints": joints,
        "visualizations": visualizations,
        "metadata": {
            "node_count": len(nodes_by_id),
            "edge_count": len(edges),
            "joint_count": len(joints),
            "visualization_count": len(visualizations),
        },
    }


def load_active_graph() -> Dict[str, Any]:
    return build_wave_f5_graph()
