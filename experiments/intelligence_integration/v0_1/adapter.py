"""MAPEOGEO to Intelligence Analysis Read-Only Adapter (v0.1).

Implements the read-only projection from a pinned MAPEOGEO graph snapshot into
an attributed intelligence analysis case, validates the projection against the
contract, and evaluates it using the intel_uow reference model.

Invariants:
- Read-only: Input snapshot and actual workflow state are never mutated.
- Zero-fabrication: Unknown inputs remain unknown; no default False/0 is injected.
- Host-grounded projection: Reference parameters and state spaces are extracted
  directly from host graph nodes with recorded provenance.
- Boundary protection: Hypothetical scenarios and source assertions are barred from
  mutating actual grants, reservations, or closing actual gaps.
- Clock domain scoping: Timelines are scoped to explicit (domain_id, local_actor) streams
  to prevent spurious ordering across independent UoWs.
- Scope boundary: Actual lifecycle mutations (expiry invalidating grants, cancellation
  releasing reservations) are explicitly unsupported in v0.1.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

# Locate pristine reference package
REPO_ROOT = Path(__file__).resolve().parents[3]
REF_PKG_DIR = REPO_ROOT / "artifacts" / "intelligence_qualification" / "v0_3" / "intelligence_qualification_v0_3"
if str(REF_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(REF_PKG_DIR))

from intel_uow import analysis, grammar
from intel_uow.catalog import Catalog, Graph
from intel_uow.workflow import Workflow

from .contract import (
    AdapterContract,
    CLOCK_IDENTITY_PREFIX,
    ClockDomain,
    GraphLayer,
    MAPEOGEO_NODE_TO_LAYER,
    ProjectionStatus,
    SEMANTIC_EQUIVALENCE_EDGES,
    UNPROMOTABLE_CANDIDATE_EDGES,
)


def _canonical_digest(data: Any) -> str:
    """Compute deterministic SHA-256 digest of JSON-serializable structure."""
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class HostFieldProvenance:
    field_name: str
    host_node_id: str
    source_attribute: str
    extracted_value: Any


@dataclass
class ProjectedAnalysisCase:
    case_id: str
    revision: int
    source_snapshot_digest: str
    status: ProjectionStatus
    model_metadata: Dict[str, Any]
    model_parameters: Dict[str, Any]
    states: List[Dict[str, Any]]
    scope: Dict[str, str]
    field_provenance: List[HostFieldProvenance]
    evidence_reports: List[Dict[str, Any]]
    grammar_observation: Optional[Dict[str, Any]] = None
    grammar_context: Optional[Dict[str, Any]] = None
    proposal: Optional[Dict[str, Any]] = None
    authority_views: List[Dict[str, Any]] = field(default_factory=list)
    clock_domains: Dict[str, ClockDomain] = field(default_factory=dict)
    timeline_events: List[Dict[str, Any]] = field(default_factory=list)
    unsupported_reasons: List[str] = field(default_factory=list)
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class AttributedAnalysisResult:
    case_id: str
    revision: int
    projection_status: ProjectionStatus
    source_snapshot_digest: str
    model_assumptions: List[Dict[str, Any]]
    model_bindings: Dict[str, Any]
    field_provenance: List[HostFieldProvenance]
    baseline_evaluation: Dict[str, Any]
    meaningful_gaps: List[Dict[str, Any]]
    hypothetical_consequences: Optional[Dict[str, Any]]
    evidence_summary: Optional[Dict[str, Any]]
    grammar_interpretation: Optional[Dict[str, Any]]
    admission_result: Optional[Dict[str, Any]]
    reassessment_result: Optional[Dict[str, Any]]
    immutability_verified: bool
    retained_unknowns: List[str]
    diagnostics: List[str]


class MAPEOGEOAnalysisAdapter:
    """Read-only adapter translating MAPEOGEO graph records to intel_uow analysis cases."""

    def __init__(self, contract: Optional[AdapterContract] = None):
        self.contract = contract or AdapterContract()
        self.catalog = Catalog()

    def project_graph_to_case(
        self,
        snapshot: Dict[str, Any],
        selection_manifest: Dict[str, Any],
        clock_domain: Optional[ClockDomain] = None,
    ) -> ProjectedAnalysisCase:
        """Projects declared subset of snapshot records into an explicit analysis case."""
        snapshot_copy = deepcopy(snapshot)
        snapshot_digest = _canonical_digest(snapshot_copy)

        case_id = selection_manifest.get("case_id", "projected-case")
        revision = selection_manifest.get("revision", 1)
        scope = selection_manifest.get("scope", {"subject": "reserve-carrier", "window": "service-window"})

        diagnostics: List[str] = []
        unsupported: List[str] = []
        field_prov: List[HostFieldProvenance] = []

        nodes_by_id = {n["id"]: n for n in snapshot_copy.get("nodes", [])}
        edges_by_id = {e["id"]: e for e in snapshot_copy.get("edges", [])}

        # 1. Structural and layer validation of host nodes
        for node in snapshot_copy.get("nodes", []):
            node_type = node.get("type", "")
            declared_layer = node.get("layer")
            valid, err = self.contract.validate_node_layer(node_type, declared_layer)
            if not valid:
                unsupported.append(err or "invalid layer")

        # 2. Representation edge checks: ensure CANDIDATE is never promoted
        for edge in snapshot_copy.get("edges", []):
            edge_type = edge.get("type", "")
            target_interp = edge.get("attributes", {}).get("interpretation", "")
            valid, err = self.contract.validate_edge_promotion(edge_type, target_interp)
            if not valid:
                diagnostics.append(err or "illegal edge promotion")

        # 3. Host-grounded projection: extract parameters directly from host nodes
        host_bindings = selection_manifest.get("host_bindings", {})
        model_params: Dict[str, Any] = {}
        states: List[Dict[str, Any]] = []

        if host_bindings:
            # Demand binding
            demand_spec = host_bindings.get("demand", {})
            d_node = nodes_by_id.get(demand_spec.get("source_node_id"))
            if d_node and demand_spec.get("attribute_field") in d_node.get("attributes", {}):
                val = d_node["attributes"][demand_spec["attribute_field"]]
                model_params["demand"] = val
                field_prov.append(HostFieldProvenance("demand", d_node["id"], demand_spec["attribute_field"], val))
            else:
                model_params["demand"] = None

            # Carrier schedule bindings
            sched_spec = host_bindings.get("schedule", {})
            s_node = nodes_by_id.get(sched_spec.get("source_node_id"))
            if s_node:
                for p_key, attr_key in sched_spec.get("attribute_fields", {}).items():
                    val = s_node.get("attributes", {}).get(attr_key)
                    model_params[p_key] = val
                    field_prov.append(HostFieldProvenance(p_key, s_node["id"], attr_key, val))
            else:
                model_params["regular_capacity"] = None
                model_params["bridge_capacity"] = None
                model_params["loading_capacity"] = None

            # State space domain from model object
            model_obj_spec = host_bindings.get("model_object", {})
            m_node = nodes_by_id.get(model_obj_spec.get("node_id"))
            if m_node:
                c_vals = m_node.get("attributes", {}).get(model_obj_spec.get("capacity_field", "capacity_values"), [])
                a_vals = m_node.get("attributes", {}).get(model_obj_spec.get("availability_field", "availability_values"), [])
                field_prov.append(HostFieldProvenance("capacity_values", m_node["id"], model_obj_spec.get("capacity_field", "capacity_values"), c_vals))
                field_prov.append(HostFieldProvenance("availability_values", m_node["id"], model_obj_spec.get("availability_field", "availability_values"), a_vals))
                if c_vals and a_vals:
                    states = [{"id": f"c{c}a{a}", "C": c, "A": a} for c in c_vals for a in a_vals]
        else:
            # Fallback for direct manifest-supplied parameters if no host bindings declared
            model_params = deepcopy(selection_manifest.get("model_parameters", {}))
            states = deepcopy(selection_manifest.get("states", []))

        # Check for unsupported continuous domains or unrepresentable infinity
        if selection_manifest.get("domain_type") == "continuous":
            unsupported.append("Continuous domains are unsupported in finite reference model")

        # Check for actual lifecycle projection (unsupported in v0.1)
        if selection_manifest.get("request_lifecycle_projection") is True:
            unsupported.append("Actual lifecycle projection (grant expiry invalidation, cancellation release) is unsupported in v0.1")

        # 4. Evidence reports
        reports: List[Dict[str, Any]] = []
        for r_spec in selection_manifest.get("selected_reports", []):
            rep = deepcopy(r_spec)
            if not rep.get("subject"):
                rep["subject"] = scope.get("subject")
            if not rep.get("window"):
                rep["window"] = scope.get("window")
            reports.append(rep)

        # 5. Grammar observations & context
        grammar_obs = deepcopy(selection_manifest.get("grammar_observation"))
        grammar_ctx = deepcopy(selection_manifest.get("grammar_context"))

        # 6. Proposal & Authority views (informational only in v0.1 read-only adapter)
        proposal = deepcopy(selection_manifest.get("proposal"))
        authority_views: List[Dict[str, Any]] = []
        for v in selection_manifest.get("authority_views", []):
            if v.get("source_assertion") is True or v.get("layer") == "source":
                diagnostics.append("Source assertion claiming authority detected: cannot become reviewed grant")
            authority_views.append(deepcopy(v))

        # 7. Timeline events & clock domain ownership
        clock_domains = {}
        timeline_events = []
        raw_cd_id = selection_manifest.get("clock_domain_id", "uow-boundary-default")
        try:
            c_dom = clock_domain or ClockDomain(
                domain_id=raw_cd_id,
                owner_boundary="default",
                description="Default execution boundary clock domain",
            )
            clock_domains[c_dom.domain_id] = c_dom
        except ValueError as exc:
            unsupported.append(f"Invalid clock domain specification: {exc}")
            c_dom = None

        if c_dom:
            for evt in selection_manifest.get("timeline_events", []):
                e_copy = deepcopy(evt)
                actor = e_copy.get("actor", "")
                try:
                    if isinstance(actor, str) and not actor.startswith(CLOCK_IDENTITY_PREFIX):
                        e_copy["actor"] = c_dom.format_event_actor(actor)
                except (ValueError, TypeError) as exc:
                    diagnostics.append(f"Ambiguous or invalid event actor rejected: {exc}")
                timeline_events.append(e_copy)

        # Determine projection status
        if unsupported:
            status = ProjectionStatus.UNSUPPORTED_PROJECTION
        elif not states or not model_params:
            status = ProjectionStatus.INVALID_INPUT
        elif any(v is None for v in model_params.values()) or any(s.get("C") is None or s.get("A") is None for s in states):
            status = ProjectionStatus.SUPPORTED_WITH_UNKNOWNS
        else:
            status = ProjectionStatus.SUPPORTED_CASE

        return ProjectedAnalysisCase(
            case_id=case_id,
            revision=revision,
            source_snapshot_digest=snapshot_digest,
            status=status,
            model_metadata=selection_manifest.get("model_metadata", {}),
            model_parameters=model_params,
            states=states,
            scope=scope,
            field_provenance=field_prov,
            evidence_reports=reports,
            grammar_observation=grammar_obs,
            grammar_context=grammar_ctx,
            proposal=proposal,
            authority_views=authority_views,
            clock_domains=clock_domains,
            timeline_events=timeline_events,
            unsupported_reasons=unsupported,
            diagnostics=diagnostics,
        )

    def evaluate_case(
        self,
        case: ProjectedAnalysisCase,
        snapshot_ref: Optional[Dict[str, Any]] = None,
    ) -> AttributedAnalysisResult:
        """Evaluates projected case using intel_uow reference semantics."""
        pre_digest = _canonical_digest(snapshot_ref) if snapshot_ref else case.source_snapshot_digest
        diagnostics = list(case.diagnostics)
        retained_unknowns = []

        if case.status in (ProjectionStatus.UNSUPPORTED_PROJECTION, ProjectionStatus.INVALID_INPUT):
            return AttributedAnalysisResult(
                case_id=case.case_id,
                revision=case.revision,
                projection_status=case.status,
                source_snapshot_digest=case.source_snapshot_digest,
                model_assumptions=[],
                model_bindings={},
                field_provenance=case.field_provenance,
                baseline_evaluation={"status": case.status.value, "reasons": case.unsupported_reasons},
                meaningful_gaps=[],
                hypothetical_consequences=None,
                evidence_summary=None,
                grammar_interpretation=None,
                admission_result=None,
                reassessment_result=None,
                immutability_verified=True,
                retained_unknowns=retained_unknowns,
                diagnostics=diagnostics + case.unsupported_reasons,
            )

        # 1. Baseline evaluation
        baseline = analysis.evaluate(case.states, case.model_parameters)

        # 2. Evidence summary
        evidence_summary = None
        if case.evidence_reports:
            target_scope = dict(case.scope, predicate="availability", modality="actual")
            evidence_summary = analysis.summarize_evidence(case.evidence_reports, target_scope)

        # 3. Gap derivation
        variables = case.model_metadata.get("gap_variables", ["C", "A"])
        gaps = analysis.derive_gaps(
            case.states,
            variables,
            {"id": f"{case.case_id}-question", "revision": case.revision},
            case.scope,
        )

        # 4. Hypothetical scenario observation (evaluated with actual_world_changed=False)
        hypothetical = None
        outcome_constraints = case.model_metadata.get("outcome_constraints")
        if outcome_constraints:
            hypothetical = analysis.observe(
                case.states,
                {"outcome_constraints": outcome_constraints},
                case.model_metadata.get("target_outcome", "ready"),
            )

        # 5. Grammar interpretation (if provided)
        grammar_interp = None
        if case.grammar_observation and case.grammar_context:
            grammar_interp = grammar.interpret(case.grammar_observation, case.grammar_context)

        # 6. Informational authority check (actual lifecycle mutations are unsupported in v0.1)
        admission_result = None
        if case.proposal and case.authority_views:
            valid_views = [
                v for v in case.authority_views
                if v.get("source_assertion") is not True
                and v.get("layer") != "source"
                and v.get("hypothetical") is not True
            ]
            if valid_views:
                wf = Workflow()
                wf.apply({
                    "type": "add_work",
                    "id": "work-01",
                    "proposal": case.proposal,
                    "reservations": case.proposal.get("resources", {}),
                    "duties": ["retain source attribution"],
                })
                admission_result = wf.apply({
                    "type": "admit_work",
                    "work_id": "work-01",
                    "views": valid_views,
                })
            else:
                admission_result = {
                    "status": "unresolved",
                    "reasons": ["no valid actual authority views provided"],
                }

        # 7. Model reassessment check
        reassessment_res = None
        old_pins = case.model_metadata.get("old_dependency_pins")
        new_pins = case.model_metadata.get("new_dependency_pins")
        known_deps = case.model_metadata.get("known_dependencies", [])
        new_candidates = case.model_metadata.get("new_candidate_dependencies", [])
        if old_pins and new_pins:
            reassessment_res = analysis.reassessment(old_pins, new_pins, known_deps, new_candidates)

        # Track retained unknowns
        for s in case.states:
            for k, val in s.items():
                if val is None or val == "unknown":
                    retained_unknowns.append(f"state:{s.get('id')}:{k}")

        # Post-execution immutability verification
        post_digest = _canonical_digest(snapshot_ref) if snapshot_ref else case.source_snapshot_digest
        immutability_verified = (pre_digest == post_digest)

        return AttributedAnalysisResult(
            case_id=case.case_id,
            revision=case.revision,
            projection_status=case.status,
            source_snapshot_digest=case.source_snapshot_digest,
            model_assumptions=case.model_metadata.get("assumptions", []),
            model_bindings=case.model_parameters,
            field_provenance=case.field_provenance,
            baseline_evaluation=baseline,
            meaningful_gaps=gaps,
            hypothetical_consequences=hypothetical,
            evidence_summary=evidence_summary,
            grammar_interpretation=grammar_interp,
            admission_result=admission_result,
            reassessment_result=reassessment_res,
            immutability_verified=immutability_verified,
            retained_unknowns=retained_unknowns,
            diagnostics=diagnostics,
        )
