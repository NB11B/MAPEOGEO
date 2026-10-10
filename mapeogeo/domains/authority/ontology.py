"""Authority Domain Ontology and Hohfeldian Modalities.

This module provides the permanent MAPEOGEO domain representation of normative
relations, legal capacities, Hohfeldian modalities, and authority case bindings.

Invariant:
    ClaimOfAuthority != LegalAssessment != AdmissionDecision
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class HohfeldianModality(str, Enum):
    """The 8 fundamental Hohfeldian legal modalities."""
    PRIVILEGE = "privilege"   # Liberty to act; opposite of duty
    CLAIM = "claim"           # Entitlement against another; correlate of duty
    RIGHT = "claim"           # Standard legal synonym for claim-right
    POWER = "power"           # Capacity to alter legal relations; correlate of liability
    IMMUNITY = "immunity"     # Freedom from legal alteration; opposite of liability
    DUTY = "duty"             # Obligation to act or forebear; correlate of claim
    NO_RIGHT = "no_right"     # Absence of claim; opposite of claim
    LIABILITY = "liability"   # Subjection to power; correlate of power
    DISABILITY = "disability" # Lack of power; opposite of power


class AuthorityDisposition(str, Enum):
    """Four canonical authority dispositions."""
    SUPPORTED = "supported_within_scope"
    PROHIBITED = "prohibited_under_reviewed_rule"
    CONDITIONS_UNMET = "conditions_unmet"
    UNRESOLVED = "unresolved"


class CertificateOutcome(str, Enum):
    """Explicit certification outcomes preserving legal uncertainty without collapse."""
    CERTIFIED = "CERTIFIED"       # supported within scope
    OBSTRUCTED = "OBSTRUCTED"     # prohibited or conditions unmet
    UNRESOLVED = "UNRESOLVED"     # material legal or factual uncertainty remains


@dataclass(frozen=True)
class ActorBinding:
    actor_id: str
    capacity: str = "default"


@dataclass(frozen=True)
class OperationBinding:
    operation_id: str
    category: str = "general"


@dataclass(frozen=True)
class ActionCase:
    """Bounded actor-to-actor action proposal evaluated under an authority model."""
    case_id: str
    actor: ActorBinding
    affected_actor: ActorBinding
    operation: OperationBinding
    context_ref: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
