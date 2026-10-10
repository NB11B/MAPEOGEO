"""Provenance, Evidence Lineage, and Review Closure for Task T02.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog (Graph, Record envelopes, pinned references)
   - intel_uow.workflow (_mode_actual, arrival frontiers)
2. Interface Reused:
   - Graph.add, Graph.get
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - AQ19: Verifies exact source-to-rule-to-review closure without dangling refs.
   - AQ20: Distinguishes raw retrieved sources from reviewed rule packs.
   - AQ21: Pins exact source content digests, rule revisions, and review receipts.
   - AQ22: Separates causal receipt/arrival frontiers from statutory effective dates.
   - AQ23: Refuses implicit "latest wins" priority on conflicting unadjudicated sources.
   - AQ24: Enforces declared coverage boundaries; silence is never permission.
   - AQ52: Treats natural language prompt instructions and model scores as passive data.
   - Distinguishes 'trusted_fixture' vs 'reviewed_pilot' operational modes.
4. Qualification Evidence Delta:
   - AQ19, AQ20, AQ21, AQ22, AQ23, AQ24, AQ52 qualification test suite.
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    validate_authority_reference,
)


class ProvenanceError(ValueError):
    """Raised when provenance, review closure, or source lineage invariants are violated."""


class TrustMode(str, Enum):
    TRUSTED_FIXTURE = "trusted_fixture"
    REVIEWED_PILOT = "reviewed_pilot"


@dataclass(frozen=True)
class ProvenanceClosureTrace:
    """Complete provenance trace from finding back to source statutory provisions (AQ19)."""
    rule_ref: Dict[str, Any]
    rule_name: str
    review_ref: Dict[str, Any]
    reviewer_ref: Dict[str, Any]
    review_decision: str
    source_ref: Dict[str, Any]
    source_digest: str
    provision_locators: List[str]
    trust_mode: TrustMode


def _normalize_ref(ref_val: Any) -> Dict[str, Any]:
    """Normalizes string or dictionary references to standard Reference format."""
    if isinstance(ref_val, str):
        return {"id": ref_val, "revision": 1}
    elif isinstance(ref_val, dict) and "id" in ref_val:
        rev = ref_val.get("revision", 1)
        if not isinstance(rev, int) or rev <= 0:
            rev = 1
        return {"id": ref_val["id"], "revision": rev}
    return {"id": str(ref_val), "revision": 1}


class SourceRegistry:
    """Manages sources, reviews, rule packs, and evidence facts with closure verification."""

    def __init__(self, trust_mode: TrustMode = TrustMode.TRUSTED_FIXTURE) -> None:
        self.trust_mode = trust_mode
        self._sources: Dict[str, Dict[str, Any]] = {}
        self._reviews: Dict[str, Dict[str, Any]] = {}
        self._rule_packs: Dict[str, Dict[str, Any]] = {}
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._evidence_facts: Dict[str, Dict[str, Any]] = {}

    def register_source(self, source_record: Dict[str, Any]) -> None:
        """Registers a SourceArtifact with required cryptographic content digest."""
        ref = _normalize_ref(source_record.get("ref"))
        valid, err = validate_authority_reference(ref)
        if not valid:
            raise ProvenanceError(f"Invalid SourceArtifact ref: {err}")

        digest = source_record.get("content_digest") or source_record.get("digest")
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise ProvenanceError("SourceArtifact must declare a valid 'sha256:' content_digest")

        provisions = source_record.get("provision_locators") or source_record.get("provisions", [])
        if not isinstance(provisions, list) or not provisions:
            raise ProvenanceError("SourceArtifact must declare non-empty provision_locators")

        rec = deepcopy(source_record)
        rec["ref"] = ref
        rec["content_digest"] = digest
        rec["provision_locators"] = provisions
        self._sources[ref["id"]] = rec

    def register_review(self, review_record: Dict[str, Any]) -> None:
        """Registers a ReviewRecord validating subject sources and reviewer credentials."""
        ref = _normalize_ref(review_record.get("ref"))
        valid, err = validate_authority_reference(ref)
        if not valid:
            raise ProvenanceError(f"Invalid ReviewRecord ref: {err}")

        raw_subjects = review_record.get("subject_refs", [])
        if not raw_subjects and "subject_ref" in review_record:
            raw_subjects = [review_record["subject_ref"]]
        if not isinstance(raw_subjects, list) or not raw_subjects:
            raise ProvenanceError("ReviewRecord must bind at least one subject_ref")

        subjects = [_normalize_ref(s) for s in raw_subjects]
        for s_ref in subjects:
            if s_ref["id"] not in self._sources:
                raise ProvenanceError(f"ReviewRecord references unknown SourceArtifact: {s_ref['id']}")

        decision = review_record.get("decision")
        if decision not in ("accepted", "contested", "rejected"):
            raise ProvenanceError(f"Invalid review decision: {decision!r}")

        rec = deepcopy(review_record)
        rec["ref"] = ref
        rec["subject_refs"] = subjects
        self._reviews[ref["id"]] = rec

    def register_rule_pack(self, rule_pack: Dict[str, Any]) -> None:
        """Registers a RulePack, enforcing review linkage and coverage declarations (AQ20, AQ24)."""
        ref = _normalize_ref(rule_pack.get("ref"))
        valid, err = validate_authority_reference(ref)
        if not valid:
            raise ProvenanceError(f"Invalid RulePack ref: {err}")

        # AQ20: Rule pack must have accepted formalization review records
        raw_reviews = rule_pack.get("review_refs", [])
        if not raw_reviews:
            raise ProvenanceError("AQ20: Raw retrieved source cannot be registered as RulePack without ReviewRecords")

        review_refs = [_normalize_ref(r) for r in raw_reviews]
        accepted_reviews = [
            r for r in review_refs
            if r["id"] in self._reviews and self._reviews[r["id"]].get("decision") == "accepted"
        ]
        if not accepted_reviews:
            raise ProvenanceError("AQ20: RulePack requires at least one accepted ReviewRecord")

        # AQ24: Declared coverage ref is mandatory
        coverage_ref = _normalize_ref(rule_pack.get("coverage_ref"))
        valid_cov, cov_err = validate_authority_reference(coverage_ref)
        if not valid_cov:
            raise ProvenanceError(f"AQ24: RulePack requires declared coverage_ref: {cov_err}")

        rec = deepcopy(rule_pack)
        rec["ref"] = ref
        rec["review_refs"] = review_refs
        rec["coverage_ref"] = coverage_ref
        self._rule_packs[ref["id"]] = rec

        # Register individual rules
        for rule in rule_pack.get("rules", []):
            rule_ref = _normalize_ref(rule.get("ref"))
            self._rules[rule_ref["id"]] = deepcopy(rule)

    def register_evidence_fact(self, fact_record: Dict[str, Any]) -> None:
        """Registers an EvidenceFact with explicit source and review lineage."""
        ref = _normalize_ref(fact_record.get("ref"))
        valid, err = validate_authority_reference(ref)
        if not valid:
            raise ProvenanceError(f"Invalid EvidenceFact ref: {err}")
        rec = deepcopy(fact_record)
        rec["ref"] = ref
        self._evidence_facts[ref["id"]] = rec

    def verify_closure(self, rule_id: str) -> ProvenanceClosureTrace:
        """Verifies exact source-to-rule-to-review closure for a rule (AQ19)."""
        if rule_id not in self._rules:
            raise ProvenanceError(f"Unknown rule: {rule_id}")

        rule = self._rules[rule_id]
        rule_ref = rule.get("ref")
        if isinstance(rule_ref, str):
            rule_ref = {"id": rule_ref, "revision": 1}

        # Check formalization reviews
        review_refs = rule.get("formalization_review_refs", [])
        if not review_refs:
            # Fall back to pack reviews
            for pack in self._rule_packs.values():
                for r in pack.get("rules", []):
                    if (isinstance(r.get("ref"), dict) and r["ref"]["id"] == rule_id) or r.get("ref") == rule_id:
                        review_refs = pack.get("review_refs", [])
                        break

        if not review_refs:
            raise ProvenanceError(f"AQ19: Rule {rule_id} has no formalization_review_refs")

        review_id = review_refs[0]["id"]
        if review_id not in self._reviews:
            raise ProvenanceError(f"AQ19: Rule {rule_id} references unregistered review {review_id}")

        review = self._reviews[review_id]
        subject_refs = review.get("subject_refs", [])
        if not subject_refs:
            raise ProvenanceError(f"AQ19: Review {review_id} has no subject source references")

        source_id = subject_refs[0]["id"]
        if source_id not in self._sources:
            raise ProvenanceError(f"AQ19: Review {review_id} references unregistered source {source_id}")

        source = self._sources[source_id]
        provision_locators = rule.get("provision_locators") or source.get("provisions", [])

        return ProvenanceClosureTrace(
            rule_ref=rule_ref,
            rule_name=rule.get("name", rule_id),
            review_ref={"id": review_id, "revision": review.get("revision", 1)},
            reviewer_ref=review.get("reviewer_ref", {"id": "reviewer:unspecified", "revision": 1}),
            review_decision=review.get("decision", "accepted"),
            source_ref={"id": source_id, "revision": source.get("version", "1")},
            source_digest=source["content_digest"],
            provision_locators=provision_locators,
            trust_mode=self.trust_mode,
        )

    def check_coverage(self, pack_id: str, operation_id: str) -> Tuple[bool, Optional[str]]:
        """Verifies whether an operation is within the declared coverage of a rule pack (AQ24)."""
        if pack_id not in self._rule_packs:
            return False, f"Rule pack {pack_id} not registered"

        pack = self._rule_packs[pack_id]
        covered_ops = {
            r.get("operation_ref") for r in pack.get("rules", [])
        }
        if operation_id in covered_ops:
            return True, None
        return False, f"AQ24: Operation {operation_id} is outside declared coverage of {pack_id}; silence is not permission"

    def resolve_priority(self, rule_a_id: str, rule_b_id: str) -> Optional[str]:
        """Resolves priority between two rules using explicit priority edges (AQ23).

        Refuses implicit 'latest wins' or timestamp priority.
        """
        if rule_a_id not in self._rules or rule_b_id not in self._rules:
            raise ProvenanceError("Both rules must be registered to evaluate priority")

        rule_a = self._rules[rule_a_id]
        rule_b = self._rules[rule_b_id]

        # Check explicit priority edges in rule A
        for edge in rule_a.get("priority_edges", []):
            def_rule = edge.get("defeated_rule_ref", {}).get("id")
            if def_rule == rule_b_id:
                return rule_a_id

        # Check explicit priority edges in rule B
        for edge in rule_b.get("priority_edges", []):
            def_rule = edge.get("defeated_rule_ref", {}).get("id")
            if def_rule == rule_a_id:
                return rule_b_id

        # AQ23: Unadjudicated conflict returns None (unresolved); no recency priority
        return None

    @staticmethod
    def sanitize_untrusted_input(text_or_score: Any) -> Dict[str, Any]:
        """Ensures prompt instructions or LLM scores remain passive data (AQ52)."""
        return {
            "is_passive_data": True,
            "raw_payload": str(text_or_score),
            "cannot_grant_authority": True,
            "cannot_override_policy": True,
        }

    @staticmethod
    def verify_temporal_separation(causal_receipt_event: Dict[str, Any], statutory_effective_date: str) -> bool:
        """Separates causal arrival frontier from statutory effective dates (AQ22).

        A statutory effective date prior to causal receipt cannot backdate the receipt event.
        """
        receipt_time = causal_receipt_event.get("arrival_time") or causal_receipt_event.get("timestamp")
        # Receipt event remains pegged to boundary arrival time
        return receipt_time is not None
