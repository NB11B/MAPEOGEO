from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from .model import Artifact, OperatorFailure
from .rigorous_math import (
    BezoutCertificate,
    GridEvaluationCertificate,
    QuadraticMeanValueCertificate,
)
from .v0_20_contracts import (
    NEW_V0_20_FAMILIES,
    V0_20_ARTIFACT_CONTRACTS,
    V0_20_CONTRACTS,
)
from .v0_20_goals import build_v0_20_corpus
from .v0_20_operators import (
    _OPERATOR_FAMILIES,
    _OPERATOR_INPUT_TYPES,
    build_v0_20_operator_registry,
)
from .v0_20_verifiers import validate_v0_20_goal_contract, verify_v0_20_goal


def _new_goals():
    corpus = build_v0_20_corpus()
    return [
        goal
        for split in corpus.values()
        for goal in split
        if goal.family in NEW_V0_20_FAMILIES
    ]


def _execute_reference_path(goal):
    registry = build_v0_20_operator_registry()
    artifacts = dict(goal.inputs)
    candidate = None
    for operator_id in goal.sealed_reference_path:
        if operator_id == "VERIFY_CANDIDATE":
            continue
        spec = registry[operator_id]
        output = spec.execute(artifacts, tuple(goal.constraints))
        assert not isinstance(output, OperatorFailure), (goal.goal_id, operator_id, output)
        step = spec.verify(tuple(artifacts.values()), output)
        assert step.passed, (goal.goal_id, operator_id, step)
        artifacts[f"derived:{operator_id}"] = output
        candidate = output
    assert candidate is not None
    return candidate


def test_new_family_contracts_are_closed_immutable_and_all_generated_goals_validate() -> None:
    assert set(V0_20_CONTRACTS) == set(NEW_V0_20_FAMILIES)
    with pytest.raises(TypeError):
        V0_20_CONTRACTS["F1"] = V0_20_CONTRACTS["F2"]  # type: ignore[index]
    goals = _new_goals()
    assert len(goals) == 7 * 6
    for goal in goals:
        result = validate_v0_20_goal_contract(goal.solver_visible())
        assert result.passed, (goal.goal_id, result)


def test_public_contract_mapping_has_no_live_mutable_backing_alias() -> None:
    from . import v0_20_contracts as contracts_module

    assert not hasattr(contracts_module, "_CONTRACT_ROWS")
    original = V0_20_CONTRACTS["F1"]
    independent = contracts_module._build_contracts()
    independent["F1"] = V0_20_CONTRACTS["F2"]
    assert V0_20_CONTRACTS["F1"] is original


def test_every_closed_operator_has_complete_input_contracts_and_objective() -> None:
    registry = build_v0_20_operator_registry()
    for operator_id, family in _OPERATOR_FAMILIES.items():
        specification = registry[operator_id]
        assert all(
            semantic_type in V0_20_ARTIFACT_CONTRACTS
            for semantic_type in _OPERATOR_INPUT_TYPES[operator_id]
        )
        if hasattr(specification, "input_ports"):
            observed = tuple(
                (
                    port.artifact_type.semantic_type,
                    port.artifact_type.representation_class,
                    port.artifact_type.exactness_class,
                )
                for port in specification.input_ports
            )
            expected = tuple(
                (
                    V0_20_ARTIFACT_CONTRACTS[semantic_type].semantic_type,
                    V0_20_ARTIFACT_CONTRACTS[semantic_type].representation_class,
                    V0_20_ARTIFACT_CONTRACTS[semantic_type].exactness_class,
                )
                for semantic_type in _OPERATOR_INPUT_TYPES[operator_id]
            )
            assert observed == expected
            assert specification.objectives == (
                V0_20_CONTRACTS[family].target.objective,
            )


def test_every_new_family_reference_pipeline_emits_a_strictly_verified_typed_certificate() -> None:
    for goal in _new_goals():
        candidate = _execute_reference_path(goal)
        contract = V0_20_CONTRACTS[goal.family]
        assert type(candidate.value) is contract.candidate_type
        assert candidate.metadata == ()
        terminal = verify_v0_20_goal(goal.solver_visible(), candidate)
        assert terminal.passed, (goal.goal_id, terminal)


