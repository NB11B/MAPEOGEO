"""Authority Domain Adapter for Host Graphs and Work Proposals.

Projects host graph records, service contracts, and work proposals into
domain-level ActionCases for deterministic authority evaluation and UoW certification.
Maintains absolute domain neutrality with zero external experiment dependencies.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from mapeogeo.domains.authority.certification import AuthorityCertificateWitness
from mapeogeo.domains.authority.evaluator import AuthorityEvaluator
from mapeogeo.domains.authority.ontology import ActionCase


EXCLUDED_SURFACES: Set[str] = {
    "actual_lifecycle_projection",
    "dynamic_grant_expiry_invalidation",
    "cancellation_reservation_release",
    "live_mutation_of_host_graph",
    "external_execution_enabled",
}


def _canonical_digest(data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AuthorityAdapter:
    """Adapter projecting host graph nodes and work proposals into authority evaluation."""

    def __init__(self, context: Dict[str, Any]) -> None:
        self.context = context
        self.evaluator = AuthorityEvaluator(context)

    def project_host_snapshot(
        self,
        snapshot: Dict[str, Any],
        case_id: str = "projected_case_v1",
        requested_surfaces: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Projects a host graph snapshot into an authority action case without mutating the host graph."""
        if not isinstance(snapshot, dict):
            return {
                "status": "invalid_input",
                "diagnostics": ["INVALID_SNAPSHOT_STRUCTURE: snapshot must be a JSON object"],
                "action_case": None,
            }

        nodes = snapshot.get("nodes", [])
        if not isinstance(nodes, list):
            return {
                "status": "invalid_input",
                "diagnostics": ["INVALID_SNAPSHOT_STRUCTURE: 'nodes' must be a list"],
                "action_case": None,
            }

        # Check excluded surfaces
        diagnostics: List[str] = []
        if requested_surfaces:
            for s in requested_surfaces:
                if s in EXCLUDED_SURFACES:
                    return {
                        "status": "unsupported_projection",
                        "diagnostics": [f"EXCLUDED_SURFACE_REQUESTED: {s}"],
                        "action_case": None,
                    }

        # Index nodes and extract parameters
        node_map: Dict[str, Dict[str, Any]] = {}
        for n in nodes:
            if isinstance(n, dict):
                nid = n.get("node_id") or n.get("id")
                if nid:
                    node_map[nid] = n

        # Extract attributes from service contract or carrier schedule if present
        svc = node_map.get("src:service_contract:v1", {})
        carrier = node_map.get("src:carrier_schedule:v1", {})

        actor_id = carrier.get("attributes", {}).get("carrier_id", "actor:carrier:unassigned")
        affected_id = svc.get("attributes", {}).get("client_id", "actor:client:unassigned")
        operation_id = svc.get("attributes", {}).get("operation_id", "op:host_service_execution")

        action_case = {
            "case_id": case_id,
            "actor_id": actor_id,
            "affected_actor_id": affected_id,
            "operation_id": operation_id,
            "context_ref": self.context.get("ref", {"id": "ctx:default", "revision": 1}),
            "parameters": {
                "demand_units": svc.get("attributes", {}).get("demand_units", 0),
                "window": svc.get("attributes", {}).get("window", 0),
            },
        }

        return {
            "status": "projected",
            "diagnostics": [],
            "action_case": action_case,
            "source_digest": _canonical_digest(snapshot),
        }

    def assess_host_contract(self, host_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Projects a host service contract or carrier schedule snapshot and evaluates authority."""
        proj = self.project_host_snapshot(host_snapshot)
        if proj["status"] == "projected" and proj["action_case"]:
            return self.evaluator.assess_case(proj["action_case"])
        return proj

    def certify_uow_proposal(self, proposal: Dict[str, Any]) -> AuthorityCertificateWitness:
        """Evaluates domain authority certification for an incoming work proposal."""
        case = proposal.get("case", proposal.get("subject", {}))
        return self.evaluator.certify_work(case)
