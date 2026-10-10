"""MAPEOGEO Authority Domain Profile Package.

Exports the Hohfeldian normative ontology, authority evaluator, delegation engine,
and domain certification witness C_A.
"""

from mapeogeo.domains.authority.ontology import (
    ActionCase,
    ActorBinding,
    AuthorityDisposition,
    CertificateOutcome,
    HohfeldianModality,
    OperationBinding,
)
from mapeogeo.domains.authority.rules import (
    ConditionRequirement,
    LegalRule,
    RuleEffect,
    RulePack,
)
from mapeogeo.domains.authority.evaluator import AuthorityEvaluator
from mapeogeo.domains.authority.delegation import DelegationChainEvaluator
from mapeogeo.domains.authority.certification import (
    AuthorityCertificateWitness,
    StandardDeficiency,
    create_authority_certificate,
    map_authority_deficiencies,
)
from mapeogeo.domains.authority.adapter import AuthorityAdapter
from mapeogeo.domains.authority.intake import (
    LegalPackIntake,
    LegalPackIntakeResult,
    ReviewerRecord,
)

__all__ = [
    "ActionCase",
    "ActorBinding",
    "OperationBinding",
    "AuthorityDisposition",
    "CertificateOutcome",
    "HohfeldianModality",
    "ConditionRequirement",
    "LegalRule",
    "RuleEffect",
    "RulePack",
    "AuthorityEvaluator",
    "DelegationChainEvaluator",
    "AuthorityCertificateWitness",
    "StandardDeficiency",
    "create_authority_certificate",
    "map_authority_deficiencies",
    "AuthorityAdapter",
    "LegalPackIntake",
    "LegalPackIntakeResult",
    "ReviewerRecord",
]
