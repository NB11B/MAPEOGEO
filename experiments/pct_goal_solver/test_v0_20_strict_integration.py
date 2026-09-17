from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import combinations

import sympy as sp

from experiments.pct_goal_solver.canonical import canonical_sha256
from experiments.pct_goal_solver.model import ArtifactType
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v0_20_contracts import V0_20_CONTRACTS
from experiments.pct_goal_solver.v0_20_goals import (
    CORE_SPLITS,
    NEW_V0_20_FAMILIES,
    build_v0_20_corpus,
)
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry
from experiments.pct_goal_solver.v0_20_verifiers import validate_v0_20_goal_contract


def test_closed_operator_registry_builds_with_typed_ports_and_terminal_objectives() -> None:
    registry = build_v0_20_operator_registry()
    terminal_operators = {
        "F1": "CERTIFY_SQRT2_CUT",
        "F2": "CERTIFY_QUADRATIC_MEAN_VALUE",
        "F3": "CERTIFY_BEZOUT",
        "C1": "CERTIFY_CAUCHY_RIEMANN",
        "C2": "CERTIFY_RATIONAL_RESIDUE",
        "X1": "CERTIFY_GRID_EVALUATION",
        "X2": "CERTIFY_RECTANGULAR_PERIODS",
    }
    for family, operator_id in terminal_operators.items():
        contract = V0_20_CONTRACTS[family]
        specification = registry[operator_id]
        assert all(type(port.artifact_type) is ArtifactType for port in specification.input_ports)
        assert specification.output == ArtifactType(
            contract.target.semantic_type,
            contract.target.representation_class,
            contract.target.exactness_class,
        )
        assert specification.objectives == (contract.target.objective,)

    assert dict(V0_20_CONTRACTS["X1"].constraints)["required_derived_types"] == (
        "SYMBOLIC_POLYNOMIAL",
        "NUMERICAL_POLYNOMIAL_EVALUATION",
        "GRID_EVALUATION_CERTIFICATE",
    )


def _root_content_digest(goal: object) -> str:
    return canonical_sha256(
        {
            key: {
                "semantic_type": artifact.semantic_type,
                "representation_class": artifact.representation_class,
                "exactness_class": artifact.exactness_class,
                "value": artifact.value,
                "metadata": artifact.metadata,
            }
            for key, artifact in sorted(goal.inputs.items())
        },
        domain="pct-v0-20-root-content-v1",
    )


def test_new_family_corpus_uses_closed_contracts_and_content_disjoint_splits() -> None:
    corpus = build_v0_20_corpus()
    for family in NEW_V0_20_FAMILIES:
        signatures: dict[str, set[str]] = {}
        for split in CORE_SPLITS:
            goals = [goal for goal in corpus[split] if goal.family == family]
            assert goals
            assert all(validate_v0_20_goal_contract(goal).passed for goal in goals)
            signatures[split] = {_root_content_digest(goal) for goal in goals}
            assert len(signatures[split]) == len(goals)
        for left, right in combinations(CORE_SPLITS, 2):
            assert signatures[left].isdisjoint(signatures[right]), (family, left, right)


def test_cross_class_goal_contract_rejects_missing_or_tampered_lineage() -> None:
    corpus = build_v0_20_corpus()
    for family in ("X1", "X2"):
        goal = next(goal for goal in corpus["CALIBRATION_V0_20"] if goal.family == family)
        assert validate_v0_20_goal_contract(goal).passed
        missing = replace(goal, lineage_obligation=None)
        assert not validate_v0_20_goal_contract(missing).passed
        tampered = replace(
            goal,
            lineage_obligation=replace(
                goal.lineage_obligation,
                required_input_keys=frozenset({next(iter(goal.inputs))}),
            ),
        )
        assert not validate_v0_20_goal_contract(tampered).passed


