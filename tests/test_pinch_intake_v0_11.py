import json
from pathlib import Path

from scripts.formal_bridge_v0_8 import proof_escape_hits
from scripts.pinch_contracts_v0_11 import run_contract


def test_v011_lean_file_has_no_escape_hatches():
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    assert proof_escape_hits(text) == []


def test_all_frozen_scopes_have_fixed_decl_names():
    cfg = json.loads(
        Path("formal/pinch_bindings_v0_11.json")
        .read_text(encoding="utf-8")
    )

    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")

    expected = [
        x["formal_decl"].split(".")[-1]
        for x in cfg["targets"]
        if x["scope_status"] == "FROZEN"
    ]

    assert len(expected) == 4
    assert all(name in text for name in expected)


def test_untested_is_not_pass():
    result = run_contract({
        "source_id": "srcdecl:proposition:3_14",
        "s3_test_state": "UNTESTED",
        "s3_contract_id": None,
        "s3_scope": None,
    })

    assert result.verdict == "UNTESTED"
    assert result.test_state == "UNTESTED"
    assert result.refused


def test_unknown_contract_is_invalid():
    result = run_contract({
        "source_id": "synthetic:test",
        "s3_test_state": "EXECUTABLE_CONTRACT",
        "s3_contract_id": "UNKNOWN_CONTRACT",
        "s3_scope": "SYNTHETIC",
    })

    assert result.verdict == "INVALID"
    assert result.refused


def test_pct_contract_is_not_applicable():
    result = run_contract({
        "source_id": "synthetic:test",
        "s3_test_state": "PCT_CONTRACT",
        "s3_contract_id": "pct_mock",
        "s3_scope": "SYNTHETIC",
    })

    assert result.verdict == "NOT_APPLICABLE"
    assert result.applicability == "NOT_APPLICABLE"


def test_all_v011_target_contracts_execute_cleanly():
    cfg = json.loads(
        Path("formal/pinch_bindings_v0_11.json")
        .read_text(encoding="utf-8")
    )

    for target in cfg["targets"]:
        res = run_contract(target)
        if target["s3_test_state"] == "UNTESTED":
            assert res.verdict == "UNTESTED"
        elif target["s3_test_state"] == "EXECUTABLE_CONTRACT":
            assert res.verdict == "PASS"
            assert res.measured.get("all_checks_passed") is True


def test_negative_escape_hatch_detection():
    assert proof_escape_hits("lemma foo : 1 = 1 := by sorry") == ["sorry"]
    assert proof_escape_hits("lemma bar : 1 = 1 := by admit") == ["admit"]
    assert proof_escape_hits("axiom bad_axiom : False") == ["axiom_declaration"]
    assert proof_escape_hits("unsafe def bad_fn : Nat := 0") == ["unsafe_declaration"]
    assert proof_escape_hits("theorem good : 1 = 1 := rfl") == []


def test_negative_forbidden_prose_keys_detected():
    from tests.validate_pinch_intake_v0_11 import FORBIDDEN_PERSISTED_KEYS
    test_node_attrs = {
        "statement_text": "Let V be a finite dimensional vector space...",
        "formal_scope": "Valid scope",
    }
    assert bool(FORBIDDEN_PERSISTED_KEYS.intersection(test_node_attrs)) is True

