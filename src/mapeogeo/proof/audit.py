"""Proof Audit Subsystem.

Implements the fundamental architectural invariant:
    generation audit != admission audit

Generation audit records the generator's internal search traces and
resource claims. Admission audit is an independent, fail-closed verification
gate executed at the boundary before admitting proof certificates into the
certified knowledge substrate. Passing generation audit never implies admission.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from mapeogeo.proof.replay import ReplayResult


@dataclass(frozen=True)
class GenerationAuditRecord:
    """Record of generation-time search, heuristics, and trace logging."""

    generator_id: str
    trace_id: str
    steps_evaluated: int
    pruned_branches: int
    cost_consumed: float
    generation_passed: bool
    timestamp_utc: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdmissionAuditRecord:
    """Independent admission-time verification record."""

    auditor_id: str
    passed: bool
    reasons: tuple[str, ...]
    verified_claim_digest: str
    verified_certificate_digest: str
    replay_result: ReplayResult | None
    admitted_at_utc: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProofAudit:
    """Comprehensive dual-audit record for a proof certificate."""

    audit_id: str
    certificate_id: str
    generation_audit: GenerationAuditRecord | None = None
    admission_audit: AdmissionAuditRecord | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_fully_certified(self) -> bool:
        """Admission requires an explicit, passing admission audit.

        Passing generation audit alone is strictly insufficient.
        """
        if self.admission_audit is None:
            return False
        return self.admission_audit.passed

    @staticmethod
    def generation_audit_differs_from_admission() -> bool:
        """Formal invariant marker."""
        return True
