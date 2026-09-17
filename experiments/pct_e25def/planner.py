from __future__ import annotations

from .atlas import run_e25d

PRIORITY_RANK = {
    "P0_CONFLICT_REMEDIATION": 0,
    "P1_EXECUTABLE_ADAPTER_READY": 1,
    "P2_EVIDENCE_SERIALIZATION_GAP": 2,
    "P3_CHAIN_OR_HOMOLOGY_MODEL_REQUIRED": 3,
    "P4_EXACT_MORPHISM_PROVENANCE_REQUIRED": 4,
    "P5_FORMALIZATION_OR_SCOPE_REQUIRED": 5,
    "NO_ACTION_NOT_APPLICABLE_OR_COMPLETE": 6,
}


def _record(component: dict, priority: str, why: str, gap: str | None, inputs: list[str], next_level: str | None) -> dict:
    return {
        "component_id": component["component_id"],
        "priority_class": priority,
        "priority_rank": PRIORITY_RANK[priority],
        "why_now": why,
        "blocking_gap": gap,
        "required_inputs": inputs,
        "expected_next_level": next_level,
        "semantic_promotion": False,
    }


def classify_next_action(component: dict) -> dict:
    closure = component["closure"]
    applicability = component["applicability_mask"]

    for level in ("C0", "C1"):
        if closure[level]["state"] in {"FAIL", "INVALID", "ERROR"}:
            return _record(
                component, "P0_CONFLICT_REMEDIATION",
                f"{level} contains a blocking identity/certificate conflict.",
                closure[level].get("reason"), ["corrected_identity_or_certificate_evidence"], level,
            )

    if applicability["C2"] and closure["C2"]["state"] != "PASS":
        if not component.get("formal_scope"):
            return _record(
                component, "P5_FORMALIZATION_OR_SCOPE_REQUIRED",
                "C2 cannot be defined without a declared formal scope.",
                closure["C2"].get("reason"), ["formal_scope", "formal_statement"], "C2",
            )
        reason = closure["C2"].get("reason", "")
        if "BINDING" in reason or "SERIAL" in reason:
            return _record(
                component, "P2_EVIDENCE_SERIALIZATION_GAP",
                "An executable result exists conceptually but its binding is insufficient for C2.",
                reason, ["bound_executable_evidence"], "C2",
            )
        return _record(
            component, "P1_EXECUTABLE_ADAPTER_READY",
            "Identity and certificate layers pass; the next unresolved applicable layer is executable C2.",
            reason or None, ["executable_contract_adapter", "sealed_test_domain"], "C2",
        )

    for level in ("C3", "C4"):
        if applicability[level] and closure[level]["state"] != "PASS":
            return _record(
                component, "P3_CHAIN_OR_HOMOLOGY_MODEL_REQUIRED",
                f"{level} is applicable but the required chain/homology model is not established.",
                closure[level].get("reason"), ["chain_complex", "chain_map", "homology_contract"], level,
            )

    if applicability["C5"] and closure["C5"]["state"] != "PASS":
        return _record(
            component, "P4_EXACT_MORPHISM_PROVENANCE_REQUIRED",
            "C0-C2 pass and C3/C4 are not applicable; exact correspondence/provenance is the next unresolved applicable layer.",
            closure["C5"].get("reason"),
            ["exact_morphism_record", "provenance_binding", "exact_correspondence_contract"],
            "C5",
        )

    return _record(
        component, "NO_ACTION_NOT_APPLICABLE_OR_COMPLETE",
        "No unresolved applicable closure layer remains under the declared contract.",
        None, [], None,
    )


def run_e25e() -> dict:
    atlas = run_e25d()
    if atlas.get("status") != "PASS":
        return {
            "experiment_id": "E25E_VERIFICATION_UPGRADE_PLANNER",
            "status": "INVALID",
            "atlas_status": atlas.get("status"),
            "queue": [],
        }
    queue = [classify_next_action(c) for c in atlas["components"]]
    queue.sort(key=lambda x: (x["priority_rank"], x["component_id"]))
    return {
        "experiment_id": "E25E_VERIFICATION_UPGRADE_PLANNER",
        "status": "PASS",
        "source_experiment": atlas["experiment_id"],
        "queue": queue,
        "priority_histogram": {
            key: sum(item["priority_class"] == key for item in queue)
            for key in PRIORITY_RANK if any(item["priority_class"] == key for item in queue)
        },
        "claim_boundary": (
            "The planner schedules evidence work only. It never promotes MAPEOGEO semantic relations or converts lower-layer PASS into higher-layer PASS."
        ),
    }
