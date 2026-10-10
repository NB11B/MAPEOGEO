r"""MAPEOGEO Certification and Deficiency Integration Bridge.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4 & Consolidation Gate):
1. Existing Component Extended:
   - mapeogeo.certifiable (Certification gates, witnesses, and deficiency structures)
   - intel_uow.catalog (Record envelopes, Diagnostic, Reference)
2. Interface Reused:
   - assess_case (intel_authority.evaluator)
   - derive_authority_gaps (intel_authority.gaps)
3. Additional Semantic Responsibility:
   - Supplies Authority Certificate Witness C_A(W, \Gamma_A) into platform certification
     without modifying the frozen four-gate kernel.
   - Maps authority gaps directly to standard platform deficiencies D = R \setminus G
     with assigned UoW operators from \Sigma_W = {O, E, K, C, F, D, S}.
4. Qualification Evidence Delta:
   - Authority certification gate integration, deficiency extraction, and operator
     routing verification.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.evaluator import assess_case


class AuthorityDisposition(str, Enum):
    SUPPORTED = "supported_within_scope"
    PROHIBITED = "prohibited_under_reviewed_rule"
    CONDITIONS_UNMET = "conditions_unmet"
    UNRESOLVED = "unresolved"


@dataclass
class AuthorityCertificateWitness:
    """Certificate witness supplying C_A into MAPEOGEO candidate course evaluation."""
    work_id: str
    status: str  # "admitted", "obstructed"
    disposition: str
    is_supported: bool
    witness_ref: Optional[Dict[str, Any]]
    decisive_rule_refs: List[str]
    obstruction_reason: Optional[str] = None
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StandardDeficiency:
    r"""Platform deficiency record D = R \setminus G mapped from authority gaps."""
    deficiency_id: str
    deficiency_type: str
    target_subject: str
    required_operator: str  # One of O, E, K, C, F, D, S
    resolution_description: str


DEFICIENCY_OPERATOR_ROUTING: Dict[str, str] = {
    "fact_gap": "O",                         # Observe: Inquire or acquire factual evidence
    "authority_evidence_missing": "K",       # Classify: Retrieve existing warrant or authorization view
    "grant_required": "S",                   # Select: Submit proposal to competent principal
    "source_applicability_gap": "C",         # Compare: Perform legal scope interpretation
    "completion_reconciliation_required": "O" # Observe: Reconcile frontier before retry
}


def evaluate_authority_certificate(
    case: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> AuthorityCertificateWitness:
    """Evaluates case and generates domain certificate witness for platform admission."""
    assessment = assess_case(case, context, budget=budget)
    disp = assessment.get("disposition", AuthorityDisposition.UNRESOLVED.value)
    is_supp = (disp == AuthorityDisposition.SUPPORTED.value)

    decisive_rules = assessment.get("decisive_rule_refs", [])
    work_id = case.get("id", "work:unnamed")

    if is_supp:
        return AuthorityCertificateWitness(
            work_id=work_id,
            status="admitted",
            disposition=disp,
            is_supported=True,
            witness_ref={"id": f"witness:authority:{work_id}", "revision": 1},
            decisive_rule_refs=decisive_rules,
        )
    else:
        return AuthorityCertificateWitness(
            work_id=work_id,
            status="obstructed",
            disposition=disp,
            is_supported=False,
            witness_ref=None,
            decisive_rule_refs=decisive_rules,
            obstruction_reason=f"Authority certification failed: disposition is '{disp}'",
            diagnostics=assessment.get("diagnostics", []),
        )


def map_authority_deficiencies(
    required_predicates: Set[str],
    grounded_predicates: Set[str],
    gap_types: Optional[Dict[str, str]] = None,
) -> List[StandardDeficiency]:
    r"""Computes D = R \setminus G and produces typed deficiencies with UoW operator routing."""
    missing = required_predicates - grounded_predicates
    deficiencies: List[StandardDeficiency] = []
    types_map = gap_types or {}

    for idx, item in enumerate(sorted(missing)):
        g_type = types_map.get(item, "fact_gap")
        op = DEFICIENCY_OPERATOR_ROUTING.get(g_type, "O")
        deficiencies.append(
            StandardDeficiency(
                deficiency_id=f"deficiency:{idx+1:03d}",
                deficiency_type=g_type,
                target_subject=item,
                required_operator=op,
                resolution_description=f"Resolve missing {item} via operator '{op}'",
            )
        )
    return deficiencies
