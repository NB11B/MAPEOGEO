from copy import deepcopy

from experiments.pct_e25ij.receipts import make_event, make_receipt
from experiments.pct_e25ij.lifecycle import build_baseline_ledger, replay_lifecycle, run_e25i_audit
from experiments.pct_e25ij.scenarios import run_e25j_scenarios


def _component(snapshot, component_id):
    return next(c for c in snapshot["components"] if c["component_id"] == component_id)


def _receipt(ledger, component_id, role):
    return next(r for r in ledger["receipts"] if r["component_id"] == component_id and r["role"] == role)


def test_receipt_id_is_deterministic_and_authority_is_not_stored():
    kwargs = dict(
        component_id="source-bound:rank:theorem_6_16",
        component_epoch=0,
        layer="C0",
        role="C0_IDENTITY",
        mathematical_verdict="PASS",
        content={"x": 1},
        dependency_receipt_ids=[],
        source_statement_sha256="abc",
        evidence_refs=["fixture"],
        predecessor_receipt_id=None,
        issuance_revision=1,
    )
    a = make_receipt(**kwargs)
    b = make_receipt(**deepcopy(kwargs))
    assert a == b
    assert len(a["receipt_id"]) == 64
    assert "authority_state" not in a


def test_e25i_reconstructs_then_promotes_four_real_components():
    result = run_e25i_audit()
    assert result["status"] == "PASS"
    assert result["real_component_count"] == 4
    assert result["synthetic_components_counted_as_real"] == 0
    assert result["pre_c5_frontier_histogram"] == {"C2": 4}
    assert result["post_c5_frontier_histogram"] == {"C5": 4}
    for component in result["components"]:
        assert component["pre_c5"]["closure"]["C3"]["state"] == "NOT_APPLICABLE"
        assert component["pre_c5"]["closure"]["C4"]["state"] == "NOT_APPLICABLE"
        assert component["post_c5"]["effective_frontier"] == "C5"


def test_missing_required_receipt_prevents_c5_without_inventing_pass():
    ledger = build_baseline_ledger()
    c5a = next(r for r in ledger["receipts"] if r["role"] == "C5A_EXACT_MORPHISM")
    reduced = deepcopy(ledger)
    reduced["receipts"] = [r for r in reduced["receipts"] if r["receipt_id"] != c5a["receipt_id"]]
    snapshot = replay_lifecycle(reduced)
    component = _component(snapshot, c5a["component_id"])
    assert component["effective_frontier"] == "C2"
    assert component["closure"]["C5"]["state"] == "NOT_ESTABLISHED"


def test_c5a_supersession_drops_only_to_c2_and_does_not_resurrect_old_c5():
    ledger = build_baseline_ledger()
    component_id = "source-bound:rank:theorem_6_16"
    old_c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    replacement = make_receipt(
        component_id=component_id,
        component_epoch=0,
        layer="C5",
        role="C5A_EXACT_MORPHISM",
        mathematical_verdict="PASS",
        content={"replacement": "exact-map-v2"},
        dependency_receipt_ids=list(old_c5a["dependency_receipt_ids"]),
        source_statement_sha256=old_c5a["source_statement_sha256"],
        evidence_refs=["synthetic:J1"],
        predecessor_receipt_id=old_c5a["receipt_id"],
        issuance_revision=100,
    )
    ledger["receipts"].append(replacement)
    event = make_event(
        revision=101,
        event_type="SUPERSEDE",
        target_receipt_id=old_c5a["receipt_id"],
        component_id=component_id,
        reason_code="J1_C5A_REPLACED",
        replacement_receipt_id=replacement["receipt_id"],
    )
    snapshot = replay_lifecycle(ledger, [event])
    c = _component(snapshot, component_id)
    assert c["effective_frontier"] == "C2"
    assert old_c5a["receipt_id"] in c["superseded_receipt_ids"]
    assert replacement["receipt_id"] in c["authoritative_receipt_ids"]
    assert c["closure"]["C5"]["state"] == "NOT_ESTABLISHED"


def test_c5b_revocation_drops_to_c2_and_stales_old_eligibility():
    ledger = build_baseline_ledger()
    component_id = "source-bound:convex:definition_44_6"
    c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    eligibility = _receipt(ledger, component_id, "C5_ELIGIBILITY")
    event = make_event(
        revision=110,
        event_type="REVOKE",
        target_receipt_id=c5b["receipt_id"],
        component_id=component_id,
        reason_code="J2_C5B_REVOKED",
    )
    c = _component(replay_lifecycle(ledger, [event]), component_id)
    assert c["effective_frontier"] == "C2"
    assert c5b["receipt_id"] in c["revoked_receipt_ids"]
    assert eligibility["receipt_id"] in c["stale_receipt_ids"]


