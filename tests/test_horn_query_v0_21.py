from __future__ import annotations

import json
from pathlib import Path
from scripts.horn_query_v0_21 import execute_horn_query, load_horn_query_spec

ROOT = Path(__file__).resolve().parents[1]


def test_horn_query_preregistration_spec():
    spec_file = ROOT / "formal" / "horn_query_v0_21.json"
    assert spec_file.is_file(), "formal/horn_query_v0_21.json missing"

    spec = load_horn_query_spec(spec_file)
    assert spec["betweenness_threshold"] == 0.05
    assert spec["view_shear_threshold"] == 0.5
    assert spec["null_model_trials"] == 100
    assert spec["mutation_policy"] == "EVIDENCE_ONLY_ZERO_GRAPH_MUTATION"


def test_horn_query_execution_is_evidence_only():
    # Execute query on mock graph
    mock_nodes = [
        {"id": "n1", "type": "DECLARATION", "attributes": {"independent_profile": {"direct_status": "EO_ONLY_DIRECT"}}},
        {"id": "n2", "type": "DECLARATION", "attributes": {"independent_profile": {"direct_status": "DUAL_DIRECT"}}},
        {"id": "n3", "type": "DECLARATION", "attributes": {"independent_profile": {"direct_status": "GEO_ONLY_DIRECT"}}},
    ]
    mock_edges = [
        {"id": "e1", "source": "n1", "target": "n2", "type": "DEPENDS_ON"},
        {"id": "e2", "source": "n2", "target": "n3", "type": "DEPENDS_ON"},
    ]
    mock_graph = {"nodes": mock_nodes, "edges": mock_edges}

    result = execute_horn_query(mock_graph)
    assert result.mutated_edges_count == 0
    assert result.mutated_nodes_count == 0
    assert result.evidence_only is True
    assert len(result.bridge_candidates) >= 0
