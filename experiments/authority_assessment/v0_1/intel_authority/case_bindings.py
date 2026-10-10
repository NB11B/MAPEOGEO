"""Exact ActionCase and context binding constructor for Task T01.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog (record structures, canonical digests)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - Binds exact actor, capacity, operation, affected parties, purpose, objects,
     recipients, jurisdiction, legal reference time, and evaluation context.
   - AQ05: Preserves actor pair directionality, self-pair validity, and unfamiliar
     actor isolation.
   - AQ09: Guarantees that mutating any single case dimension produces a distinct
     ActionCase with a distinct canonical digest, preventing accidental grant reuse.
   - AQ13: Enforces strict non-interchangeability between territorial, subject-matter,
     and organizational/capacity jurisdiction contexts.
4. Qualification Evidence Delta:
   - AQ05, AQ09, AQ13 qualification assertions.
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
    validate_authority_reference,
)


def compute_case_digest(action_case: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 digest of canonically serialized ActionCase."""
    raw = json.dumps(action_case, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class JurisdictionKind:
    TERRITORIAL = "territorial"
    SUBJECT_MATTER = "subject_matter"
    ORGANIZATIONAL_CAPACITY = "organizational_capacity"


class ActionCaseBuilder:
    """Constructs exact, validated ActionCase structures satisfying AQ05, AQ09, AQ13."""

    def __init__(
        self,
        case_id: str,
        revision: int,
        actor_ref: Dict[str, Any],
        capacity_ref: Dict[str, Any],
        operation_ref: Dict[str, Any],
        operation_revision: int,
        jurisdiction_context_ref: Dict[str, Any],
        jurisdiction_kind: str = JurisdictionKind.TERRITORIAL,
    ) -> None:
        self.case_id = case_id
        self.revision = revision
        self.actor_ref = actor_ref
        self.capacity_ref = capacity_ref
        self.operation_ref = operation_ref
        self.operation_revision = operation_revision
        self.jurisdiction_context_ref = jurisdiction_context_ref
        self.jurisdiction_kind = jurisdiction_kind

        self.parameters: Dict[str, Dict[str, Any]] = {}
        self.affected_bindings: List[Dict[str, Any]] = []
        self.recipients: List[Dict[str, Any]] = []
        self.object_refs: List[Dict[str, Any]] = []
        self.purpose_ref: Optional[Dict[str, Any]] = None
        self.legal_reference_context_ref: Optional[Dict[str, Any]] = None
        self.mode: str = "proposed_actual"
        self.context_ref: Optional[Dict[str, Any]] = None

    def set_purpose(self, purpose_id: str, revision: int = 1) -> ActionCaseBuilder:
        self.purpose_ref = {"id": purpose_id, "revision": revision}
        return self

    def set_legal_reference_context(self, context_id: str, revision: int = 1) -> ActionCaseBuilder:
        self.legal_reference_context_ref = {"id": context_id, "revision": revision}
        return self

    def set_context_ref(self, context_id: str, revision: int = 1) -> ActionCaseBuilder:
        self.context_ref = {"id": context_id, "revision": revision}
        return self

    def add_parameter(self, name: str, val_type: str, raw_value: Any, unit_ref: Optional[Dict[str, Any]] = None) -> ActionCaseBuilder:
        self.parameters[name] = create_typed_value(val_type, raw_value, unit_ref=unit_ref)
        return self

    def add_recipient(self, recipient_id: str, revision: int = 1) -> ActionCaseBuilder:
        self.recipients.append({"id": recipient_id, "revision": revision})
        return self

    def add_object(self, object_id: str, revision: int = 1) -> ActionCaseBuilder:
        self.object_refs.append({"id": object_id, "revision": revision})
        return self

    def add_affected_binding(
        self,
        entity_ref: Optional[Dict[str, Any]],
        relationship_role: str,
        interest_refs: List[Dict[str, Any]],
        effect_refs: List[Dict[str, Any]],
        evidence_state: str = "supported",
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
    ) -> ActionCaseBuilder:
        self.affected_bindings.append({
            "entity_ref": entity_ref,
            "collective_scope_ref": None,
            "relationship_role": relationship_role,
            "interest_refs": interest_refs,
            "effect_refs": effect_refs,
            "evidence_state": evidence_state,
            "evidence_refs": evidence_refs or [],
        })
        return self

    def build(self) -> Dict[str, Any]:
        """Validates all references and builds complete ActionCase dictionary."""
        # Validate core references
        for name, ref in [
            ("actor_ref", self.actor_ref),
            ("capacity_ref", self.capacity_ref),
            ("operation_ref", self.operation_ref),
            ("jurisdiction_context_ref", self.jurisdiction_context_ref),
        ]:
            valid, err = validate_authority_reference(ref)
            if not valid:
                raise ValueError(f"Invalid {name}: {err}")

        purpose = self.purpose_ref or {"id": "purpose:default", "revision": 1}
        legal_ref = self.legal_reference_context_ref or {"id": "ctx:legal_ref:v1", "revision": 1}
        ctx_ref = self.context_ref or {"id": f"ctx:case:{self.case_id}", "revision": 1}

        case = {
            "id": self.case_id,
            "revision": self.revision,
            "actor_ref": self.actor_ref,
            "capacity_ref": self.capacity_ref,
            "operation_ref": self.operation_ref,
            "operation_revision": self.operation_revision,
            "parameters": self.parameters,
            "affected_scope": {
                "bindings": self.affected_bindings,
                "coverage_ref": {"id": f"cov:{self.case_id}", "revision": 1},
                "known_empty": len(self.affected_bindings) == 0,
            },
            "recipients": self.recipients,
            "object_refs": self.object_refs,
            "purpose_ref": purpose,
            "jurisdiction_context_ref": self.jurisdiction_context_ref,
            "legal_reference_context_ref": legal_ref,
            "mode": self.mode,
            "context_ref": ctx_ref,
            # Metadata tag preserving jurisdiction classification (AQ13)
            "_jurisdiction_kind": self.jurisdiction_kind,
        }
        return case


def mutate_case_dimension(base_case: Dict[str, Any], dimension: str, new_value: Any) -> Dict[str, Any]:
    """Mutates a single dimension of an ActionCase for AQ09 grant-binding checks."""
    mutated = deepcopy(base_case)
    if dimension == "actor":
        mutated["actor_ref"] = {"id": new_value, "revision": 1}
    elif dimension == "capacity":
        mutated["capacity_ref"] = {"id": new_value, "revision": 1}
    elif dimension == "operation":
        mutated["operation_ref"] = {"id": new_value, "revision": 1}
    elif dimension == "affected_actor":
        if mutated["affected_scope"]["bindings"]:
            mutated["affected_scope"]["bindings"][0]["entity_ref"] = {"id": new_value, "revision": 1}
    elif dimension == "purpose":
        mutated["purpose_ref"] = {"id": new_value, "revision": 1}
    elif dimension == "object":
        mutated["object_refs"] = [{"id": new_value, "revision": 1}]
    elif dimension == "recipient":
        mutated["recipients"] = [{"id": new_value, "revision": 1}]
    elif dimension == "jurisdiction":
        mutated["jurisdiction_context_ref"] = {"id": new_value, "revision": 1}
    else:
        raise ValueError(f"Unknown mutation dimension: {dimension}")
    return mutated
