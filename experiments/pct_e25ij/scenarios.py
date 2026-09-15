from __future__ import annotations

from copy import deepcopy
from typing import Any

from experiments.pct_e25ij.lifecycle import GLOBAL_COMPONENT, build_baseline_ledger, replay_lifecycle
from experiments.pct_e25ij.receipts import make_event, make_receipt


def _receipt(ledger: dict[str, Any], component_id: str, role: str) -> dict[str, Any]:
    candidates = [r for r in ledger["receipts"] if r["component_id"] == component_id and r["role"] == role]
    return max(candidates, key=lambda r: (r["issuance_revision"], r["receipt_id"]))


def _component(snapshot: dict[str, Any], component_id: str) -> dict[str, Any]:
    return next(c for c in snapshot["components"] if c["component_id"] == component_id)


def _summary(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "component_state": component["component_state"],
        "component_epoch": component["component_epoch"],
        "effective_frontier": component["effective_frontier"],
        "state_digest": component["state_digest"],
        "authoritative_receipt_count": len(component["authoritative_receipt_ids"]),
        "stale_receipt_count": len(component["stale_receipt_ids"]),
        "revoked_receipt_count": len(component["revoked_receipt_ids"]),
        "superseded_receipt_count": len(component["superseded_receipt_ids"]),
        "invalid_receipt_count": len(component["invalid_receipt_ids"]),
    }


def _replacement(
    old: dict[str, Any],
    *,
    revision: int,
    marker: str,
    dependencies: list[str] | None = None,
    epoch: int | None = None,
    source_hash: str | None = None,
) -> dict[str, Any]:
    return make_receipt(
        component_id=old["component_id"],
        component_epoch=old["component_epoch"] if epoch is None else epoch,
        layer=old["layer"],
        role=old["role"],
        mathematical_verdict="PASS",
        content={"synthetic_revalidation": marker, "role": old["role"]},
        dependency_receipt_ids=list(old["dependency_receipt_ids"] if dependencies is None else dependencies),
        source_statement_sha256=old["source_statement_sha256"] if source_hash is None else source_hash,
        evidence_refs=[f"synthetic:{marker}"],
        predecessor_receipt_id=old["receipt_id"],
        issuance_revision=revision,
    )


def _eligibility(
    old: dict[str, Any],
    *,
    revision: int,
    dependencies: list[str],
    marker: str,
    epoch: int | None = None,
) -> dict[str, Any]:
    return make_receipt(
        component_id=old["component_id"],
        component_epoch=old["component_epoch"] if epoch is None else epoch,
        layer="C5",
        role="C5_ELIGIBILITY",
        mathematical_verdict="PASS",
        content={"policy": "STRICT_AND", "synthetic_revalidation": marker},
        dependency_receipt_ids=list(dependencies),
        source_statement_sha256=old["source_statement_sha256"],
        evidence_refs=[f"synthetic:{marker}"],
        predecessor_receipt_id=old["receipt_id"],
        issuance_revision=revision,
    )


def _single_component_record(
    *,
    scenario_type: str,
    component_id: str,
    downgrade_ledger: dict[str, Any],
    downgrade_events: list[dict[str, Any]],
    recovery_ledger: dict[str, Any],
    recovery_events: list[dict[str, Any]],
    expected_frontier: str | None,
    old_downstream_ids: list[str],
    new_receipt_ids: list[str],
) -> dict[str, Any]:
    downgrade_snapshot = replay_lifecycle(downgrade_ledger, downgrade_events)
    downgrade_replay = replay_lifecycle(downgrade_ledger, downgrade_events)
    recovery_snapshot = replay_lifecycle(recovery_ledger, recovery_events)
    recovery_replay = replay_lifecycle(recovery_ledger, recovery_events)
    down = _component(downgrade_snapshot, component_id)
    recovered = _component(recovery_snapshot, component_id)
    old_reactivated = any(rid in recovered["authoritative_receipt_ids"] for rid in old_downstream_ids)
    new_ids_distinct = not set(new_receipt_ids).intersection(old_downstream_ids) and len(new_receipt_ids) == len(set(new_receipt_ids))
    deterministic = (
        downgrade_snapshot["state_digest"] == downgrade_replay["state_digest"]
        and recovery_snapshot["state_digest"] == recovery_replay["state_digest"]
    )
    passed = (
        down["effective_frontier"] == expected_frontier
        and recovered["effective_frontier"] == "C5"
        and not old_reactivated
        and new_ids_distinct
        and deterministic
    )
    return {
        "scenario_id": f"{scenario_type}:{component_id}",
        "scenario_type": scenario_type,
        "provenance_class": "SYNTHETIC_CONTROL",
        "target_component_ids": [component_id],
        "expected_frontier": expected_frontier,
        "observed_frontier": down["effective_frontier"],
        "recovered_frontier": recovered["effective_frontier"],
        "downgrade": _summary(down),
        "recovery": _summary(recovered),
        "downgrade_event_ids": [e["event_id"] for e in downgrade_events],
        "recovery_event_ids": [e["event_id"] for e in recovery_events],
        "old_downstream_receipt_ids": sorted(old_downstream_ids),
        "new_receipt_ids": sorted(new_receipt_ids),
        "old_downstream_receipts_reactivated": old_reactivated,
        "replacement_receipt_ids_distinct": new_ids_distinct,
        "replay_deterministic": deterministic,
        "status": "PASS" if passed else "FAIL",
    }


