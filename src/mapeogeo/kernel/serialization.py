"""Deterministic serialization for UoW Kernel components and states.

Enforces byte-for-byte reproducibility with explicit schema and schema_version.
"""

from __future__ import annotations

import json
from typing import Any

from mapeogeo.kernel.deficiency import DeficiencyDistribution
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.tools.deterministic_json import serialize_deterministic


def serialize_knowledge_state(state: KnowledgeState) -> str:
    """Serialize KnowledgeState to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.kernel.knowledge_state",
        "schema_version": 1,
        "t": state.t,
        "signatures": sorted(state.signatures),
        "witness_ids": sorted(state.witness_ids),
        "cumulative_ability": state.cumulative_ability,
        "state_hash": state.state_hash,
        "certified_nodes": [
            {
                "node_id": n.node_id,
                "provided_signatures": sorted(n.provided_signatures),
                "dependencies": sorted(n.dependencies),
                "witness_id": n.witness_id,
            }
            for n in state.certified_nodes
        ],
        "metadata": state.metadata,
    }
    return serialize_deterministic(data)


def deserialize_knowledge_state(raw: str | dict[str, Any]) -> KnowledgeState:
    """Deserialize JSON data to KnowledgeState."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.kernel.knowledge_state":
        raise ValueError(f"Invalid schema: {data.get('schema')}")

    nodes = tuple(
        MachineryNode(
            node_id=d["node_id"],
            provided_signatures=tuple(d["provided_signatures"]),
            dependencies=tuple(d["dependencies"]),
            witness_id=d.get("witness_id"),
        )
        for d in data.get("certified_nodes", [])
    )

    return KnowledgeState(
        t=int(data["t"]),
        signatures=frozenset(data["signatures"]),
        certified_nodes=nodes,
        witness_ids=frozenset(data.get("witness_ids", [])),
        cumulative_ability=float(data.get("cumulative_ability", 0.0)),
        state_hash=data.get("state_hash", ""),
        metadata=data.get("metadata", {}),
    )


def serialize_deficiency_distribution(dist: DeficiencyDistribution) -> str:
    """Serialize DeficiencyDistribution to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.kernel.deficiency_distribution",
        "schema_version": 1,
        "t": dist.t,
        "total_requirements": dist.total_requirements,
        "covered_requirements": dist.covered_requirements,
        "deficient_requirements": dist.deficient_requirements,
        "total_deficient_severity": dist.total_deficient_severity,
        "signature_frequency": dist.signature_frequency,
        "signature_impact": dist.signature_impact,
        "records": [
            {
                "req_id": r.req_id,
                "weight": r.weight,
                "required": list(r.required),
                "missing": list(r.missing),
                "covered": list(r.covered),
                "is_covered": r.is_covered,
                "coverage_ratio": r.coverage_ratio,
            }
            for r in dist.records
        ],
    }
    return serialize_deterministic(data)


def serialize_machinery_candidate(cand: MachineryCandidate) -> str:
    """Serialize MachineryCandidate to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.kernel.machinery_candidate",
        "schema_version": 1,
        "candidate_id": cand.candidate_id,
        "provided_signatures": sorted(cand.provided_signatures),
        "cost": cand.cost,
        "witness_ids": sorted(cand.witness_ids),
        "nodes": [
            {
                "node_id": n.node_id,
                "provided_signatures": sorted(n.provided_signatures),
                "dependencies": sorted(n.dependencies),
                "witness_id": n.witness_id,
            }
            for n in cand.nodes
        ],
        "metadata": cand.metadata,
    }
    return serialize_deterministic(data)