def test_all_new_families_solve_through_the_strict_planner_authority() -> None:
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    goals = [
        goal
        for goal in corpus["VALIDATION_V0_20"]
        if goal.family in NEW_V0_20_FAMILIES
    ]
    assert {goal.family for goal in goals} == set(NEW_V0_20_FAMILIES)
    traces = {goal.family: solve(goal.solver_visible(), registry) for goal in goals}
    for family, trace in traces.items():
        assert trace.final_verdict == "PASS", (family, trace.failure_reason, trace.falsification_events)
        assert trace.verifier_chain[-1].verifier_class == "PCT_V0_20_STRICT_CERTIFICATE"
    assert traces["X1"].operator_path == (
        "EXACT_TO_SYMBOLIC_POLYNOMIAL",
        "SYMBOLIC_TO_NUMERICAL_EVALUATION",
        "CERTIFY_GRID_EVALUATION",
        "VERIFY_CANDIDATE",
    )
    assert traces["X2"].operator_path == (
        "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE",
        "CERTIFY_RECTANGULAR_PERIODS",
        "VERIFY_CANDIDATE",
    )


def test_historical_g4_comparison_uses_one_common_persistence_grid() -> None:
    goal = next(
        goal
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == "G4" and goal.goal_id.endswith(":01")
    )
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())

    assert trace.final_verdict == "PASS"
    assert trace.candidate_artifact is not None
    assert trace.candidate_artifact.value == {"level": "BETTI", "distinct": True}


def _historical_g4_with_barcodes(barcode_a: object, barcode_b: object):
    goal = next(
        goal
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == "G4" and goal.goal_id.endswith(":01")
    )
    inputs = dict(goal.inputs)
    inputs["barcode_a"] = replace(inputs["barcode_a"], value=barcode_a)
    inputs["barcode_b"] = replace(inputs["barcode_b"], value=barcode_b)
    return replace(goal, inputs=inputs)


def test_historical_g4_normalizes_mixed_barcode_row_containers() -> None:
    goal = _historical_g4_with_barcodes(
        [(0, 0, 2), [1, 0, 2]],
        [],
    )

    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())

    assert trace.final_verdict == "PASS"
    assert trace.candidate_artifact is not None
    assert trace.candidate_artifact.value == {"level": "BETTI", "distinct": True}


def test_historical_g4_normalizes_semantically_equal_barcode_encodings() -> None:
    goal = _historical_g4_with_barcodes(
        [(0, 0, 1)],
        [[0, 0, 1]],
    )

    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())

    assert trace.final_verdict == "PASS"
    assert trace.candidate_artifact is not None
    assert trace.candidate_artifact.value == {"level": "NONE", "distinct": False}


def test_x1_binary64_infeasibility_refuses_without_invalidating_exact_math() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "X1"
    )
    registry = build_v0_20_operator_registry()
    for coefficients in (
        (Fraction(10**20), Fraction(1, 3)),
        (Fraction(10**400),),
    ):
        inputs = dict(base.inputs)
        inputs["coefficients"] = replace(
            inputs["coefficients"],
            value=coefficients,
        )
        inputs["grid"] = replace(inputs["grid"], value=(Fraction(1),))
        goal = replace(base, inputs=inputs)

        assert validate_v0_20_goal_contract(goal).passed is True
        trace = solve(goal.solver_visible(), registry)
        assert trace.final_verdict == "NOT_ESTABLISHED"
        assert trace.candidate_artifact is None

    overflow_trace = solve(
        replace(
            base.solver_visible(),
            inputs={
                **base.solver_visible().inputs,
                "coefficients": replace(
                    base.inputs["coefficients"],
                    value=(Fraction(10**400),),
                ),
                "grid": replace(base.inputs["grid"], value=(Fraction(1),)),
            },
        ),
        registry,
    )
    assert overflow_trace.refusal is not None
    assert overflow_trace.refusal.code == "NUMERICALLY_UNSAFE"


def test_x2_near_degenerate_valid_curves_have_verified_safe_outcomes() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "X2"
    )
    registry = build_v0_20_operator_registry()
    for gap_exponent in (60, 256):
        inputs = dict(base.inputs)
        inputs["g2"] = replace(inputs["g2"], value=Fraction(3))
        inputs["g3"] = replace(
            inputs["g3"],
            value=-Fraction(1) + Fraction(1, 2**gap_exponent),
        )
        goal = replace(base, inputs=inputs)

        assert validate_v0_20_goal_contract(goal).passed is True
        trace = solve(goal.solver_visible(), registry)

        assert trace.final_verdict in {"PASS", "NOT_ESTABLISHED"}
        assert trace.final_verdict != "INVALID"
        if trace.final_verdict == "PASS":
            assert trace.candidate_artifact is not None
            assert trace.verifier_chain[-1].passed is True
        else:
            assert trace.refusal is not None
            assert trace.refusal.code == "NUMERICALLY_UNSAFE"


