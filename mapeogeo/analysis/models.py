"""Data models, enums, and witness types for Wave F4 Quantified Real Analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


class AnalysisVerdict(str, Enum):
    VERIFIED_QUANTIFIED_COMMUTATION = "VERIFIED_QUANTIFIED_COMMUTATION"
    OUTSIDE_CURRENT_SCOPE = "OUTSIDE_CURRENT_SCOPE"
    NONCOMMUTATIVE_UNDER_CONTRACT = "NONCOMMUTATIVE_UNDER_CONTRACT"
    QUANTIFIER_DEPENDENCY_VIOLATION = "QUANTIFIER_DEPENDENCY_VIOLATION"
    UNJUSTIFIED_EVIDENCE_PROMOTION = "UNJUSTIFIED_EVIDENCE_PROMOTION"
    FLOAT_IN_PROOF_EVIDENCE_ERROR = "FLOAT_IN_PROOF_EVIDENCE_ERROR"
    IMPLEMENTATION_ERROR = "IMPLEMENTATION_ERROR"


class EvidenceTier(str, Enum):
    FORMAL_GENERAL = "FORMAL_GENERAL"
    CHECKED_SYMBOLIC_FAMILY = "CHECKED_SYMBOLIC_FAMILY"
    EXACT_BOUNDED_INSTANCE = "EXACT_BOUNDED_INSTANCE"
    NUMERICAL_PROBE_ONLY = "NUMERICAL_PROBE_ONLY"
    COUNTEREXAMPLE_CERTIFIED = "COUNTEREXAMPLE_CERTIFIED"
    OUTSIDE_CURRENT_SCOPE = "OUTSIDE_CURRENT_SCOPE"


class AnalysisContract(str, Enum):
    QUANTIFIED_DUAL_VIEW_COMMUTATION = "QUANTIFIED_DUAL_VIEW_COMMUTATION"
    SYMBOLIC_FAMILY_COMMUTATION = "SYMBOLIC_FAMILY_COMMUTATION"
    EXACT_BOUNDED_INSTANCE_COMMUTATION = "EXACT_BOUNDED_INSTANCE_COMMUTATION"
    NUMERICAL_PROBE = "NUMERICAL_PROBE"


class RelationType(str, Enum):
    IMPLICATION = "IMPLICATION"
    EQUIVALENCE = "EQUIVALENCE"
    SPECIALIZATION = "SPECIALIZATION"
    CONSTRUCTION = "CONSTRUCTION"
    CHARACTERIZATION = "CHARACTERIZATION"
    PRESERVATION = "PRESERVATION"
    INTERCHANGE = "INTERCHANGE"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"


class QuantifierType(str, Enum):
    FORALL = "FORALL"
    EXISTS = "EXISTS"


@dataclass(frozen=True)
class QuantifierBlock:
    """A single quantifier block in an ordered quantifier sequence."""
    type: QuantifierType
    var: str
    domain: str
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "var": self.var,
            "domain": self.domain,
            "depends_on": self.depends_on,
        }


@dataclass(frozen=True)
class QuantifierSignature:
    """Full quantified dependency signature for an analysis theorem or concept."""
    canonical_id: str
    blocks: list[QuantifierBlock]
    hypotheses: list[str]
    conclusion: str
    permitted_dependencies: dict[str, list[str]]
    forbidden_dependencies: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "blocks": [b.to_dict() for b in self.blocks],
            "hypotheses": self.hypotheses,
            "conclusion": self.conclusion,
            "permitted_dependencies": self.permitted_dependencies,
            "forbidden_dependencies": self.forbidden_dependencies,
        }


@dataclass(frozen=True)
class AnalysisEORealization:
    """Exact Operator / Algebraic representation of a real analysis concept."""
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
class AnalysisGEORealization:
    """Geometric / Structural / Topological representation of a real analysis concept."""
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
class WaveF4AuditRecord:
    """Result record of the dual-view commutation audit for a real analysis concept."""
    canonical_id: str
    name: str
    family: str
    domain: str
    contract: AnalysisContract
    verdict: AnalysisVerdict
    evidence_tier: EvidenceTier
    eo_hash: str
    geo_hash: str
    sem_eo_digest: str
    sem_geo_digest: str
    redacted_commutation_passed: bool
    delta_metric: float
    bound_source_hashes: list[str] = field(default_factory=list)
    quantifier_verified: bool = True
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
            "evidence_tier": self.evidence_tier.value,
            "eo_hash": self.eo_hash,
            "geo_hash": self.geo_hash,
            "sem_eo_digest": self.sem_eo_digest,
            "sem_geo_digest": self.sem_geo_digest,
            "redacted_commutation_passed": self.redacted_commutation_passed,
            "delta_metric": self.delta_metric,
            "bound_source_hashes": self.bound_source_hashes,
            "quantifier_verified": self.quantifier_verified,
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
    verdict: AnalysisVerdict
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
    verdict: AnalysisVerdict
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
