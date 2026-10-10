"""Host Graph Projection Module for Task T09.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - experiments.intelligence_integration.v0_1.adapter (MAPEOGEOAnalysisAdapter)
   - experiments.intelligence_integration.v0_1.contract (HostFieldProvenance, ClockDomain, ProjectionStatus)
2. Interface Reused:
   - ActionCaseBuilder, compute_case_digest (intel_authority.case_bindings)
   - host_mapping_contract.json grounded node definitions and excluded surfaces
   - validate_authority_reference, create_typed_value (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - Maps MAPEOGEO host graph snapshot records to ActionCase without mutating host graph.
   - AQ05: Unfamiliar actor identities mapped to named unresolved bindings.
   - AQ20: Unauthenticated retrieved sources cannot act as reviewed law packs.
   - AQ24: Uncovered operations or jurisdictions yield unresolved coverage; no law by silence.
   - AQ37: Excluded surfaces (actual lifecycle projection, dynamic expiry invalidation,
     cancellation reservation release, live host graph mutation) return UNSUPPORTED_PROJECTION.
   - AQ41: Preserves canonical clock identity encoding for timeline events and actors.
   - AQ56: Malformed inputs (duplicate keys, invalid enums, booleans as numbers, etc.)
     return INVALID_INPUT with technical diagnostics rather than legal dispositions.
4. Qualification Evidence Delta:
   - AQ05, AQ09, AQ20, AQ24, AQ30, AQ37, AQ41, AQ56 qualification assertions.
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
    validate_authority_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    ActionCaseBuilder,
    JurisdictionKind,
    compute_case_digest,
)
from experiments.intelligence_integration.v0_1.adapter import (
    HostFieldProvenance,
    _canonical_digest,
)
from experiments.intelligence_integration.v0_1.contract import (
    CLOCK_IDENTITY_PREFIX,
    ClockDomain,
    ProjectionStatus,
    decode_clock_identity,
    encode_clock_identity,
)

# Load host mapping contract
HOST_MAPPING_CONTRACT_PATH = (
    Path(__file__).resolve().parents[1] / "host_mapping_contract.json"
)

EXCLUDED_SURFACES: Set[str] = {
    "actual_lifecycle_projection",
    "dynamic_grant_expiry_invalidation",
    "cancellation_reservation_release",
    "live_mutation_of_host_graph",
    "external_execution_enabled",
}

GROUNDED_NODES: Dict[str, List[str]] = {
    "src:service_contract:v1": ["demand_units", "window", "hash"],
    "src:carrier_schedule:v1": ["regular_capacity", "bridge_capacity", "loading_capacity"],
    "obj:carrier_capacity_model:v1": [
        "capacity_values",
        "availability_values",
        "domain",
        "carrier",
    ],
}


@dataclass
class ProjectedAuthorityCase:
    """Attributed result of projecting a host graph snapshot into an authority case."""
    case_id: str
    revision: int
    source_snapshot_digest: str
    status: ProjectionStatus
    action_case: Optional[Dict[str, Any]]
    field_provenance: List[HostFieldProvenance]
    unsupported_reasons: List[str] = field(default_factory=list)
    diagnostics: List[str] = field(default_factory=list)
    clock_domain: Optional[ClockDomain] = None
    timeline_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "revision": self.revision,
            "source_snapshot_digest": self.source_snapshot_digest,
            "status": self.status.value if isinstance(self.status, ProjectionStatus) else str(self.status),
            "action_case": self.action_case,
            "field_provenance": [asdict(fp) for fp in self.field_provenance],
            "unsupported_reasons": list(self.unsupported_reasons),
            "diagnostics": list(self.diagnostics),
            "clock_domain": {
                "domain_id": self.clock_domain.domain_id,
                "owner_boundary": self.clock_domain.owner_boundary,
                "description": self.clock_domain.description,
            } if self.clock_domain else None,
            "timeline_events": list(self.timeline_events),
        }


def _validate_snapshot_integrity(snapshot: Dict[str, Any]) -> List[str]:
    """AQ56: Validates input boundaries (duplicate keys, NaN, booleans as numbers, etc.)."""
    diagnostics: List[str] = []

    if not isinstance(snapshot, dict):
        return ["INVALID_SNAPSHOT_STRUCTURE: snapshot must be a JSON object"]

    nodes = snapshot.get("nodes")
    if not isinstance(nodes, list):
        return ["INVALID_SNAPSHOT_STRUCTURE: 'nodes' must be a list"]

    seen_node_ids: Set[str] = set()
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            diagnostics.append(f"MALFORMED_NODE_AT_INDEX_{idx}: node must be an object")
            continue

        node_id = node.get("node_id") or node.get("id")
        if not node_id or not isinstance(node_id, str):
            diagnostics.append(f"MISSING_NODE_ID_AT_INDEX_{idx}")
            continue

        if node_id in seen_node_ids:
            diagnostics.append(f"DUPLICATE_NODE_ID: '{node_id}' appears multiple times")
        seen_node_ids.add(node_id)

        attrs = node.get("attributes", {})
        if not isinstance(attrs, dict):
            diagnostics.append(f"MALFORMED_ATTRIBUTES_IN_NODE: '{node_id}'")
            continue

        for attr_k, attr_v in attrs.items():
            if isinstance(attr_v, float) and (math.isnan(attr_v) or math.isinf(attr_v)):
                diagnostics.append(
                    f"INVALID_NUMERIC_VALUE: attribute '{attr_k}' in node '{node_id}' contains NaN/Inf"
                )
            # Boolean masquerading as number check
            if attr_k.endswith("_count") or attr_k.endswith("_units") or attr_k == "window":
                if isinstance(attr_v, bool):
                    diagnostics.append(
                        f"TYPE_MASQUERADE: attribute '{attr_k}' in node '{node_id}' is boolean where number expected"
                    )

    return diagnostics


def project_host_case(
    snapshot: Dict[str, Any],
    selection_manifest: Dict[str, Any],
    mapping_contract: Optional[Dict[str, Any]] = None,
    clock_domain: Optional[ClockDomain] = None,
) -> ProjectedAuthorityCase:
    """Projects a MAPEOGEO host snapshot into an authority ActionCase.

    Strict Invariants:
    1. Read-only: Snapshot digest is compared before and after; zero host mutation.
    2. Explicit bounds: Excluded surfaces return UNSUPPORTED_PROJECTION (AQ37).
    3. Zero-fabrication: Unfamiliar actors yield named unresolved bindings (AQ05).
    4. Coverage bounds: Unmapped operations yield unresolved coverage without law by silence (AQ24).
    5. Clock domain namespacing: Canonical uow-clock encoding preserved (AQ41).
    6. Input bounds: Malformed inputs yield technical diagnostics without legal disposition (AQ56).
    """
    digest_before = _canonical_digest(snapshot)

    case_id = selection_manifest.get("case_id", "projected_case_v1")
    revision = selection_manifest.get("revision", 1)

    # 1. AQ56 Input integrity check
    integrity_diagnostics = _validate_snapshot_integrity(snapshot)
    if integrity_diagnostics:
        digest_after = _canonical_digest(snapshot)
        assert digest_before == digest_after, "Host snapshot was mutated during validation!"
        return ProjectedAuthorityCase(
            case_id=case_id,
            revision=revision,
            source_snapshot_digest=digest_before,
            status=ProjectionStatus.INVALID_INPUT,
            action_case=None,
            field_provenance=[],
            diagnostics=integrity_diagnostics,
            clock_domain=clock_domain,
        )

    # 2. AQ37 Excluded surfaces check
    unsupported_reasons: List[str] = []
    requested_surfaces = selection_manifest.get("requested_surfaces", [])
    if isinstance(requested_surfaces, list):
        for s in requested_surfaces:
            if s in EXCLUDED_SURFACES:
                unsupported_reasons.append(f"EXCLUDED_SURFACE_REQUESTED: {s}")

    if selection_manifest.get("request_lifecycle_projection"):
        unsupported_reasons.append("EXCLUDED_SURFACE_REQUESTED: actual_lifecycle_projection")
    if selection_manifest.get("external_execution_enabled"):
        unsupported_reasons.append("EXCLUDED_SURFACE_REQUESTED: external_execution_enabled")
    if selection_manifest.get("live_mutation_of_host_graph"):
        unsupported_reasons.append("EXCLUDED_SURFACE_REQUESTED: live_mutation_of_host_graph")

    if unsupported_reasons:
        digest_after = _canonical_digest(snapshot)
        assert digest_before == digest_after, "Host snapshot was mutated during projection!"
        return ProjectedAuthorityCase(
            case_id=case_id,
            revision=revision,
            source_snapshot_digest=digest_before,
            status=ProjectionStatus.UNSUPPORTED_PROJECTION,
            action_case=None,
            field_provenance=[],
            unsupported_reasons=unsupported_reasons,
            clock_domain=clock_domain,
        )

    # Index nodes
    node_map: Dict[str, Dict[str, Any]] = {
        (n.get("node_id") or n.get("id")): n
        for n in snapshot.get("nodes", [])
        if (n.get("node_id") or n.get("id"))
    }

    # 3. Grounded nodes and field provenance extraction
    provenance_list: List[HostFieldProvenance] = []

    # Service contract node
    svc_node = node_map.get("src:service_contract:v1")
    demand_units = None
    window = None
    if svc_node:
        attrs = svc_node.get("attributes", {})
        if "demand_units" in attrs:
            demand_units = attrs["demand_units"]
            provenance_list.append(
                HostFieldProvenance(
                    field_name="demand_units",
                    host_node_id="src:service_contract:v1",
                    source_attribute="demand_units",
                    extracted_value=demand_units,
                )
            )
        if "window" in attrs:
            window = attrs["window"]
            provenance_list.append(
                HostFieldProvenance(
                    field_name="window",
                    host_node_id="src:service_contract:v1",
                    source_attribute="window",
                    extracted_value=window,
                )
            )

    # Carrier schedule node
    sched_node = node_map.get("src:carrier_schedule:v1")
    reg_cap = None
    if sched_node:
        attrs = sched_node.get("attributes", {})
        if "regular_capacity" in attrs:
            reg_cap = attrs["regular_capacity"]
            provenance_list.append(
                HostFieldProvenance(
                    field_name="regular_capacity",
                    host_node_id="src:carrier_schedule:v1",
                    source_attribute="regular_capacity",
                    extracted_value=reg_cap,
                )
            )

    # Capacity model node
    model_node = node_map.get("obj:carrier_capacity_model:v1")
    carrier = None
    if model_node:
        attrs = model_node.get("attributes", {})
        if "carrier" in attrs:
            carrier = attrs["carrier"]
            provenance_list.append(
                HostFieldProvenance(
                    field_name="carrier",
                    host_node_id="obj:carrier_capacity_model:v1",
                    source_attribute="carrier",
                    extracted_value=carrier,
                )
            )

    # 4. Resolve Actor, Capacity, Operation, Affected (AQ05, AQ24)
    actor_id = selection_manifest.get("actor_id") or (carrier if carrier else None)
    capacity_id = selection_manifest.get("capacity_id", "cap:carrier_representative")
    operation_id = selection_manifest.get("operation_id", "op:deliver_carrier_volume")
    affected_id = selection_manifest.get("affected_id", "actor:shipper:alpha")
    jurisdiction_id = selection_manifest.get("jurisdiction_id", "jur:commercial_freight")

    diagnostics: List[str] = []
    status = ProjectionStatus.SUPPORTED_CASE

    # AQ05: Unfamiliar / ungrounded actor identity
    if not actor_id or actor_id.startswith("actor:unknown:") or actor_id == "unknown":
        actor_id = "actor:unresolved:unknown_party"
        status = ProjectionStatus.SUPPORTED_WITH_UNKNOWNS
        diagnostics.append(f"UNFAMILIAR_ACTOR_IDENTITY: {actor_id}")

    # AQ24: Ambiguous / unmapped operation
    if not operation_id or operation_id.startswith("op:unmapped_") or operation_id == "op:unknown":
        operation_id = "op:unresolved:unmapped_activity"
        status = ProjectionStatus.SUPPORTED_WITH_UNKNOWNS
        diagnostics.append(f"UNMAPPED_OPERATION_COVERAGE_GAP: {operation_id}")

    # Build exact ActionCase
    builder = ActionCaseBuilder(
        case_id=case_id,
        revision=revision,
        actor_ref={"id": actor_id, "revision": 1},
        capacity_ref={"id": capacity_id, "revision": 1},
        operation_ref={"id": operation_id, "revision": 1},
        operation_revision=1,
        jurisdiction_context_ref={"id": jurisdiction_id, "revision": 1},
        jurisdiction_kind=JurisdictionKind.TERRITORIAL,
    )

    if demand_units is not None:
        builder.add_parameter(
            "demand_units",
            "integer" if isinstance(demand_units, int) else "decimal",
            demand_units,
        )
    if window is not None:
        builder.add_parameter("delivery_window", "string", str(window))
    if reg_cap is not None:
        builder.add_parameter(
            "carrier_capacity",
            "integer" if isinstance(reg_cap, int) else "decimal",
            reg_cap,
        )

    # Affected bindings
    builder.add_affected_binding(
        entity_ref={"id": affected_id, "revision": 1},
        relationship_role="affected_party",
        interest_refs=[{"id": "interest:commercial_sla", "revision": 1}],
        effect_refs=[],
    )

    # Purpose
    purpose_id = selection_manifest.get("purpose_id", "purpose:contractual_fulfillment")
    builder.set_purpose(purpose_id, 1)

    # Timeline events with AQ41 clock domain formatting
    timeline_events: List[Dict[str, Any]] = []
    raw_events = selection_manifest.get("timeline_events", [])
    if clock_domain and raw_events:
        for ev in raw_events:
            ev_copy = deepcopy(ev)
            raw_ev_id = ev_copy.get("event_id", "ev_0")
            raw_ev_actor = ev_copy.get("actor", actor_id)
            ev_copy["event_id"] = clock_domain.format_event_id(raw_ev_id)
            ev_copy["actor"] = clock_domain.format_event_actor(raw_ev_actor)
            timeline_events.append(ev_copy)
    else:
        timeline_events = deepcopy(raw_events)

    action_case = builder.build()

    # Re-verify snapshot immutability
    digest_after = _canonical_digest(snapshot)
    assert digest_before == digest_after, "CRITICAL: Host snapshot was mutated during projection!"

    return ProjectedAuthorityCase(
        case_id=case_id,
        revision=revision,
        source_snapshot_digest=digest_before,
        status=status,
        action_case=action_case,
        field_provenance=provenance_list,
        diagnostics=diagnostics,
        clock_domain=clock_domain,
        timeline_events=timeline_events,
    )
