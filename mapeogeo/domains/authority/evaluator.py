"""Direct Authority Evaluator and Authority Matrix M_A(a, b | o, c).

This module provides the permanent MAPEOGEO domain evaluator for legal authority,
normative relations, and Hohfeldian modalities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case as _assess_case_impl,
)
from mapeogeo.domains.authority.certification import (
    AuthorityCertificateWitness,
    create_authority_certificate,
)
from mapeogeo.domains.authority.ontology import (
    ActionCase,
    AuthorityDisposition,
)


class AuthorityEvaluator:
    """Evaluates legal authority over bounded action cases."""

    def __init__(self, context: Dict[str, Any]) -> None:
        self.context = context

    def assess_case(
        self,
        case: Dict[str, Any] | ActionCase,
        budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Direct authority evaluation returning complete LegalAssessment."""
        case_dict = case if isinstance(case, dict) else {
            "ref": {"id": case.case_id, "revision": 1},
            "actor_ref": {"id": case.actor.actor_id, "revision": 1},
            "capacity_ref": {"id": case.actor.capacity, "revision": 1},
            "affected_actor_ref": {"id": case.affected_actor.actor_id, "revision": 1},
            "operation_ref": {"id": case.operation.operation_id, "revision": 1},
            "parameters": case.parameters,
        }
        return _assess_case_impl(case_dict, self.context, budget=budget)

    def evaluate_matrix_cell(
        self,
        actor_id: str,
        affected_actor_id: str,
        operation_id: str,
        capacity: str = "default",
        budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Computes M_A(a, b | o, c) for an actor pair and operation."""
        case = {
            "ref": {"id": f"case:{actor_id}:{affected_actor_id}:{operation_id}", "revision": 1},
            "actor_ref": {"id": actor_id, "revision": 1},
            "capacity_ref": {"id": capacity, "revision": 1},
            "affected_actor_ref": {"id": affected_actor_id, "revision": 1},
            "operation_ref": {"id": operation_id, "revision": 1},
        }
        return self.assess_case(case, budget=budget)

    def certify_work(
        self,
        case: Dict[str, Any] | ActionCase,
        budget: Optional[Dict[str, Any]] = None,
    ) -> AuthorityCertificateWitness:
        """Evaluates case and returns domain certification witness C_A."""
        assessment = self.assess_case(case, budget=budget)
        disp = assessment.get("disposition", AuthorityDisposition.UNRESOLVED.value)
        rules = assessment.get("decisive_rule_refs", [])
        work_id = assessment.get("ref", {}).get("id", "work:unnamed")
        return create_authority_certificate(
            work_id=work_id,
            disposition=disp,
            decisive_rule_refs=rules,
            diagnostics=assessment.get("diagnostics", []),
        )
