from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import replace

import pytest

from experiments.pct_goal_solver import shortcut_proof
from experiments.pct_goal_solver.v0_20_contracts import V0_20_CONTRACTS
from experiments.pct_goal_solver.v0_20_goals import (
    CROSS_CLASS_FAMILIES,
    TerminalControlKind,
    build_v0_20_corpus,
    build_v0_20_terminal_controls,
    prove_no_same_class_shortcut,
)
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry
from experiments.pct_goal_solver.v0_20_verifiers import (
    validate_v0_20_goal_contract,
    verify_v0_20_goal,
)


def _sealed_cross_class_goal(family: str):
    return next(
        goal
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == family
    )


@pytest.mark.parametrize("family", CROSS_CLASS_FAMILIES)
def test_live_registry_produces_a_replay_validated_no_shortcut_proof(family: str) -> None:
    goal = _sealed_cross_class_goal(family)
    receipt = prove_no_same_class_shortcut(goal, build_v0_20_operator_registry())

    assert receipt["status"] == "PROVED"
    assert receipt["proven_no_shortcut"] is True
    assert receipt["proof_validated"] is True
    assert len(receipt["proof_digest"]) == 64
    assert receipt["witness"] is not None
    assert receipt["counterexample"] is None


@pytest.mark.parametrize(
    ("family", "required_operator"),
    (
        ("X1", "EXACT_TO_SYMBOLIC_POLYNOMIAL"),
        ("X2", "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE"),
    ),
)
def test_removing_a_required_bridge_cannot_be_reported_as_a_proof(
    family: str,
    required_operator: str,
) -> None:
    goal = _sealed_cross_class_goal(family)
    registry = build_v0_20_operator_registry()
    del registry[required_operator]

    receipt = prove_no_same_class_shortcut(goal, registry)

    assert receipt["status"] == "UNREACHABLE"
    assert receipt["proven_no_shortcut"] is False
    assert receipt["proof_validated"] is True
    assert receipt["witness"] is None


def test_direct_target_operator_is_a_validated_counterexample_not_a_proof() -> None:
    goal = _sealed_cross_class_goal("X1")
    registry = build_v0_20_operator_registry()
    source = registry["EXACT_TO_SYMBOLIC_POLYNOMIAL"]
    direct = replace(
        source,
        operator_id="ADVERSARIAL_DIRECT_GRID_CERTIFICATE",
        output=goal.target.artifact_type,
        objectives=(goal.target.objective,),
        applicability_id="ADVERSARIAL_DIRECT_GRID_CERTIFICATE:applicability:v1",
        execution_id="ADVERSARIAL_DIRECT_GRID_CERTIFICATE:execution:v1",
        verifier_id="ADVERSARIAL_DIRECT_GRID_CERTIFICATE:verifier:v1",
    )
    registry[direct.operator_id] = direct

    receipt = prove_no_same_class_shortcut(goal, registry)

    assert receipt["status"] == "REFUTED"
    assert receipt["proven_no_shortcut"] is False
    assert receipt["proof_validated"] is True
    assert receipt["counterexample"] is not None


def test_empty_and_internally_inconsistent_registries_fail_closed() -> None:
    goal = _sealed_cross_class_goal("X1")
    empty = prove_no_same_class_shortcut(goal, {})
    assert empty["status"] == "ERROR"
    assert empty["proven_no_shortcut"] is False
    assert empty["proof_validated"] is False

    registry = build_v0_20_operator_registry()
    registry["MISMATCHED_REGISTRY_KEY"] = registry["EXACT_TO_SYMBOLIC_POLYNOMIAL"]
    inconsistent = prove_no_same_class_shortcut(goal, registry)
    assert inconsistent["status"] == "ERROR"
    assert inconsistent["proven_no_shortcut"] is False
    assert inconsistent["proof_validated"] is False

    class ExplodingOperatorId:
        def __eq__(self, other):
            raise AssertionError("untrusted operator-id equality was invoked")

    registry = build_v0_20_operator_registry()
    source = registry["EXACT_TO_SYMBOLIC_POLYNOMIAL"]
    registry["MALFORMED_OPERATOR"] = replace(
        source,
        operator_id=ExplodingOperatorId(),  # type: ignore[arg-type]
    )
    malformed = prove_no_same_class_shortcut(goal, registry)
    assert malformed["status"] == "ERROR"
    assert malformed["proven_no_shortcut"] is False
    assert malformed["proof_validated"] is False


