"""Data models and enums for Wave F2 EO/GEO Dual-View Realization and Commutation Audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


class CommutationVerdict(str, Enum):
    VERIFIED_COMMUTATIVE = "VERIFIED_COMMUTATIVE"
    UNSUPPORTED = "UNSUPPORTED"
    WOUNDED = "WOUNDED"
    REJECTED = "REJECTED"
    IMPLEMENTATION_ERROR = "IMPLEMENTATION_ERROR"


class EquivalenceContract(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    ISOMORPHIC_WITNESS = "ISOMORPHIC_WITNESS"
    HOMOLOGY_EQUIVALENCE = "HOMOLOGY_EQUIVALENCE"
    BOUNDED_MODEL_EQUIVALENCE = "BOUNDED_MODEL_EQUIVALENCE"
    PARTIAL_ONE_SIDED = "PARTIAL_ONE_SIDED"
    UNSUPPORTED_INFINITE = "UNSUPPORTED_INFINITE"


class CanonicalDomain(str, Enum):
    LOGIC_PROOF_THEORY = "Logic & Proof Theory"
    SET_THEORY = "Set Theory"
    DISCRETE_MATHEMATICS = "Discrete Mathematics & Combinatorics"


@dataclass(frozen=True)
class EORealization:
    """Exact Operator / Algebraic representation of a canonical concept."""
    canonical_id: str
    representation_type: str
    algebraic_payload: dict[str, Any]
    structural_signature: str = ""

    def compute_hash(self) -> str:
        raw = json.dumps({
            "canonical_id": self.canonical_id,
            "representation_type": self.representation_type,
            "algebraic_payload": self.algebraic_payload,
            "structural_signature": self.structural_signature,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GEORealization:
    """Geometric / Structural / Topological representation of a canonical concept."""
    canonical_id: str
    representation_type: str
    geometric_payload: dict[str, Any]
    structural_signature: str = ""

    def compute_hash(self) -> str:
        raw = json.dumps({
            "canonical_id": self.canonical_id,
            "representation_type": self.representation_type,
            "geometric_payload": self.geometric_payload,
            "structural_signature": self.structural_signature,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SemanticInterpretation:
    """Evaluated semantic state in the shared interpretation space S."""
    canonical_id: str
    view_source: str  # "EO" or "GEO"
    semantic_type: str
    normalized_values: dict[str, Any]
    invariants: dict[str, Any] = field(default_factory=dict)

    def compute_digest(self) -> str:
        raw = json.dumps({
            "canonical_id": self.canonical_id,
            "semantic_type": self.semantic_type,
            "normalized_values": self.normalized_values,
            "invariants": self.invariants,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CommutationRecord:
    """Result record of the commutation audit for one canonical concept."""
    canonical_id: str
    name: str
    domain: str
    contract: EquivalenceContract
    verdict: CommutationVerdict
    eo_hash: str
    geo_hash: str
    sem_eo_digest: str
    sem_geo_digest: str
    delta_metric: float
    witness: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "name": self.name,
            "domain": self.domain,
            "contract": self.contract.value,
            "verdict": self.verdict.value,
            "eo_hash": self.eo_hash,
            "geo_hash": self.geo_hash,
            "sem_eo_digest": self.sem_eo_digest,
            "sem_geo_digest": self.sem_geo_digest,
            "delta_metric": self.delta_metric,
            "witness": self.witness,
            "notes": self.notes,
        }