def _component_scenarios(component_id: str, ordinal: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    base_revision = 1000 + ordinal * 100

    # J1: exact-morphism receipt superseded; replacement alone cannot revive old eligibility.
    ledger = build_baseline_ledger()
    old_c0 = _receipt(ledger, component_id, "C0_IDENTITY")
    old_c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
    old_c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
    old_c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    old_c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    old_elig = _receipt(ledger, component_id, "C5_ELIGIBILITY")
    policy = _receipt(ledger, GLOBAL_COMPONENT, "GLOBAL_C5_STRICT_POLICY")
    new_c5a = _replacement(old_c5a, revision=base_revision + 1, marker=f"J1:{component_id}")
    downgrade = deepcopy(ledger)
    downgrade["receipts"].append(new_c5a)
    j1_event = make_event(
        revision=base_revision + 2,
        event_type="SUPERSEDE",
        target_receipt_id=old_c5a["receipt_id"],
        component_id=component_id,
        reason_code="J1_C5A_REPLACED",
        replacement_receipt_id=new_c5a["receipt_id"],
    )
    recovery = deepcopy(downgrade)
    new_elig = _eligibility(
        old_elig,
        revision=base_revision + 3,
        marker=f"J1_ELIG:{component_id}",
        dependencies=[
            old_c0["receipt_id"], old_c1["receipt_id"], old_c2["receipt_id"],
            new_c5a["receipt_id"], old_c5b["receipt_id"], policy["receipt_id"],
        ],
    )
    recovery["receipts"].append(new_elig)
    out.append(_single_component_record(
        scenario_type="J1_C5A_SUPERSEDED",
        component_id=component_id,
        downgrade_ledger=downgrade,
        downgrade_events=[j1_event],
        recovery_ledger=recovery,
        recovery_events=[j1_event],
        expected_frontier="C2",
        old_downstream_ids=[old_elig["receipt_id"]],
        new_receipt_ids=[new_c5a["receipt_id"], new_elig["receipt_id"]],
    ))

    # J2: provenance receipt revoked; recovery requires new C5b and new eligibility.
    ledger = build_baseline_ledger()
    old_c0 = _receipt(ledger, component_id, "C0_IDENTITY")
    old_c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
    old_c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
    old_c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    old_c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    old_elig = _receipt(ledger, component_id, "C5_ELIGIBILITY")
    policy = _receipt(ledger, GLOBAL_COMPONENT, "GLOBAL_C5_STRICT_POLICY")
    j2_event = make_event(
        revision=base_revision + 10,
        event_type="REVOKE",
        target_receipt_id=old_c5b["receipt_id"],
        component_id=component_id,
        reason_code="J2_C5B_REVOKED",
    )
    downgrade = deepcopy(ledger)
    recovery = deepcopy(ledger)
    new_c5b = _replacement(old_c5b, revision=base_revision + 11, marker=f"J2:{component_id}")
    new_elig = _eligibility(
        old_elig,
        revision=base_revision + 12,
        marker=f"J2_ELIG:{component_id}",
        dependencies=[
            old_c0["receipt_id"], old_c1["receipt_id"], old_c2["receipt_id"],
            old_c5a["receipt_id"], new_c5b["receipt_id"], policy["receipt_id"],
        ],
    )
    recovery["receipts"].extend([new_c5b, new_elig])
    out.append(_single_component_record(
        scenario_type="J2_C5B_REVOKED",
        component_id=component_id,
        downgrade_ledger=downgrade,
        downgrade_events=[j2_event],
        recovery_ledger=recovery,
        recovery_events=[j2_event],
        expected_frontier="C2",
        old_downstream_ids=[old_elig["receipt_id"]],
        new_receipt_ids=[new_c5b["receipt_id"], new_elig["receipt_id"]],
    ))

    # J3: executable receipt superseded; both C5 axes and eligibility must be reissued.
    ledger = build_baseline_ledger()
    old_c0 = _receipt(ledger, component_id, "C0_IDENTITY")
    old_c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
    old_c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
    old_c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    old_c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    old_elig = _receipt(ledger, component_id, "C5_ELIGIBILITY")
    policy = _receipt(ledger, GLOBAL_COMPONENT, "GLOBAL_C5_STRICT_POLICY")
    j3_event = make_event(
        revision=base_revision + 20,
        event_type="SUPERSEDE",
        target_receipt_id=old_c2["receipt_id"],
        component_id=component_id,
        reason_code="J3_C2_REPLACED",
    )
    downgrade = deepcopy(ledger)
    recovery = deepcopy(ledger)
    new_c2 = _replacement(old_c2, revision=base_revision + 21, marker=f"J3_C2:{component_id}")
    new_c5a = _replacement(old_c5a, revision=base_revision + 22, marker=f"J3_C5A:{component_id}", dependencies=[new_c2["receipt_id"]])
    new_c5b = _replacement(old_c5b, revision=base_revision + 23, marker=f"J3_C5B:{component_id}", dependencies=[new_c2["receipt_id"]])
    new_elig = _eligibility(
        old_elig,
        revision=base_revision + 24,
        marker=f"J3_ELIG:{component_id}",
        dependencies=[
            old_c0["receipt_id"], old_c1["receipt_id"], new_c2["receipt_id"],
            new_c5a["receipt_id"], new_c5b["receipt_id"], policy["receipt_id"],
        ],
    )
    recovery["receipts"].extend([new_c2, new_c5a, new_c5b, new_elig])
    out.append(_single_component_record(
        scenario_type="J3_C2_SUPERSEDED",
        component_id=component_id,
        downgrade_ledger=downgrade,
        downgrade_events=[j3_event],
        recovery_ledger=recovery,
        recovery_events=[j3_event],
        expected_frontier="C1",
        old_downstream_ids=[old_c5a["receipt_id"], old_c5b["receipt_id"], old_elig["receipt_id"]],
        new_receipt_ids=[new_c2["receipt_id"], new_c5a["receipt_id"], new_c5b["receipt_id"], new_elig["receipt_id"]],
    ))

    # J4: certificate binding revoked; every downstream role must be reissued.
    ledger = build_baseline_ledger()
    old_c0 = _receipt(ledger, component_id, "C0_IDENTITY")
    old_c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
    old_c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
    old_c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    old_c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    old_elig = _receipt(ledger, component_id, "C5_ELIGIBILITY")
    policy = _receipt(ledger, GLOBAL_COMPONENT, "GLOBAL_C5_STRICT_POLICY")
    j4_event = make_event(
        revision=base_revision + 30,
        event_type="REVOKE",
        target_receipt_id=old_c1["receipt_id"],
        component_id=component_id,
        reason_code="J4_C1_REVOKED",
    )
    downgrade = deepcopy(ledger)
    recovery = deepcopy(ledger)
    new_c1 = _replacement(old_c1, revision=base_revision + 31, marker=f"J4_C1:{component_id}", dependencies=[old_c0["receipt_id"]])
    new_c2 = _replacement(old_c2, revision=base_revision + 32, marker=f"J4_C2:{component_id}", dependencies=[new_c1["receipt_id"]])
    new_c5a = _replacement(old_c5a, revision=base_revision + 33, marker=f"J4_C5A:{component_id}", dependencies=[new_c2["receipt_id"]])
    new_c5b = _replacement(old_c5b, revision=base_revision + 34, marker=f"J4_C5B:{component_id}", dependencies=[new_c2["receipt_id"]])
    new_elig = _eligibility(
        old_elig,
        revision=base_revision + 35,
        marker=f"J4_ELIG:{component_id}",
        dependencies=[
            old_c0["receipt_id"], new_c1["receipt_id"], new_c2["receipt_id"],
            new_c5a["receipt_id"], new_c5b["receipt_id"], policy["receipt_id"],
        ],
    )
    recovery["receipts"].extend([new_c1, new_c2, new_c5a, new_c5b, new_elig])
    out.append(_single_component_record(
        scenario_type="J4_C1_REVOKED",
        component_id=component_id,
        downgrade_ledger=downgrade,
        downgrade_events=[j4_event],
        recovery_ledger=recovery,
        recovery_events=[j4_event],
        expected_frontier="C0",
        old_downstream_ids=[old_c2["receipt_id"], old_c5a["receipt_id"], old_c5b["receipt_id"], old_elig["receipt_id"]],
        new_receipt_ids=[new_c1["receipt_id"], new_c2["receipt_id"], new_c5a["receipt_id"], new_c5b["receipt_id"], new_elig["receipt_id"]],
    ))

    # J5: identity conflict forces a new component epoch and complete downstream reissue.
    ledger = build_baseline_ledger()
    old_c0 = _receipt(ledger, component_id, "C0_IDENTITY")
    old_c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
    old_c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
    old_c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    old_c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    old_elig = _receipt(ledger, component_id, "C5_ELIGIBILITY")
    policy = _receipt(ledger, GLOBAL_COMPONENT, "GLOBAL_C5_STRICT_POLICY")
    conflict = make_event(
        revision=base_revision + 40,
        event_type="IDENTITY_CONFLICT",
        target_receipt_id=old_c0["receipt_id"],
        component_id=component_id,
        reason_code="J5_SOURCE_IDENTITY_CONFLICT",
    )
    downgrade = deepcopy(ledger)
    recovery = deepcopy(ledger)
    new_epoch = 1
    new_c0 = _replacement(old_c0, revision=base_revision + 41, marker=f"J5_C0:{component_id}", dependencies=[], epoch=new_epoch)
    new_c1 = _replacement(old_c1, revision=base_revision + 42, marker=f"J5_C1:{component_id}", dependencies=[new_c0["receipt_id"]], epoch=new_epoch)
    new_c2 = _replacement(old_c2, revision=base_revision + 43, marker=f"J5_C2:{component_id}", dependencies=[new_c1["receipt_id"]], epoch=new_epoch)
    new_c5a = _replacement(old_c5a, revision=base_revision + 44, marker=f"J5_C5A:{component_id}", dependencies=[new_c2["receipt_id"]], epoch=new_epoch)
    new_c5b = _replacement(old_c5b, revision=base_revision + 45, marker=f"J5_C5B:{component_id}", dependencies=[new_c2["receipt_id"]], epoch=new_epoch)
    new_elig = _eligibility(
        old_elig,
        revision=base_revision + 46,
        marker=f"J5_ELIG:{component_id}",
        epoch=new_epoch,
        dependencies=[
            new_c0["receipt_id"], new_c1["receipt_id"], new_c2["receipt_id"],
            new_c5a["receipt_id"], new_c5b["receipt_id"], policy["receipt_id"],
        ],
    )
    recovery["receipts"].extend([new_c0, new_c1, new_c2, new_c5a, new_c5b, new_elig])
    rebind = make_event(
        revision=base_revision + 47,
        event_type="IDENTITY_REBIND",
        target_receipt_id=old_c0["receipt_id"],
        component_id=component_id,
        reason_code="J5_IDENTITY_REBOUND",
        replacement_receipt_id=new_c0["receipt_id"],
        new_component_epoch=new_epoch,
    )
    out.append(_single_component_record(
        scenario_type="J5_IDENTITY_CONFLICT",
        component_id=component_id,
        downgrade_ledger=downgrade,
        downgrade_events=[conflict],
        recovery_ledger=recovery,
        recovery_events=[conflict, rebind],
        expected_frontier=None,
        old_downstream_ids=[old_c1["receipt_id"], old_c2["receipt_id"], old_c5a["receipt_id"], old_c5b["receipt_id"], old_elig["receipt_id"]],
        new_receipt_ids=[new_c0["receipt_id"], new_c1["receipt_id"], new_c2["receipt_id"], new_c5a["receipt_id"], new_c5b["receipt_id"], new_elig["receipt_id"]],
    ))

    return out


def _shared_policy_scenario() -> dict[str, Any]:
    ledger = build_baseline_ledger()
    old_policy = _receipt(ledger, GLOBAL_COMPONENT, "GLOBAL_C5_STRICT_POLICY")
    old_eligibilities = {
        c["component_id"]: _receipt(ledger, c["component_id"], "C5_ELIGIBILITY")
        for c in ledger["components"]
    }
    new_policy = _replacement(old_policy, revision=9001, marker="J6_STRICT_POLICY")
    downgrade = deepcopy(ledger)
    downgrade["receipts"].append(new_policy)
    event = make_event(
        revision=9002,
        event_type="SUPERSEDE",
        target_receipt_id=old_policy["receipt_id"],
        component_id=GLOBAL_COMPONENT,
        reason_code="J6_STRICT_POLICY_REPLACED",
        replacement_receipt_id=new_policy["receipt_id"],
    )
    down_snapshot = replay_lifecycle(downgrade, [event])
    down_replay = replay_lifecycle(downgrade, [event])

    recovery = deepcopy(downgrade)
    new_eligibility_ids: list[str] = []
    for index, metadata in enumerate(sorted(ledger["components"], key=lambda x: x["component_id"])):
        component_id = metadata["component_id"]
        c0 = _receipt(ledger, component_id, "C0_IDENTITY")
        c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
        c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
        c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
        c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
        old_elig = old_eligibilities[component_id]
        new_elig = _eligibility(
            old_elig,
            revision=9010 + index,
            marker=f"J6_ELIG:{component_id}",
            dependencies=[
                c0["receipt_id"], c1["receipt_id"], c2["receipt_id"],
                c5a["receipt_id"], c5b["receipt_id"], new_policy["receipt_id"],
            ],
        )
        recovery["receipts"].append(new_elig)
        new_eligibility_ids.append(new_elig["receipt_id"])

    recovery_snapshot = replay_lifecycle(recovery, [event])
    recovery_replay = replay_lifecycle(recovery, [event])
    old_ids = sorted(x["receipt_id"] for x in old_eligibilities.values())
    active_after = {rid for c in recovery_snapshot["components"] for rid in c["authoritative_receipt_ids"]}
    old_reactivated = any(rid in active_after for rid in old_ids)
    deterministic = (
        down_snapshot["state_digest"] == down_replay["state_digest"]
        and recovery_snapshot["state_digest"] == recovery_replay["state_digest"]
    )
    passed = (
        down_snapshot["frontier_histogram"] == {"C2": 4}
        and recovery_snapshot["frontier_histogram"] == {"C5": 4}
        and not old_reactivated
        and deterministic
    )
    return {
        "scenario_id": "J6_STRICT_POLICY_SUPERSEDED:GLOBAL",
        "scenario_type": "J6_STRICT_POLICY_SUPERSEDED",
        "provenance_class": "SYNTHETIC_CONTROL",
        "target_component_ids": sorted(old_eligibilities),
        "downgrade_frontiers": down_snapshot["frontier_histogram"],
        "recovery_frontiers": recovery_snapshot["frontier_histogram"],
        "downgrade_state_digest": down_snapshot["state_digest"],
        "recovery_state_digest": recovery_snapshot["state_digest"],
        "event_ids": [event["event_id"]],
        "old_downstream_receipt_ids": old_ids,
        "new_receipt_ids": sorted([new_policy["receipt_id"], *new_eligibility_ids]),
        "old_downstream_receipts_reactivated": old_reactivated,
        "replay_deterministic": deterministic,
        "status": "PASS" if passed else "FAIL",
    }


def run_e25j_scenarios() -> dict[str, Any]:
    baseline = build_baseline_ledger()
    component_ids = [c["component_id"] for c in sorted(baseline["components"], key=lambda x: x["component_id"])]
    scenarios: list[dict[str, Any]] = []
    for ordinal, component_id in enumerate(component_ids):
        scenarios.extend(_component_scenarios(component_id, ordinal))
    scenarios.append(_shared_policy_scenario())

    component_count = sum(1 for s in scenarios if s["scenario_type"] != "J6_STRICT_POLICY_SUPERSEDED")
    shared_count = sum(1 for s in scenarios if s["scenario_type"] == "J6_STRICT_POLICY_SUPERSEDED")
    all_pass = all(s["status"] == "PASS" for s in scenarios)
    return {
        "experiment_id": "E25J_REVOCATION_STALENESS_RECOVERY_MATRIX",
        "status": "PASS" if all_pass and len(scenarios) == 21 else "FAIL",
        "scenario_count": len(scenarios),
        "component_scenario_count": component_count,
        "shared_policy_scenario_count": shared_count,
        "scenario_type_counts": {
            key: sum(1 for s in scenarios if s["scenario_type"] == key)
            for key in [
                "J1_C5A_SUPERSEDED",
                "J2_C5B_REVOKED",
                "J3_C2_SUPERSEDED",
                "J4_C1_REVOKED",
                "J5_IDENTITY_CONFLICT",
                "J6_STRICT_POLICY_SUPERSEDED",
            ]
        },
        "scenarios": scenarios,
        "claim_boundary": "All 21 lifecycle faults are SYNTHETIC_CONTROL scenarios over the four frozen REAL_SOURCE_BOUND contracts; they test lifecycle behavior and do not imply real graph defects.",
    }