def test_roots_are_not_answer_bearing_and_swapped_or_padded_roots_fail_closed() -> None:
    for generated in _new_goals():
        assert all(artifact.metadata == () for artifact in generated.inputs.values())
        assert all(artifact.provenance == () for artifact in generated.inputs.values())

    goal = next(goal for goal in _new_goals() if goal.family == "F1")
    visible = goal.solver_visible()

    swapped = dict(visible.inputs)
    swapped["lower_bound"], swapped["upper_bound"] = swapped["upper_bound"], swapped["lower_bound"]
    assert not validate_v0_20_goal_contract(replace(visible, inputs=swapped)).passed

    padded = dict(visible.inputs)
    padded["answer"] = Artifact("answer", "ANSWER", "SCALAR", 42, "EXACT")
    assert not validate_v0_20_goal_contract(replace(visible, inputs=padded)).passed


def test_wrong_family_target_constraints_and_root_metadata_are_rejected() -> None:
    goal = next(goal for goal in _new_goals() if goal.family == "F2").solver_visible()
    assert not validate_v0_20_goal_contract(replace(goal, family="F1")).passed
    assert not validate_v0_20_goal_contract(
        replace(goal, target=replace(goal.target, semantic_type="BEZOUT_CERTIFICATE"))
    ).passed
    assert not validate_v0_20_goal_contract(
        replace(goal, constraints=goal.constraints + (("answer", 1),))
    ).passed
    roots = dict(goal.inputs)
    coefficients = roots["coefficients"]
    roots["coefficients"] = replace(coefficients, metadata=(("answer", "midpoint"),))
    assert not validate_v0_20_goal_contract(replace(goal, inputs=roots)).passed


def test_candidate_schema_rejects_dicts_wrong_types_metadata_and_bool_integer_forgery() -> None:
    goal = next(goal for goal in _new_goals() if goal.family == "F3")
    candidate = _execute_reference_path(goal)
    visible = goal.solver_visible()
    assert not verify_v0_20_goal(visible, replace(candidate, value={"gcd": 1})).passed
    assert not verify_v0_20_goal(visible, replace(candidate, metadata=(("verified", True),))).passed
    assert not verify_v0_20_goal(visible, replace(candidate, metadata=(("residual", float("nan")),))).passed
    assert not verify_v0_20_goal(visible, replace(candidate, semantic_type="OTHER")).passed
    forged = replace(candidate.value, verified=1)
    assert isinstance(forged, BezoutCertificate)
    assert not verify_v0_20_goal(visible, replace(candidate, value=forged)).passed


def test_f2_accepts_valid_alternative_affine_witness_but_rejects_endpoints() -> None:
    goal = next(
        goal
        for goal in _new_goals()
        if goal.family == "F2" and goal.inputs["coefficients"].value[0] == 0
    )
    candidate = _execute_reference_path(goal)
    certificate = candidate.value
    assert isinstance(certificate, QuadraticMeanValueCertificate)
    left, right = goal.inputs["interval"].value
    witness = left + (right - left) / 3
    alternate = replace(
        certificate,
        witness=witness,
        derivative_at_witness=certificate.coefficients[1],
    )
    assert verify_v0_20_goal(goal.solver_visible(), replace(candidate, value=alternate)).passed
    endpoint = replace(
        certificate,
        witness=left,
        derivative_at_witness=certificate.coefficients[1],
    )
    assert not verify_v0_20_goal(goal.solver_visible(), replace(candidate, value=endpoint)).passed


def test_f3_accepts_every_source_bound_bezout_solution_including_zero_zero() -> None:
    for goal in [goal for goal in _new_goals() if goal.family == "F3"]:
        candidate = _execute_reference_path(goal)
        certificate = candidate.value
        assert isinstance(certificate, BezoutCertificate)
        a = goal.inputs["integer_a"].value
        b = goal.inputs["integer_b"].value
        if certificate.gcd:
            alternative = replace(
                certificate,
                x=certificate.x + b // certificate.gcd,
                y=certificate.y - a // certificate.gcd,
            )
        else:
            alternative = replace(certificate, x=-123, y=456)
        assert verify_v0_20_goal(goal.solver_visible(), replace(candidate, value=alternative)).passed


def test_x1_forged_nan_and_source_mismatch_fail_even_with_verified_flag() -> None:
    goal = next(goal for goal in _new_goals() if goal.family == "X1")
    candidate = _execute_reference_path(goal)
    certificate = candidate.value
    assert isinstance(certificate, GridEvaluationCertificate)
    nan_values = (float("nan"),) + certificate.numerical_values[1:]
    forged_nan = replace(certificate, numerical_values=nan_values, verified=True)
    assert not verify_v0_20_goal(goal.solver_visible(), replace(candidate, value=forged_nan)).passed
    forged_source = replace(
        certificate,
        coefficients=(certificate.coefficients[0] + 1,) + certificate.coefficients[1:],
    )
    assert not verify_v0_20_goal(goal.solver_visible(), replace(candidate, value=forged_source)).passed