def test_c2_supersession_drops_to_c1_and_stales_both_c5_axes():
    ledger = build_baseline_ledger()
    component_id = "source-bound:lp:theorem_47_9"
    c2 = _receipt(ledger, component_id, "C2_EXECUTABLE_CONTRACT")
    c5a = _receipt(ledger, component_id, "C5A_EXACT_MORPHISM")
    c5b = _receipt(ledger, component_id, "C5B_PROVENANCE_BINDING")
    event = make_event(
        revision=120,
        event_type="SUPERSEDE",
        target_receipt_id=c2["receipt_id"],
        component_id=component_id,
        reason_code="J3_C2_REPLACED",
    )
    c = _component(replay_lifecycle(ledger, [event]), component_id)
    assert c["effective_frontier"] == "C1"
    assert c5a["receipt_id"] in c["stale_receipt_ids"]
    assert c5b["receipt_id"] in c["stale_receipt_ids"]


def test_c1_revocation_drops_to_c0():
    ledger = build_baseline_ledger()
    component_id = "source-bound:gauss:definition_53_4"
    c1 = _receipt(ledger, component_id, "C1_CERTIFICATE_BINDING")
    event = make_event(
        revision=130,
        event_type="REVOKE",
        target_receipt_id=c1["receipt_id"],
        component_id=component_id,
        reason_code="J4_C1_REVOKED",
    )
    c = _component(replay_lifecycle(ledger, [event]), component_id)
    assert c["effective_frontier"] == "C0"
    assert c1["receipt_id"] in c["revoked_receipt_ids"]


def test_identity_conflict_invalidates_component_and_removes_frontier():
    ledger = build_baseline_ledger()
    component_id = "source-bound:rank:theorem_6_16"
    c0 = _receipt(ledger, component_id, "C0_IDENTITY")
    conflict = make_event(
        revision=140,
        event_type="IDENTITY_CONFLICT",
        target_receipt_id=c0["receipt_id"],
        component_id=component_id,
        reason_code="J5_SOURCE_HASH_CONFLICT",
    )
    c = _component(replay_lifecycle(ledger, [conflict]), component_id)
    assert c["effective_frontier"] is None
    assert c["component_state"] == "INVALID"
    assert c0["receipt_id"] in c["invalid_receipt_ids"]


def test_shared_policy_supersession_drops_all_four_to_c2():
    ledger = build_baseline_ledger()
    policy = next(r for r in ledger["receipts"] if r["role"] == "GLOBAL_C5_STRICT_POLICY")
    replacement = make_receipt(
        component_id=policy["component_id"],
        component_epoch=0,
        layer="C5",
        role="GLOBAL_C5_STRICT_POLICY",
        mathematical_verdict="PASS",
        content={"replacement": "strict-policy-v2"},
        dependency_receipt_ids=[],
        source_statement_sha256=policy["source_statement_sha256"],
        evidence_refs=["synthetic:J6"],
        predecessor_receipt_id=policy["receipt_id"],
        issuance_revision=150,
    )
    ledger["receipts"].append(replacement)
    event = make_event(
        revision=151,
        event_type="SUPERSEDE",
        target_receipt_id=policy["receipt_id"],
        component_id=policy["component_id"],
        reason_code="J6_POLICY_REPLACED",
        replacement_receipt_id=replacement["receipt_id"],
    )
    snapshot = replay_lifecycle(ledger, [event])
    assert snapshot["frontier_histogram"] == {"C2": 4}


def test_e25j_runs_exactly_21_preregistered_scenarios():
    result = run_e25j_scenarios()
    assert result["status"] == "PASS"
    assert result["scenario_count"] == 21
    assert result["component_scenario_count"] == 20
    assert result["shared_policy_scenario_count"] == 1


def test_e25j_downgrades_to_exact_remaining_frontier_and_recovers():
    result = run_e25j_scenarios()
    expected = {
        "J1_C5A_SUPERSEDED": "C2",
        "J2_C5B_REVOKED": "C2",
        "J3_C2_SUPERSEDED": "C1",
        "J4_C1_REVOKED": "C0",
        "J5_IDENTITY_CONFLICT": None,
    }
    for scenario in result["scenarios"]:
        if scenario["scenario_type"] in expected:
            assert scenario["observed_frontier"] == expected[scenario["scenario_type"]]
            assert scenario["recovered_frontier"] == "C5"
            assert scenario["old_downstream_receipts_reactivated"] is False


def test_shared_policy_replacement_drops_all_four_then_requires_new_eligibility():
    result = run_e25j_scenarios()
    j6 = next(x for x in result["scenarios"] if x["scenario_type"] == "J6_STRICT_POLICY_SUPERSEDED")
    assert j6["downgrade_frontiers"] == {"C2": 4}
    assert j6["recovery_frontiers"] == {"C5": 4}
    assert j6["old_downstream_receipts_reactivated"] is False
