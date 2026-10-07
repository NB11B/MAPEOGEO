"""Deterministic serialization for PSMSL primitives and signatures.

Enforces byte-for-byte replay with explicit schemas and schema versions.
"""

from __future__ import annotations

import json
from typing import Any

from mapeogeo.psmsl.latent import LatentGenerator, ObservableSignature, Observation
from mapeogeo.psmsl.operator import OperatorWord, TransformationOperator
from mapeogeo.tools.deterministic_json import serialize_deterministic


def serialize_operator(op: TransformationOperator) -> str:
    """Serialize a TransformationOperator to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.psmsl.transformation_operator",
        "schema_version": 1,
        "operator_id": op.operator_id,
        "domain_dim": op.domain_dim,
        "codomain_dim": op.codomain_dim,
        "matrix": [list(row) for row in op.matrix],
    }
    return serialize_deterministic(data)


def deserialize_operator(raw: str | dict[str, Any]) -> TransformationOperator:
    """Deserialize JSON data to TransformationOperator."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.psmsl.transformation_operator":
        raise ValueError(f"Invalid schema: {data.get('schema')}")
    mat = tuple(tuple(float(x) for x in r) for r in data["matrix"])
    return TransformationOperator(operator_id=data["operator_id"], matrix=mat)


def serialize_operator_word(word: OperatorWord) -> str:
    """Serialize an OperatorWord to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.psmsl.operator_word",
        "schema_version": 1,
        "word_id": word.word_id,
        "operators": [
            {
                "operator_id": op.operator_id,
                "domain_dim": op.domain_dim,
                "codomain_dim": op.codomain_dim,
                "matrix": [list(row) for row in op.matrix],
            }
            for op in word.operators
        ],
    }
    return serialize_deterministic(data)


def deserialize_operator_word(raw: str | dict[str, Any]) -> OperatorWord:
    """Deserialize JSON data to OperatorWord."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.psmsl.operator_word":
        raise ValueError(f"Invalid schema: {data.get('schema')}")
    ops = [
        TransformationOperator(
            operator_id=item["operator_id"],
            matrix=tuple(tuple(float(x) for x in r) for r in item["matrix"]),
        )
        for item in data["operators"]
    ]
    return OperatorWord(word_id=data["word_id"], operators=tuple(ops))


def serialize_observation(obs: Observation) -> str:
    """Serialize an Observation to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.psmsl.observation",
        "schema_version": 1,
        "observation_id": obs.observation_id,
        "values": list(obs.values),
        "timestamp": obs.timestamp,
        "metadata": obs.metadata,
    }
    return serialize_deterministic(data)


def deserialize_observation(raw: str | dict[str, Any]) -> Observation:
    """Deserialize JSON data to Observation."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.psmsl.observation":
        raise ValueError(f"Invalid schema: {data.get('schema')}")
    return Observation(
        observation_id=data["observation_id"],
        values=tuple(float(x) for x in data["values"]),
        timestamp=float(data.get("timestamp", 0.0)),
        metadata=data.get("metadata", {}),
    )


def serialize_observable_signature(sig: ObservableSignature) -> str:
    """Serialize an ObservableSignature to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.psmsl.observable_signature",
        "schema_version": 1,
        "signature_id": sig.signature_id,
        "observations": [
            {
                "observation_id": o.observation_id,
                "values": list(o.values),
                "timestamp": o.timestamp,
                "metadata": o.metadata,
            }
            for o in sig.observations
        ],
        "metadata": sig.metadata,
    }
    return serialize_deterministic(data)


def deserialize_observable_signature(raw: str | dict[str, Any]) -> ObservableSignature:
    """Deserialize JSON data to ObservableSignature."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.psmsl.observable_signature":
        raise ValueError(f"Invalid schema: {data.get('schema')}")
    obs = [
        Observation(
            observation_id=d["observation_id"],
            values=tuple(float(x) for x in d["values"]),
            timestamp=float(d.get("timestamp", 0.0)),
            metadata=d.get("metadata", {}),
        )
        for d in data["observations"]
    ]
    return ObservableSignature(
        signature_id=data["signature_id"],
        observations=tuple(obs),
        metadata=data.get("metadata", {}),
    )


def serialize_latent_generator(gen: LatentGenerator) -> str:
    """Serialize a LatentGenerator to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.psmsl.latent_generator",
        "schema_version": 1,
        "generator_id": gen.generator_id,
        "status": gen.status,
        "estimated_state": list(gen.estimated_state) if gen.estimated_state else None,
        "nullity": gen.nullity,
        "evidence_observations": list(gen.evidence_observations),
        "metadata": gen.metadata,
    }
    return serialize_deterministic(data)


def deserialize_latent_generator(raw: str | dict[str, Any]) -> LatentGenerator:
    """Deserialize JSON data to LatentGenerator."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    if data.get("schema") != "mapeogeo.psmsl.latent_generator":
        raise ValueError(f"Invalid schema: {data.get('schema')}")
    est_state = (
        tuple(float(x) for x in data["estimated_state"])
        if data.get("estimated_state") is not None
        else None
    )
    return LatentGenerator(
        generator_id=data["generator_id"],
        status=data.get("status", "unknown"),
        estimated_state=est_state,
        nullity=int(data.get("nullity", 0)),
        evidence_observations=tuple(data.get("evidence_observations", [])),
        metadata=data.get("metadata", {}),
    )
