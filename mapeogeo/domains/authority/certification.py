"""Authority Domain Certification Witness C_A and Deficiency Mapping.

This module provides the permanent domain certification witness for MAPEOGEO/UoW
admission and course planning, strictly preserving the four-outcome model without
collapsing unresolved uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from mapeogeo.domains.authority.ontology import (
    AuthorityDisposition,
    CertificateOutcome,
)


@dataclass
class AuthorityCertificateWitness:
    """Certificate witness supplying C_A into MAPEOGEO candidate course evaluation.

    Explicit 4-outcome distinction:
    - CERTIFIED: Supported within scope (witness present, work admitted).
    - OBSTRUCTED: Explicit prohibition or unmet indispensable condition.
    - UNRESOLVED: Material uncertainty remains; insufficient authority evidence
      (does NOT collapse into either certified or prohibited).
    """
    work_id: str
    outcome: CertificateOutcome
    status: str  # "admitted", "obstructed", "unresolved"
    disposition: str
    is_supported: bool
    witness_ref: Optional[Dict[str, Any]]
    decisive_rule_refs: List[str]
    obstruction_reason: Optional[str] = None
    uncertainty_description: Optional[str] = None
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_certified(self) -> bool:
        return self.outcome == CertificateOutcome.CERTIFIED

    @property
    def is_obstructed(self) -> bool:
        return self.outcome == CertificateOutcome.OBSTRUCTED

    @property
    def is_unresolved(self) -> bool:
        return self.outcome == CertificateOutcome.UNRESOLVED


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
    "completion_reconciliation_required": "O",# Observe: Reconcile frontier before retry
}


def create_authority_certificate(
    work_id: str,
    disposition: str,
    decisive_rule_refs: List[str],
    diagnostics: Optional[List[Dict[str, Any]]] = None,
) -> AuthorityCertificateWitness:
    """Constructs a typed AuthorityCertificateWitness preserving 4-outcome semantics."""
    diag = diagnostics or []
    if disposition == AuthorityDisposition.SUPPORTED.value:
        return AuthorityCertificateWitness(
            work_id=work_id,
            outcome=CertificateOutcome.CERTIFIED,
            status="admitted",
            disposition=disposition,
            is_supported=True,
            witness_ref={"id": f"witness:authority:{work_id}", "revision": 1},
            decisive_rule_refs=decisive_rule_refs,
            diagnostics=diag,
        )
    elif disposition in (AuthorityDisposition.PROHIBITED.value, AuthorityDisposition.CONDITIONS_UNMET.value):
        return AuthorityCertificateWitness(
            work_id=work_id,
            outcome=CertificateOutcome.OBSTRUCTED,
            status="obstructed",
            disposition=disposition,
            is_supported=False,
            witness_ref=None,
            decisive_rule_refs=decisive_rule_refs,
            obstruction_reason=f"Authority certification failed: disposition is '{disposition}'",
            diagnostics=diag,
        )
    else:  # UNRESOLVED
        return AuthorityCertificateWitness(
            work_id=work_id,
            outcome=CertificateOutcome.UNRESOLVED,
            status="unresolved",
            disposition=disposition,
            is_supported=False,
            witness_ref=None,
            decisive_rule_refs=decisive_rule_refs,
            uncertainty_description="Insufficient authority evidence to certify this work; material uncertainty remains.",
            diagnostics=diag,
        )


def map_authority_deficiencies(
    required_requirements: Set[str],
    grounded_propositions: Set[str],
    gap_types: Dict[str, str],
) -> List[StandardDeficiency]:
    r"""Maps authority deficiency set D = R \setminus G into standard platform deficiency items."""
    missing = required_requirements - grounded_propositions
    deficiencies = []
    for idx, subject in enumerate(sorted(missing)):
        gap_type = gap_types.get(subject, "fact_gap")
        op = DEFICIENCY_OPERATOR_ROUTING.get(gap_type, "O")
        deficiencies.append(
            StandardDeficiency(
                deficiency_id=f"def:auth:{idx+1}",
                deficiency_type=gap_type,
                target_subject=subject,
                required_operator=op,
                resolution_description=f"Authority deficiency: missing '{subject}' requires operator '{op}'",
            )
        )
    return deficiencies
