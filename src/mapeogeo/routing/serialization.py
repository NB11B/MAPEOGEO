"""Deterministic JSON Serialization for Routing and Contract Subsystems.

Enforces byte-for-byte reproducibility with explicit schema and schema_version headers.
"""

from __future__ import annotations

import json
from typing import Any

from mapeogeo.routing.contracts import (
    AuthorityRequirement,
    ResourceRequirement,
    WorkContract,
)
from mapeogeo.routing.route import RouteCertificate
from mapeogeo.tools.deterministic_json import serialize_deterministic


def serialize_work_contract(contract: WorkContract) -> str:
    """Serialize WorkContract to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.routing.work_contract",
        "schema_version": 1,
        "contract_id": contract.contract_id,
        "source": contract.source,
        "target": contract.target,
        "preconditions": sorted(contract.preconditions),
        "postconditions": sorted(contract.postconditions),
        "cost": contract.cost,
        "error_tolerance": contract.error_tolerance,
        "is_certified": contract.is_certified,
        "requires_materialization": contract.requires_materialization,
        "resources": {
            "cpu_cores": contract.resources.cpu_cores,
            "ram_mb": contract.resources.ram_mb,
            "gpu_count": contract.resources.gpu_count,
            "npu_count": contract.resources.npu_count,
            "energy_joules": contract.resources.energy_joules,
            "custom": contract.resources.custom,
        },
        "authority": {
            "required_role": contract.authority.required_role,
            "security_clearance": contract.authority.security_clearance,
            "allowed_scopes": sorted(contract.authority.allowed_scopes),
            "requires_audit_receipt": contract.authority.requires_audit_receipt,
        },
        "invariants": sorted(contract.invariants),
        "metadata": contract.metadata,
    }
    return serialize_deterministic(data)


def deserialize_work_contract(raw: str | dict[str, Any]) -> WorkContract:
    """Deserialize WorkContract from deterministic JSON."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.routing.work_contract":
        raise ValueError(f"Invalid schema: {data.get('schema')}")

    res_data = data.get("resources", {})
    auth_data = data.get("authority", {})

    return WorkContract(
        contract_id=data["contract_id"],
        source=data["source"],
        target=data["target"],
        preconditions=tuple(data.get("preconditions", [])),
        postconditions=tuple(data.get("postconditions", [])),
        cost=float(data.get("cost", 1.0)),
        error_tolerance=float(data.get("error_tolerance", 0.0)),
        is_certified=bool(data.get("is_certified", True)),
        requires_materialization=bool(data.get("requires_materialization", False)),
        resources=ResourceRequirement(
            cpu_cores=float(res_data.get("cpu_cores", 0.0)),
            ram_mb=float(res_data.get("ram_mb", 0.0)),
            gpu_count=float(res_data.get("gpu_count", 0.0)),
            npu_count=float(res_data.get("npu_count", 0.0)),
            energy_joules=float(res_data.get("energy_joules", 0.0)),
            custom=dict(res_data.get("custom", {})),
        ),
        authority=AuthorityRequirement(
            required_role=str(auth_data.get("required_role", "")),
            security_clearance=str(auth_data.get("security_clearance", "")),
            allowed_scopes=frozenset(auth_data.get("allowed_scopes", [])),
            requires_audit_receipt=bool(auth_data.get("requires_audit_receipt", False)),
        ),
        invariants=tuple(data.get("invariants", [])),
        metadata=dict(data.get("metadata", {})),
    )


def serialize_route_certificate(cert: RouteCertificate) -> str:
    """Serialize RouteCertificate to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.routing.route_certificate",
        "schema_version": 1,
        "target": cert.target,
        "route_contract_ids": list(cert.route_contract_ids),
        "input_nodes": sorted(cert.input_nodes),
        "output_node": cert.output_node,
        "total_cost": cert.total_cost,
        "total_error": cert.total_error,
        "certified": cert.certified,
        "materialized": cert.materialized,
        "sha256_seal": cert.sha256_seal,
    }
    return serialize_deterministic(data)
