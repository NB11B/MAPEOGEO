"""Integration Mapping Contract: MAPEOGEO to Intelligence Analysis Reference Model (v0.1).

Defines the explicit semantic translation rules, layer mappings, representation
distinctions, authority boundaries, and timeline clock domain semantics between
MAPEOGEO graph records and the intel_uow reference model.

Design Invariants:
1. Zero-fabrication: Missing facts remain unknown; no default truth values, zero quantities,
   or empty domains are inferred.
2. Layer isolation: Source assertions and hypothetical events cannot mutate actual UoW
   state, create grants, or close actual gaps.
3. Representation distinction: CANDIDATE_REPRESENTS / CANDIDATE_EO / CANDIDATE_GEO
   must NEVER be collapsed or promoted to SAME_SEMANTICS or EQUIVALENT_TO.
4. Authority separation: Claims about authority inside source material or scenarios
   remain claims; only explicitly reviewed authority views can admit proposals.
5. Clock domain ownership: Timeline sequence counters are owned by explicit (domain_id, local_actor)
   streams. Unrelated local sequences cannot be ordered together.
6. Scope boundary for v0.1: Actual lifecycle projection (dynamic grant expiry invalidation,
   cancellation release of reservations, runtime mutation of actual UoW state) is explicitly
   unsupported in v0.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Set, Tuple


# ==============================================================================
# 1. PROJECTION STATUS AND DIAGNOSTIC CODES
# ==============================================================================

class ProjectionStatus(str, Enum):
    """The three fundamental conditions defined by the integration milestone."""
    SUPPORTED_CASE = "supported_case"
    SUPPORTED_WITH_UNKNOWNS = "supported_with_unknowns"
    UNSUPPORTED_PROJECTION = "unsupported_projection"
    INVALID_INPUT = "invalid_input"


# ==============================================================================
# 2. GRAPH LAYER CLASSIFICATIONS
# ==============================================================================

class GraphLayer(str, Enum):
    SOURCE = "source"
    SUBJECT_HYPOTHESIS = "subject_hypothesis"
    ANALYTICAL_DERIVATION = "analytical_derivation"
    SCENARIO = "scenario"
    ACTUAL_UOW = "actual_uow"
    REGISTRY = "registry"


# Mapping from MAPEOGEO node types to declared reference graph layers
MAPEOGEO_NODE_TO_LAYER: Mapping[str, GraphLayer] = {
    # Provenance and source declarations
    "SOURCE": GraphLayer.SOURCE,
    "STATEMENT": GraphLayer.SOURCE,
    "PROOF_STEP": GraphLayer.SOURCE,
    "PROOF_PATH": GraphLayer.SOURCE,
    "WOUND": GraphLayer.SOURCE,
    
    # Mathematical objects and analytical models
    "OBJECT": GraphLayer.SUBJECT_HYPOTHESIS,
    "OPERATOR": GraphLayer.SUBJECT_HYPOTHESIS,
    "REPRESENTATION": GraphLayer.SUBJECT_HYPOTHESIS,
    
    # Executable certificates & verified derivations
    "CERTIFICATE": GraphLayer.ANALYTICAL_DERIVATION,
    "DERIVATION": GraphLayer.ANALYTICAL_DERIVATION,
    
    # Scenarios and hypothetical views
    "SCENARIO": GraphLayer.SCENARIO,
    "OBSERVATION": GraphLayer.SCENARIO,
    
    # Actual UoW workflow, journal entries, and transactions
    "UOW_TASK": GraphLayer.ACTUAL_UOW,
    "ADMISSION_RECORD": GraphLayer.ACTUAL_UOW,
    "JOURNAL_ENTRY": GraphLayer.ACTUAL_UOW,
    "TRANSACTION": GraphLayer.ACTUAL_UOW,
    
    # Registry definitions, contracts, policies
    "POLICY": GraphLayer.REGISTRY,
    "CONTRACT": GraphLayer.REGISTRY,
    "OPERATION_DEF": GraphLayer.REGISTRY,
}


# ==============================================================================
# 3. REPRESENTATION RELATION DISTINCTIONS
# ==============================================================================

class RepresentationRelationKind(str, Enum):
    """Strictly separated relationship classes."""
    CANDIDATE_REPRESENTS = "CANDIDATE_REPRESENTS"
    CANDIDATE_EO = "CANDIDATE_EO"
    CANDIDATE_GEO = "CANDIDATE_GEO"
    REPRESENTS = "REPRESENTS"
    SAME_SEMANTICS = "SAME_SEMANTICS"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    SCOPED_OVERLAP = "SCOPED_OVERLAP"
    RELATED_TO = "RELATED_TO"


# Never allow automatic semantic promotion
UNPROMOTABLE_CANDIDATE_EDGES: FrozenSet[str] = frozenset({
    "CANDIDATE_EO",
    "CANDIDATE_GEO",
    "CANDIDATE_REPRESENTS",
})

SEMANTIC_EQUIVALENCE_EDGES: FrozenSet[str] = frozenset({
    "SAME_SEMANTICS",
    "EQUIVALENT_TO",
})


# ==============================================================================
# 4. TIMELINE CLOCK DOMAIN OWNERSHIP & ENCODING RULES
# ==============================================================================

@dataclass(frozen=True)
class ClockDomain:
    """Explicitly bounds sequence counter ownership to prevent cross-UoW ordering."""
    domain_id: str
    owner_boundary: str  # e.g., 'uow:boundary:uow-01', 'worker:proc:1024'
    description: str

    def __post_init__(self) -> None:
        if not self.domain_id or "::" in self.domain_id:
            raise ValueError(f"domain_id must be nonempty and cannot contain '::', got: {self.domain_id}")

    def format_event_actor(self, local_actor: str) -> str:
        """Namespaces the actor to its clock domain so workflow.py's `(actor, seq)`

        partial order respects the local timeline and avoids collisions.
        Requires local_actor to be free of '::' to prevent ambiguous delimiter collisions.
        """
        if not local_actor or "::" in local_actor:
            raise ValueError(f"local_actor must be nonempty and cannot contain '::', got: {local_actor}")
        return f"{self.domain_id}::{local_actor}"

    def format_event_id(self, local_event_id: str) -> str:
        """Namespaces event identifiers to avoid collision across domains."""
        return f"{self.domain_id}:{local_event_id}"


# ==============================================================================
# 5. ADAPTER MAPPING CONTRACT SPECIFICATION
# ==============================================================================

@dataclass
class AdapterContract:
    adapter_id: str = "mapeogeo.intelligence-integration.adapter.v0_1"
    version: str = "0.1.0"
    target_reference_version: str = "0.3"
    
    # Supported analytical models in v0.1
    supported_models: List[str] = field(default_factory=lambda: [
        "uow.intelligence.meaningful_gaps.carrier_continuity.v0_3",
        "finite_carrier_capacity_model.v1"
    ])
    
    # Explicitly declared unsupported features in v0.1
    unsupported_features: List[str] = field(default_factory=lambda: [
        "continuous_probability_distributions",
        "unbounded_infinite_state_domains",
        "cross_domain_global_clock_synchronization",
        "unauthenticated_source_claimed_authority",
        "implicit_candidate_to_semantic_promotion",
        "actual_lifecycle_projection",  # Dynamic grant expiry invalidation, cancellation, and actual state mutation
    ])

    def validate_node_layer(self, node_type: str, declared_layer: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        expected_layer = MAPEOGEO_NODE_TO_LAYER.get(node_type)
        if expected_layer is None:
            return False, f"Unknown MAPEOGEO node type: {node_type}"
        if declared_layer and declared_layer != expected_layer.value:
            return False, f"Layer mismatch for {node_type}: declared {declared_layer}, expected {expected_layer.value}"
        return True, None

    def validate_edge_promotion(self, edge_type: str, target_interpretation: str) -> Tuple[bool, Optional[str]]:
        if edge_type in UNPROMOTABLE_CANDIDATE_EDGES and target_interpretation in ("SAME_SEMANTICS", "EQUIVALENT_TO"):
            return False, f"Illegal promotion: candidate edge {edge_type} cannot become {target_interpretation}"
        return True, None
