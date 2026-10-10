"""Build synthetic fixtures, direct oracle (288 cells), reverse domains, and host mapping contract for Gate G0a/G0b.

Deterministic qualification expectations authored independently before candidate evaluator implementation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE_DIR = Path(r"c:\Users\nateb\Documents\MAPEOGEO-frozen-main\experiments\authority_assessment\v0_1")
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"
QUAL_DIR = BASE_DIR / "qualification"

FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
QUAL_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# 1. Synthetic Actors, Operations, Interests
# ------------------------------------------------------------------------------
ACTORS = [
    {"id": "actor:regulator:alpha", "name": "Alpha Oversight Board", "capacity": "regulator", "jurisdiction": "jur:fictional:state"},
    {"id": "actor:investigator:beta", "name": "Beta Investigation Unit", "capacity": "investigator", "jurisdiction": "jur:fictional:state"},
    {"id": "actor:licensee:gamma", "name": "Gamma Commercial Carrier", "capacity": "licensee", "jurisdiction": "jur:fictional:state"},
    {"id": "actor:auditor:delta", "name": "Delta Compliance Auditor", "capacity": "auditor", "jurisdiction": "jur:fictional:state"},
    {"id": "actor:citizen:epsilon", "name": "Epsilon Private Subject", "capacity": "citizen", "jurisdiction": "jur:fictional:state"},
    {"id": "actor:third_party:zeta", "name": "Zeta Data Services", "capacity": "third_party", "jurisdiction": "jur:fictional:state"},
]

OPERATIONS = [
    {"id": "op:request_record", "name": "request_record", "mode": "voluntary", "requires_coercion": False},
    {"id": "op:compel_record", "name": "compel_record", "mode": "coercive", "requires_coercion": True},
    {"id": "op:retain_record", "name": "retain_record", "mode": "custodial", "requires_coercion": False},
    {"id": "op:share_record", "name": "share_record", "mode": "transmissive", "requires_coercion": False},
]

INTERESTS = [
    {"id": "interest:confidentiality", "name": "Commercial and Personal Confidentiality"},
    {"id": "interest:due_process", "name": "Due Process & Statutory Authority Limits"},
    {"id": "interest:compliance", "name": "Operational Regulatory Compliance"},
    {"id": "interest:transparency", "name": "Public Record Transparency"},
]

(FIXTURES_DIR / "actors.json").write_text(json.dumps(ACTORS, indent=2), encoding="utf-8")
(FIXTURES_DIR / "operations.json").write_text(json.dumps(OPERATIONS, indent=2), encoding="utf-8")
(FIXTURES_DIR / "interests.json").write_text(json.dumps(INTERESTS, indent=2), encoding="utf-8")

# ------------------------------------------------------------------------------
# 2. Rule Packs: Commercial Privacy & Public Oversight
# ------------------------------------------------------------------------------
RULE_PACK_PRIVACY = {
    "pack_id": "pack:commercial_privacy_v1",
    "name": "Fictional Commercial Privacy & Data Protection Rules",
    "version": "1.0",
    "rules": [
        {
            "id": "rule:priv:01",
            "name": "Voluntary Request Permission",
            "operation": "op:request_record",
            "norm": "permission",
            "performer_capacities": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
            "target_capacities": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
            "condition": "true",
            "interest": "interest:transparency",
        },
        {
            "id": "rule:priv:02",
            "name": "Coercive Compulsion Prohibition on Private Entities",
            "operation": "op:compel_record",
            "norm": "prohibition",
            "performer_capacities": ["licensee", "citizen", "third_party"],
            "target_capacities": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
            "condition": "true",
            "interest": "interest:due_process",
        },
        {
            "id": "rule:priv:03",
            "name": "Data Sharing Requires Explicit Consent",
            "operation": "op:share_record",
            "norm": "permission",
            "performer_capacities": ["licensee", "auditor", "third_party"],
            "target_capacities": ["citizen", "licensee"],
            "condition": "has_explicit_consent",
            "interest": "interest:confidentiality",
        },
        {
            "id": "rule:priv:04",
            "name": "Retention Restricted to Operating Scope",
            "operation": "op:retain_record",
            "norm": "permission",
            "performer_capacities": ["regulator", "investigator", "licensee", "auditor"],
            "target_capacities": ["licensee", "citizen"],
            "condition": "within_statutory_window",
            "interest": "interest:compliance",
        },
    ]
}

RULE_PACK_OVERSIGHT = {
    "pack_id": "pack:public_oversight_v1",
    "name": "Fictional Public Oversight & Statutory Compulsion Rules",
    "version": "1.0",
    "rules": [
        {
            "id": "rule:over:01",
            "name": "Statutory Regulatory Compulsion Power",
            "operation": "op:compel_record",
            "norm": "power",
            "performer_capacities": ["regulator", "investigator"],
            "target_capacities": ["licensee", "auditor", "third_party"],
            "condition": "has_active_warrant_or_order",
            "interest": "interest:compliance",
        },
        {
            "id": "rule:over:02",
            "name": "Compulsion of Regulatory Authority Prohibited",
            "operation": "op:compel_record",
            "norm": "prohibition",
            "performer_capacities": ["licensee", "auditor", "citizen", "third_party"],
            "target_capacities": ["regulator"],
            "condition": "true",
            "interest": "interest:due_process",
        },
        {
            "id": "rule:over:03",
            "name": "Mandatory Regulatory Audit Sharing",
            "operation": "op:share_record",
            "norm": "duty",
            "performer_capacities": ["licensee", "auditor"],
            "target_capacities": ["regulator", "investigator"],
            "condition": "audit_completed",
            "interest": "interest:transparency",
        },
        {
            "id": "rule:over:04",
            "name": "Statutory Retention Obligation for Oversight",
            "operation": "op:retain_record",
            "norm": "duty",
            "performer_capacities": ["regulator", "investigator", "licensee"],
            "target_capacities": ["licensee", "citizen", "auditor", "third_party"],
            "condition": "true",
            "interest": "interest:compliance",
        },
    ]
}

(FIXTURES_DIR / "rule_pack_commercial_privacy.json").write_text(json.dumps(RULE_PACK_PRIVACY, indent=2), encoding="utf-8")
(FIXTURES_DIR / "rule_pack_public_oversight.json").write_text(json.dumps(RULE_PACK_OVERSIGHT, indent=2), encoding="utf-8")

# ------------------------------------------------------------------------------
# 3. Direct Oracle: 288 Cells (6 actors x 6 affected x 4 operations x 2 packs)
# ------------------------------------------------------------------------------
oracle_cells = []
cell_idx = 0

packs = [
    ("pack:commercial_privacy_v1", RULE_PACK_PRIVACY),
    ("pack:public_oversight_v1", RULE_PACK_OVERSIGHT),
]

for pack_id, pack_def in packs:
    for actor in ACTORS:
        for affected in ACTORS:
            for op in OPERATIONS:
                cell_idx += 1
                cell_id = f"cell_{cell_idx:03d}"
                actor_id = actor["id"]
                actor_cap = actor["capacity"]
                affected_id = affected["id"]
                affected_cap = affected["capacity"]
                op_id = op["id"]

                # Determine expected disposition under fictional rules
                disposition = "unresolved"
                applicable_rules = []
                decisive_rules = []
                conditions = {}
                interests = []
                gaps = []

                if pack_id == "pack:commercial_privacy_v1":
                    if op_id == "op:request_record":
                        # Voluntary requests are universally permitted under priv:01
                        disposition = "supported_within_scope"
                        applicable_rules = ["rule:priv:01"]
                        decisive_rules = ["rule:priv:01"]
                        interests = ["interest:transparency"]
                    elif op_id == "op:compel_record":
                        if actor_cap in ["licensee", "citizen", "third_party"]:
                            # Private entities are explicitly prohibited from compulsion under priv:02
                            disposition = "prohibited_under_reviewed_rule"
                            applicable_rules = ["rule:priv:02"]
                            decisive_rules = ["rule:priv:02"]
                            interests = ["interest:due_process"]
                        else:
                            # Regulators / investigators compelling under privacy pack without oversight pack rule
                            disposition = "unresolved"
                            gaps = ["missing_statutory_basis"]
                    elif op_id == "op:share_record":
                        if actor_cap in ["licensee", "auditor", "third_party"] and affected_cap in ["citizen", "licensee"]:
                            # Permitted if consent condition met, but in default baseline condition is unknown
                            disposition = "conditions_unmet"
                            applicable_rules = ["rule:priv:03"]
                            decisive_rules = ["rule:priv:03"]
                            conditions["has_explicit_consent"] = "refuted"
                            interests = ["interest:confidentiality"]
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_sharing_authorization"]
                    elif op_id == "op:retain_record":
                        if actor_cap in ["regulator", "investigator", "licensee", "auditor"] and affected_cap in ["licensee", "citizen"]:
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:priv:04"]
                            decisive_rules = ["rule:priv:04"]
                            conditions["within_statutory_window"] = "supported"
                            interests = ["interest:compliance"]
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_retention_authority"]

                elif pack_id == "pack:public_oversight_v1":
                    if op_id == "op:compel_record":
                        if actor_cap in ["licensee", "auditor", "citizen", "third_party"] and affected_cap == "regulator":
                            disposition = "prohibited_under_reviewed_rule"
                            applicable_rules = ["rule:over:02"]
                            decisive_rules = ["rule:over:02"]
                            interests = ["interest:due_process"]
                        elif actor_cap in ["regulator", "investigator"] and affected_cap in ["licensee", "auditor", "third_party"]:
                            # Statutory power exists, but active warrant/order condition is needed
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:over:01"]
                            decisive_rules = ["rule:over:01"]
                            conditions["has_active_warrant_or_order"] = "supported"
                            interests = ["interest:compliance"]
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_jurisdictional_authority"]
                    elif op_id == "op:share_record":
                        if actor_cap in ["licensee", "auditor"] and affected_cap in ["regulator", "investigator"]:
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:over:03"]
                            decisive_rules = ["rule:over:03"]
                            conditions["audit_completed"] = "supported"
                            interests = ["interest:transparency"]
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_statutory_duty"]
                    elif op_id == "op:retain_record":
                        if actor_cap in ["regulator", "investigator", "licensee"]:
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:over:04"]
                            decisive_rules = ["rule:over:04"]
                            interests = ["interest:compliance"]
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_custodial_duty"]
                    elif op_id == "op:request_record":
                        # Oversight pack doesn't govern voluntary requests; remains unresolved without privacy pack
                        disposition = "unresolved"
                        gaps = ["missing_oversight_provision"]

                # Case digest
                case_raw = f"{pack_id}:{actor_id}:{affected_id}:{op_id}"
                case_digest = hashlib.sha256(case_raw.encode("utf-8")).hexdigest()

                oracle_cells.append({
                    "cell_id": cell_id,
                    "actor": actor_id,
                    "performer_capacity": actor_cap,
                    "affected_actor": affected_id,
                    "affected_capacity": affected_cap,
                    "operation": op_id,
                    "scope_pack": pack_id,
                    "case_digest": case_digest,
                    "disposition": disposition,
                    "applicable_rule_refs": applicable_rules,
                    "decisive_rule_refs": decisive_rules,
                    "condition_states": conditions,
                    "affected_interest_refs": interests,
                    "coverage_state": "complete_coverage" if disposition != "unresolved" else "partial_coverage",
                    "expected_gap_kinds": gaps,
                })

assert len(oracle_cells) == 288, f"Expected 288 cells, got {len(oracle_cells)}"

oracle_data = {
    "catalog_id": "mapeogeo_authority_direct_oracle",
    "version": "0.1",
    "status": "frozen_independent_oracle",
    "author": "Nathanael J. Bocker",
    "total_cells": len(oracle_cells),
    "dimension_summary": {
        "actors": len(ACTORS),
        "affected_actors": len(ACTORS),
        "operations": len(OPERATIONS),
        "scope_packs": len(packs),
        "cells": len(oracle_cells),
    },
    "disposition_counts": {
        "supported_within_scope": sum(1 for c in oracle_cells if c["disposition"] == "supported_within_scope"),
        "conditions_unmet": sum(1 for c in oracle_cells if c["disposition"] == "conditions_unmet"),
        "prohibited_under_reviewed_rule": sum(1 for c in oracle_cells if c["disposition"] == "prohibited_under_reviewed_rule"),
        "unresolved": sum(1 for c in oracle_cells if c["disposition"] == "unresolved"),
    },
    "cells": oracle_cells,
}

(QUAL_DIR / "direct_oracle_v0_1.json").write_text(json.dumps(oracle_data, indent=2), encoding="utf-8")
print(f"Generated direct oracle with {len(oracle_cells)} cells. Dispositions: {oracle_data['disposition_counts']}")

# ------------------------------------------------------------------------------
# 4. Reverse Domains
# ------------------------------------------------------------------------------
reverse_domains = {
    "catalog_id": "mapeogeo_authority_reverse_domains",
    "version": "0.1",
    "status": "frozen_reverse_domains",
    "complete_actor_domain": [a["id"] for a in ACTORS],
    "complete_capacity_domain": sorted(list({a["capacity"] for a in ACTORS})),
    "complete_operation_domain": [o["id"] for o in OPERATIONS],
    "scope_packs": [p[0] for p in packs],
    "sample_queries": [
        {
            "query_type": "enumerate_actions",
            "actor": "actor:regulator:alpha",
            "affected_actor": "actor:licensee:gamma",
            "scope_pack": "pack:commercial_privacy_v1",
            "expected_supported_actions": ["op:request_record", "op:retain_record"],
        },
        {
            "query_type": "enumerate_actors",
            "operation": "op:compel_record",
            "affected_actor": "actor:licensee:gamma",
            "scope_pack": "pack:public_oversight_v1",
            "expected_supported_actors": ["actor:regulator:alpha", "actor:investigator:beta"],
        },
    ]
}
(QUAL_DIR / "reverse_domains_v0_1.json").write_text(json.dumps(reverse_domains, indent=2), encoding="utf-8")
print("Generated reverse domains specification.")

# ------------------------------------------------------------------------------
# 5. Host Mapping Contract (Gate G0b)
# ------------------------------------------------------------------------------
host_mapping = {
    "contract_id": "mapeogeo_authority_host_mapping_contract_v0_1",
    "version": "0.1",
    "date": "2026-10-09",
    "status": "gate_g0b_inspected_and_complete",
    "inspected_host_commit": "f7e6ee6b12c28bca95a967e212593bbadb7b8bb9",
    "inspected_host_adapter": "experiments/intelligence_integration/v0_1/adapter.py",
    "inspected_clock_identity": "experiments/intelligence_integration/v0_1/clock_identity.py",
    "clock_identity_format": "uow-clock:v1:[domain_id, local_actor]",
    "host_grounded_nodes": [
        {"node_id": "src:service_contract:v1", "attribute": "demand_units"},
        {"node_id": "src:carrier_schedule:v1", "attribute": "capacity_values"},
        {"node_id": "obj:carrier_capacity_model:v1", "attribute": "capacity_values"}
    ],
    "excluded_surfaces": [
        "actual_lifecycle_projection",
        "dynamic_grant_expiry_invalidation",
        "cancellation_reservation_release",
        "live_mutation_of_host_graph"
    ],
    "gate_g0b_determination": "Actual host interface, host commit, and clock-domain mapping are inspected and documented. Standalone kernel proceeds with host projection contract ready."
}
(BASE_DIR / "host_mapping_contract.json").write_text(json.dumps(host_mapping, indent=2), encoding="utf-8")
print("Generated host_mapping_contract.json for Gate G0b.")
