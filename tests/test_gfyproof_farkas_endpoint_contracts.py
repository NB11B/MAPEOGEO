from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

import pytest

from mapeogeo.farkas_contracts_v1 import (
    FARKAS_SPECS,
    FarkasContractError,
    LINEAR_SEMANTICS_KEY,
    attach_source_grounded_linear_semantics,
    apply_farkas_endpoint_overlay,
    build_farkas_endpoint_overlay,
    validate_farkas_spec_semantic_binding,
)


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_GRAPH_PATH = (
    ROOT
    / "artifacts"
    / "foundation_backfill"
    / "mapeogeo_foundation_graph.json.gz"
)


def test_farkas_specs_are_source_grounded() -> None:
    assert len(FARKAS_SPECS) == 5
    for spec in FARKAS_SPECS:
        assert spec.semantic_id == "GFY.FARKAS_IMPLICATION.v1"
        assert spec.contract_id.startswith("mapeogeo.farkas.")
        assert "matrix" in spec.payload
        assert "bounds" in spec.payload
        assert "multipliers" in spec.payload
        assert len(spec.source_evidence) >= 1


def test_real_foundation_graph_rejects_unbound_farkas_overlay() -> None:
    if not FOUNDATION_GRAPH_PATH.exists():
        pytest.skip("Foundation graph not present")

    with gzip.open(
        FOUNDATION_GRAPH_PATH,
        "rt",
        encoding="utf-8",
    ) as handle:
        graph = json.load(handle)

    with pytest.raises(
        FarkasContractError,
        match="missing source-bound Farkas premise semantics",
    ):
        build_farkas_endpoint_overlay(graph)


def test_real_foundation_graph_accepts_source_grounded_farkas_overlay() -> None:
    if not FOUNDATION_GRAPH_PATH.exists():
        pytest.skip("Foundation graph not present")

    with gzip.open(
        FOUNDATION_GRAPH_PATH,
        "rt",
        encoding="utf-8",
    ) as handle:
        graph = json.load(handle)

    graph_with_semantics = attach_source_grounded_linear_semantics(graph)
    overlay = build_farkas_endpoint_overlay(graph_with_semantics)
    assert overlay["schema"] == "mapeogeo.endpoint-semantic-overlay.v1"
    assert len(overlay["contracts"]) == 5

    enriched = apply_farkas_endpoint_overlay(graph_with_semantics, overlay)
    nodes = {n["id"]: n for n in enriched.get("nodes", []) if n.get("id")}
    for spec in FARKAS_SPECS:
        p_contracts = nodes[spec.premise_id]["attributes"]["semantic_contracts"]
        c_contracts = nodes[spec.conclusion_id]["attributes"]["semantic_contracts"]
        assert any(c["contract_id"] == spec.contract_id for c in p_contracts)
        assert any(c["contract_id"] == spec.contract_id for c in c_contracts)


def test_source_hashed_linear_semantics_can_bind_one_farkas_spec() -> None:
    spec = FARKAS_SPECS[0]

    premise_source = {
        "id": "src:test:premise",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "a" * 64},
    }
    conclusion_source = {
        "id": "src:test:conclusion",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "b" * 64},
    }

    premise = {
        "id": spec.premise_id,
        "type": "CANONICAL_OBJECT",
        "attributes": {
            "is_foundation": True,
            LINEAR_SEMANTICS_KEY: [
                {
                    "semantic_id": spec.semantic_id,
                    "role": "premise",
                    "declared_contract": spec.declared_contract,
                    "variables": ["x1", "x2"],
                    "matrix": copy.deepcopy(spec.payload["matrix"]),
                    "bounds": copy.deepcopy(spec.payload["bounds"]),
                    "source_evidence": [
                        {
                            "subject_id": premise_source["id"],
                            "statement_sha256": "a" * 64,
                        }
                    ],
                }
            ],
        },
    }
    conclusion = {
        "id": spec.conclusion_id,
        "type": "CANONICAL_OBJECT",
        "attributes": {
            "is_foundation": False,
            LINEAR_SEMANTICS_KEY: [
                {
                    "semantic_id": spec.semantic_id,
                    "role": "conclusion",
                    "declared_contract": spec.declared_contract,
                    "variables": ["x1", "x2"],
                    "target_coefficients": copy.deepcopy(
                        spec.payload["target_coefficients"]
                    ),
                    "target_bound": copy.deepcopy(
                        spec.payload["target_bound"]
                    ),
                    "source_evidence": [
                        {
                            "subject_id": conclusion_source["id"],
                            "statement_sha256": "b" * 64,
                        }
                    ],
                }
            ],
        },
    }

    graph = {
        "nodes": [
            premise_source,
            conclusion_source,
            premise,
            conclusion,
        ],
        "edges": [],
    }

    binding = validate_farkas_spec_semantic_binding(graph, spec)
    assert binding["variables"] == ["x1", "x2"]

    premise["attributes"][LINEAR_SEMANTICS_KEY][0]["bounds"][0] = 999
    with pytest.raises(
        FarkasContractError,
        match="premise semantics do not match certificate",
    ):
        validate_farkas_spec_semantic_binding(graph, spec)
