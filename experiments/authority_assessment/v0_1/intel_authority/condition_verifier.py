"""Authority Condition and Applicability Verifier for Task T03.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (evaluator, condition matching)
   - intel_uow.catalog (Record envelope, Diagnostic)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
   - SourceRegistry (intel_authority.provenance_evidence)
3. Additional Semantic Responsibility:
   - AQ03: Evaluates prerequisites distinguishing supported, refuted, unknown,
     and conflicting states; known-unmet yields conditions_unmet, unknown yields
     unresolved with missing factual gap.
   - AQ14: Enforces exact alignment across all required scope dimensions
     (territory, person, subject matter, action, context).
   - AQ15: Evaluates intersection of multiple applicable scopes, ensuring least-
     restrictive or silent scopes never override an explicit constraint.
   - AQ38: Preserves evidence alignment and lineage across reports to target propositions.
   - AQ42: Evaluates legal effective intervals independently of causal counters.
   - AQ49: Implements bilateral 4-state logic over 16 AND, 16 OR, 4 NOT pairs;
     preserves non-explosive uncertainty; evaluates unit-checked quantitative limits.
4. Qualification Evidence Delta:
   - AQ03, AQ14, AQ15, AQ38, AQ42, AQ49 qualification assertions.
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from fractions import Fraction
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
    extract_typed_value,
    validate_authority_reference,
)


class EvidenceState(str, Enum):
    SUPPORTED = "supported"
    REFUTED = "refuted"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


@dataclass(frozen=True)
class BilateralState:
    """Bilateral representation (support, refutation) for 4-state logic (AQ49)."""
    support: bool
    refutation: bool

    @classmethod
    def from_enum(cls, state: EvidenceState | str) -> BilateralState:
        s = state.value if isinstance(state, EvidenceState) else state
        if s == "supported":
            return cls(True, False)
        elif s == "refuted":
            return cls(False, True)
        elif s == "conflicting":
            return cls(True, True)
        elif s == "unknown":
            return cls(False, False)
        raise ValueError(f"Unknown evidence state: {state!r}")

    def to_enum(self) -> EvidenceState:
        if self.support and not self.refutation:
            return EvidenceState.SUPPORTED
        elif not self.support and self.refutation:
            return EvidenceState.REFUTED
        elif self.support and self.refutation:
            return EvidenceState.CONFLICTING
        else:
            return EvidenceState.UNKNOWN

    def logical_not(self) -> BilateralState:
        """NOT (s, r) = (r, s)."""
        return BilateralState(self.refutation, self.support)

    def logical_and(self, other: BilateralState) -> BilateralState:
        """AND (s1, r1) & (s2, r2) = (s1 & s2, r1 | r2)."""
        return BilateralState(
            self.support and other.support,
            self.refutation or other.refutation,
        )

    def logical_or(self, other: BilateralState) -> BilateralState:
        """OR (s1, r1) | (s2, r2) = (s1 | s2, r1 & r2)."""
        return BilateralState(
            self.support or other.support,
            self.refutation and other.refutation,
        )


def evaluate_four_state_not(state: EvidenceState | str) -> EvidenceState:
    """Evaluates 4-state logical negation (AQ49)."""
    return BilateralState.from_enum(state).logical_not().to_enum()


def evaluate_four_state_and(left: EvidenceState | str, right: EvidenceState | str) -> EvidenceState:
    """Evaluates 4-state logical conjunction (AQ49)."""
    return BilateralState.from_enum(left).logical_and(BilateralState.from_enum(right)).to_enum()


def evaluate_four_state_or(left: EvidenceState | str, right: EvidenceState | str) -> EvidenceState:
    """Evaluates 4-state logical disjunction (AQ49)."""
    return BilateralState.from_enum(left).logical_or(BilateralState.from_enum(right)).to_enum()


class ConditionVerifier:
    """Evaluates authority condition expressions and applicability over evidence snapshots."""

    def __init__(self, evidence_facts: Optional[List[Dict[str, Any]]] = None) -> None:
        self.evidence_facts = evidence_facts or []

    def evaluate_leaf_proposition(self, predicate_id: str, subject_id: Optional[str] = None) -> Tuple[EvidenceState, List[Dict[str, Any]]]:
        """Resolves all aligned accepted evidence for a predicate/subject (AQ38, AQ49)."""
        matching = []
        for fact in self.evidence_facts:
            pred = fact.get("predicate_ref", {})
            pred_id = pred.get("id") if isinstance(pred, dict) else str(pred)
            if pred_id != predicate_id:
                continue

            if subject_id is not None:
                subj = fact.get("subject_ref", {})
                subj_id = subj.get("id") if isinstance(subj, dict) else str(subj)
                if subj_id != subject_id:
                    continue

            matching.append(fact)

        if not matching:
            return EvidenceState.UNKNOWN, []

        has_support = any(f.get("value") in ("supported", "support", True) or f.get("polarity") == "support" for f in matching)
        has_refutation = any(f.get("value") in ("refuted", "refutation", False) or f.get("polarity") == "refutation" for f in matching)

        if has_support and has_refutation:
            return EvidenceState.CONFLICTING, matching
        elif has_support:
            return EvidenceState.SUPPORTED, matching
        elif has_refutation:
            return EvidenceState.REFUTED, matching
        else:
            return EvidenceState.UNKNOWN, matching

    def evaluate_quantitative_comparison(
        self,
        op: str,
        case_val: Any,
        case_unit: Optional[str],
        limit_val: Any,
        limit_unit: Optional[str],
    ) -> Tuple[EvidenceState, Optional[str]]:
        """Evaluates quantitative inequality with unit compatibility and conflict handling (AQ49)."""
        # Unit compatibility check
        if case_unit != limit_unit:
            return EvidenceState.UNKNOWN, f"Incompatible units: case has '{case_unit}', limit requires '{limit_unit}'"

        try:
            c_num = Decimal(str(case_val))
            l_num = Decimal(str(limit_val))
        except Exception:
            return EvidenceState.UNKNOWN, "Malformed numeric parameter in quantitative comparison"

        if op in ("le", "<="):
            return (EvidenceState.SUPPORTED if c_num <= l_num else EvidenceState.REFUTED), None
        elif op in ("lt", "<"):
            return (EvidenceState.SUPPORTED if c_num < l_num else EvidenceState.REFUTED), None
        elif op in ("ge", ">="):
            return (EvidenceState.SUPPORTED if c_num >= l_num else EvidenceState.REFUTED), None
        elif op in ("gt", ">"):
            return (EvidenceState.SUPPORTED if c_num > l_num else EvidenceState.REFUTED), None
        elif op in ("eq", "=="):
            return (EvidenceState.SUPPORTED if c_num == l_num else EvidenceState.REFUTED), None
        else:
            return EvidenceState.UNKNOWN, f"Unknown comparison operator: {op}"

    def evaluate_condition_expr(self, expr: Dict[str, Any], context_params: Optional[Dict[str, Any]] = None) -> EvidenceState:
        """Recursively evaluates a ConditionExpr using 4-state bilattice logic."""
        if not isinstance(expr, dict):
            return EvidenceState.UNKNOWN

        op = expr.get("op", "fact")

        if op == "fact":
            fact_ref = expr.get("fact_ref", {})
            pred_id = fact_ref.get("id") if isinstance(fact_ref, dict) else str(fact_ref)
            subj_ref = expr.get("subject_ref", {})
            subj_id = subj_ref.get("id") if isinstance(subj_ref, dict) else None
            state, _ = self.evaluate_leaf_proposition(pred_id, subj_id)
            return state

        elif op == "not":
            args = expr.get("args", [])
            if not args:
                return EvidenceState.UNKNOWN
            inner = self.evaluate_condition_expr(args[0], context_params)
            return evaluate_four_state_not(inner)

        elif op == "all":
            args = expr.get("args", [])
            if not args:
                return EvidenceState.SUPPORTED
            current = self.evaluate_condition_expr(args[0], context_params)
            for a in args[1:]:
                nxt = self.evaluate_condition_expr(a, context_params)
                current = evaluate_four_state_and(current, nxt)
            return current

        elif op == "any":
            args = expr.get("args", [])
            if not args:
                return EvidenceState.REFUTED
            current = self.evaluate_condition_expr(args[0], context_params)
            for a in args[1:]:
                nxt = self.evaluate_condition_expr(a, context_params)
                current = evaluate_four_state_or(current, nxt)
            return current

        elif op in ("le", "ge", "eq"):
            left = expr.get("left", {})
            right = expr.get("right", {})
            c_val = left.get("value")
            c_unit = left.get("unit")
            l_val = right.get("value")
            l_unit = right.get("unit")
            state, _ = self.evaluate_quantitative_comparison(op, c_val, c_unit, l_val, l_unit)
            return state

        return EvidenceState.UNKNOWN

    @staticmethod
    def verify_scope_alignment(
        required_scope: Dict[str, str],
        presented_scope: Dict[str, str],
    ) -> Tuple[bool, List[str]]:
        """Verifies exact alignment across territory, person, subject matter, and action (AQ14)."""
        mismatches = []
        for dim in ("territory", "person", "subject_matter", "action"):
            req = required_scope.get(dim)
            pres = presented_scope.get(dim)
            if req is not None and req != pres:
                mismatches.append(f"Scope mismatch on '{dim}': required '{req}', presented '{pres}'")
        return len(mismatches) == 0, mismatches

    @staticmethod
    def intersect_applicable_scopes(scopes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Intersects multiple applicable scopes preserving strictest constraints (AQ15).

        A silent or less-restrictive scope cannot override an explicit prohibition or duty.
        """
        if not scopes:
            return {"prohibitions": [], "duties": [], "permissions": []}

        all_prohibitions: Set[str] = set()
        all_duties: Set[str] = set()
        all_permissions: Set[str] = set()

        for s in scopes:
            all_prohibitions.update(s.get("prohibitions", []))
            all_duties.update(s.get("duties", []))
            all_permissions.update(s.get("permissions", []))

        # Prohibitions trump permissions
        effective_permissions = sorted(list(all_permissions - all_prohibitions))

        return {
            "prohibitions": sorted(list(all_prohibitions)),
            "duties": sorted(list(all_duties)),
            "permissions": effective_permissions,
            "has_conflicting_prohibition": bool(all_permissions & all_prohibitions),
        }

    def evaluate_corroborated_leaf_proposition(
        self,
        predicate_id: str,
        subject_id: Optional[str] = None,
        min_independent_sources: int = 1,
    ) -> Tuple[EvidenceState, Set[str], List[Dict[str, Any]]]:
        """Resolves leaf proposition with strict lineage tracking across distinct origins (AQ38).

        Repeated reports from the same common source artifact do not count as independent corroboration.
        """
        state, matching = self.evaluate_leaf_proposition(predicate_id, subject_id)
        if state != EvidenceState.SUPPORTED:
            return state, set(), matching

        # Track distinct source artifact lineages
        origins: Set[str] = set()
        for f in matching:
            origin = f.get("source_artifact_ref", {})
            origin_id = origin.get("id") if isinstance(origin, dict) else str(origin)
            if origin_id:
                origins.add(origin_id)

        if len(origins) < min_independent_sources:
            return EvidenceState.UNKNOWN, origins, matching

        return EvidenceState.SUPPORTED, origins, matching

    @staticmethod
    def verify_effective_time_interval(
        effective_from: Optional[str],
        effective_to: Optional[str],
        case_time: Optional[str],
        has_calibrated_mapping: bool = False,
    ) -> Tuple[EvidenceState, Optional[str]]:
        """Evaluates legal effective time intervals separately from UoW counters (AQ42).

        A raw causal counter or missing reference time mapping leaves applicability unresolved (UNKNOWN).
        """
        if case_time is None:
            return EvidenceState.UNKNOWN, "Missing case reference time"

        # Check if case_time is a raw UoW sequence/counter rather than calibrated wall/calendar time
        if not has_calibrated_mapping and (
            case_time.isdigit()
            or case_time.startswith("seq:")
            or case_time.startswith("uow:")
            or case_time.startswith("step:")
        ):
            return EvidenceState.UNKNOWN, f"Raw UoW counter '{case_time}' cannot determine statutory effective time without clock mapping"

        # If calibrated mapping is present or case_time is an ISO timestamp / calendar date
        try:
            if effective_from and case_time < effective_from:
                return EvidenceState.REFUTED, f"Case time '{case_time}' precedes statutory effective_from '{effective_from}'"
            if effective_to and case_time > effective_to:
                return EvidenceState.REFUTED, f"Case time '{case_time}' exceeds statutory effective_to '{effective_to}'"
            return EvidenceState.SUPPORTED, None
        except Exception as e:
            return EvidenceState.UNKNOWN, f"Cannot evaluate effective time interval: {e}"
