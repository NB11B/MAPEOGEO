"""Rule Packs, Normative Propositions, and Priority Models for Authority Profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RuleEffect(str, Enum):
    PERMIT = "permit"
    PROHIBIT = "prohibit"
    OBLIGATE = "obligate"
    EMPOWER = "empower"


@dataclass(frozen=True)
class ConditionRequirement:
    """Precondition or constraint required for rule activation."""
    condition_id: str
    description: str
    fact_key: str
    required_value: Any = True
    indispensable: bool = True


@dataclass(frozen=True)
class LegalRule:
    """A formalized normative rule within a reviewed rule pack."""
    rule_id: str
    name: str
    effect: RuleEffect
    applicable_operations: List[str]
    conditions: List[ConditionRequirement] = field(default_factory=list)
    priority: int = 100
    statutory_interval: Optional[Dict[str, Any]] = None
    revoked: bool = False


@dataclass(frozen=True)
class RulePack:
    """A collection of reviewed legal rules governing a specific jurisdiction or subject domain."""
    pack_id: str
    title: str
    rules: List[LegalRule]
    coverage_scope: str = "general"
    review_receipt_ref: Optional[str] = None
