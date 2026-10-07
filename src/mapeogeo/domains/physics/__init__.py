"""Physics Domain Layer.

Canonical domain adapter binding empirical physics to the UoW architecture:
    K_v2 + D_physics

Governing rule:
    Physics adapts to the kernel; the kernel does not adapt to physics.
    Mathematical admissibility != physical establishment.
    Effect observed != source identified.
"""

from __future__ import annotations

from mapeogeo.domains.physics.adapter import PhysicsAdapter
from mapeogeo.domains.physics.certification import PhysicalCertificationBoundary
from mapeogeo.domains.physics.grammar_mapping import (
    FactoringAuditRecord,
    FactoringClassification,
    PhysicalGrammarFactorer,
)
from mapeogeo.domains.physics.latent_inference import (
    LatentGeneratorInverter,
    LatentInferenceResult,
)
from mapeogeo.domains.physics.ontology import (
    EpistemicStatus,
    MeasuredObservation,
    PhysicalCertificate,
    PhysicalCertificationVerdict,
    PhysicalConstraint,
    PhysicalHypothesis,
    PhysicalMachinery,
    PhysicalObjective,
)

__all__ = [
    "EpistemicStatus",
    "FactoringAuditRecord",
    "FactoringClassification",
    "LatentGeneratorInverter",
    "LatentInferenceResult",
    "MeasuredObservation",
    "PhysicsAdapter",
    "PhysicalCertificate",
    "PhysicalCertificationBoundary",
    "PhysicalCertificationVerdict",
    "PhysicalConstraint",
    "PhysicalGrammarFactorer",
    "PhysicalHypothesis",
    "PhysicalMachinery",
    "PhysicalObjective",
]