def test_x2_discriminant_convention_and_period_certificate_are_source_bound() -> None:
    goal = next(goal for goal in _new_goals() if goal.family == "X2")
    registry = build_v0_20_operator_registry()
    curve = registry["EXACT_INVARIANTS_TO_SYMBOLIC_CURVE"].execute(
        goal.inputs,
        tuple(goal.constraints),
    )
    assert not isinstance(curve, OperatorFailure)
    g2 = goal.inputs["g2"].value
    g3 = goal.inputs["g3"].value
    assert curve.value.elliptic_discriminant == g2**3 - 27 * g3**2
    assert curve.value.polynomial_discriminant == 16 * (g2**3 - 27 * g3**2)

    candidate = _execute_reference_path(goal)
    forged = replace(candidate.value, g2=candidate.value.g2 + 1)
    assert not verify_v0_20_goal(goal.solver_visible(), replace(candidate, value=forged)).passed


@pytest.mark.parametrize("family", ["X1", "X2"])
def test_cross_class_terminal_rejects_missing_or_fabricated_pipeline_receipts(family: str) -> None:
    goal = next(goal for goal in _new_goals() if goal.family == family)
    candidate = _execute_reference_path(goal)

    assert not verify_v0_20_goal(
        goal.solver_visible(),
        replace(candidate, artifact_id="forged", provenance=()),
    ).passed
    assert not verify_v0_20_goal(
        goal.solver_visible(),
        replace(candidate, artifact_id="forged", provenance=("invented",)),
    ).passed


def test_operator_step_replay_binds_content_derived_id_and_exact_provenance() -> None:
    goal = next(goal for goal in _new_goals() if goal.family == "X1")
    registry = build_v0_20_operator_registry()
    spec = registry["EXACT_TO_SYMBOLIC_POLYNOMIAL"]
    original_inputs = {"coefficients": goal.inputs["coefficients"]}
    original = spec.execute(original_inputs, tuple(goal.constraints))
    assert not isinstance(original, OperatorFailure)

    assert not spec.verify(
        tuple(original_inputs.values()),
        replace(original, artifact_id="wrong-id"),
    ).passed
    assert not spec.verify(
        tuple(original_inputs.values()),
        replace(original, provenance=("invented",)),
    ).passed

    changed_root = replace(
        goal.inputs["coefficients"],
        value=(goal.inputs["coefficients"].value[0] + 1,)
        + goal.inputs["coefficients"].value[1:],
    )
    changed = spec.execute({"coefficients": changed_root}, tuple(goal.constraints))
    assert not isinstance(changed, OperatorFailure)
    assert changed.artifact_id != original.artifact_id


def test_terminal_verifier_is_total_on_malformed_candidate_and_goal_objects() -> None:
    goal = next(goal for goal in _new_goals() if goal.family == "C1")
    candidate = _execute_reference_path(goal)
    assert not verify_v0_20_goal(object(), candidate).passed  # type: ignore[arg-type]
    assert not verify_v0_20_goal(goal.solver_visible(), object()).passed  # type: ignore[arg-type]
    assert not validate_v0_20_goal_contract(object()).passed  # type: ignore[arg-type]


def test_operator_boundaries_return_static_failures_for_oversized_or_out_of_domain_inputs() -> None:
    registry = build_v0_20_operator_registry()
    oversized = Artifact(
        "oversized",
        "POLYNOMIAL_COEFFICIENTS_EXACT",
        "RATIONAL_VECTOR",
        (Fraction(1),) * 4097,
        "EXACT",
    )
    result = registry["EXACT_TO_SYMBOLIC_POLYNOMIAL"].execute({"coefficients": oversized}, ())
    assert isinstance(result, OperatorFailure)
    assert result.reason == "bounded certificate construction rejected input"

    g2 = Artifact("g2", "WEIERSTRASS_G2_EXACT", "RATIONAL_SCALAR", Fraction(0), "EXACT")
    g3 = Artifact("g3", "WEIERSTRASS_G3_EXACT", "RATIONAL_SCALAR", Fraction(1), "EXACT")
    result = registry["EXACT_INVARIANTS_TO_SYMBOLIC_CURVE"].execute({"g2": g2, "g3": g3}, ())
    assert isinstance(result, OperatorFailure)
    assert result.reason == "bounded certificate construction rejected input"
