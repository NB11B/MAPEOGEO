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
LINEAR_SEMANTICS_KEY = "farkas_linear_semantics_v1"


@dataclass(frozen=True)
class FarkasContractSpec:
    contract_id: str
    premise_id: str
    conclusion_id: str
    semantic_id: str
    semantic_object: str
    declared_contract: str
    payload: Mapping[str, Any]
    source_evidence: tuple[Mapping[str, str], ...] = ()
    variables: tuple[str, ...] = ("x1", "x2")


SOURCE_GROUNDED_FARKAS_SPECS = (
    FarkasContractSpec(
        contract_id="mapeogeo.farkas.cvx.polyhedron_simplex.v1",
        premise_id="canonical:foundation:set:set_operations_and_boolean_algebra",
        conclusion_id="canonical:convex:convex_set",
        semantic_id="GFY.FARKAS_IMPLICATION.v1",
        semantic_object="Farkas polyhedral implication",
        declared_contract="Boyd CVX Section 2.2 unit simplex polyhedral halfspace intersection implies supporting bounding inequality",
        payload={
            "certificate_type": "implication",
            "matrix": [[-1, 0], [0, -1], [1, 1]],
            "bounds": [0, 0, 1],
            "target_coefficients": [1, 2],
            "target_bound": 2,
            "multipliers": [1, 0, 2],
        },
        source_evidence=(
            {
                "subject_id": "srcdecl:cvx:section:2_2",
                "statement_sha256": "9ae2845c9ed81151ef6cc174d4675a9acfc86b155305a4f67ab7c6cbc6d557a4",
            },
        ),
    ),
    FarkasContractSpec(
        contract_id="mapeogeo.farkas.cvx.supporting_hyperplane.v1",
        premise_id="canonical:foundation:geom:euclidean_space_and_metrics",
        conclusion_id="canonical:convex:convex_set",
        semantic_id="GFY.FARKAS_IMPLICATION.v1",
        semantic_object="Farkas polyhedral implication",
        declared_contract="Boyd CVX Section 2.5 bounded rectangle polytope implies supporting hyperplane inequality",
        payload={
            "certificate_type": "implication",
            "matrix": [[-1, 0], [0, -1], [1, 0], [0, 1]],
            "bounds": [0, 0, 2, 3],
            "target_coefficients": [3, 4],
            "target_bound": 18,
            "multipliers": [0, 0, 3, 4],
        },
        source_evidence=(
            {
                "subject_id": "srcdecl:cvx:section:2_5",
                "statement_sha256": "5cbeeca1abaa6380c15dbff99dc07870cbce5ef7148d09b627076186f08094a9",
            },
        ),
    ),
    FarkasContractSpec(
        contract_id="mapeogeo.farkas.cvx.lp_inequality_bound.v1",
        premise_id="canonical:foundation:geom:euclidean_space_and_metrics",
        conclusion_id="canonical:optimization:linear_program",
        semantic_id="GFY.FARKAS_IMPLICATION.v1",
        semantic_object="Farkas polyhedral implication",
        declared_contract="Boyd CVX Section 4.3 linear optimization primal inequality system implies dual objective bound",
        payload={
            "certificate_type": "implication",
            "matrix": [[2, 1], [1, 2], [-1, 0], [0, -1]],
            "bounds": [4, 5, 0, 0],
            "target_coefficients": [3, 3],
            "target_bound": 9,
            "multipliers": [1, 1, 0, 0],
        },
        source_evidence=(
            {
                "subject_id": "srcdecl:cvx:section:4_3",
                "statement_sha256": "630dafac08fc5c72b950e565adbcde7e3d57b1597888ba317156af8d566e9c9f",
            },
        ),
    ),
    FarkasContractSpec(
        contract_id="mapeogeo.farkas.cvx.theorems_of_alternatives.v1",
        premise_id="canonical:foundation:rel:orders_posets_and_lattices",
        conclusion_id="canonical:convex:dual_cone",
        semantic_id="GFY.FARKAS_IMPLICATION.v1",
        semantic_object="Farkas polyhedral implication",
        declared_contract="Boyd CVX Section 5.8 theorem of alternatives non-negative linear combination cone implication",
        payload={
            "certificate_type": "implication",
            "matrix": [[1, 0], [0, 1], [1, 1], [-1, 0]],
            "bounds": [2, 2, 3, 0],
            "target_coefficients": [2, 3],
            "target_bound": 8,
            "multipliers": [0, 1, 2, 0],
        },
        source_evidence=(
            {
                "subject_id": "srcdecl:cvx:section:5_8",
                "statement_sha256": "931dbd8c1315a7fe0b246461344ce0c49b609163b465a01bba9e877a7ae3d9a0",
            },
        ),
    ),
    FarkasContractSpec(
        contract_id="mapeogeo.farkas.gallier.polyhedral_cone_dual.v1",
        premise_id="canonical:foundation:seq:order_bounds_and_absolute_value",
        conclusion_id="canonical:convex:convex_set",
        semantic_id="GFY.FARKAS_IMPLICATION.v1",
        semantic_object="Farkas polyhedral implication",
        declared_contract="Gallier-Quaintance Chapter 15 polyhedral cone dual cone containment certificate",
        payload={
            "certificate_type": "implication",
            "matrix": [[-1, 0], [0, -1], [-1, 1]],
            "bounds": [0, 0, 0],
            "target_coefficients": [-3, 1],
            "target_bound": 0,
            "multipliers": [2, 0, 1],
        },
        source_evidence=(
            {
                "subject_id": "srcdecl:definition:15_1",
                "statement_sha256": "3be18dbe63ce2b24c81750e27fa74120019ab71f78305b58a7697a0e361869d4",
            },
            {
                "subject_id": "srcdecl:theorem:15_5",
                "statement_sha256": "17f99c215c89678710b4d015e9c9b61cb7483c5d6dd092ee5b0a5ea540ddbbc5",
            },
        ),
    ),
)

