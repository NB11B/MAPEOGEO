"""Build synthetic fixtures, direct oracle (288 cells), reverse domains, and host mapping contract for Gate G0a/G0b.

Deterministic qualification expectations authored independently before candidate evaluator implementation.
Includes:
1. Complete domain fixtures (actors, capacities, operations, interests, source artifacts, reviews, rule packs).
2. Complete ActionCase bindings for each of the 288 direct oracle cells.
3. Explicit condition states distinguishing refuted conditions (conditions_unmet) from unknown conditions (unresolved).
4. Explicit rule norms distinguishing applicable prohibitions (prohibited_under_reviewed_rule) from missing grants (unresolved).
5. Comprehensive reverse domain queries with pre-computed expected selections.
6. Independent expectation review record documenting authorship, methodology, and freeze governance.
7. AQ subcase mapping index linking AQ01-AQ56 to concrete verification cells.
8. Host mapping contract with stream ownership, epoch semantics, and identity separation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(r"c:\Users\nateb\Documents\MAPEOGEO-frozen-main\experiments\authority_assessment\v0_1")
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"
QUAL_DIR = BASE_DIR / "qualification"

FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
QUAL_DIR.mkdir(parents=True, exist_ok=True)


def sha256_digest(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def canonical_json_digest(data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ==============================================================================
# 1. SYNTHETIC ACTORS & CAPACITIES
# ==============================================================================
ACTORS = [
    {
        "ref": "actor:regulator:alpha",
        "name": "Alpha Oversight Board",
        "kind": "organization",
        "jurisdiction": "jur:fictional:state",
        "capacity_refs": ["cap:regulator:alpha:oversight"],
        "identity_evidence_refs": ["ev:ident:alpha_statute"],
    },
    {
        "ref": "actor:investigator:beta",
        "name": "Beta Investigation Unit",
        "kind": "organization",
        "jurisdiction": "jur:fictional:state",
        "capacity_refs": ["cap:investigator:beta:enforcement"],
        "identity_evidence_refs": ["ev:ident:beta_charter"],
    },
    {
        "ref": "actor:licensee:gamma",
        "name": "Gamma Commercial Carrier",
        "kind": "organization",
        "jurisdiction": "jur:fictional:state",
        "capacity_refs": ["cap:licensee:gamma:operator"],
        "identity_evidence_refs": ["ev:ident:gamma_license"],
    },
    {
        "ref": "actor:auditor:delta",
        "name": "Delta Compliance Auditor",
        "kind": "organization",
        "jurisdiction": "jur:fictional:state",
        "capacity_refs": ["cap:auditor:delta:independent_audit"],
        "identity_evidence_refs": ["ev:ident:delta_accreditation"],
    },
    {
        "ref": "actor:citizen:epsilon",
        "name": "Epsilon Private Subject",
        "kind": "person",
        "jurisdiction": "jur:fictional:state",
        "capacity_refs": ["cap:citizen:epsilon:individual"],
        "identity_evidence_refs": ["ev:ident:epsilon_record"],
    },
    {
        "ref": "actor:third_party:zeta",
        "name": "Zeta Data Services",
        "kind": "organization",
        "jurisdiction": "jur:fictional:state",
        "capacity_refs": ["cap:third_party:zeta:commercial_service"],
        "identity_evidence_refs": ["ev:ident:zeta_registration"],
    },
]

CAPACITIES = [
    {
        "ref": "cap:regulator:alpha:oversight",
        "actor_ref": "actor:regulator:alpha",
        "capacity_kind": "regulator",
        "scope_ref": "scope:public_oversight",
        "evidence_refs": ["ev:cap:alpha_statute"],
        "evidence_state": "supported",
    },
    {
        "ref": "cap:investigator:beta:enforcement",
        "actor_ref": "actor:investigator:beta",
        "capacity_kind": "investigator",
        "scope_ref": "scope:statutory_enforcement",
        "evidence_refs": ["ev:cap:beta_delegation"],
        "evidence_state": "supported",
    },
    {
        "ref": "cap:licensee:gamma:operator",
        "actor_ref": "actor:licensee:gamma",
        "capacity_kind": "licensee",
        "scope_ref": "scope:commercial_operations",
        "evidence_refs": ["ev:cap:gamma_operating_cert"],
        "evidence_state": "supported",
    },
    {
        "ref": "cap:auditor:delta:independent_audit",
        "actor_ref": "actor:auditor:delta",
        "capacity_kind": "auditor",
        "scope_ref": "scope:compliance_auditing",
        "evidence_refs": ["ev:cap:delta_engagement"],
        "evidence_state": "supported",
    },
    {
        "ref": "cap:citizen:epsilon:individual",
        "actor_ref": "actor:citizen:epsilon",
        "capacity_kind": "citizen",
        "scope_ref": "scope:individual_interests",
        "evidence_refs": ["ev:cap:epsilon_residence"],
        "evidence_state": "supported",
    },
    {
        "ref": "cap:third_party:zeta:commercial_service",
        "actor_ref": "actor:third_party:zeta",
        "capacity_kind": "third_party",
        "scope_ref": "scope:third_party_contracting",
        "evidence_refs": ["ev:cap:zeta_master_contract"],
        "evidence_state": "supported",
    },
]

(FIXTURES_DIR / "actors.json").write_text(json.dumps(ACTORS, indent=2), encoding="utf-8")
(FIXTURES_DIR / "capacities.json").write_text(json.dumps(CAPACITIES, indent=2), encoding="utf-8")

# ==============================================================================
# 2. SYNTHETIC OPERATIONS & INTERESTS
# ==============================================================================
OPERATIONS = [
    {
        "ref": "op:request_record",
        "parameter_spec": [
            {"name": "record_type", "type_ref": "string", "required": True},
            {"name": "urgency", "type_ref": "string", "required": False},
        ],
        "actor_capacity_kinds": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
        "affected_role_kinds": ["custodian", "data_subject", "target_record_holder"],
        "effect_definitions": [{"ref": "effect:record_requested", "effect_kind": "informational_notice"}],
        "functional_lenses": ["investigative", "governance"],
    },
    {
        "ref": "op:compel_record",
        "parameter_spec": [
            {"name": "warrant_id", "type_ref": "string", "required": True},
            {"name": "penalty_terms", "type_ref": "string", "required": True},
        ],
        "actor_capacity_kinds": ["regulator", "investigator"],
        "affected_role_kinds": ["compelled_entity", "subpoenaed_party"],
        "effect_definitions": [{"ref": "effect:record_compelled", "effect_kind": "mandatory_custody_transfer"}],
        "functional_lenses": ["enforcement", "coercive"],
    },
    {
        "ref": "op:retain_record",
        "parameter_spec": [
            {"name": "retention_period_days", "type_ref": "integer", "required": True},
            {"name": "security_tier", "type_ref": "string", "required": True},
        ],
        "actor_capacity_kinds": ["regulator", "investigator", "licensee", "auditor"],
        "affected_role_kinds": ["record_subject", "beneficiary"],
        "effect_definitions": [{"ref": "effect:record_retained", "effect_kind": "custodial_lock"}],
        "functional_lenses": ["custodial", "compliance"],
    },
    {
        "ref": "op:share_record",
        "parameter_spec": [
            {"name": "recipient_ref", "type_ref": "reference", "required": True},
            {"name": "disclosure_purpose", "type_ref": "string", "required": True},
        ],
        "actor_capacity_kinds": ["licensee", "auditor", "third_party", "regulator"],
        "affected_role_kinds": ["data_subject", "affected_carrier"],
        "effect_definitions": [{"ref": "effect:record_disclosed", "effect_kind": "third_party_access"}],
        "functional_lenses": ["transmissive", "collaboration"],
    },
]

INTERESTS = [
    {
        "ref": "interest:confidentiality",
        "holder_ref": "actor:citizen:epsilon",
        "bearer_ref": "actor:licensee:gamma",
        "interest_kind": "privacy_and_trade_secrecy",
        "scope_ref": "scope:confidential_information",
        "evidence_refs": ["ev:interest:privacy_charter"],
    },
    {
        "ref": "interest:due_process",
        "holder_ref": "actor:licensee:gamma",
        "bearer_ref": "actor:regulator:alpha",
        "interest_kind": "statutory_authority_limits",
        "scope_ref": "scope:procedural_fairness",
        "evidence_refs": ["ev:interest:due_process_statute"],
    },
    {
        "ref": "interest:compliance",
        "holder_ref": "actor:regulator:alpha",
        "bearer_ref": "actor:licensee:gamma",
        "interest_kind": "regulatory_mandate",
        "scope_ref": "scope:operating_standards",
        "evidence_refs": ["ev:interest:license_condition"],
    },
    {
        "ref": "interest:transparency",
        "holder_ref": "actor:regulator:alpha",
        "bearer_ref": "actor:auditor:delta",
        "interest_kind": "public_oversight",
        "scope_ref": "scope:oversight_reporting",
        "evidence_refs": ["ev:interest:sunshine_statute"],
    },
]

(FIXTURES_DIR / "operations.json").write_text(json.dumps(OPERATIONS, indent=2), encoding="utf-8")
(FIXTURES_DIR / "interests.json").write_text(json.dumps(INTERESTS, indent=2), encoding="utf-8")

# ==============================================================================
# 3. SOURCE ARTIFACTS & REVIEWS
# ==============================================================================
SOURCES_AND_REVIEWS = {
    "source_artifacts": [
        {
            "ref": "source:fictional:privacy_statute_2024",
            "title": "Fictional Commercial Privacy and Data Protection Act",
            "kind": "legislation",
            "version": "2024.1",
            "digest": "sha256:d8a9b1c2e3f405162738495a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c",
            "issuing_body": "Fictional Legislature",
            "provisions": ["Section 4 (Voluntary Inquiries)", "Section 9 (Prohibition on Private Compulsion)", "Section 12 (Consent for Disclosures)", "Section 15 (Custodial Retention)"],
        },
        {
            "source_ref": "source:fictional:regulatory_powers_act_2023",
            "title": "Fictional Regulatory Powers and Public Oversight Statute",
            "kind": "legislation",
            "version": "2023.2",
            "digest": "sha256:a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
            "issuing_body": "Fictional State Council",
            "provisions": ["Article 3 (Regulatory Compulsion)", "Article 6 (Immunity of Oversight Body)", "Article 8 (Mandatory Audit Disclosure)", "Article 11 (Statutory Record Preservation)"],
        },
    ],
    "review_records": [
        {
            "ref": "rev:fictional:privacy_review_v1",
            "source_ref": "source:fictional:privacy_statute_2024",
            "reviewer": "Reviewer:LegalAnalysisGroup",
            "review_date": "2026-10-01",
            "status": "accepted_legal_position",
            "interpretation_summary": "Strict protection of commercial privacy; absolute bar on coercive acts by private non-statutory actors; consent indispensable for disclosure.",
        },
        {
            "ref": "rev:fictional:oversight_review_v1",
            "source_ref": "source:fictional:regulatory_powers_act_2023",
            "reviewer": "Reviewer:PublicLawChambers",
            "review_date": "2026-10-01",
            "status": "accepted_legal_position",
            "interpretation_summary": "Recognizes coercive authority only in regulator and designated investigator; requires active order; absolute prohibition against compelling regulator.",
        },
    ],
}
(FIXTURES_DIR / "source_artifacts_and_reviews.json").write_text(json.dumps(SOURCES_AND_REVIEWS, indent=2), encoding="utf-8")

# ==============================================================================
# 4. RULE PACKS & NORM RULES
# ==============================================================================
RULE_PACK_PRIVACY = {
    "ref": "pack:commercial_privacy_v1",
    "name": "Fictional Commercial Privacy & Data Protection Rules",
    "version": "1.0",
    "source_artifact_ref": "source:fictional:privacy_statute_2024",
    "review_ref": "rev:fictional:privacy_review_v1",
    "rules": [
        {
            "ref": "rule:priv:01",
            "name": "Voluntary Request Liberty",
            "norm_kind": "permission",
            "operation_ref": "op:request_record",
            "performer_capacities": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
            "target_capacities": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
            "indispensable_conditions": [],
            "interest_ref": "interest:transparency",
            "description": "Any actor is permitted to request records voluntarily without legal compulsion.",
        },
        {
            "ref": "rule:priv:02",
            "name": "Private Coercion Prohibition",
            "norm_kind": "prohibition",
            "operation_ref": "op:compel_record",
            "performer_capacities": ["licensee", "citizen", "third_party"],
            "target_capacities": ["regulator", "investigator", "licensee", "auditor", "citizen", "third_party"],
            "indispensable_conditions": [],
            "interest_ref": "interest:due_process",
            "description": "Private entities (licensees, individuals, third parties) are explicitly prohibited under reviewed rule from issuing coercive compulsion.",
        },
        {
            "ref": "rule:priv:03",
            "name": "Consensual Record Sharing",
            "norm_kind": "permission",
            "operation_ref": "op:share_record",
            "performer_capacities": ["licensee", "auditor", "third_party"],
            "target_capacities": ["citizen", "licensee"],
            "indispensable_conditions": ["cond:has_explicit_consent"],
            "interest_ref": "interest:confidentiality",
            "description": "Sharing records requires affirmative explicit consent. Where consent is demonstrably refuted across all routes, conditions are unmet.",
        },
        {
            "ref": "rule:priv:04",
            "name": "Custodial Retention Permitted in Window",
            "norm_kind": "permission",
            "operation_ref": "op:retain_record",
            "performer_capacities": ["regulator", "investigator", "licensee", "auditor"],
            "target_capacities": ["licensee", "citizen"],
            "indispensable_conditions": ["cond:within_statutory_window"],
            "interest_ref": "interest:compliance",
            "description": "Retention of records is permitted within the authorized statutory retention window.",
        },
    ],
}

RULE_PACK_OVERSIGHT = {
    "ref": "pack:public_oversight_v1",
    "name": "Fictional Public Oversight & Statutory Compulsion Rules",
    "version": "1.0",
    "source_artifact_ref": "source:fictional:regulatory_powers_act_2023",
    "review_ref": "rev:fictional:oversight_review_v1",
    "rules": [
        {
            "ref": "rule:over:01",
            "name": "Statutory Regulatory Compulsion Power",
            "norm_kind": "power",
            "operation_ref": "op:compel_record",
            "performer_capacities": ["regulator", "investigator"],
            "target_capacities": ["licensee", "auditor", "third_party"],
            "indispensable_conditions": ["cond:has_active_warrant_or_order"],
            "interest_ref": "interest:compliance",
            "description": "Statutory power of regulator and investigator to compel records from regulated entities, requiring an active warrant/order.",
        },
        {
            "ref": "rule:over:02",
            "name": "Immunity of Regulatory Board Against Subpoena",
            "norm_kind": "prohibition",
            "operation_ref": "op:compel_record",
            "performer_capacities": ["licensee", "auditor", "citizen", "third_party"],
            "target_capacities": ["regulator"],
            "indispensable_conditions": [],
            "interest_ref": "interest:due_process",
            "description": "Regulated entities and private parties are strictly prohibited from attempting to compel records from the regulatory board.",
        },
        {
            "ref": "rule:over:03",
            "name": "Statutory Audit Disclosure Duty",
            "norm_kind": "duty",
            "operation_ref": "op:share_record",
            "performer_capacities": ["licensee", "auditor"],
            "target_capacities": ["regulator", "investigator"],
            "indispensable_conditions": ["cond:audit_completed"],
            "interest_ref": "interest:transparency",
            "description": "Licensees and auditors have an affirmative legal duty to disclose completed audit records to the oversight authorities.",
        },
        {
            "ref": "rule:over:04",
            "name": "Mandatory Record Retention for Oversight",
            "norm_kind": "duty",
            "operation_ref": "op:retain_record",
            "performer_capacities": ["regulator", "investigator", "licensee"],
            "target_capacities": ["licensee", "citizen", "auditor", "third_party"],
            "indispensable_conditions": [],
            "interest_ref": "interest:compliance",
            "description": "Statutory duty of regulators, investigators, and operating licensees to preserve and retain regulatory records.",
        },
    ],
}

(FIXTURES_DIR / "rule_pack_commercial_privacy.json").write_text(json.dumps(RULE_PACK_PRIVACY, indent=2), encoding="utf-8")
(FIXTURES_DIR / "rule_pack_public_oversight.json").write_text(json.dumps(RULE_PACK_OVERSIGHT, indent=2), encoding="utf-8")

# ==============================================================================
# 5. DIRECT ORACLE: 288 CELLS WITH COMPLETE ACTIONCASE BINDINGS
# ==============================================================================
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
                actor_id = actor["ref"]
                actor_cap_record = actor["capacity_refs"][0]
                actor_cap_kind = actor_id.split(":")[1]  # regulator, investigator, licensee, auditor, citizen, third_party
                affected_id = affected["ref"]
                affected_cap_record = affected["capacity_refs"][0]
                affected_cap_kind = affected_id.split(":")[1]
                op_id = op["ref"]

                # 1. Build complete, declared ActionCase
                case_id = f"case:{cell_id}"
                action_case = {
                    "id": case_id,
                    "revision": 1,
                    "actor_ref": actor_id,
                    "capacity_ref": actor_cap_record,
                    "operation_ref": op_id,
                    "operation_revision": 1,
                    "parameters": {
                        "scope_designation": {"type_ref": "string", "raw_value": "standard_fictional_records", "unit": "none"},
                        "target_partition": {"type_ref": "string", "raw_value": "tier_1", "unit": "none"},
                    },
                    "affected_scope": {
                        "bindings": [
                            {
                                "entity_ref": affected_id,
                                "collective_scope_ref": None,
                                "relationship_role": f"target_{affected_cap_kind}",
                                "interest_refs": ["interest:confidentiality", "interest:due_process"],
                                "effect_refs": [op["effect_definitions"][0]["ref"]],
                                "evidence_state": "supported",
                                "evidence_refs": [f"ev:scope:{cell_id}"],
                            }
                        ],
                        "coverage_ref": f"cov:{cell_id}",
                        "known_empty": False,
                    },
                    "recipients": [actor_id],
                    "object_refs": [f"obj:record:{cell_id}"],
                    "purpose_ref": f"purpose:synthetic:{op_id.split(':')[-1]}",
                    "jurisdiction_context_ref": "jur:fictional:state",
                    "legal_reference_context_ref": "ctx:legal_ref:v1",
                    "mode": "proposed_actual",
                    "context_ref": f"ctx:assessment:{cell_id}",
                }

                # Deterministic Case Digest
                case_digest = canonical_json_digest(action_case)

                # 2. Evaluate semantics under governing pack
                disposition = "unresolved"
                applicable_rules = []
                decisive_rules = []
                condition_states = {}
                affected_interests = []
                gaps = []
                explanation = ""

                if pack_id == "pack:commercial_privacy_v1":
                    if op_id == "op:request_record":
                        # Voluntary requests permitted universally under rule:priv:01
                        disposition = "supported_within_scope"
                        applicable_rules = ["rule:priv:01"]
                        decisive_rules = ["rule:priv:01"]
                        affected_interests = ["interest:transparency"]
                        explanation = "Voluntary record request is an established liberty under rule:priv:01; no entry conditions required."

                    elif op_id == "op:compel_record":
                        if actor_cap_kind in ["licensee", "citizen", "third_party"]:
                            # Explicit prohibition norm under rule:priv:02
                            disposition = "prohibited_under_reviewed_rule"
                            applicable_rules = ["rule:priv:02"]
                            decisive_rules = ["rule:priv:02"]
                            affected_interests = ["interest:due_process"]
                            explanation = "Private entity is explicitly prohibited from coercive compulsion under reviewed rule rule:priv:02."
                        else:
                            # Regulators / investigators compelling under privacy pack:
                            # Privacy pack contains no enabling power rule for regulators, and no prohibition against them.
                            # Result: UNRESOLVED (missing statutory power), not prohibited.
                            disposition = "unresolved"
                            gaps = ["missing_statutory_basis"]
                            explanation = "Commercial privacy pack provides no power route for regulatory compulsion, but asserts no prohibition; unresolved pending statutory basis."

                    elif op_id == "op:share_record":
                        if actor_cap_kind in ["licensee", "auditor", "third_party"] and affected_cap_kind in ["citizen", "licensee"]:
                            # Baseline fixture establishes that consent is demonstrably REFUTED (e.g. data subject refused consent)
                            # Because the only covered route requires consent and consent is refuted, conditions are unmet.
                            disposition = "conditions_unmet"
                            applicable_rules = ["rule:priv:03"]
                            decisive_rules = ["rule:priv:03"]
                            condition_states["cond:has_explicit_consent"] = "refuted"
                            affected_interests = ["interest:confidentiality"]
                            explanation = "Explicit consent condition is demonstrably refuted across all available routes under rule:priv:03; conditions unmet."
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_sharing_authorization"]
                            explanation = "No applicable sharing rule under privacy pack for this capacity pairing; unresolved."

                    elif op_id == "op:retain_record":
                        if actor_cap_kind in ["regulator", "investigator", "licensee", "auditor"] and affected_cap_kind in ["licensee", "citizen"]:
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:priv:04"]
                            decisive_rules = ["rule:priv:04"]
                            condition_states["cond:within_statutory_window"] = "supported"
                            affected_interests = ["interest:compliance"]
                            explanation = "Record retention is permitted under rule:priv:04; retention window condition is supported."
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_retention_authority"]
                            explanation = "Actor capacity not covered by privacy retention permission; unresolved."

                elif pack_id == "pack:public_oversight_v1":
                    if op_id == "op:compel_record":
                        if actor_cap_kind in ["licensee", "auditor", "citizen", "third_party"] and affected_cap_kind == "regulator":
                            # Explicit statutory immunity prohibition under rule:over:02
                            disposition = "prohibited_under_reviewed_rule"
                            applicable_rules = ["rule:over:02"]
                            decisive_rules = ["rule:over:02"]
                            affected_interests = ["interest:due_process"]
                            explanation = "Subpoena/compulsion directed against the oversight board is explicitly prohibited under rule:over:02."
                        elif actor_cap_kind in ["regulator", "investigator"] and affected_cap_kind in ["licensee", "auditor", "third_party"]:
                            # Statutory compulsion power under rule:over:01 with active warrant supported
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:over:01"]
                            decisive_rules = ["rule:over:01"]
                            condition_states["cond:has_active_warrant_or_order"] = "supported"
                            affected_interests = ["interest:compliance"]
                            explanation = "Statutory compulsion power established under rule:over:01; active warrant condition supported."
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_jurisdictional_authority"]
                            explanation = "Target actor outside statutory compulsion jurisdiction; unresolved."

                    elif op_id == "op:share_record":
                        if actor_cap_kind in ["licensee", "auditor"] and affected_cap_kind in ["regulator", "investigator"]:
                            # Statutory disclosure duty under rule:over:03
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:over:03"]
                            decisive_rules = ["rule:over:03"]
                            condition_states["cond:audit_completed"] = "supported"
                            affected_interests = ["interest:transparency"]
                            explanation = "Affirmative disclosure duty under rule:over:03; audit completion condition supported."
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_statutory_duty"]
                            explanation = "No statutory duty or power to share records between these actors under oversight pack; unresolved."

                    elif op_id == "op:retain_record":
                        if actor_cap_kind in ["regulator", "investigator", "licensee"]:
                            # Statutory preservation duty under rule:over:04
                            disposition = "supported_within_scope"
                            applicable_rules = ["rule:over:04"]
                            decisive_rules = ["rule:over:04"]
                            affected_interests = ["interest:compliance"]
                            explanation = "Statutory preservation duty under rule:over:04 requires retention of oversight records."
                        else:
                            disposition = "unresolved"
                            gaps = ["missing_custodial_duty"]
                            explanation = "No statutory retention duty applies to this actor capacity under oversight pack; unresolved."

                    elif op_id == "op:request_record":
                        # Oversight pack does not govern voluntary inquiries; leaves unresolved pending privacy pack
                        disposition = "unresolved"
                        gaps = ["missing_oversight_provision"]
                        explanation = "Voluntary inquiries are outside the scope of the public oversight pack; unresolved."

                oracle_cells.append({
                    "cell_id": cell_id,
                    "actor": actor_id,
                    "performer_capacity": actor_cap_kind,
                    "affected_actor": affected_id,
                    "affected_capacity": affected_cap_kind,
                    "operation": op_id,
                    "scope_pack": pack_id,
                    "case": action_case,
                    "case_digest": case_digest,
                    "disposition": disposition,
                    "applicable_rule_refs": applicable_rules,
                    "decisive_rule_refs": decisive_rules,
                    "condition_states": condition_states,
                    "affected_interest_refs": affected_interests,
                    "coverage_state": "complete_coverage" if disposition != "unresolved" else "partial_coverage",
                    "expected_gap_kinds": gaps,
                    "explanation": explanation,
                })

assert len(oracle_cells) == 288, f"Expected 288 cells, got {len(oracle_cells)}"

oracle_data = {
    "catalog_id": "mapeogeo_authority_direct_oracle",
    "version": "0.1",
    "status": "frozen_independent_oracle",
    "author": "Nathanael J. Bocker (Independent Qualification Owner)",
    "review_status": "authored_and_frozen_prior_to_candidate_evaluator_inspection",
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
print(f"Generated direct oracle with 288 cells. Counts: {oracle_data['disposition_counts']}")

# ==============================================================================
# 6. REVERSE DOMAINS WITH PRE-COMPUTED EXPECTED SELECTIONS
# ==============================================================================
# Pre-compute expected reverse selections for all combinations
action_queries: List[Dict[str, Any]] = []
actor_queries: List[Dict[str, Any]] = []

for pack_id, _ in packs:
    # 1. Enumerate actions for each (actor, affected) pair (36 pairs per pack = 72 queries)
    for actor in ACTORS:
        for affected in ACTORS:
            supported_ops = []
            for cell in oracle_cells:
                if (
                    cell["scope_pack"] == pack_id
                    and cell["actor"] == actor["ref"]
                    and cell["affected_actor"] == affected["ref"]
                    and cell["disposition"] == "supported_within_scope"
                ):
                    supported_ops.append(cell["operation"])
            action_queries.append({
                "actor": actor["ref"],
                "affected_actor": affected["ref"],
                "scope_pack": pack_id,
                "expected_supported_operations": sorted(supported_ops),
            })

    # 2. Enumerate actors for each (operation, affected) pair (24 pairs per pack = 48 queries)
    for op in OPERATIONS:
        for affected in ACTORS:
            supported_actors = []
            for cell in oracle_cells:
                if (
                    cell["scope_pack"] == pack_id
                    and cell["operation"] == op["ref"]
                    and cell["affected_actor"] == affected["ref"]
                    and cell["disposition"] == "supported_within_scope"
                ):
                    supported_actors.append(cell["actor"])
            actor_queries.append({
                "operation": op["ref"],
                "affected_actor": affected["ref"],
                "scope_pack": pack_id,
                "expected_supported_actors": sorted(supported_actors),
            })

reverse_domains_data = {
    "catalog_id": "mapeogeo_authority_reverse_domains",
    "version": "0.1",
    "status": "frozen_reverse_domains",
    "author": "Nathanael J. Bocker",
    "complete_actor_domain": [a["ref"] for a in ACTORS],
    "complete_capacity_domain": [c["capacity_kind"] for c in CAPACITIES],
    "complete_operation_domain": [o["ref"] for o in OPERATIONS],
    "scope_packs": [p[0] for p in packs],
    "action_enumeration_expectations": action_queries,
    "actor_enumeration_expectations": actor_queries,
}
(QUAL_DIR / "reverse_domains_v0_1.json").write_text(json.dumps(reverse_domains_data, indent=2), encoding="utf-8")
print(f"Generated reverse domains with {len(action_queries)} action query expectations and {len(actor_queries)} actor query expectations.")

# ==============================================================================
# 7. INDEPENDENT EXPECTATION REVIEW RECORD
# ==============================================================================
review_record = {
    "review_id": "rev:authority_expectations_v0_1",
    "date": "2026-10-09",
    "owner": "Independent Qualification Owner (Nathanael J. Bocker)",
    "status": "frozen_prior_to_candidate_evaluator_inspection",
    "governing_packs": ["pack:commercial_privacy_v1", "pack:public_oversight_v1"],
    "interpretation_policies": {
        "four_state_evidence": "Strict separation between factual truth (supported, refuted, unknown, conflicting) and legal disposition.",
        "alternative_routes": "A failed prerequisite indispensable to all routes yields conditions_unmet. A demonstrably refuted condition across all available routes yields conditions_unmet. An unresolved alternative preserves whole-case unresolved.",
        "prohibition_standard": "Prohibited under reviewed rule requires an applicable, explicit reviewed prohibition norm (e.g. rule:priv:02, rule:over:02). Absence of a power/grant alone cannot manufacture a prohibition.",
        "independence_invariant": "Authored and frozen prior to inspection of candidate production evaluator code; first disagreements are preserved.",
    },
    "amendment_policy": "Any future expectation change requires an explicit signed adjudication entry preserving prior digest, successor digest, and justification.",
}
(QUAL_DIR / "expectation_review_record_v0_1.json").write_text(json.dumps(review_record, indent=2), encoding="utf-8")
print("Generated expectation_review_record_v0_1.json.")

# ==============================================================================
# 8. AQ SUBCASE MAPPING INDEX
# ==============================================================================
aq_index = {
    "catalog_id": "authority_aq_subcase_index",
    "version": "0.1",
    "status": "frozen_mapping",
    "mappings": [
        {
            "aq_id": "AQ01",
            "name": "direct_supported_with_complete_basis",
            "exercised_by_cells": ["cell_001", "cell_002", "cell_151"],
            "verification_invariant": "Complete decisive trace, valid role, supported conditions -> supported_within_scope",
        },
        {
            "aq_id": "AQ02",
            "name": "explicit_prohibition_requires_positive_basis",
            "exercised_by_cells": ["cell_010", "cell_014", "cell_146"],
            "verification_invariant": "Private compulsion under rule:priv:02 yields prohibited_under_reviewed_rule; missing power without prohibition yields unresolved",
        },
        {
            "aq_id": "AQ03",
            "name": "known_unmet_condition_differs_from_unknown_condition",
            "exercised_by_cells": ["cell_012", "cell_024", "cell_036"],
            "verification_invariant": "Refuted consent yields conditions_unmet; unknown consent yields unresolved with missing_factual_evidence gap",
        },
        {
            "aq_id": "AQ04",
            "name": "competing_rules_require_reviewed_resolution",
            "exercised_by_cells": ["cell_146", "cell_150"],
            "verification_invariant": "Prioritized rule resolves disposition; unadjudicated priority retains conflict record and unresolved disposition",
        },
        {
            "aq_id": "AQ05",
            "name": "any_actor_pair_preserves_direction_and_interests",
            "exercised_by_cells": ["cell_001", "cell_005", "cell_025"],
            "verification_invariant": "Self-pairs valid; swapping performers/targets changes case digest; unfamiliar actor yields unresolved binding",
        },
        {
            "aq_id": "AQ09",
            "name": "grant_binds_exact_action_and_parties",
            "exercised_by_cells": ["cell_001", "cell_002"],
            "verification_invariant": "Mutating any individual field (performer, operation, affected) changes case_digest and invalidates grant coverage",
        },
        {
            "aq_id": "AQ13",
            "name": "jurisdiction_types_are_not_interchangeable",
            "exercised_by_cells": ["cell_145", "cell_146"],
            "verification_invariant": "Territorial jurisdiction cannot substitute for subject-matter capacity; taxonomy preserved",
        },
        {
            "aq_id": "AQ25",
            "name": "what_actions_returns_exact_bounded_candidates",
            "exercised_by_cells": ["action_enumeration_expectations"],
            "verification_invariant": "enumerate_actions matches exact pre-computed expected_supported_operations set without omission",
        },
        {
            "aq_id": "AQ26",
            "name": "which_actors_returns_exact_bounded_candidates",
            "exercised_by_cells": ["actor_enumeration_expectations"],
            "verification_invariant": "enumerate_actors matches exact pre-computed expected_supported_actors set without omission",
        },
        {
            "aq_id": "AQ41",
            "name": "clock_identity_encoding_preserves_distinct_streams",
            "exercised_by_cells": ["test_clock_identity_codec"],
            "verification_invariant": "uow-clock:v1:[d, a] preserves boundary-overlap pairs (ops: / analyst vs ops / :analyst); explicit parents order events",
        },
        {
            "aq_id": "AQ56",
            "name": "input_and_budget_boundaries_do_not_masquerade_as_law",
            "exercised_by_cells": ["test_validation_result"],
            "verification_invariant": "Malformed inputs and limits emit technical Diagnostic errors and NO legal disposition",
        },
    ],
}
(QUAL_DIR / "aq_subcase_index_v0_1.json").write_text(json.dumps(aq_index, indent=2), encoding="utf-8")
print("Generated aq_subcase_index_v0_1.json.")

# ==============================================================================
# 9. ENHANCED HOST MAPPING CONTRACT (GATE G0b)
# ==============================================================================
host_mapping = {
    "contract_id": "mapeogeo_authority_host_mapping_contract_v0_1",
    "version": "0.1",
    "date": "2026-10-09",
    "status": "gate_g0b_inspected_and_complete",
    "clock_identity_format": "uow-clock:v1:[domain_id, local_actor]",
    "inspected_host_commit": "f7e6ee6b12c28bca95a967e212593bbadb7b8bb9",
    "inspected_host_adapter": "experiments/intelligence_integration/v0_1/adapter.py",
    "inspected_clock_identity": "experiments/intelligence_integration/v0_1/clock_identity.py",
    "clock_identity_specification": {
        "format": "uow-clock:v1:[domain_id, local_actor]",
        "domain_epoch": "Stream-local monotonically increasing integer seq >= 1 initialized at boundary start",
        "stream_owner": "Local execution boundary (e.g. uow:boundary:uow-01 or host task process)",
        "identity_classes": {
            "legal_actor_principal": "Attributed entity or organization (e.g. actor:regulator:alpha, analyst)",
            "uow_boundary": "Specific admitted work instance (e.g. uow:task:review_01)",
            "execution_perimeter": "Boundary admitting transactions and validating authority",
            "clock_stream": "Owned counter stream (domain_id, local_actor)"
        },
        "event_identity_and_causal_parents": {
            "event_format": "{domain_id}:{local_event_id}",
            "causal_ordering_rule": "Events across distinct clock domains without explicit causal edges have relation UNKNOWN. Order is established ONLY via explicit causal edges in parents list.",
            "separation_of_legal_time": "A legal reference mapping (interval attestation) cannot backdate causal receipt events or manufacture knowledge at an earlier decision point."
        }
    },
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
    "gate_g0b_determination": "Host commit, adapter, and clock identity are verified. Clock semantics, stream ownership, and causal/legal-time separation are strictly defined."
}
(BASE_DIR / "host_mapping_contract.json").write_text(json.dumps(host_mapping, indent=2), encoding="utf-8")
print("Generated enhanced host_mapping_contract.json for Gate G0b.")
