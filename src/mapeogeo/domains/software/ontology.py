"""Software Domain Ontology.

Defines the domain-specific representations for Software Systems Engineering:
- SoftwareObjective: high-level systems engineering objective
- SoftwareRequirement: formal requirement with interface and verification contracts
- SoftwareMachinery: concrete software library / component candidate
- SoftwareEvidence: verification audit traces for the 5-gate boundary
- SoftwareCertificate: deterministic certificate of verified software capability
- SoftwareVerificationGates: contract specifications for { T, U, S, L, F }
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EpistemicSoftwareStatus(StrEnum):
    """Epistemic status of a software component."""

    SOURCE_SPECIFIED = "SOURCE_SPECIFIED"
    STATICALLY_TYPED = "STATICALLY_TYPED"
    BEHAVIORALLY_TESTED = "BEHAVIORALLY_TESTED"
    CONTRACT_VERIFIED = "CONTRACT_VERIFIED"
    CERTIFIED_CAPABILITY = "CERTIFIED_CAPABILITY"


class SoftwareCertificationVerdict(StrEnum):
    """Certification verdict for software components."""

    CERTIFIED = "CERTIFIED"
    FALSIFIED = "FALSIFIED"
    INCOMPLETE_CONTRACT = "INCOMPLETE_CONTRACT"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"


@dataclass(frozen=True)
class SoftwareVerificationContracts:
    """Explicit contracts required for the 5-Gate Software Certification Boundary.

    Boundary: C_sw = { T, U, S, L, F }.
    """

    type_contract: str = ""
    unit_test_spec: str = ""
    static_analysis_rule: str = ""
    latency_bound_ms: float = 100.0
    concurrency_invariant: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SoftwareRequirement:
    """Formal software requirement with functional signatures and verification contracts."""

    requirement_id: str
    title: str
    domain: str
    weight: float
    required_signatures: tuple[str, ...]
    contracts: SoftwareVerificationContracts = field(default_factory=SoftwareVerificationContracts)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SoftwareObjective:
    """High-level software systems engineering objective."""

    objective_id: str
    title: str
    requirements: tuple[SoftwareRequirement, ...]
    system_domain: str = "Distributed Systems"
    sla_latency_target_ms: float = 100.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SoftwareEvidence:
    """Execution evidence submitted to the 5-gate software verification boundary."""

    type_safety_pass: bool = False
    unit_tests_pass: bool = False
    static_analysis_pass: bool = False
    measured_latency_ms: float = 999.0
    fault_tolerance_pass: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SoftwareMachinery:
    """Software machinery package proposing capabilities to eliminate deficiencies."""

    machinery_id: str
    name: str
    domain: str
    cost: float
    provided_signatures: tuple[str, ...]
    witness_id: str | None = None
    witness_symbol: str | None = None
    evidence: SoftwareEvidence = field(default_factory=SoftwareEvidence)
    required_authority: str = "STANDARD"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SoftwareCertificate:
    """Deterministic certificate issued upon passing all 5 software verification gates."""

    certificate_id: str
    machinery_id: str
    verdict: SoftwareCertificationVerdict
    is_certified: bool
    gates_passed: tuple[str, ...]
    falsifications_checked: tuple[str, ...]
    epistemic_status: EpistemicSoftwareStatus
    measured_latency_ms: float
    failure_reason: str | None = None
    timestamp: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
