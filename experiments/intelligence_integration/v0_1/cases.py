"""Constructed Test Cases for MAPEOGEO Intelligence Integration (v0.1).

Contains the pinned MAPEOGEO graph snapshots, selection manifests, and corresponding
direct reference inputs for:
1. Standard capacity & continuity case (exact reference parity)
2. Case with unknown facts (retaining uncertainty)
3. Multi-lineage and shared-origin evidence cases
4. Independent UoW clock domains (local counter isolation)
5. Unsupported projection cases (continuous distributions, global clock sync)
6. Boundary defense cases (candidate promotion, hypothetical leakage, source authority)
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from .contract import ClockDomain


def build_constructed_capacity_snapshot() -> Dict[str, Any]:
    """Builds a pinned MAPEOGEO graph snapshot representing the carrier continuity problem."""
    nodes = [
        # Source layer declarations
        {
            "id": "src:service_contract:v1",
            "type": "SOURCE",
            "layer": "source",
            "label": "Master Service Delivery Contract W1",
            "attributes": {
                "demand_units": 10,
                "window": "service-window",
                "hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            },
        },
        {
            "id": "src:carrier_schedule:v1",
            "type": "SOURCE",
            "layer": "source",
            "label": "Carrier Allocation Schedule",
            "attributes": {
                "regular_capacity": 4,
                "bridge_capacity": 6,
                "loading_capacity": 10,
            },
        },
        {
            "id": "src:assessment_note:v1",
            "type": "SOURCE",
            "layer": "source",
            "label": "Reserve Carrier Readiness Review Note",
            "attributes": {
                "content": "constructed review note: accepted",
                "author": "reviewer",
            },
        },
        # Subject hypothesis / Mathematical objects layer
        {
            "id": "obj:carrier_capacity_model:v1",
            "type": "OBJECT",
            "layer": "subject_hypothesis",
            "label": "Finite Carrier Capacity and Availability Model",
            "attributes": {
                "domain": "finite_discrete",
                "carrier": "reserve-carrier",
                "capacity_values": [3, 6],
                "availability_values": [0, 1],
            },
        },
        {
            "id": "repr:eo_candidate:v1",
            "type": "REPRESENTATION",
            "layer": "subject_hypothesis",
            "label": "Operator View: Carrier Composition",
            "attributes": {"view": "EO"},
        },
        {
            "id": "repr:geo_candidate:v1",
            "type": "REPRESENTATION",
            "layer": "subject_hypothesis",
            "label": "Geometric View: State Space Mesh",
            "attributes": {"view": "GEO"},
        },
        # Analytical derivation layer
        {
            "id": "cert:capacity_bound:v1",
            "type": "CERTIFICATE",
            "layer": "analytical_derivation",
            "label": "Minimax Shortfall Certificate",
            "attributes": {"upper_bound": "6"},
        },
        # Actual UoW layer
        {
            "id": "uow:task:review_01",
            "type": "UOW_TASK",
            "layer": "actual_uow",
            "label": "Service Uncertainty Review Task",
            "attributes": {
                "actor": "analyst",
                "purpose": "assess service uncertainty",
            },
        },
    ]

    edges = [
        # Provenance edges
        {
            "id": "edge:prov:01",
            "source": "src:service_contract:v1",
            "target": "obj:carrier_capacity_model:v1",
            "type": "SOURCED_FROM",
        },
        # Candidate representation edges (must NOT be promoted to SAME_SEMANTICS)
        {
            "id": "edge:eo_cand:01",
            "source": "obj:carrier_capacity_model:v1",
            "target": "repr:eo_candidate:v1",
            "type": "CANDIDATE_EO",
            "attributes": {"interpretation": "CANDIDATE_REPRESENTS"},
        },
        {
            "id": "edge:geo_cand:01",
            "source": "obj:carrier_capacity_model:v1",
            "target": "repr:geo_candidate:v1",
            "type": "CANDIDATE_GEO",
            "attributes": {"interpretation": "CANDIDATE_REPRESENTS"},
        },
        # Governed UoW relationship
        {
            "id": "edge:uow:01",
            "source": "uow:task:review_01",
            "target": "obj:carrier_capacity_model:v1",
            "type": "DEPENDS_ON",
        },
    ]

    return {
        "snapshot_id": "mapeogeo-snapshot:capacity-carrier:2026-10-09",
        "version": 1,
        "nodes": nodes,
        "edges": edges,
    }


def build_constructed_selection_manifest() -> Dict[str, Any]:
    """Builds the selection manifest to project the capacity case."""
    scope = {"subject": "reserve-carrier", "window": "service-window"}
    states = [
        {"id": f"c{c}a{a}", "C": c, "A": a}
        for c in (3, 6)
        for a in (0, 1)
    ]
    model_params = {
        "demand": 10,
        "regular_capacity": 4,
        "bridge_capacity": 6,
        "loading_capacity": 10,
    }
    model_metadata = {
        "model_id": "uow.intelligence.meaningful_gaps.carrier_continuity.v0_3",
        "version": "0.3.0",
        "gap_variables": ["C", "A"],
        "outcome_constraints": {"ready": [{"A": 0}, {"A": 1}]},
        "target_outcome": "ready",
        "assumptions": [
            {"id": "ASM_DEMAND", "statement": "Demand is 10 units in service window."},
            {"id": "ASM_REGULAR", "statement": "Regular carrier contributes 4."},
            {"id": "ASM_RESERVE", "statement": "Reserve capacity in {3,6}, availability in {0,1}."},
            {"id": "ASM_BRIDGE", "statement": "Bridge booking adds 6 units."},
        ],
        "old_dependency_pins": {"loading-model": 1},
        "new_dependency_pins": {"loading-model": 2},
        "known_dependencies": ["loading-model"],
        "new_candidate_dependencies": ["alternative-realization"],
    }

    claim = {"id": "availability-claim", "speaker": "reporter", "proposition": "Carrier is available"}
    grammar_obs = {
        "before": {"claims": [claim], "assessments": []},
        "after": {
            "claims": [claim],
            "assessments": [
                {
                    "id": "assessment",
                    "author": "reviewer",
                    "claim": claim["id"],
                    "disposition": "accepted",
                }
            ],
        },
        "coverage": {"claims": "complete", "assessments": "complete"},
        "evidence": [
            {
                "id": "review-witness",
                "source": "src:assessment_note:v1",
                "status": "supported",
                "type": "assessment_record",
                "assessment": "assessment",
                "author": "reviewer",
                "claim": claim["id"],
            }
        ],
    }
    grammar_ctx = {
        "id": "meaning-context",
        "revision": 1,
        "vocabulary_ref": {"id": "typed-operators", "revision": 1},
        "source_convention": {
            "id": "review-language",
            "revision": 1,
            "alternative_type_lists": True,
            "author_dispositions": ["accepted", "rejected", "deferred"],
        },
        "focal_occurrence": "review-act",
        "focal_witness_ids": ["review-witness"],
        "alternative_coverage": "complete",
    }

    target = dict(scope, predicate="availability", modality="actual")
    reports = [
        dict(target, id="positive-report", polarity="positive", origin="origin-1", status="supported"),
        dict(target, id="negative-report", polarity="negative", origin="origin-2", status="supported"),
    ]

    proposal = {
        "id": "review-proposal",
        "revision": 1,
        "actor": "analyst",
        "action": "review_records",
        "purpose": "assess service uncertainty",
        "scope": scope,
        "resources": {"analyst_hours": 1},
        "recipients": ["case-review-team"],
    }

    grant = {
        "status": "established",
        "actor": proposal["actor"],
        "actions": ["review_records"],
        "purpose": proposal["purpose"],
        "scope": scope,
        "resource_limits": {"analyst_hours": 2},
        "recipients": proposal["recipients"],
        "grant_id": "review-grant",
        "grant_revision": 1,
        "grant_effective": True,
    }

    host_bindings = {
        "demand": {
            "source_node_id": "src:service_contract:v1",
            "attribute_field": "demand_units",
        },
        "schedule": {
            "source_node_id": "src:carrier_schedule:v1",
            "attribute_fields": {
                "regular_capacity": "regular_capacity",
                "bridge_capacity": "bridge_capacity",
                "loading_capacity": "loading_capacity",
            },
        },
        "model_object": {
            "node_id": "obj:carrier_capacity_model:v1",
            "capacity_field": "capacity_values",
            "availability_field": "availability_values",
            "carrier_field": "carrier",
        },
    }

    return {
        "case_id": "capacity-continuity-case",
        "revision": 1,
        "scope": scope,
        "host_bindings": host_bindings,
        "model_metadata": model_metadata,
        "selected_reports": reports,
        "grammar_observation": grammar_obs,
        "grammar_context": grammar_ctx,
        "proposal": proposal,
        "authority_views": [grant],
        "clock_domain_id": "uow:boundary:carrier-service-01",
    }


def build_direct_reference_evaluation() -> Dict[str, Any]:
    """Runs direct evaluation using reference package functions for exact parity check."""
    from intel_uow import analysis, grammar

    scope = {"subject": "reserve-carrier", "window": "service-window"}
    states = [
        {"id": f"c{c}a{a}", "C": c, "A": a}
        for c in (3, 6)
        for a in (0, 1)
    ]
    model = {"demand": 10, "regular_capacity": 4, "bridge_capacity": 6, "loading_capacity": 10}

    claim = {"id": "availability-claim", "speaker": "reporter", "proposition": "Carrier is available"}
    observation = {
        "before": {"claims": [claim], "assessments": []},
        "after": {
            "claims": [claim],
            "assessments": [
                {
                    "id": "assessment",
                    "author": "reviewer",
                    "claim": claim["id"],
                    "disposition": "accepted",
                }
            ],
        },
        "coverage": {"claims": "complete", "assessments": "complete"},
        "evidence": [
            {
                "id": "review-witness",
                "source": "source-review",
                "status": "supported",
                "type": "assessment_record",
                "assessment": "assessment",
                "author": "reviewer",
                "claim": claim["id"],
            }
        ],
    }
    interpretation = grammar.interpret(
        observation,
        {
            "id": "meaning-context",
            "revision": 1,
            "vocabulary_ref": {"id": "typed-operators", "revision": 1},
            "source_convention": {
                "id": "review-language",
                "revision": 1,
                "alternative_type_lists": True,
                "author_dispositions": ["accepted", "rejected", "deferred"],
            },
            "focal_occurrence": "review-act",
            "focal_witness_ids": ["review-witness"],
            "alternative_coverage": "complete",
        },
    )

    target = dict(scope, predicate="availability", modality="actual")
    reports = [
        dict(target, id="positive-report", polarity="positive", origin="origin-1", status="supported"),
        dict(target, id="negative-report", polarity="negative", origin="origin-2", status="supported"),
    ]
    evidence = analysis.summarize_evidence(reports, target)
    baseline = analysis.evaluate(states, model)
    gaps = analysis.derive_gaps(states, ["C", "A"], {"id": "capacity-continuity-case-question", "revision": 1}, scope)
    hypothetical = analysis.observe(states, {"outcome_constraints": {"ready": [{"A": 0}, {"A": 1}]}}, "ready")
    reassessment = analysis.reassessment(
        {"loading-model": 1},
        {"loading-model": 2},
        ["loading-model"],
        new_candidates=["alternative-realization"],
    )

    return {
        "baseline": baseline,
        "evidence": evidence,
        "gaps": gaps,
        "hypothetical": hypothetical,
        "interpretation": interpretation,
        "reassessment": reassessment,
    }
