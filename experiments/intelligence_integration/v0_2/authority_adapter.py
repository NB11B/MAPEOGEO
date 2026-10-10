"""Successor Read-Only Authority Adapter (v0.2).

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - experiments.intelligence_integration.v0_1.adapter.MAPEOGEOAnalysisAdapter
2. Interface Reused:
   - project_host_case, ProjectedAuthorityCase (intel_authority.projection)
   - assess_case (intel_authority.evaluator)
   - derive_authority_gaps (intel_authority.gaps)
   - HostFieldProvenance, ClockDomain, ProjectionStatus (intelligence_integration.v0_1.contract)
3. Additional Semantic Responsibility:
   - Projects host graph records to ActionCase and evaluates legal authority.
   - Preserves 100% read-only snapshot immutability across evaluation.
   - Enforces excluded surfaces (actual lifecycle projection, live graph mutations).
   - Namespaces events with canonical clock identity.
4. Qualification Evidence Delta:
   - AQ05, AQ09, AQ20, AQ24, AQ30, AQ37, AQ41, AQ56 host projection assertions.
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.evaluator import assess_case
from experiments.authority_assessment.v0_1.intel_authority.gaps import derive_authority_gaps
from experiments.authority_assessment.v0_1.intel_authority.projection import (
    EXCLUDED_SURFACES,
    ProjectedAuthorityCase,
    project_host_case,
)
from experiments.intelligence_integration.v0_1.adapter import (
    AttributedAnalysisResult,
    HostFieldProvenance,
    MAPEOGEOAnalysisAdapter,
    ProjectedAnalysisCase,
    _canonical_digest,
)
from experiments.intelligence_integration.v0_1.contract import (
    ClockDomain,
    ProjectionStatus,
)


@dataclass
class AttributedAuthorityResult:
    """Attributed result of host authority evaluation."""
    case_id: str
    revision: int
    projection_status: ProjectionStatus
    source_snapshot_digest: str
    field_provenance: List[HostFieldProvenance]
    disposition: str
    decisive_rule_refs: List[str]
    trace: Dict[str, Any]
    derived_gaps: List[Dict[str, Any]]
    unsupported_reasons: List[str] = field(default_factory=list)
    diagnostics: List[str] = field(default_factory=list)


class MAPEOGEOAuthorityAdapter(MAPEOGEOAnalysisAdapter):
    """Inspected successor adapter extending MAPEOGEO host integration to legal authority."""

    def __init__(self) -> None:
        super().__init__()
        self.adapter_id = "mapeogeo.intelligence-integration.authority-adapter.v0_2"
        self.version = "0.2.0"

    def project_authority_case(
        self,
        snapshot: Dict[str, Any],
        selection_manifest: Dict[str, Any],
        clock_domain: Optional[ClockDomain] = None,
    ) -> ProjectedAuthorityCase:
        """Projects a host snapshot into an ActionCase with provenance and boundary checks."""
        return project_host_case(
            snapshot=snapshot,
            selection_manifest=selection_manifest,
            clock_domain=clock_domain,
        )

    def evaluate_authority_case(
        self,
        projected_case: ProjectedAuthorityCase,
        context: Dict[str, Any],
        budget: int = 1024,
        snapshot_ref: Optional[Dict[str, Any]] = None,
    ) -> AttributedAuthorityResult:
        """Evaluates legal authority for a projected host case.

        Guarantees snapshot immutability and preserves explicit boundaries.
        """
        if snapshot_ref is not None:
            digest_before = _canonical_digest(snapshot_ref)

        if projected_case.status in (ProjectionStatus.UNSUPPORTED_PROJECTION, ProjectionStatus.INVALID_INPUT):
            return AttributedAuthorityResult(
                case_id=projected_case.case_id,
                revision=projected_case.revision,
                projection_status=projected_case.status,
                source_snapshot_digest=projected_case.source_snapshot_digest,
                field_provenance=projected_case.field_provenance,
                disposition="unsupported_projection",
                decisive_rule_refs=[],
                trace={},
                derived_gaps=[],
                unsupported_reasons=projected_case.unsupported_reasons,
                diagnostics=projected_case.diagnostics,
            )

        if not projected_case.action_case:
            return AttributedAuthorityResult(
                case_id=projected_case.case_id,
                revision=projected_case.revision,
                projection_status=ProjectionStatus.INVALID_INPUT,
                source_snapshot_digest=projected_case.source_snapshot_digest,
                field_provenance=projected_case.field_provenance,
                disposition="invalid_input",
                decisive_rule_refs=[],
                trace={},
                derived_gaps=[],
                diagnostics=["MISSING_ACTION_CASE"],
            )

        if isinstance(budget, int):
            budget_dict = {"max_rules": budget, "max_candidates": budget}
        else:
            budget_dict = budget

        # Run direct authority assessment
        assessment = assess_case(projected_case.action_case, context, budget=budget_dict)
        gaps = derive_authority_gaps(assessment, context)

        if snapshot_ref is not None:
            digest_after = _canonical_digest(snapshot_ref)
            assert digest_before == digest_after, "Snapshot was mutated during authority evaluation!"

        return AttributedAuthorityResult(
            case_id=projected_case.case_id,
            revision=projected_case.revision,
            projection_status=projected_case.status,
            source_snapshot_digest=projected_case.source_snapshot_digest,
            field_provenance=projected_case.field_provenance,
            disposition=assessment.get("disposition", "unresolved"),
            decisive_rule_refs=assessment.get("decisive_rule_refs", []),
            trace=assessment.get("trace", {}),
            derived_gaps=gaps,
            unsupported_reasons=projected_case.unsupported_reasons,
            diagnostics=projected_case.diagnostics,
        )