FARKAS_SPECS = SOURCE_GROUNDED_FARKAS_SPECS


def attach_source_grounded_linear_semantics(
    graph: Mapping[str, Any],
    specs: tuple[FarkasContractSpec, ...] = SOURCE_GROUNDED_FARKAS_SPECS,
) -> dict[str, Any]:
    enriched = copy.deepcopy(dict(graph))
    nodes = {
        str(n["id"]): n
        for n in enriched.get("nodes", [])
        if isinstance(n, dict) and n.get("id")
    }
    for spec in specs:
        premise_node = nodes.get(spec.premise_id)
        conclusion_node = nodes.get(spec.conclusion_id)
        if premise_node is None or conclusion_node is None:
            continue
        p_attrs = premise_node.setdefault("attributes", {})
        c_attrs = conclusion_node.setdefault("attributes", {})
        if not isinstance(p_attrs, dict) or not isinstance(c_attrs, dict):
            continue
        p_sem = p_attrs.setdefault(LINEAR_SEMANTICS_KEY, [])
        c_sem = c_attrs.setdefault(LINEAR_SEMANTICS_KEY, [])
        if not isinstance(p_sem, list) or not isinstance(c_sem, list):
            continue

        p_rec = {
            "semantic_id": spec.semantic_id,
            "role": "premise",
            "declared_contract": spec.declared_contract,
            "variables": list(spec.variables),
            "matrix": copy.deepcopy(dict(spec.payload)["matrix"]),
            "bounds": copy.deepcopy(dict(spec.payload)["bounds"]),
            "source_evidence": [dict(e) for e in spec.source_evidence],
        }
        if p_rec not in p_sem:
            p_sem.append(p_rec)

        c_rec = {
            "semantic_id": spec.semantic_id,
            "role": "conclusion",
            "declared_contract": spec.declared_contract,
            "variables": list(spec.variables),
            "target_coefficients": copy.deepcopy(
                dict(spec.payload)["target_coefficients"]
            ),
            "target_bound": copy.deepcopy(dict(spec.payload)["target_bound"]),
            "source_evidence": [dict(e) for e in spec.source_evidence],
        }
        if c_rec not in c_sem:
            c_sem.append(c_rec)

    return enriched


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


def _statement_hash(node: Mapping[str, Any]) -> str | None:
    attrs = node.get("attributes", {})
    if not isinstance(attrs, dict):
        return None
    value = attrs.get("statement_sha256")
    if not value:
        profile = attrs.get("independent_profile", {})
        if isinstance(profile, dict):
            value = profile.get("statement_sha256")
    if not value:
        value = attrs.get("source_segment_sha256")
    if (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    ):
        return value
    return None