def test_f2_contract_rejects_roots_whose_derived_certificate_exceeds_bounds() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "F2"
    )
    large = Fraction(2**3000)
    inputs = dict(base.inputs)
    inputs["coefficients"] = replace(
        inputs["coefficients"],
        value=(large, Fraction(0), Fraction(0)),
    )
    inputs["interval"] = replace(
        inputs["interval"],
        value=(Fraction(0), large),
    )
    goal = replace(base, inputs=inputs)

    assert validate_v0_20_goal_contract(goal).passed is False
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.candidate_artifact is None


def test_x1_contract_bounds_exact_horner_intermediates() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "X1"
    )
    large = Fraction(2**3000)
    inputs = dict(base.inputs)
    inputs["coefficients"] = replace(
        inputs["coefficients"],
        value=(large, large),
    )
    inputs["grid"] = replace(inputs["grid"], value=(large,))
    goal = replace(base, inputs=inputs)

    assert validate_v0_20_goal_contract(goal).passed is False
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.candidate_artifact is None


def test_x1_contract_rejects_roots_whose_symbolic_receipt_exceeds_bounds() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "X1"
    )
    # Every root is individually within the advertised 4096-bit/4096-item
    # bounds, and Horner evaluation at zero remains bounded.  The repeated
    # exact coefficient nevertheless makes the required symbolic-stage receipt
    # exceed its canonical text budget, so the closed goal domain must reject
    # it before planner execution.
    large = Fraction(2**4095 - 1, 2**4094)
    inputs = dict(base.inputs)
    inputs["coefficients"] = replace(
        inputs["coefficients"],
        value=(large,) * 4096,
    )
    inputs["grid"] = replace(inputs["grid"], value=(Fraction(0),))
    goal = replace(base, inputs=inputs)

    assert validate_v0_20_goal_contract(goal).passed is False
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.candidate_artifact is None


def test_c1_contract_rejects_roots_whose_symbolic_receipt_exceeds_bounds() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "C1"
    )
    coefficient = sp.Rational(2**4095 - 1, 2**4094)
    oversized_exact_constant = sp.Add(
        *([coefficient] * 4090),
        evaluate=False,
    )
    assert sum(1 for _ in sp.preorder_traversal(oversized_exact_constant)) <= 4096
    inputs = dict(base.inputs)
    inputs["real_part"] = replace(
        inputs["real_part"],
        value=oversized_exact_constant,
    )
    inputs["imag_part"] = replace(inputs["imag_part"], value=sp.Integer(0))
    goal = replace(base, inputs=inputs)

    assert validate_v0_20_goal_contract(goal).passed is False


def test_c2_contract_rejects_roots_whose_symbolic_receipt_exceeds_bounds() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "C2"
    )
    variable = base.inputs["variable"].value
    coefficient = sp.Rational(2**4095 - 1, 2**4094)
    oversized_meromorphic_form = sp.Add(
        *([coefficient] * 4085),
        1 / variable,
        evaluate=False,
    )
    assert sum(1 for _ in sp.preorder_traversal(oversized_meromorphic_form)) <= 4096
    inputs = dict(base.inputs)
    inputs["form"] = replace(inputs["form"], value=oversized_meromorphic_form)
    inputs["pole"] = replace(inputs["pole"], value=Fraction(0))
    goal = replace(base, inputs=inputs)

    assert validate_v0_20_goal_contract(goal).passed is False


def test_c2_contract_still_requires_a_pole_in_the_reduced_rational_form() -> None:
    base = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "C2"
    )
    variable = base.inputs["variable"].value
    inputs = dict(base.inputs)
    inputs["form"] = replace(inputs["form"], value=variable + 1)
    goal = replace(base, inputs=inputs)

    assert validate_v0_20_goal_contract(goal).passed is False
