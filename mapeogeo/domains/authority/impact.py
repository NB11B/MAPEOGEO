"""Tertiary Impact & Counterparty Interest Modeling (Hohfeldian Jural Relations).

Enforces:
1. Invariant AQ07: Counterparty right/interest is a constraint, not an operational grant.
2. Hohfeldian Jural Correlatives and Opposites:
   - Correlatives: Right <-> Duty, Privilege <-> No-Right, Power <-> Liability, Immunity <-> Disability.
   - Opposites: Right vs No-Right, Privilege vs Duty, Power vs Disability, Immunity vs Liability.
3. Tertiary third-party impact assessment:
   When Actor A performs an operation toward Actor B that touches shared data, infrastructure,
   or rights, any third party Actor C with registered immunities or claim-rights acts as a
   binding legal constraint on operational admission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from mapeogeo.domains.authority.ontology import (
    ActionCase,
    AuthorityDisposition,
    HohfeldianModality,
)


class ImpactConstraintStatus(str, Enum):
    """Impact of counterparty / third-party rights on the proposed action."""
    UNCONSTRAINED = "unconstrained"
    CONSTRAINED_SAFEGUARD_REQUIRED = "constrained_safeguard_required"
    BLOCKED_BY_IMMUNITY = "blocked_by_immunity"


# Hohfeldian Jural System Tables
HOHFELDIAN_CORRELATIVES: Dict[HohfeldianModality, HohfeldianModality] = {
    HohfeldianModality.RIGHT: HohfeldianModality.DUTY,
    HohfeldianModality.DUTY: HohfeldianModality.RIGHT,
    HohfeldianModality.PRIVILEGE: HohfeldianModality.NO_RIGHT,
    HohfeldianModality.NO_RIGHT: HohfeldianModality.PRIVILEGE,
    HohfeldianModality.POWER: HohfeldianModality.LIABILITY,
    HohfeldianModality.LIABILITY: HohfeldianModality.POWER,
    HohfeldianModality.IMMUNITY: HohfeldianModality.DISABILITY,
    HohfeldianModality.DISABILITY: HohfeldianModality.IMMUNITY,
}

HOHFELDIAN_OPPOSITES: Dict[HohfeldianModality, HohfeldianModality] = {
    HohfeldianModality.RIGHT: HohfeldianModality.NO_RIGHT,
    HohfeldianModality.NO_RIGHT: HohfeldianModality.RIGHT,
    HohfeldianModality.PRIVILEGE: HohfeldianModality.DUTY,
    HohfeldianModality.DUTY: HohfeldianModality.PRIVILEGE,
    HohfeldianModality.POWER: HohfeldianModality.DISABILITY,
    HohfeldianModality.DISABILITY: HohfeldianModality.POWER,
    HohfeldianModality.IMMUNITY: HohfeldianModality.LIABILITY,
    HohfeldianModality.LIABILITY: HohfeldianModality.IMMUNITY,
}


@dataclass(frozen=True)
class TertiaryExposureRecord:
    """Attributed impact record on a third party's legal interests."""
    third_party_id: str
    interest_ref: str
    protected_modality: HohfeldianModality
    correlative_actor_modality: HohfeldianModality
    constraint_status: ImpactConstraintStatus
    required_safeguard: Optional[str] = None
    description: str = ""


@dataclass
class ImpactAssessmentReport:
    """Comprehensive counterparty and third-party impact assessment."""
    case_id: str
    overall_constraint_status: ImpactConstraintStatus
    exposures: List[TertiaryExposureRecord]
    can_proceed: bool
    diagnostics: List[str] = field(default_factory=list)


class CounterpartyInterestEvaluator:
    """Assesses tertiary counterparty interests and enforces Hohfeldian constraints."""

    def __init__(self, registered_interests: Optional[List[Dict[str, Any]]] = None) -> None:
        # Map: entity_id -> list of interest dictionaries
        self.interests_by_entity: Dict[str, List[Dict[str, Any]]] = {}
        if registered_interests:
            for item in registered_interests:
                eid = item.get("entity_id")
                if eid:
                    self.interests_by_entity.setdefault(eid, []).append(item)

    def register_interest(
        self,
        entity_id: str,
        interest_ref: str,
        modality: HohfeldianModality,
        scope: str = "general",
    ) -> None:
        self.interests_by_entity.setdefault(entity_id, []).append({
            "entity_id": entity_id,
            "interest_ref": interest_ref,
            "modality": modality,
            "scope": scope,
        })

    def assess_impact(
        self,
        case: Dict[str, Any],
        affected_third_parties: Optional[List[str]] = None,
    ) -> ImpactAssessmentReport:
        """Assesses tertiary legal impact of the proposed ActionCase."""
        case_id = case.get("id") or case.get("ref", {}).get("id", "case:unnamed")
        actor_id = case.get("actor_ref", {}).get("id", "actor:unknown")
        third_parties = list(affected_third_parties or [])

        # Also extract any entity references in parameters or affected_scope
        affected_scope = case.get("affected_scope", {})
        for b in affected_scope.get("bindings", []):
            ent_id = b.get("entity_ref", {}).get("id")
            if ent_id and ent_id not in third_parties:
                third_parties.append(ent_id)

        exposures: List[TertiaryExposureRecord] = []
        overall_status = ImpactConstraintStatus.UNCONSTRAINED
        can_proceed = True
        diagnostics = []

        for tp_id in third_parties:
            for interest in self.interests_by_entity.get(tp_id, []):
                mod = interest["modality"]
                correlative = HOHFELDIAN_CORRELATIVES[mod]

                # If third party has IMMUNITY, actor has DISABILITY -> BLOCKED unless explicit waiver
                if mod == HohfeldianModality.IMMUNITY:
                    status = ImpactConstraintStatus.BLOCKED_BY_IMMUNITY
                    overall_status = ImpactConstraintStatus.BLOCKED_BY_IMMUNITY
                    can_proceed = False
                    diagnostics.append(
                        f"Third party '{tp_id}' holds IMMUNITY under '{interest['interest_ref']}'; actor possesses DISABILITY"
                    )
                # If third party has RIGHT, actor has DUTY -> Requires safeguard or consent
                elif mod == HohfeldianModality.RIGHT:
                    status = ImpactConstraintStatus.CONSTRAINED_SAFEGUARD_REQUIRED
                    if overall_status != ImpactConstraintStatus.BLOCKED_BY_IMMUNITY:
                        overall_status = ImpactConstraintStatus.CONSTRAINED_SAFEGUARD_REQUIRED
                    diagnostics.append(
                        f"Third party '{tp_id}' holds RIGHT under '{interest['interest_ref']}'; imposes affirmative DUTY"
                    )
                else:
                    status = ImpactConstraintStatus.UNCONSTRAINED

                exposures.append(
                    TertiaryExposureRecord(
                        third_party_id=tp_id,
                        interest_ref=interest["interest_ref"],
                        protected_modality=mod,
                        correlative_actor_modality=correlative,
                        constraint_status=status,
                        required_safeguard="redaction_or_prior_notice" if status == ImpactConstraintStatus.CONSTRAINED_SAFEGUARD_REQUIRED else None,
                        description=f"Tertiary interest {interest['interest_ref']} evaluated under Hohfeldian correlation",
                    )
                )

        return ImpactAssessmentReport(
            case_id=case_id,
            overall_constraint_status=overall_status,
            exposures=exposures,
            can_proceed=can_proceed,
            diagnostics=diagnostics,
        )
