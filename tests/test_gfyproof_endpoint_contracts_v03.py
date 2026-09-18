from __future__ import annotations

import copy
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from mapeogeo.semantic_contracts_v03 import (
    EndpointContractError,
    FIXTURE_SPECS,
    apply_endpoint_overlay,
    build_endpoint_overlay,
)


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "gallier_quaintance_graph_v0_3.json.gz"
CURRENT_GRAPH_PATH = ROOT / "data" / "mapeogeo_v0_11_graph.json.gz"
RESULTS_PATH = ROOT / "data" / "gallier_quaintance_results_v0_3.json"


def _load_graph() -> dict:
    with gzip.open(GRAPH_PATH, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _load_results() -> dict:
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def test_endpoint_overlay_builds_from_frozen_v03_graph() -> None:
    graph = _load_graph()
    results = _load_results()
    overlay = build_endpoint_overlay(graph, results)

    assert overlay["schema"] == "mapeogeo.endpoint-semantic-overlay.v1"
    assert overlay["base_test_id"] == "MAPEOGEO-CROSS-DOMAIN-V0.3"
    assert len(overlay["contracts"]) == len(FIXTURE_SPECS) == 8

    by_case = {
        contract["semantic_object"]: contract
        for contract in overlay["contracts"]
    }
    assert set(by_case) == {
        "Cyclic group composition",
        "SO(3) rotation",
        "Eigenpairs",
        "Graph Laplacian",
        "Projective homogeneous equivalence",
        "Linear-programming duality",
        "Orthogonal projection",
        "Gaussian positive-definite kernel",
    }
    assert all(
        contract["evidence"]["status"] == "PASS"
        for contract in overlay["contracts"]
    )
    assert all(
        contract["evidence"]["eo_view"]
        and contract["evidence"]["geo_view"]
        and contract["evidence"]["declared_contract"]
        for contract in overlay["contracts"]
    )


def test_overlay_enriches_exactly_twenty_four_fixture_nodes() -> None:
    graph = _load_graph()
    overlay = build_endpoint_overlay(graph, _load_results())
    enriched = apply_endpoint_overlay(graph, overlay)

    before = {
        node["id"]: node
        for node in graph["nodes"]
    }
    after = {
        node["id"]: node
        for node in enriched["nodes"]
    }

    changed = []
    for node_id, node in after.items():
        if node != before[node_id]:
            changed.append(node_id)

    expected = set()
    for spec in FIXTURE_SPECS:
        expected.update(
            {
                f"op:eo:test:{spec.test_index:02d}",
                f"op:geo:test:{spec.test_index:02d}",
                f"obj:test:{spec.test_index:02d}",
            }
        )
    assert set(changed) == expected

    for spec in FIXTURE_SPECS:
        ids = [
            f"op:eo:test:{spec.test_index:02d}",
            f"op:geo:test:{spec.test_index:02d}",
            f"obj:test:{spec.test_index:02d}",
        ]
        records = [
            after[node_id]["attributes"]["semantic_contracts"][0]
            for node_id in ids
        ]
        assert {record["semantic_id"] for record in records} == {
            spec.semantic_id
        }
        assert len({record["contract_digest"] for record in records}) == 1
        assert len({record["semantic_payload_sha256"] for record in records}) == 1
        assert {record["binding_mode"] for record in records} == {
            "ENDPOINT_CONTRACT_BOUND"
        }
        assert {record["role"] for record in records} == {
            "eo",
            "geo",
            "object",
        }


def test_endpoint_identity_mutation_invalidates_overlay() -> None:
    graph = _load_graph()
    overlay = build_endpoint_overlay(graph, _load_results())
    mutated = copy.deepcopy(graph)

    target = next(
        node
        for node in mutated["nodes"]
        if node["id"] == "op:eo:test:05"
    )
    target["label"] = str(target.get("label", "")) + " MUTATED"

    with pytest.raises(
        EndpointContractError,
        match="endpoint identity changed",
    ):
        apply_endpoint_overlay(mutated, overlay)


def test_result_row_mutation_prevents_contract_construction() -> None:
    graph = _load_graph()
    results = _load_results()
    mutated = copy.deepcopy(results)

    row = next(
        item
        for item in mutated["tests"]
        if item["case"] == "Eigenpairs"
    )
    row["status"] = "FAIL"

    with pytest.raises(
        EndpointContractError,
        match="semantic evidence mismatch",
    ):
        build_endpoint_overlay(graph, mutated)


def test_v03_endpoint_identities_are_preserved_in_v011() -> None:
    base = _load_graph()
    with gzip.open(CURRENT_GRAPH_PATH, "rt", encoding="utf-8") as handle:
        current = json.load(handle)

    base_nodes = {node["id"]: node for node in base["nodes"]}
    current_nodes = {node["id"]: node for node in current["nodes"]}

    for spec in FIXTURE_SPECS:
        for prefix in ("op:eo:test", "op:geo:test", "obj:test"):
            node_id = f"{prefix}:{spec.test_index:02d}"
            assert node_id in base_nodes
            assert node_id in current_nodes
            assert current_nodes[node_id] == base_nodes[node_id], node_id


def test_v03_overlay_applies_cleanly_to_v011_fixture_layer() -> None:
    base = _load_graph()
    overlay = build_endpoint_overlay(base, _load_results())
    with gzip.open(CURRENT_GRAPH_PATH, "rt", encoding="utf-8") as handle:
        current = json.load(handle)

    enriched = apply_endpoint_overlay(current, overlay)
    nodes = {node["id"]: node for node in enriched["nodes"]}

    for spec in FIXTURE_SPECS:
        for prefix in ("op:eo:test", "op:geo:test", "obj:test"):
            node_id = f"{prefix}:{spec.test_index:02d}"
            records = nodes[node_id]["attributes"]["semantic_contracts"]
            assert len(records) == 1
            assert records[0]["semantic_id"] == spec.semantic_id
            assert records[0]["binding_mode"] == "ENDPOINT_CONTRACT_BOUND"


def test_overlay_does_not_modify_sealed_graph_file() -> None:
    before = hashlib.sha256(GRAPH_PATH.read_bytes()).hexdigest()
    graph = _load_graph()
    overlay = build_endpoint_overlay(graph, _load_results())
    _ = apply_endpoint_overlay(graph, overlay)
    after = hashlib.sha256(GRAPH_PATH.read_bytes()).hexdigest()
    assert before == after
