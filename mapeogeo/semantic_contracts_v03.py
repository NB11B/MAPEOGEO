"""Endpoint-bound semantic-contract overlay for the frozen MAPEOGEO v0.3 fixtures.

The sealed graph is never rewritten. Contracts are built from:
- exact pre-overlay node identities;
- the accepted v0.3 result row;
- an explicit finite replay payload;
and applied only in memory.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.compute_foundation_depth import node_identity_sha256


CONTRACT_SCHEMA = "mapeogeo.endpoint-semantic-contract.v1"
OVERLAY_SCHEMA = "mapeogeo.endpoint-semantic-overlay.v1"


@dataclass(frozen=True)
class FixtureContractSpec:
    test_index: int
    case: str
    chapter: int
    semantic_id: str
    payload: Mapping[str, Any]


FIXTURE_SPECS = (
    FixtureContractSpec(
        1,
        "Cyclic group composition",
        2,
        "GFY.CYCLIC_GROUP_COMPOSITION.v1",
        {
            "modulus": 17,
            "order": 16,
            "generator": 3,
            "exp_a": 5,
            "val_a": 5,
            "exp_b": 7,
            "val_b": 11,
            "exp_sum": 12,
            "val_product": 4,
        },
    ),
    FixtureContractSpec(
        5,
        "SO(3) rotation",
        16,
        "GFY.SO3_ROTATION.v1",
        {
            "matrix": [
                [0.0, -1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            "tolerance": 1e-6,
        },
    ),
    FixtureContractSpec(
        6,
        "Eigenpairs",
        15,
        "GFY.EIGENPAIR_RESIDUAL.v1",
        {
            "matrix": [[2.0, 1.0], [1.0, 2.0]],
            "eigenpairs": [
                {"value": 3.0, "vector": [1.0, 1.0]},
                {"value": 1.0, "vector": [1.0, -1.0]},
            ],
            "tolerance": 1e-6,
        },
    ),
    FixtureContractSpec(
        18,
        "Orthogonal projection",
        48,
        "GFY.ORTHOGONAL_PROJECTION.v1",
        {
            "matrix": [[0.5, 0.5], [0.5, 0.5]],
            "test_vector": [3.0, 1.0],
            "tolerance": 1e-6,
        },
    ),
)


class EndpointContractError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any, *, domain: str) -> str:
    return hashlib.sha256(
        domain.encode("utf-8") + b"\0" + _canonical_bytes(value)
    ).hexdigest()


def _result_rows(results: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = results.get("tests", [])
    if not isinstance(rows, list):
        raise EndpointContractError("v0.3 results tests must be a list")
    mapped = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("case"):
            raise EndpointContractError("malformed v0.3 result row")
        mapped[str(row["case"])] = row
    return mapped


def build_endpoint_overlay(
    graph: Mapping[str, Any],
    results: Mapping[str, Any],
) -> dict[str, Any]:
    nodes = {
        str(node["id"]): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
    rows = _result_rows(results)

    contracts = []
    for spec in FIXTURE_SPECS:
        row = rows.get(spec.case)
        if row is None:
            raise EndpointContractError(f"missing v0.3 result row: {spec.case}")
        if (
            int(row.get("chapter", -1)) != spec.chapter
            or row.get("status") != "PASS"
            or not row.get("eo_view")
            or not row.get("geo_view")
            or not row.get("contract")
        ):
            raise EndpointContractError(
                f"v0.3 semantic evidence mismatch for {spec.case}"
            )

        eo_id = f"op:eo:test:{spec.test_index:02d}"
        geo_id = f"op:geo:test:{spec.test_index:02d}"
        obj_id = f"obj:test:{spec.test_index:02d}"
        endpoint_ids = (eo_id, geo_id, obj_id)
        missing = [node_id for node_id in endpoint_ids if node_id not in nodes]
        if missing:
            raise EndpointContractError(
                f"fixture endpoints missing for {spec.case}: {missing}"
            )

        obj_label = str(nodes[obj_id].get("label", ""))
        if obj_label != spec.case:
            raise EndpointContractError(
                f"semantic-object label mismatch for test {spec.test_index}: "
                f"{obj_label!r} != {spec.case!r}"
            )

        endpoint_hashes = {
            "eo": {
                "id": eo_id,
                "base_node_identity_sha256": node_identity_sha256(nodes[eo_id]),
            },
            "geo": {
                "id": geo_id,
                "base_node_identity_sha256": node_identity_sha256(nodes[geo_id]),
            },
            "object": {
                "id": obj_id,
                "base_node_identity_sha256": node_identity_sha256(nodes[obj_id]),
            },
        }
        payload = copy.deepcopy(dict(spec.payload))
        payload_sha = _sha256(
            payload,
            domain="mapeogeo-endpoint-semantic-payload-v1",
        )
        evidence = {
            "test_id": str(results.get("test_id", "")),
            "seed": int(results.get("seed", 0)),
            "case": spec.case,
            "chapter": spec.chapter,
            "checks": int(row.get("checks", 0)),
            "status": str(row.get("status", "")),
            "max_error": row.get("max_error"),
            "evidence_class": str(row.get("evidence_class", "")),
            "eo_view": str(row["eo_view"]),
            "geo_view": str(row["geo_view"]),
            "declared_contract": str(row["contract"]),
        }
        body = {
            "schema": CONTRACT_SCHEMA,
            "contract_id": (
                f"mapeogeo.v03.fixture.{spec.test_index:02d}."
                f"endpoint-contract.v1"
            ),
            "semantic_id": spec.semantic_id,
            "semantic_object": spec.case,
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
        "base_test_id": str(results.get("test_id", "")),
        "contracts": contracts,
    }
    overlay = dict(overlay_body)
    overlay["overlay_digest"] = _sha256(
        overlay_body,
        domain="mapeogeo-endpoint-semantic-overlay-v1",
    )
    return overlay


def apply_endpoint_overlay(
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
        raise EndpointContractError("overlay digest missing")
    if _sha256(
        overlay_body,
        domain="mapeogeo-endpoint-semantic-overlay-v1",
    ) != overlay_digest:
        raise EndpointContractError("overlay digest mismatch")
    if overlay_body.get("schema") != OVERLAY_SCHEMA:
        raise EndpointContractError("unsupported overlay schema")

    for contract in overlay_body.get("contracts", []):
        if not isinstance(contract, dict):
            raise EndpointContractError("malformed endpoint contract")
        contract_body = dict(contract)
        contract_digest = contract_body.pop("contract_digest", None)
        if not isinstance(contract_digest, str):
            raise EndpointContractError("contract digest missing")
        if _sha256(
            contract_body,
            domain="mapeogeo-endpoint-semantic-contract-v1",
        ) != contract_digest:
            raise EndpointContractError("contract digest mismatch")

        semantic_id = str(contract["semantic_id"])
        payload = copy.deepcopy(contract["semantic_payload"])
        payload_sha = str(contract["semantic_payload_sha256"])
        if _sha256(
            payload,
            domain="mapeogeo-endpoint-semantic-payload-v1",
        ) != payload_sha:
            raise EndpointContractError("semantic payload digest mismatch")

        for role, endpoint in contract["endpoints"].items():
            node_id = str(endpoint["id"])
            if node_id not in nodes:
                raise EndpointContractError(f"overlay endpoint missing: {node_id}")
            actual_base_hash = node_identity_sha256(nodes[node_id])
            expected_base_hash = str(endpoint["base_node_identity_sha256"])
            if actual_base_hash != expected_base_hash:
                raise EndpointContractError(
                    f"endpoint identity changed before overlay: {node_id}"
                )

            attrs = nodes[node_id].setdefault("attributes", {})
            if not isinstance(attrs, dict):
                raise EndpointContractError(
                    f"endpoint attributes are not a mapping: {node_id}"
                )
            contracts = attrs.setdefault("semantic_contracts", [])
            record = {
                "contract_id": contract["contract_id"],
                "contract_digest": contract_digest,
                "semantic_id": semantic_id,
                "semantic_object": contract["semantic_object"],
                "role": role,
                "base_node_identity_sha256": expected_base_hash,
                "semantic_payload": payload,
                "semantic_payload_sha256": payload_sha,
                "evidence": copy.deepcopy(contract["evidence"]),
                "binding_mode": "ENDPOINT_CONTRACT_BOUND",
            }
            if record not in contracts:
                contracts.append(record)

    return enriched


def build_overlay_from_files(
    graph_path: Path,
    results_path: Path,
) -> dict[str, Any]:
    import gzip

    with gzip.open(graph_path, "rt", encoding="utf-8") as handle:
        graph = json.load(handle)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    return build_endpoint_overlay(graph, results)
