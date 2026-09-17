"""Data models, enums, and witness types for Wave F3 Abstract Algebra & Number Theory."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


class AlgebraVerdict(str, Enum):
    VERIFIED_BOUNDED_CONTRACT_COMMUTATION = "VERIFIED_BOUNDED_CONTRACT_COMMUTATION"
    OUTSIDE_CURRENT_EXECUTABLE_SCOPE = "OUTSIDE_CURRENT_EXECUTABLE_SCOPE"
    PARTIAL_ONE_SIDED_REALIZATION = "PARTIAL_ONE_SIDED_REALIZATION"
    NONCOMMUTATIVE_UNDER_CONTRACT = "NONCOMMUTATIVE_UNDER_CONTRACT"
    IMPLEMENTATION_ERROR = "IMPLEMENTATION_ERROR"


class AlgebraContract(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    ISOMORPHIC_WITNESS = "ISOMORPHIC_WITNESS"
    HOMOLOGY_EQUIVALENCE = "HOMOLOGY_EQUIVALENCE"
    BOUNDED_MODEL_EQUIVALENCE = "BOUNDED_MODEL_EQUIVALENCE"
    PARTIAL_ONE_SIDED = "PARTIAL_ONE_SIDED"
    UNSUPPORTED_INFINITE = "UNSUPPORTED_INFINITE"


class RelationType(str, Enum):
    IDENTITY = "IDENTITY"
    EQUIVALENCE = "EQUIVALENCE"
    IMPLICATION = "IMPLICATION"
    SPECIALIZATION = "SPECIALIZATION"
    QUOTIENT = "QUOTIENT"
    HOMOMORPHISM = "HOMOMORPHISM"
    CONSTRUCTION = "CONSTRUCTION"
    PARTITION = "PARTITION"
    DECOMPOSITION = "DECOMPOSITION"
    ISOMORPHISM = "ISOMORPHISM"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"


@dataclass(frozen=True)
class AlgebraEORealization:
    """Exact Operator / Algebraic representation of an algebra concept."""
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
class AlgebraGEORealization:
    """Geometric / Structural / Topological representation of an algebra concept."""
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
class RedactedSemanticWitness:
    """Pure mathematical witness in interpretation space S with zero concept metadata."""
    view_source: str  # "EO" or "GEO"
    mathematical_domain: str
    canonical_structure_type: str
    normalized_values: dict[str, Any]
    structural_invariants: dict[str, Any] = field(default_factory=dict)

    def compute_digest(self) -> str:
        raw = json.dumps({
            "canonical_structure_type": self.canonical_structure_type,
            "normalized_values": self.normalized_values,
            "structural_invariants": self.structural_invariants,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WaveF3AuditRecord:
    """Result record of the dual-view commutation audit for an algebra concept."""
    canonical_id: str
    name: str
    family: str
    domain: str
    contract: AlgebraContract
    verdict: AlgebraVerdict
    eo_hash: str
    geo_hash: str
    sem_eo_digest: str
    sem_geo_digest: str
    redacted_commutation_passed: bool
    delta_metric: float
    bound_source_hashes: list[str] = field(default_factory=list)
    witness: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "name": self.name,
            "family": self.family,
            "domain": self.domain,
            "contract": self.contract.value,
            "verdict": self.verdict.value,
            "eo_hash": self.eo_hash,
            "geo_hash": self.geo_hash,
            "sem_eo_digest": self.sem_eo_digest,
            "sem_geo_digest": self.sem_geo_digest,
            "redacted_commutation_passed": self.redacted_commutation_passed,
            "delta_metric": self.delta_metric,
            "bound_source_hashes": self.bound_source_hashes,
            "witness": self.witness,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class RelationshipEdgeRecord:
    """Result record of evaluating a typed mathematical relationship edge."""
    relation_id: str
    relation_type: RelationType
    source_canonical_id: str
    target_canonical_id: str
    mathematical_claim: str
    commutation_verified: bool
    relationship_witness: dict[str, Any]
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type.value,
            "source_canonical_id": self.source_canonical_id,
            "target_canonical_id": self.target_canonical_id,
            "mathematical_claim": self.mathematical_claim,
            "commutation_verified": self.commutation_verified,
            "relationship_witness": self.relationship_witness,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class FalsificationMutantRecord:
    """Result record of a mutation falsification test."""
    mutant_id: str
    family: str
    mutation_class: str
    target_canonical_id: str
    description: str
    mutant_killed: bool
    verdict: AlgebraVerdict
    detection_witness: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutant_id": self.mutant_id,
            "family": self.family,
            "mutation_class": self.mutation_class,
            "target_canonical_id": self.target_canonical_id,
            "description": self.description,
            "mutant_killed": self.mutant_killed,
            "verdict": self.verdict.value,
            "detection_witness": self.detection_witness,
        }

@dataclass(frozen=True)
class CrossPairAuditResult:
    eo_canonical_id: str
    geo_canonical_id: str
    is_diagonal: bool
    verdict: AlgebraVerdict
    sem_eo_digest: str
    sem_geo_digest: str
    discriminates_correctly: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "eo_canonical_id": self.eo_canonical_id,
            "geo_canonical_id": self.geo_canonical_id,
            "is_diagonal": self.is_diagonal,
            "verdict": self.verdict.value,
            "sem_eo_digest": self.sem_eo_digest,
            "sem_geo_digest": self.sem_geo_digest,
            "discriminates_correctly": self.discriminates_correctly,
            "notes": self.notes,
        }
