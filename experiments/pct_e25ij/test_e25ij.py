from copy import deepcopy

from experiments.pct_e25ij.receipts import make_receipt
from experiments.pct_e25ij.lifecycle import build_baseline_ledger, replay_lifecycle, run_e25i_audit


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
    component = next(c for c in snapshot["components"] if c["component_id"] == c5a["component_id"])
    assert component["effective_frontier"] == "C2"
    assert component["closure"]["C5"]["state"] == "NOT_ESTABLISHED"
