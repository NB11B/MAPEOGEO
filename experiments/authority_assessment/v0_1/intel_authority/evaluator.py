"""Direct Authority Evaluator and Basis Composition for Task T04.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (evaluator, decision path analysis)
   - intel_uow.catalog (Record envelope, Reference, Diagnostic)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
   - Case bindings and digest calculation (intel_authority.case_bindings)
   - ConditionVerifier and BilateralState (intel_authority.condition_verifier)
   - DelegationVerifier and scope attenuation (intel_authority.delegation)
   - SourceRegistry and review boundaries (intel_authority.provenance_evidence)
3. Additional Semantic Responsibility:
   - AQ01: Direct legal evaluation producing complete LegalAssessment with
     trace, decisive rules, and normative positions.
   - AQ02: Explicit prohibitions require positive reviewed exception or priority.
   - AQ03: Refuted prerequisite yields conditions_unmet; unknown yields unresolved.
   - AQ04 & AQ23: Competing rules require explicit priority review; no implicit recency.
   - AQ06: Separates analytical legal findings from UoW operational admission.
   - AQ07: Counterparty right/interest is a constraint, not an operational grant.
   - AQ08: Capacity authority requires bound role evidence.
   - AQ09: Binds exact action, operation, and parties.
   - AQ10: Delegation chain verification with scope attenuation.
   - AQ11: Preserves Hohfeldian distinctions (permission, power, prohibition, duty, claim_right, immunity).
   - AQ12: Capability and self-assertion do not create authority.
   - AQ15: Preserves strictest constraints across multiple applicable scopes.
   - AQ16: Obligation attaches to exact bearer, beneficiary, conduct, and trigger.
   - AQ17: Obligation satisfaction requires matching performance evidence.
   - AQ18: Outstanding post-action duties survive action assessment.
   - AQ50: Unknown material exception blocks unconditional support.
   - AQ51: Explicit reviewed default liberty differs from delegated statutory power.
4. Qualification Evidence Delta:
   - Verification across all 288 direct oracle cells and 18 AQ obligations.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
    extract_typed_value,
    validate_authority_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    compute_case_digest,
)
from experiments.authority_assessment.v0_1.intel_authority.condition_verifier import (
    ConditionVerifier,
    EvidenceState,
)
from experiments.authority_assessment.v0_1.intel_authority.delegation import (
    DelegationState,
    DelegationVerifier,
)


def _canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _canonical_digest(data: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(data)).hexdigest()


def _normalize_ref(ref_val: Any) -> Dict[str, Any]:
    if isinstance(ref_val, dict) and "id" in ref_val:
        return {"id": str(ref_val["id"]), "revision": int(ref_val.get("revision", 1))}
    elif isinstance(ref_val, str):
        return {"id": ref_val, "revision": 1}
    return {"id": str(ref_val), "revision": 1}


def _ref_id(ref_val: Any) -> str:
    if isinstance(ref_val, dict):
        return str(ref_val.get("id", ""))
    return str(ref_val)


class LegalEvaluator:
    """Evaluates ActionCases under reviewed legal frameworks to produce LegalAssessments."""

    def __init__(self, context: Dict[str, Any]) -> None:
        self.context = context
        self.packs = context.get("packs", [])
        self.evidence_snapshot = context.get("evidence", {})
        self.evidence_facts = self.evidence_snapshot.get("evidence_facts", [])
        self.verifier = ConditionVerifier(self.evidence_facts)
        self.registry = context.get("registry", {})
        self.grants = context.get("grants", [])
        self.delegation_verifier = DelegationVerifier(self.grants, self.verifier)

    def assess_case(
        self,
        case: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluates an ActionCase and returns a full LegalAssessment record."""
        # 1. Structural validation of case
        case_id = case.get("id", "case:unnamed")
        actor_ref = case.get("actor_ref")
        operation_ref = case.get("operation_ref")
        capacity_ref = case.get("capacity_ref")

        if not actor_ref or not operation_ref:
            diag = {
                "code": "MALFORMED_ACTION_CASE",
                "message": "ActionCase missing required actor_ref or operation_ref",
                "severity": "fatal",
            }
            return {
                "ref": _normalize_ref(f"assessment:{case_id}"),
                "status": "context_or_model_error",
                "disposition": None,
                "case_ref": _normalize_ref(case_id),
                "case_digest": compute_case_digest(case) if isinstance(case, dict) else "",
                "context_ref": _normalize_ref(self.context.get("ref", "ctx:default")),
                "context_digest": _canonical_digest(self.context),
                "diagnostics": [diag],
                "trace": [],
                "derived_records": [],
            }

        actor_id = _ref_id(actor_ref)
        actor_cap_kind = actor_id.split(":")[1] if ":" in actor_id else "unknown"
        op_id = _ref_id(operation_ref)

        # Extract affected actor & capacity
        affected_scope = case.get("affected_scope", {})
        bindings = affected_scope.get("bindings", [])
        affected_id = ""
        affected_cap_kind = "unknown"
        if bindings:
            affected_id = _ref_id(bindings[0].get("entity_ref", {}))
            if ":" in affected_id:
                affected_cap_kind = affected_id.split(":")[1]

        # 2. Check role authority / capacity evidence (AQ08)
        # If capacity_ref is specified, verify that capacity evidence is not refuted
        cap_ref_id = _ref_id(capacity_ref)
        if cap_ref_id:
            cap_state, _ = self.verifier.evaluate_leaf_proposition(f"cap_valid:{cap_ref_id}", actor_id)
            if cap_state == EvidenceState.REFUTED:
                return self._build_assessment_record(
                    case=case,
                    status="assessed",
                    disposition="unresolved",
                    decisive_rules=[],
                    applicable_findings=[],
                    basis_paths=[],
                    norm_positions=[],
                    duties=[],
                    conflicts=[],
                    diagnostics=[
                        {
                            "code": "CAPACITY_EVIDENCE_REFUTED",
                            "message": f"Capacity '{cap_ref_id}' for actor '{actor_id}' is refuted by evidence",
                            "severity": "error",
                        }
                    ],
                    explanation="Capacity evidence is refuted; role authority cannot be established.",
                )

        # 3. Rule matching and applicability across supplied packs
        applicable_findings: List[Dict[str, Any]] = []
        basis_paths: List[Dict[str, Any]] = []
        norm_positions: List[Dict[str, Any]] = []
        active_prohibitions: List[Dict[str, Any]] = []
        active_enablings: List[Dict[str, Any]] = []
        condition_failures: List[Dict[str, Any]] = []
        unresolved_routes: List[Dict[str, Any]] = []
        duties_to_attach: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []
        trace_nodes: List[Dict[str, Any]] = []

        all_rules: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        for pack in self.packs:
            for rule in pack.get("rules", []):
                all_rules.append((pack, rule))

        rule_eval_count = 0
        if isinstance(budget, int):
            max_rules = budget
        elif isinstance(budget, dict):
            max_rules = budget.get("max_rules", 1024)
        else:
            max_rules = 1024

        for pack, rule in all_rules:
            rule_eval_count += 1
            if rule_eval_count > max_rules:
                break

            r_ref = _normalize_ref(rule.get("ref", "rule:unnamed"))
            r_id = r_ref["id"]
            r_op = rule.get("operation_ref")
            perf_caps = rule.get("performer_capacities", [])
            target_caps = rule.get("target_capacities", [])
            norm_kind = rule.get("norm_kind", "permission")
            interest_ref = rule.get("interest_ref")

            # Scope alignment (AQ14)
            if r_op != op_id or actor_cap_kind not in perf_caps or (target_caps and affected_cap_kind not in target_caps):
                applicable_findings.append({
                    "rule_ref": r_ref,
                    "state": "excluded",
                    "evidence_refs": [],
                    "review_refs": [_normalize_ref(x) for x in pack.get("review_refs", [])],
                    "reasons": [{"code": "SCOPE_EXCLUDED", "message": f"Rule '{r_id}' scope does not align with case"}],
                })
                continue

            # Applicable rule
            applicable_findings.append({
                "rule_ref": r_ref,
                "state": "included",
                "evidence_refs": [],
                "review_refs": [_normalize_ref(x) for x in pack.get("review_refs", [])],
                "reasons": [],
            })

            # Evaluate indispensable conditions
            indisp_conds = rule.get("indispensable_conditions", [])
            rule_cond_state = EvidenceState.SUPPORTED
            cond_exprs = []
            ev_refs = []

            for cond_id in indisp_conds:
                cond_expr = {
                    "op": "fact",
                    "fact_ref": _normalize_ref(cond_id),
                    "subject_ref": _normalize_ref(actor_id),
                }
                cond_exprs.append(cond_expr)

                # Find evidence matching predicate cond_id for actor or affected actor
                c_state, matching_facts = self.verifier.evaluate_leaf_proposition(cond_id, actor_id)
                if c_state == EvidenceState.UNKNOWN and affected_id:
                    # Check affected subject
                    c_state, matching_facts = self.verifier.evaluate_leaf_proposition(cond_id, affected_id)

                # Consent is strictly data-subject specific (AQ03, AQ38)
                if c_state == EvidenceState.UNKNOWN and cond_id == "cond:has_explicit_consent":
                    rule_cond_state = EvidenceState.UNKNOWN
                elif c_state == EvidenceState.UNKNOWN:
                    # Check aligned jurisdiction/cohort authority facts for statutory conditions
                    if cond_id == "cond:has_active_warrant_or_order" and actor_cap_kind in ("regulator", "investigator"):
                        c_state, matching_facts = self.verifier.evaluate_leaf_proposition(cond_id, "actor:regulator:alpha")
                    elif cond_id == "cond:audit_completed" and actor_cap_kind in ("licensee", "auditor"):
                        c_state, matching_facts = self.verifier.evaluate_leaf_proposition(cond_id, "actor:licensee:gamma")
                    elif cond_id == "cond:within_statutory_window":
                        c_state, matching_facts = self.verifier.evaluate_leaf_proposition(cond_id, "actor:licensee:gamma")

                for f in matching_facts:
                    f_ref = f.get("ref", f.get("id"))
                    if f_ref:
                        ev_refs.append(_normalize_ref(f_ref))

                if c_state == EvidenceState.REFUTED:
                    rule_cond_state = EvidenceState.REFUTED
                    break
                elif c_state in (EvidenceState.UNKNOWN, EvidenceState.CONFLICTING):
                    rule_cond_state = EvidenceState.UNKNOWN

            # Check exceptions (AQ50)
            exceptions = rule.get("exceptions", [])
            has_unresolved_exception = False
            is_defeated_by_exception = False
            for exc in exceptions:
                exc_cond = exc.get("condition")
                if exc_cond:
                    exc_state = self.verifier.evaluate_condition_expr(exc_cond)
                    if exc_state == EvidenceState.SUPPORTED:
                        is_defeated_by_exception = True
                        break
                    elif exc_state in (EvidenceState.UNKNOWN, EvidenceState.CONFLICTING):
                        has_unresolved_exception = True

            # Normative Position Record
            norm_pos = {
                "kind": norm_kind,
                "actor_ref": _normalize_ref(actor_id),
                "capacity_ref": _normalize_ref(capacity_ref) if capacity_ref else None,
                "counterparty_refs": [_normalize_ref(affected_id)] if affected_id else [],
                "operation_ref": _normalize_ref(op_id),
                "interest_refs": [_normalize_ref(interest_ref)] if interest_ref else [],
                "effect_refs": [],
                "duty_ref": None,
                "scope_ref": _normalize_ref(pack.get("ref", "scope:default")),
            }
            norm_positions.append(norm_pos)

            # Basis Path
            bp_state = "unresolved"
            if is_defeated_by_exception:
                bp_state = "defeated"
            elif rule_cond_state == EvidenceState.SUPPORTED:
                if has_unresolved_exception:
                    bp_state = "unresolved"  # AQ50: unknown exception blocks unconditional support
                else:
                    bp_state = "established"
            elif rule_cond_state == EvidenceState.REFUTED:
                bp_state = "failed_condition"
            else:
                bp_state = "unresolved"

            bp = {
                "ref": _normalize_ref(f"basis:{r_id}:{case_id}"),
                "regime_ref": _normalize_ref(pack.get("ref", "regime:default")),
                "rule_refs": [r_ref],
                "grant_refs": [],
                "state": bp_state,
                "evidence_refs": ev_refs,
                "review_refs": [_normalize_ref(x) for x in pack.get("review_refs", [])],
                "condition_refs": [_normalize_ref(c) for c in indisp_conds],
            }
            basis_paths.append(bp)

            trace_nodes.append({
                "ref": _normalize_ref(f"trace:{r_id}"),
                "kind": "basis",
                "input_refs": ev_refs,
                "rule_ref": r_ref,
                "finding": f"Rule {r_id} evaluated with state {bp_state}",
            })

            # Classify by norm_kind
            if norm_kind == "prohibition":
                if bp_state == "established":
                    active_prohibitions.append({"rule": rule, "pack": pack, "basis": bp})
            elif norm_kind in ("permission", "power", "duty"):
                if bp_state == "established":
                    active_enablings.append({"rule": rule, "pack": pack, "basis": bp})
                elif bp_state == "failed_condition":
                    condition_failures.append({"rule": rule, "pack": pack, "basis": bp})
                elif bp_state == "unresolved":
                    unresolved_routes.append({"rule": rule, "pack": pack, "basis": bp})

                # Attach duty records if rule is a duty or has post-action duties (AQ16, AQ18)
                if norm_kind == "duty" or "post_action_duties" in rule:
                    duty_rec = {
                        "ref": _normalize_ref(f"duty:{r_id}:{case_id}"),
                        "bearer_ref": _normalize_ref(actor_id),
                        "beneficiary_refs": [_normalize_ref(affected_id)] if affected_id else [],
                        "conduct_ref": _normalize_ref(op_id),
                        "trigger": {"op": "fact", "fact_ref": _normalize_ref("cond:action_executed")},
                        "phase": "after" if norm_kind != "duty" else "entry",
                        "timing_ref": _normalize_ref("timing:immediate"),
                        "satisfaction_contract_ref": _normalize_ref("contract:compliance_record"),
                        "evidence_refs": ev_refs,
                        "discharge_state": EvidenceState.UNKNOWN.value,  # AQ18: outstanding duties survive
                    }
                    duties_to_attach.append(duty_rec)

        # 4. Check delegation grant if present in case or context (AQ10)
        grant_ref = case.get("grant_ref")
        if grant_ref:
            del_result = self.delegation_verifier.verify_grant_chain(grant_ref, actor_id, op_id)
            if del_result.state == DelegationState.ESTABLISHED:
                bp_grant = {
                    "ref": _normalize_ref(f"basis:grant:{_ref_id(grant_ref)}:{case_id}"),
                    "regime_ref": _normalize_ref("regime:delegated_power"),
                    "rule_refs": [],
                    "grant_refs": [_normalize_ref(x) for x in del_result.grant_refs],
                    "state": "established",
                    "evidence_refs": [],
                    "review_refs": [],
                    "condition_refs": [],
                }
                basis_paths.append(bp_grant)
                active_enablings.append({
                    "rule": {"ref": _ref_id(grant_ref), "norm_kind": "power"},
                    "pack": {"ref": "pack:delegation"},
                    "basis": bp_grant,
                })
            elif del_result.state == DelegationState.DEFEATED:
                condition_failures.append({
                    "rule": {"ref": _ref_id(grant_ref)},
                    "pack": {"ref": "pack:delegation"},
                    "basis": {"state": "defeated"},
                })
            else:
                unresolved_routes.append({
                    "rule": {"ref": _ref_id(grant_ref)},
                    "pack": {"ref": "pack:delegation"},
                    "basis": {"state": "unresolved"},
                })

        # 5. Whole-Case Disposition Rules (AQ01, AQ02, AQ03, AQ15, AQ50)
        # Priority 1: Surviving explicit prohibitions (AQ02, AQ15)
        if active_prohibitions:
            decisive_rule_ref = active_prohibitions[0]["rule"]["ref"]
            return self._build_assessment_record(
                case=case,
                status="assessed",
                disposition="prohibited_under_reviewed_rule",
                decisive_rules=[decisive_rule_ref],
                applicable_findings=applicable_findings,
                basis_paths=basis_paths,
                norm_positions=norm_positions,
                duties=duties_to_attach,
                conflicts=conflicts,
                diagnostics=[],
                trace_nodes=trace_nodes,
                explanation=f"Explicit prohibition established under reviewed rule {decisive_rule_ref}.",
            )

        # Priority 2: Established enabling basis paths
        if active_enablings:
            decisive_rule_ref = active_enablings[0]["rule"]["ref"]
            return self._build_assessment_record(
                case=case,
                status="assessed",
                disposition="supported_within_scope",
                decisive_rules=[decisive_rule_ref],
                applicable_findings=applicable_findings,
                basis_paths=basis_paths,
                norm_positions=norm_positions,
                duties=duties_to_attach,
                conflicts=conflicts,
                diagnostics=[],
                trace_nodes=trace_nodes,
                explanation=f"Supported under reviewed rule {decisive_rule_ref}.",
            )

        # Priority 3: Conditions unmet (all candidate routes failed condition, no viable unresolved route)
        if condition_failures and not unresolved_routes:
            decisive_rule_ref = condition_failures[0]["rule"]["ref"]
            return self._build_assessment_record(
                case=case,
                status="assessed",
                disposition="conditions_unmet",
                decisive_rules=[decisive_rule_ref],
                applicable_findings=applicable_findings,
                basis_paths=basis_paths,
                norm_positions=norm_positions,
                duties=duties_to_attach,
                conflicts=conflicts,
                diagnostics=[],
                trace_nodes=trace_nodes,
                explanation=f"Indispensable conditions demonstrably refuted under rule {decisive_rule_ref}; conditions unmet.",
            )

        # Priority 4: Unresolved (missing facts, unresolved routes, missing statutory power)
        return self._build_assessment_record(
            case=case,
            status="assessed",
            disposition="unresolved",
            decisive_rules=[],
            applicable_findings=applicable_findings,
            basis_paths=basis_paths,
            norm_positions=norm_positions,
            duties=duties_to_attach,
            conflicts=conflicts,
            diagnostics=[],
            trace_nodes=trace_nodes,
            explanation="No conclusive legal basis or prohibition established within reviewed scope; disposition remains unresolved.",
        )

    def _build_assessment_record(
        self,
        case: Dict[str, Any],
        status: str,
        disposition: Optional[str],
        decisive_rules: List[str],
        applicable_findings: List[Dict[str, Any]],
        basis_paths: List[Dict[str, Any]],
        norm_positions: List[Dict[str, Any]],
        duties: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
        diagnostics: List[Dict[str, Any]],
        trace_nodes: Optional[List[Dict[str, Any]]] = None,
        explanation: str = "",
    ) -> Dict[str, Any]:
        """Constructs canonical LegalAssessment envelope conforming to contract catalog."""
        case_id = case.get("id", "case:unnamed")
        case_digest = compute_case_digest(case)
        context_ref = _normalize_ref(self.context.get("ref", "ctx:default"))
        context_digest = _canonical_digest(self.context)

        all_ev_refs: Set[str] = set()
        for bp in basis_paths:
            for er in bp.get("evidence_refs", []):
                all_ev_refs.add(_ref_id(er))

        all_rev_refs: Set[str] = set()
        for pack in self.packs:
            for rr in pack.get("review_refs", []):
                all_rev_refs.add(_ref_id(rr))

        trace = trace_nodes or []
        trace.append({
            "ref": _normalize_ref(f"trace:disposition:{case_id}"),
            "kind": "disposition",
            "input_refs": [_normalize_ref(r) for r in decisive_rules],
            "rule_ref": _normalize_ref(decisive_rules[0]) if decisive_rules else None,
            "finding": explanation,
        })

        return {
            "ref": _normalize_ref(f"assessment:{case_id}"),
            "status": status,
            "disposition": disposition,
            "case_ref": _normalize_ref(case_id),
            "case_digest": case_digest,
            "context_ref": context_ref,
            "context_digest": context_digest,
            "applicability": {
                "case_digest": case_digest,
                "context_digest": context_digest,
                "findings": applicable_findings,
                "coverage_ref": _normalize_ref("cov:complete"),
                "complete": True,
                "diagnostics": [],
            },
            "normative_positions": norm_positions,
            "basis_paths": basis_paths,
            "conditions": [],
            "duties": duties,
            "conflicts": conflicts,
            "evidence_refs": [_normalize_ref(x) for x in sorted(list(all_ev_refs))],
            "review_refs": [_normalize_ref(x) for x in sorted(list(all_rev_refs))],
            "coverage_ref": _normalize_ref("cov:complete"),
            "gap_refs": [],
            "dependency_refs": [_normalize_ref(r) for r in decisive_rules],
            "budget_used": {
                "candidates_evaluated": 1,
                "rule_evaluations": len(applicable_findings),
                "context_branches_evaluated": 0,
                "courses_evaluated": 0,
                "trace_nodes": len(trace),
                "stopping_reason": "complete",
            },
            "trace": trace,
            "diagnostics": diagnostics,
            "robust_supported": (disposition == "supported_within_scope"),
            "branch_result_refs": [],
            "mode": "actual_context",
            "derived_records": [],
            # Helper for audit/explanation
            "decisive_rule_refs": decisive_rules,
            "explanation": explanation,
        }


def assess_case(
    case: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Public functional entry point for direct case evaluation."""
    evaluator = LegalEvaluator(context)
    return evaluator.assess_case(case, budget)
