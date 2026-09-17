"""Slice 9 Tests: Cumulative Graph Assembly & Visual Interrogation Descriptors."""

import json
import pytest
from pathlib import Path
from mapeogeo.wave_f5.intake import build_wave_f5_graph, load_active_graph

FORMAL_DIR = Path(__file__).resolve().parent.parent.parent / "formal" / "wave_f5"
VISUALIZATIONS_PATH = FORMAL_DIR / "visualizations.json"
RELATIONS_PATH = FORMAL_DIR / "relations.json"


def test_visualizations_json_registered():
    assert VISUALIZATIONS_PATH.exists(), "formal/wave_f5/visualizations.json must exist"
    with open(VISUALIZATIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    views = data.get("views", [])
    assert len(views) >= 10, f"Expected at least 10 visual descriptors, found {len(views)}"
    
    # Check that required view modes and fields are present
    modes = {v.get("view_mode") for v in views}
    assert "PHASE_SPACE_GEOMETRY" in modes
    assert "SPECTRAL_PLANE" in modes
    assert "PROOF_DEPENDENCY" in modes
    assert "ERROR_ENVELOPE" in modes
    assert "OPERATOR_IMAGE" in modes

    for v in views:
        assert "view_id" in v
        assert "claim_id" in v
        assert "scope" in v
        assert "evidence_kind" in v


def test_relations_json_registered():
    assert RELATIONS_PATH.exists(), "formal/wave_f5/relations.json must exist"
    with open(RELATIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    joints = data.get("joints", [])
    assert len(joints) >= 5, f"Expected at least 5 mechanism joints, found {len(joints)}"

    for j in joints:
        assert "joint_id" in j
        assert "joint_type" in j
        assert "relationship" in j
        assert "feet" in j
        assert j["relationship"] not in ("SAME_SEMANTICS", "EQUIVALENT_TO", "IDENTICAL_TO")


def test_build_wave_f5_graph_integrity():
    graph = build_wave_f5_graph()
    assert graph["schema_version"] == "0.22"
    assert "nodes" in graph
    assert "edges" in graph
    assert "joints" in graph
    assert "visualizations" in graph

    # All nodes must have unique node_id
    node_ids = [n["node_id"] for n in graph["nodes"]]
    assert len(node_ids) == len(set(node_ids)), "Duplicate node IDs detected in cumulative graph"

    # All edges must connect existing nodes
    node_set = set(node_ids)
    for edge in graph["edges"]:
        src = edge["source"]
        tgt = edge["target"]
        assert src in node_set, f"Edge source '{src}' does not exist in graph nodes"
        assert tgt in node_set, f"Edge target '{tgt}' does not exist in graph nodes"

    # All joints feet must connect existing nodes
    for joint in graph["joints"]:
        for foot in joint["feet"]:
            fid = foot["node_id"]
            assert fid in node_set, f"Joint foot '{fid}' does not exist in graph nodes"
