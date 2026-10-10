"""Catalog and Graph Extension for Authority Assessment (Task T01).

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog.Catalog
   - intel_uow.catalog.Graph
2. Interface Reused:
   - Catalog.__init__, Catalog.validate
   - Graph.__init__, Graph.add, Graph.get, Graph.relate, Graph.snapshot
3. Additional Semantic Responsibility:
   - Extends the pristine reference Catalog with declared authority records from
     authority_contracts_v0_1.json without mutating the base contracts file.
   - Enforces layer boundaries and context-pinning rules for authority records.
   - Emits technical Diagnostic records for malformed structures without
     fabricating substantive legal dispositions (AQ56).
   - Manages envelope mapping between base catalog envelopes and authority payloads.
4. Qualification Evidence Delta:
   - Immutability of base contracts.
   - AQ56 (input and budget boundaries do not masquerade as law).
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure access to pinned reference intel_uow package
REPO_ROOT = Path(__file__).resolve().parents[4]
REF_PKG_DIR = REPO_ROOT / "artifacts" / "intelligence_qualification" / "v0_3" / "intelligence_qualification_v0_3"
if str(REF_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(REF_PKG_DIR))

from intel_uow.catalog import Catalog, Graph, _reference, _revision


# Authority Record Required Fields from authority_contracts_v0_1.json
AUTHORITY_RECORDS: Dict[str, Tuple[str, ...]] = {
    "ActorRecord": ("ref", "kind", "identity_evidence_refs", "capacity_refs"),
    "CapacityRecord": ("ref", "actor_ref", "capacity_kind", "scope_ref", "evidence_refs", "evidence_state"),
    "InterestRecord": ("ref", "holder_ref", "interest_kind", "scope_ref", "evidence_refs"),
    "OperationDefinition": ("ref", "parameter_spec", "actor_capacity_kinds", "affected_role_kinds", "effect_definitions", "functional_lenses"),
    "ActionCase": ("id", "revision", "actor_ref", "capacity_ref", "operation_ref", "operation_revision", "parameters", "affected_scope", "recipients", "object_refs", "purpose_ref", "jurisdiction_context_ref", "legal_reference_context_ref", "mode", "context_ref"),
    "ClaimOfAuthority": ("ref", "claimant_ref", "case_ref", "source_refs", "claim_text", "evidence_state", "mode"),
    "SourceArtifact": ("ref", "source_kind", "uri", "provision_locators", "provenance_refs", "legal_time_claim_refs", "content_digest"),
    "ReviewRecord": ("ref", "reviewer_ref", "review_capacity_ref", "review_kind", "subject_refs", "decision", "scope_ref", "rationale", "limitations", "boundary_ref", "acceptance_receipt_ref", "trust_mode"),
    "RulePack": ("ref", "source_refs", "review_refs", "jurisdiction_profile_ref", "interpretation_profile_ref", "coverage_ref", "rules", "basis_policy", "default_basis_rule_refs", "composition_policy_ref", "registry_ref", "semantic_profile"),
    "NormRule": ("ref", "source_refs", "provision_locators", "formalization_review_refs", "applicability", "antecedent", "conclusion", "entry_conditions", "duty_refs", "exception_rule_refs", "priority_edges"),
    "DutyRecord": ("ref", "bearer_ref", "beneficiary_refs", "conduct_ref", "trigger", "phase", "timing_ref", "satisfaction_contract_ref", "evidence_refs", "discharge_state"),
    "EvidenceFact": ("ref", "subject_ref", "predicate_ref", "value", "evidence_state", "source_ref", "review_ref"),
    "LegalAssessment": ("ref", "case_ref", "scope_pack_ref", "disposition", "applicable_rule_refs", "decisive_rule_refs", "condition_states", "affected_interest_refs", "coverage_state", "gaps", "explanation", "case_digest"),
    "AdmissionDecision": ("ref", "work_item_ref", "proposal_ref", "admitted", "reason", "assigned_budget"),
}

# Authority Allowed Storage Layers
AUTHORITY_ALLOWED_LAYERS: Dict[str, Set[str]] = {
    "ActorRecord": {"registry"},
    "CapacityRecord": {"registry"},
    "InterestRecord": {"registry"},
    "OperationDefinition": {"registry"},
    "ActionCase": {"subject_hypothesis"},
    "ClaimOfAuthority": {"source", "scenario", "actual_uow"},
    "SourceArtifact": {"source"},
    "ReviewRecord": {"source", "registry"},
    "RulePack": {"registry"},
    "NormRule": {"registry"},
    "DutyRecord": {"registry"},
    "EvidenceFact": {"source", "actual_uow"},
    "LegalAssessment": {"actual_uow"},
    "AdmissionDecision": {"actual_uow"},
}


class AuthorityCatalog(Catalog):
    """Extends the reference Catalog with domain-specific authority records.

    Leaves base contracts and existing schema completely unchanged.
    """

    def __init__(self, base_contracts_path: Optional[Path] = None) -> None:
        super().__init__(base_contracts_path)

        # Register authority records without modifying underlying base catalog json
        for rec_name, fields in AUTHORITY_RECORDS.items():
            self.required[rec_name] = fields
            self.allowed_layers[rec_name] = frozenset(AUTHORITY_ALLOWED_LAYERS.get(rec_name, self.layers))

        # Register authority relation vocabulary
        authority_relations = {
            "ASSESSED_UNDER",
            "GOVERNED_BY_RULE",
            "DELEGATES_TO",
            "DISCHARGES_DUTY",
            "BURDENS_INTEREST",
        }
        self.relation_kinds = frozenset(set(self.relation_kinds) | authority_relations)

    def validate_authority_record(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validates an authority record, returning technical Diagnostic structures (AQ56)."""
        diagnostics = []
        if not isinstance(record, dict):
            return [{"code": "MALFORMED_RECORD", "path": "", "message": "Record must be an object", "related_refs": []}]

        kind = record.get("record_type")
        if not isinstance(kind, str) or kind not in self.required:
            diagnostics.append({
                "code": "UNKNOWN_RECORD_TYPE",
                "path": "record_type",
                "message": f"Unknown record_type: {kind}",
                "related_refs": [],
            })
            return diagnostics

        rec_id = record.get("record_id")
        if not isinstance(rec_id, str) or not rec_id:
            diagnostics.append({
                "code": "INVALID_RECORD_ID",
                "path": "record_id",
                "message": "record_id must be a nonempty string",
                "related_refs": [],
            })

        rev = record.get("revision")
        if not _revision(rev):
            diagnostics.append({
                "code": "INVALID_REVISION",
                "path": "revision",
                "message": "revision must be a positive integer",
                "related_refs": [],
            })

        layer = record.get("layer")
        if not isinstance(layer, str) or layer not in self.layers:
            diagnostics.append({
                "code": "UNKNOWN_LAYER",
                "path": "layer",
                "message": f"Unknown graph layer: {layer}",
                "related_refs": [],
            })
        elif layer not in self.allowed_layers.get(kind, self.layers):
            diagnostics.append({
                "code": "ILLEGAL_LAYER",
                "path": "layer",
                "message": f"Record type {kind} not permitted in layer {layer}",
                "related_refs": [],
            })

        for field in self.required[kind]:
            if field not in record:
                diagnostics.append({
                    "code": "MISSING_REQUIRED_FIELD",
                    "path": field,
                    "message": f"Missing required field: {field}",
                    "related_refs": [],
                })

        return diagnostics


class AuthorityGraph(Graph):
    """Extends the reference Graph with authority record support."""

    def __init__(self, catalog: Optional[AuthorityCatalog] = None) -> None:
        super().__init__(catalog=catalog or AuthorityCatalog())

    def add_authority_record(
        self,
        record_type: str,
        record_id: str,
        revision: int,
        layer: str,
        payload: Dict[str, Any],
        context_refs: Optional[List[Dict[str, Any]]] = None,
        provenance_refs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Wraps and adds an authority record into the Graph envelope."""
        envelope: Dict[str, Any] = {
            "record_type": record_type,
            "record_id": record_id,
            "revision": revision,
            "layer": layer,
            "context_refs": context_refs or [],
            "provenance_refs": provenance_refs or [],
        }
        envelope.update(payload)
        return self.add(envelope)