def _linear_semantics_records(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    attrs = node.get("attributes", {})
    if not isinstance(attrs, dict):
        return []
    value = attrs.get(LINEAR_SEMANTICS_KEY, [])
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _validate_source_evidence(
    nodes: Mapping[str, Mapping[str, Any]],
    evidence: Any,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(evidence, list) or not evidence:
        raise FarkasContractError(
            "Farkas linear semantics require nonempty source_evidence"
        )
    validated: list[tuple[str, str]] = []
    for record in evidence:
        if not isinstance(record, dict):
            raise FarkasContractError("malformed Farkas source evidence")
        subject_id = str(record.get("subject_id", ""))
        expected_hash = str(record.get("statement_sha256", ""))
        subject = nodes.get(subject_id)
        if subject is None:
            raise FarkasContractError(
                f"Farkas source evidence subject missing: {subject_id}"
            )
        actual_hash = _statement_hash(subject)
        if actual_hash is None or actual_hash != expected_hash:
            raise FarkasContractError(
                f"Farkas source evidence hash mismatch: {subject_id}"
            )
        validated.append((subject_id, expected_hash))
    return tuple(validated)


def _find_bound_linear_semantics(
    *,
    nodes: Mapping[str, Mapping[str, Any]],
    node: Mapping[str, Any],
    role: str,
    spec: FarkasContractSpec,
) -> Mapping[str, Any]:
    for record in _linear_semantics_records(node):
        if (
            record.get("semantic_id") == spec.semantic_id
            and record.get("role") == role
            and record.get("declared_contract") == spec.declared_contract
        ):
            _validate_source_evidence(nodes, record.get("source_evidence"))
            return record
    raise FarkasContractError(
        f"missing source-bound Farkas {role} semantics for "
        f"{node.get('id')}"
    )


def validate_farkas_spec_semantic_binding(
    graph: Mapping[str, Any],
    spec: FarkasContractSpec,
) -> dict[str, Any]:
    nodes = {
        str(node["id"]): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
    premise = nodes.get(spec.premise_id)
    conclusion = nodes.get(spec.conclusion_id)
    if premise is None:
        raise FarkasContractError(f"premise node missing: {spec.premise_id}")
    if conclusion is None:
        raise FarkasContractError(f"conclusion node missing: {spec.conclusion_id}")

    premise_semantics = _find_bound_linear_semantics(
        nodes=nodes,
        node=premise,
        role="premise",
        spec=spec,
    )
    conclusion_semantics = _find_bound_linear_semantics(
        nodes=nodes,
        node=conclusion,
        role="conclusion",
        spec=spec,
    )

    variables = premise_semantics.get("variables")
    if (
        not isinstance(variables, list)
        or not variables
        or variables != conclusion_semantics.get("variables")
        or any(not isinstance(name, str) or not name for name in variables)
    ):
        raise FarkasContractError("Farkas variable basis mismatch")

    payload = dict(spec.payload)
    if payload.get("certificate_type") != "implication":
        raise FarkasContractError(
            "endpoint semantic binding currently supports implication certificates only"
        )

    if (
        premise_semantics.get("matrix") != payload.get("matrix")
        or premise_semantics.get("bounds") != payload.get("bounds")
    ):
        raise FarkasContractError(
            "Farkas premise semantics do not match certificate A,b"
        )
    if (
        conclusion_semantics.get("target_coefficients")
        != payload.get("target_coefficients")
        or conclusion_semantics.get("target_bound")
        != payload.get("target_bound")
    ):
        raise FarkasContractError(
            "Farkas conclusion semantics do not match certificate c,d"
        )

    return {
        "variables": copy.deepcopy(variables),
        "premise_source_evidence": copy.deepcopy(
            premise_semantics["source_evidence"]
        ),
        "conclusion_source_evidence": copy.deepcopy(
            conclusion_semantics["source_evidence"]
        ),
    }


def build_farkas_endpoint_overlay(
    graph: Mapping[str, Any],
    specs: tuple[FarkasContractSpec, ...] = SOURCE_GROUNDED_FARKAS_SPECS,
) -> dict[str, Any]:
    nodes = {
        str(node["id"]): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }

    contracts = []
    for spec in specs:
        if spec.premise_id not in nodes:
            raise FarkasContractError(f"premise node missing: {spec.premise_id}")
        if spec.conclusion_id not in nodes:
            raise FarkasContractError(f"conclusion node missing: {spec.conclusion_id}")

        semantic_binding = validate_farkas_spec_semantic_binding(
            graph,
            spec,
        )

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
            "evidence_class": "SOURCE_BOUND_EXACT_FARKAS_IMPLICATION",
            "variables": semantic_binding["variables"],
            "premise_source_evidence": semantic_binding[
                "premise_source_evidence"
            ],
            "conclusion_source_evidence": semantic_binding[
                "conclusion_source_evidence"
            ],
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
