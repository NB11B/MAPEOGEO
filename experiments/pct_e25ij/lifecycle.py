from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from experiments.pct_e25ij.receipts import canonical_sha256, make_receipt

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_COMPONENT = "__GLOBAL_C5_POLICY__"


def _load(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build_baseline_ledger() -> dict[str, Any]:
    e25d = _load("evidence/pct_e25d_closure_atlas.json")
    e25g_a = _load("evidence/pct_e25g_exact_morphism_audit.json")
    e25g_b = _load("evidence/pct_e25g_provenance_bindings.json")
    e25h = _load("evidence/pct_e25h_policy_comparison.json")

    c5a_by_contract = {x["contract"]: x for x in e25g_a["components"]}
    c5b_by_component = {x["component_id"]: x for x in e25g_b["components"]}
    h_by_contract = {x["contract"]: x for x in e25h["contracts"]}

    receipts: list[dict[str, Any]] = []
    revision = 1
    policy_receipt = make_receipt(
        component_id=GLOBAL_COMPONENT,
        component_epoch=0,
        layer="C5",
        role="GLOBAL_C5_STRICT_POLICY",
        mathematical_verdict="PASS" if e25h["strict_policy_acceptable"] else "FAIL",
        content={
            "strict_policy_acceptable": e25h["strict_policy_acceptable"],
            "strict_metrics": e25h["policies"]["STRICT_AND"],
        },
        dependency_receipt_ids=[],
        source_statement_sha256="GLOBAL_C5_STRICT_POLICY",
        evidence_refs=["evidence/pct_e25h_policy_comparison.json"],
        predecessor_receipt_id=None,
        issuance_revision=revision,
    )
    receipts.append(policy_receipt)
    revision += 1

    components: list[dict[str, Any]] = []
    for source_component in sorted(e25d["components"], key=lambda x: x["component_id"]):
        component_id = source_component["component_id"]
        contract = source_component["contract"]
        c5a_evidence = c5a_by_contract[contract]
        c5b_evidence = c5b_by_component[component_id]
        policy_contract = h_by_contract[contract]
        source_hash = source_component["source_statement_sha256"]
        epoch = 0

        c0 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C0",
            role="C0_IDENTITY",
            mathematical_verdict=source_component["closure"]["C0"]["state"],
            content={
                "anchor_id": source_component["anchor_id"],
                "eo_id": source_component["eo_id"],
                "geo_id": source_component["geo_id"],
                "formal_id": source_component["formal_id"],
                "source_statement_sha256": source_hash,
            },
            dependency_receipt_ids=[],
            source_statement_sha256=source_hash,
            evidence_refs=list(source_component["closure"]["C0"]["evidence_refs"]),
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c1 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C1",
            role="C1_CERTIFICATE_BINDING",
            mathematical_verdict=source_component["closure"]["C1"]["state"],
            content={
                "certificate_ids": c5b_evidence["certificate_ids"],
                "formal_scope": c5b_evidence["formal_scope"],
            },
            dependency_receipt_ids=[c0["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=list(source_component["closure"]["C1"]["evidence_refs"]),
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c2 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C2",
            role="C2_EXECUTABLE_CONTRACT",
            mathematical_verdict=source_component["closure"]["C2"]["state"],
            content={
                "contract": contract,
                "exact_inputs": source_component["closure"]["C2"].get("exact_inputs"),
                "pairwise_path_equalities": source_component["closure"]["C2"].get("pairwise_path_equalities"),
            },
            dependency_receipt_ids=[c1["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=list(source_component["closure"]["C2"]["evidence_refs"]),
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c5a = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C5",
            role="C5A_EXACT_MORPHISM",
            mathematical_verdict="PASS" if c5a_evidence["all_routes_agree"] else "FAIL",
            content=c5a_evidence,
            dependency_receipt_ids=[c2["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=["evidence/pct_e25g_exact_morphism_audit.json"],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c5b = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C5",
            role="C5B_PROVENANCE_BINDING",
            mathematical_verdict=c5b_evidence["provenance_state"],
            content=c5b_evidence,
            dependency_receipt_ids=[c2["receipt_id"]],
            source_statement_sha256=source_hash,
            evidence_refs=["evidence/pct_e25g_provenance_bindings.json"],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        c5 = make_receipt(
            component_id=component_id,
            component_epoch=epoch,
            layer="C5",
            role="C5_ELIGIBILITY",
            mathematical_verdict="PASS" if policy_contract["strict_c5_eligible"] and e25h["strict_policy_acceptable"] else "FAIL",
            content={
                "contract": contract,
                "policy": "STRICT_AND",
                "c5a_state": policy_contract["c5a_valid_state"],
                "c5b_state": policy_contract["c5b_valid_state"],
            },
            dependency_receipt_ids=[
                c0["receipt_id"],
                c1["receipt_id"],
                c2["receipt_id"],
                c5a["receipt_id"],
                c5b["receipt_id"],
                policy_receipt["receipt_id"],
            ],
            source_statement_sha256=source_hash,
            evidence_refs=["evidence/pct_e25h_policy_comparison.json"],
            predecessor_receipt_id=None,
            issuance_revision=revision,
        )
        revision += 1
        receipts.extend([c0, c1, c2, c5a, c5b, c5])
        components.append(
            {
                "component_id": component_id,
                "contract": contract,
                "component_epoch": epoch,
                "provenance_class": source_component["provenance_class"],
                "source_statement_sha256": source_hash,
                "applicability_mask": deepcopy(source_component["applicability_mask"]),
                "applicability_reasons": {
                    "C3": source_component["closure"]["C3"].get("reason"),
                    "C4": source_component["closure"]["C4"].get("reason"),
                },
            }
        )

    return {
        "experiment_id": "E25I_CLOSURE_RECEIPT_LEDGER",
        "status": "PASS",
        "source_evidence": [
            "evidence/pct_e25d_real_component_manifest.json",
            "evidence/pct_e25d_closure_atlas.json",
            "evidence/pct_e25g_exact_morphism_audit.json",
            "evidence/pct_e25g_provenance_bindings.json",
            "evidence/pct_e25h_policy_comparison.json",
        ],
        "components": components,
        "receipts": receipts,
        "events": [],
        "claim_boundary": "Lifecycle receipts cover only the four frozen REAL_SOURCE_BOUND contracts and the frozen STRICT_AND policy result.",
    }


def apply_event_state(
    receipts: list[dict[str, Any]],
    events: list[dict[str, Any]],
    component_epochs: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Derive lifecycle authority without mutating immutable receipt payloads."""
    receipt_by_id = {r["receipt_id"]: r for r in receipts}
    epochs = dict(component_epochs or {})
    states = {r["receipt_id"]: "ACTIVE" for r in receipts}
    invalid_components: set[str] = set()

    for event in sorted(events, key=lambda e: (e["revision"], e["event_id"])):
        event_type = event["event_type"]
        target_id = event["target_receipt_id"]
        component_id = event["component_id"]

        if event_type in {"REVOKE", "DEPENDENCY_INVALIDATE", "SUPERSEDE", "IDENTITY_CONFLICT"} and target_id not in receipt_by_id:
            raise ValueError(f"event target receipt does not exist: {target_id}")

        if event_type == "REVOKE":
            states[target_id] = "REVOKED"
        elif event_type == "SUPERSEDE":
            states[target_id] = "SUPERSEDED"
            replacement_id = event.get("replacement_receipt_id")
            if replacement_id is not None and replacement_id not in receipt_by_id:
                raise ValueError(f"replacement receipt does not exist: {replacement_id}")
        elif event_type == "DEPENDENCY_INVALIDATE":
            states[target_id] = "INVALID"
        elif event_type == "IDENTITY_CONFLICT":
            states[target_id] = "INVALID"
            invalid_components.add(component_id)
        elif event_type == "IDENTITY_REBIND":
            new_epoch = event.get("new_component_epoch")
            if new_epoch is None:
                raise ValueError("IDENTITY_REBIND requires new_component_epoch")
            if component_id not in epochs:
                raise ValueError(f"unknown component for IDENTITY_REBIND: {component_id}")
            if new_epoch <= epochs[component_id]:
                raise ValueError("IDENTITY_REBIND must increase component_epoch")
            epochs[component_id] = new_epoch
            invalid_components.discard(component_id)
        elif event_type in {"ISSUE", "REVALIDATE"}:
            pass
        else:
            raise ValueError(f"unsupported lifecycle event type: {event_type}")

    changed = True
    while changed:
        changed = False
        for receipt in receipts:
            rid = receipt["receipt_id"]
            if states[rid] != "ACTIVE":
                continue
            component_id = receipt["component_id"]
            if component_id != GLOBAL_COMPONENT:
                current_epoch = epochs.get(component_id)
                if current_epoch is None or receipt["component_epoch"] != current_epoch:
                    states[rid] = "STALE"
                    changed = True
                    continue
            if any(dep_id not in receipt_by_id or states.get(dep_id) != "ACTIVE" for dep_id in receipt["dependency_receipt_ids"]):
                states[rid] = "STALE"
                changed = True

    return {
        "receipt_states": states,
        "component_epochs": epochs,
        "invalid_components": sorted(invalid_components),
    }


def _role_receipt(
    receipts: list[dict[str, Any]],
    states: dict[str, str],
    component_id: str,
    role: str,
) -> dict[str, Any] | None:
    candidates = [
        r
        for r in receipts
        if r["component_id"] == component_id and r["role"] == role and states.get(r["receipt_id"]) == "ACTIVE"
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: (r["issuance_revision"], r["receipt_id"]))


def replay_lifecycle(ledger: dict[str, Any], events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    receipts = ledger["receipts"]
    all_events = list(ledger.get("events", [])) + list(events or [])
    initial_epochs = {c["component_id"]: c["component_epoch"] for c in ledger["components"]}
    authority = apply_event_state(receipts, all_events, initial_epochs)
    states: dict[str, str] = authority["receipt_states"]
    component_epochs: dict[str, int] = authority["component_epochs"]
    invalid_components = set(authority["invalid_components"])
    components_out: list[dict[str, Any]] = []

    for metadata in sorted(ledger["components"], key=lambda x: x["component_id"]):
        component_id = metadata["component_id"]
        is_invalid = component_id in invalid_components
        closure: dict[str, dict[str, Any]] = {}
        role_for_layer = {
            "C0": "C0_IDENTITY",
            "C1": "C1_CERTIFICATE_BINDING",
            "C2": "C2_EXECUTABLE_CONTRACT",
        }
        for layer, role in role_for_layer.items():
            receipt = _role_receipt(receipts, states, component_id, role)
            if is_invalid and layer == "C0":
                closure[layer] = {"state": "INVALID", "receipt_id": None}
            else:
                closure[layer] = {
                    "state": "PASS" if receipt and receipt["mathematical_verdict"] == "PASS" else "NOT_ESTABLISHED",
                    "receipt_id": receipt["receipt_id"] if receipt else None,
                }

        for layer in ("C3", "C4"):
            if metadata["applicability_mask"].get(layer) is False:
                closure[layer] = {
                    "state": "NOT_APPLICABLE",
                    "reason": metadata["applicability_reasons"].get(layer),
                }
            else:
                closure[layer] = {"state": "NOT_ESTABLISHED"}

        c5 = _role_receipt(receipts, states, component_id, "C5_ELIGIBILITY")
        closure["C5"] = {
            "state": "PASS" if (not is_invalid and c5 and c5["mathematical_verdict"] == "PASS") else "NOT_ESTABLISHED",
            "receipt_id": c5["receipt_id"] if (not is_invalid and c5) else None,
        }

        frontier = None
        if not is_invalid:
            for layer in ("C5", "C4", "C3", "C2", "C1", "C0"):
                if closure[layer]["state"] == "PASS":
                    frontier = layer
                    break

        component_receipts = [r for r in receipts if r["component_id"] == component_id]
        base = {
            "component_id": component_id,
            "contract": metadata["contract"],
            "component_epoch": component_epochs[component_id],
            "component_state": "INVALID" if is_invalid else "VALID",
            "closure": closure,
            "effective_frontier": frontier,
            "authoritative_receipt_ids": sorted(r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "ACTIVE"),
            "stale_receipt_ids": sorted(r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "STALE"),
            "revoked_receipt_ids": sorted(r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "REVOKED"),
            "superseded_receipt_ids": sorted(r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "SUPERSEDED"),
            "invalid_receipt_ids": sorted(r["receipt_id"] for r in component_receipts if states[r["receipt_id"]] == "INVALID"),
        }
        base["state_digest"] = canonical_sha256(base)
        components_out.append(base)

    histogram: dict[str, int] = {}
    for component in components_out:
        key = component["effective_frontier"] or "NONE"
        histogram[key] = histogram.get(key, 0) + 1

    snapshot: dict[str, Any] = {
        "experiment_id": "E25I_DERIVED_CLOSURE_SNAPSHOT",
        "status": "PASS",
        "component_count": len(components_out),
        "components": components_out,
        "frontier_histogram": histogram,
        "event_ids": [e["event_id"] for e in sorted(all_events, key=lambda e: (e["revision"], e["event_id"]))],
    }
    snapshot["state_digest"] = canonical_sha256(snapshot)
    return snapshot


def run_e25i_audit() -> dict[str, Any]:
    ledger = build_baseline_ledger()
    pre_ledger = deepcopy(ledger)
    pre_ledger["receipts"] = [
        r for r in pre_ledger["receipts"] if r["role"] in {"C0_IDENTITY", "C1_CERTIFICATE_BINDING", "C2_EXECUTABLE_CONTRACT"}
    ]
    pre = replay_lifecycle(pre_ledger)
    post = replay_lifecycle(ledger)
    e25d = _load("evidence/pct_e25d_closure_atlas.json")
    e25d_by_component = {x["component_id"]: x for x in e25d["components"]}

    reconstructed = True
    component_pairs: list[dict[str, Any]] = []
    for post_component in post["components"]:
        component_id = post_component["component_id"]
        pre_component = next(x for x in pre["components"] if x["component_id"] == component_id)
        historical = e25d_by_component[component_id]
        reconstructed = reconstructed and pre_component["effective_frontier"] == historical["closure_frontier"]
        for layer in ("C0", "C1", "C2", "C3", "C4"):
            reconstructed = reconstructed and pre_component["closure"][layer]["state"] == historical["closure"][layer]["state"]
        component_pairs.append({"component_id": component_id, "pre_c5": pre_component, "post_c5": post_component})

    all_c5 = all(x["post_c5"]["effective_frontier"] == "C5" for x in component_pairs)
    synthetic_count = sum(1 for x in ledger["components"] if x["provenance_class"] != "REAL_SOURCE_BOUND")
    status = "PASS" if reconstructed and all_c5 and synthetic_count == 0 else "FAIL"
    return {
        "experiment_id": "E25I_CLOSURE_PROMOTION_STATE_MACHINE",
        "status": status,
        "real_component_count": len(ledger["components"]),
        "synthetic_components_counted_as_real": synthetic_count,
        "pre_c5_frontier_histogram": pre["frontier_histogram"],
        "post_c5_frontier_histogram": post["frontier_histogram"],
        "e25d_reconstructed_exactly": reconstructed,
        "components": component_pairs,
        "ledger": ledger,
        "snapshot": post,
        "claim_boundary": "E25I derives lifecycle closure only for the four frozen REAL_SOURCE_BOUND contracts; it does not mutate repository semantics.",
    }
