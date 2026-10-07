"""UoW Kernel Layer.

Domain-neutral execution engine governed by the 9-tuple:
    K = (M_6, Omega, rho, G, D, P, U, C, A)
"""

from __future__ import annotations

from mapeogeo.kernel.certification import CertificationBoundary, CertificationResult
from mapeogeo.kernel.deficiency import (
    DeficiencyConservationError,
    DeficiencyDistribution,
    DeficiencyExtractor,
    DeficiencyRecord,
    WorkRequirement,
)
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.obstruction import ObstructionOperator, ObstructionReport, RepairOperator
from mapeogeo.kernel.planning import ProspectivePlan, ProspectivePlanner
from mapeogeo.kernel.reach import compute_ability, is_learning_event
from mapeogeo.kernel.serialization import (
    deserialize_knowledge_state,
    serialize_deficiency_distribution,
    serialize_knowledge_state,
    serialize_machinery_candidate,
)
from mapeogeo.kernel.spec import KERNEL_9_TUPLE, ComponentSpec, compute_kernel_9_tuple_seal
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import (
    DEFAULT_REFUSAL_THRESHOLD_TAU_J,
    StateTransitionEngine,
    TransitionOutcome,
)
from mapeogeo.kernel.utility import UtilityEstimate, UtilityModel

__all__ = [
    "DEFAULT_REFUSAL_THRESHOLD_TAU_J",
    "CertificationBoundary",
    "CertificationResult",
    "ComponentSpec",
    "DeficiencyConservationError",
    "DeficiencyDistribution",
    "DeficiencyExtractor",
    "DeficiencyRecord",
    "KERNEL_9_TUPLE",
    "KnowledgeState",
    "MachineryCandidate",
    "MachineryNode",
    "ObstructionOperator",
    "ObstructionReport",
    "ProspectivePlan",
    "ProspectivePlanner",
    "RepairOperator",
    "StateTransitionEngine",
    "TransitionOutcome",
    "UtilityEstimate",
    "UtilityModel",
    "WorkRequirement",
    "compute_ability",
    "compute_kernel_9_tuple_seal",
    "deserialize_knowledge_state",
    "is_learning_event",
    "serialize_deficiency_distribution",
    "serialize_knowledge_state",
    "serialize_machinery_candidate",
]
