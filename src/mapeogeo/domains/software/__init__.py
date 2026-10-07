"""Software Domain Layer.

Canonical domain adapter binding software systems engineering to the UoW architecture:
    K_v2 + D_software

Governing rule:
    Software adapts to the kernel; the kernel does not adapt to software.
    source code exists != software capability certified.
"""

from __future__ import annotations

from mapeogeo.domains.software.adapter import SoftwareAdapter
from mapeogeo.domains.software.certification import SoftwareCertificationBoundary
from mapeogeo.domains.software.grammar_mapping import (
    FactoringAuditRecord,
    FactoringClassification,
    SoftwareGrammarFactorer,
)
from mapeogeo.domains.software.ontology import (
    EpistemicSoftwareStatus,
    SoftwareCertificate,
    SoftwareCertificationVerdict,
    SoftwareEvidence,
    SoftwareMachinery,
    SoftwareObjective,
    SoftwareRequirement,
    SoftwareVerificationContracts,
)

__all__ = [
    "EpistemicSoftwareStatus",
    "FactoringAuditRecord",
    "FactoringClassification",
    "SoftwareAdapter",
    "SoftwareCertificate",
    "SoftwareCertificationBoundary",
    "SoftwareCertificationVerdict",
    "SoftwareEvidence",
    "SoftwareGrammarFactorer",
    "SoftwareMachinery",
    "SoftwareObjective",
    "SoftwareRequirement",
    "SoftwareVerificationContracts",
]