def test_adapter_rejects_a_proof_when_independent_replay_rejects_it(monkeypatch) -> None:
    goal = _sealed_cross_class_goal("X1")
    monkeypatch.setattr(shortcut_proof, "validate_lineage_proof", lambda *args, **kwargs: False)

    receipt = prove_no_same_class_shortcut(goal, build_v0_20_operator_registry())

    assert receipt["status"] == "ERROR"
    assert receipt["proven_no_shortcut"] is False
    assert receipt["proof_validated"] is False
    assert receipt["reason"] == "PROOF_REPLAY_VALIDATION_FAILED"


def test_malformed_goal_fails_closed_before_reading_goal_fields() -> None:
    receipt = prove_no_same_class_shortcut(  # type: ignore[arg-type]
        None,
        build_v0_20_operator_registry(),
    )

    assert receipt["status"] == "ERROR"
    assert receipt["proven_no_shortcut"] is False
    assert receipt["proof_validated"] is False


def test_shortcut_adapter_rejects_split_view_mapping_registries() -> None:
    goal = _sealed_cross_class_goal("X1")
    safe = build_v0_20_operator_registry()
    source = safe["EXACT_TO_SYMBOLIC_POLYNOMIAL"]
    direct = replace(
        source,
        operator_id="SPLIT_VIEW_DIRECT_TARGET",
        output=goal.target.artifact_type,
        objectives=(goal.target.objective,),
        applicability_id="SPLIT_VIEW_DIRECT_TARGET:applicability:v1",
        execution_id="SPLIT_VIEW_DIRECT_TARGET:execution:v1",
        verifier_id="SPLIT_VIEW_DIRECT_TARGET:verifier:v1",
    )

    class SplitViewRegistry(Mapping[str, object]):
        def __iter__(self) -> Iterator[str]:
            return iter((*safe, direct.operator_id))

        def __len__(self) -> int:
            return len(safe) + 1

        def __getitem__(self, key: str) -> object:
            return direct if key == direct.operator_id else safe[key]

        def items(self):
            return safe.items()

    receipt = prove_no_same_class_shortcut(goal, SplitViewRegistry())

    assert receipt["status"] == "ERROR"
    assert receipt["proven_no_shortcut"] is False
    assert receipt["proof_validated"] is False
    assert receipt["reason"] == "REGISTRY_MUST_BE_AN_EXACT_DICT_SNAPSHOT"


def test_terminal_controls_conform_to_the_strict_split_root_contracts() -> None:
    controls = build_v0_20_terminal_controls()

    assert len(controls) == 22
    for control in controls:
        contract_result = validate_v0_20_goal_contract(control.goal)
        result = verify_v0_20_goal(control.goal, control.candidate)
        assert result.passed is control.expected_verification_pass, control.control_id
        if control.kind is TerminalControlKind.DOMAIN_REFUSAL:
            assert contract_result.passed is False
        else:
            assert contract_result.passed is True, control.control_id
        if control.expected_verification_pass:
            assert type(control.candidate.value) is V0_20_CONTRACTS[control.family].candidate_type


def test_only_mathematically_nonunique_certificates_claim_distinct_alternatives() -> None:
    controls = build_v0_20_terminal_controls()
    distinct = {
        control.family
        for control in controls
        if control.kind is TerminalControlKind.EXTERNAL_VALID_CERTIFICATE
        and control.is_distinct_alternative
    }

    # The strict X1 receipt is a deterministic replay of its exact-to-symbolic-
    # to-numerical producer chain.  Calling its one admissible receipt a
    # distinct alternative would be a false scientific claim.
    assert distinct == {"F2", "F3"}


def test_negative_controls_are_mathematically_negative_not_just_named_negative() -> None:
    negative = {
        control.family: control.candidate.value
        for control in build_v0_20_terminal_controls()
        if control.kind is TerminalControlKind.VALID_NEGATIVE_RESULT
    }

    assert negative["F2"].secant_slope < 0
    assert negative["F3"].gcd == 0
    assert negative["C1"].holomorphic is False
    assert negative["C2"].residue == 0
    assert all(value < 0 for value in negative["X1"].exact_values)
