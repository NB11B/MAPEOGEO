"""Endpoint-bound Farkas semantic-contract overlay for the MAPEOGEO foundation backfill.

The sealed graph is never rewritten. Contracts are built from:
- exact pre-overlay node identities;
- exact rational Farkas certificates (matrix, bounds, target_coefficients, target_bound, multipliers);
- explicit finite replay payloads;
and applied only in memory.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


CONTRACT_SCHEMA = "mapeogeo.endpoint-semantic-contract.v1"
OVERLAY_SCHEMA = "mapeogeo.endpoint-semantic-overlay.v1"


@dataclass(frozen=True)
class FarkasContractSpec:
    contract_id: str
    premise_id: str
    conclusion_id: str
    semantic_id: str
    semantic_object: str
    declared_contract: str
    payload: Mapping[str, Any]


FARKAS_SPECS = (
    FarkasContractSpec(
        "mapeogeo.farkas.logic.vector_space.v1",
        "canonical:foundation:logic:propositional_calculus",
        "canonical:linear_algebra:vector_space",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "polyhedral implication from boolean logic hypercube to finite vector space cone",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [-1, 0], [0, 1], [0, -1]],
            "bounds": [1, 0, 1, 0],
            "target_coefficients": [1, 2],
            "target_bound": 3,
            "multipliers": [1, 0, 2, 0],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.logic.topological_space.v1",
        "canonical:foundation:logic:propositional_calculus",
        "canonical:topology:topological_space",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "polyhedral implication from boolean algebra to finite topology basis cone",
        {
            "certificate_type": "implication",
            "matrix": [[1, 1], [1, 0], [0, 1]],
            "bounds": [2, 1, 1],
            "target_coefficients": [2, 1],
            "target_bound": 3,
            "multipliers": [1, 1, 0],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.logic.sigma_algebra.v1",
        "canonical:foundation:logic:propositional_calculus",
        "canonical:measure:sigma_algebra",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "polyhedral implication from boolean ring to finite measurable event cone",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [0, 1], [-1, 0], [0, -1]],
            "bounds": [1, 1, 0, 0],
            "target_coefficients": [1, 1],
            "target_bound": 2,
            "multipliers": [1, 1, 0, 0],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.set.convex_set.v1",
        "canonical:foundation:set:set_operations_and_boolean_algebra",
        "canonical:convex:convex_set",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "polyhedral halfspace intersection implies supporting bounding inequality",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [0, 1], [1, 2]],
            "bounds": [1, 2, 4],
            "target_coefficients": [3, 4],
            "target_bound": 9,
            "multipliers": [1, 0, 2],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.geom.convex_set.v1",
        "canonical:foundation:geom:euclidean_space_and_metrics",
        "canonical:convex:convex_set",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "Euclidean metric polytope containment implies bounded convex support",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1]],
            "bounds": [2, 0, 2, 0, 3],
            "target_coefficients": [2, 3],
            "target_bound": 8,
            "multipliers": [0, 0, 1, 0, 2],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.geom.norm_and_distance.v1",
        "canonical:foundation:geom:euclidean_space_and_metrics",
        "canonical:linear_algebra:norm_and_distance",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "Euclidean norm unit ball polyhedral approximation bounding inequality",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [-1, 0], [0, 1], [-1, -1]],
            "bounds": [1, 1, 2, 0],
            "target_coefficients": [1, 2],
            "target_bound": 5,
            "multipliers": [1, 0, 2, 0],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.geom.linear_program.v1",
        "canonical:foundation:geom:euclidean_space_and_metrics",
        "canonical:optimization:linear_program",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "Euclidean polyhedral feasibility implies bounded linear objective bound",
        {
            "certificate_type": "implication",
            "matrix": [[2, 1], [1, 2], [1, 0]],
            "bounds": [4, 5, 2],
            "target_coefficients": [3, 3],
            "target_bound": 9,
            "multipliers": [1, 1, 0],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.rel.convex_set.v1",
        "canonical:foundation:rel:orders_posets_and_lattices",
        "canonical:convex:convex_set",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "poset cone ordering implies non-negative dual cone certificate",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [0, 1], [1, 1]],
            "bounds": [0, 0, 0],
            "target_coefficients": [3, 5],
            "target_bound": 0,
            "multipliers": [0, 2, 3],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.seq.convex_set.v1",
        "canonical:foundation:seq:order_bounds_and_absolute_value",
        "canonical:convex:convex_set",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "order bound interval intersection implies convex bounding inequality",
        {
            "certificate_type": "implication",
            "matrix": [[1, 0], [-1, 0], [0, 1], [0, -1]],
            "bounds": [3, 1, 4, 2],
            "target_coefficients": [2, 1],
            "target_bound": 10,
            "multipliers": [2, 0, 1, 0],
        },
    ),
    FarkasContractSpec(
        "mapeogeo.farkas.calc.convex_function.v1",
        "canonical:foundation:calc:mean_value_theorems_and_extrema",
        "canonical:convex:convex_function",
        "GFY.FARKAS_IMPLICATION.v1",
        "Farkas polyhedral implication",
        "first-order Taylor subgradient polyhedral epigraph implication",
        {
            "certificate_type": "implication",
            "matrix": [[1, -1], [-1, -1], [2, 1]],
            "bounds": [0, 0, 3],
            "target_coefficients": [2, 0],
            "target_bound": 6,
            "multipliers": [0, 2, 2],
        },
    ),
)


class FarkasContractError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _base_node_identity_sha256(node: Mapping[str, Any]) -> str:
    cleaned = copy.deepcopy(dict(node))
    attrs = cleaned.get("attributes")
    if isinstance(attrs, dict):
        attrs.pop("semantic_contracts", None)
    return hashlib.sha256(_canonical_bytes(cleaned)).hexdigest()


def _sha256(value: Any, *, domain: str) -> str:
    return hashlib.sha256(
        domain.encode("utf-8") + b"\0" + _canonical_bytes(value)
    ).hexdigest()


def build_farkas_endpoint_overlay(graph: Mapping[str, Any]) -> dict[str, Any]:
    nodes = {
        str(node["id"]): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }

    contracts = []
    for spec in FARKAS_SPECS:
        if spec.premise_id not in nodes:
            raise FarkasContractError(f"premise node missing: {spec.premise_id}")
        if spec.conclusion_id not in nodes:
            raise FarkasContractError(f"conclusion node missing: {spec.conclusion_id}")

        premise_hash = _base_node_identity_sha256(nodes[spec.premise_id])
        conclusion_hash = _base_node_identity_sha256(nodes[spec.conclusion_id])

        endpoint_hashes = {
            "premise": {
                "id": spec.premise_id,
                "base_node_identity_sha256": premise_hash,
            },
            "conclusion": {
                "id": spec.conclusion_id,
                "base_node_identity_sha256": conclusion_hash,
            },
        }
        payload = copy.deepcopy(dict(spec.payload))
        payload_sha = _sha256(
            payload,
            domain="mapeogeo-endpoint-semantic-payload-v1",
        )
        evidence = {
            "declared_contract": spec.declared_contract,
            "status": "PASS",
            "evidence_class": "EXACT_FARKAS_IMPLICATION",
        }
        body = {
            "schema": CONTRACT_SCHEMA,
            "contract_id": spec.contract_id,
            "semantic_id": spec.semantic_id,
            "semantic_object": spec.semantic_object,
            "endpoints": endpoint_hashes,
            "evidence": evidence,
            "semantic_payload": payload,
            "semantic_payload_sha256": payload_sha,
        }
        contract = dict(body)
        contract["contract_digest"] = _sha256(
            body,
            domain="mapeogeo-endpoint-semantic-contract-v1",
        )
        contracts.append(contract)

    overlay_body = {
        "schema": OVERLAY_SCHEMA,
        "base_test_id": "mapeogeo.farkas.backfill.batch1",
        "contracts": contracts,
    }
    overlay = dict(overlay_body)
    overlay["overlay_digest"] = _sha256(
        overlay_body,
        domain="mapeogeo-endpoint-semantic-overlay-v1",
    )
    return overlay


def apply_farkas_endpoint_overlay(
    graph: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    enriched = copy.deepcopy(dict(graph))
    nodes = {
        str(node["id"]): node
        for node in enriched.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }

    overlay_body = dict(overlay)
    overlay_digest = overlay_body.pop("overlay_digest", None)
    if not isinstance(overlay_digest, str):
        raise FarkasContractError("overlay digest missing")
    if _sha256(
        overlay_body,
        domain="mapeogeo-endpoint-semantic-overlay-v1",
    ) != overlay_digest:
        raise FarkasContractError("overlay digest mismatch")
    if overlay_body.get("schema") != OVERLAY_SCHEMA:
        raise FarkasContractError("unsupported overlay schema")

    for contract in overlay_body.get("contracts", []):
        if not isinstance(contract, dict):
            raise FarkasContractError("malformed endpoint contract")
        contract_body = dict(contract)
        contract_digest = contract_body.pop("contract_digest", None)
        if not isinstance(contract_digest, str):
            raise FarkasContractError("contract digest missing")
        if _sha256(
            contract_body,
            domain="mapeogeo-endpoint-semantic-contract-v1",
        ) != contract_digest:
            raise FarkasContractError("contract digest mismatch")

        semantic_id = str(contract["semantic_id"])
        payload = copy.deepcopy(contract["semantic_payload"])
        payload_sha = str(contract["semantic_payload_sha256"])
        if _sha256(
            payload,
            domain="mapeogeo-endpoint-semantic-payload-v1",
        ) != payload_sha:
            raise FarkasContractError("semantic payload digest mismatch")

        for role, endpoint in contract["endpoints"].items():
            node_id = str(endpoint["id"])
            if node_id not in nodes:
                raise FarkasContractError(f"overlay endpoint missing: {node_id}")
            actual_base_hash = _base_node_identity_sha256(nodes[node_id])
            expected_base_hash = str(endpoint["base_node_identity_sha256"])
            if actual_base_hash != expected_base_hash:
                raise FarkasContractError(
                    f"endpoint identity changed before overlay: {node_id}"
                )

            attrs = nodes[node_id].setdefault("attributes", {})
            if not isinstance(attrs, dict):
                raise FarkasContractError(
                    f"endpoint attributes are not a mapping: {node_id}"
                )
            contracts = attrs.setdefault("semantic_contracts", [])
            record = {
                "schema": contract["schema"],
                "contract_id": contract["contract_id"],
                "contract_digest": contract_digest,
                "semantic_id": semantic_id,
                "semantic_object": contract["semantic_object"],
                "role": role,
                "base_node_identity_sha256": expected_base_hash,
                "endpoints": copy.deepcopy(contract["endpoints"]),
                "semantic_payload": payload,
                "semantic_payload_sha256": payload_sha,
                "evidence": copy.deepcopy(contract["evidence"]),
                "binding_mode": "ENDPOINT_CONTRACT_BOUND",
            }
            if record not in contracts:
                contracts.append(record)

    return enriched
