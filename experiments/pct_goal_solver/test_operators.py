from __future__ import annotations

import math

from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import Artifact, OperatorFailure
from experiments.pct_goal_solver.operators import build_operator_registry


def test_registry_contains_frozen_operator_ids():
    reg = build_operator_registry()
    assert len(reg) == 33
    assert {
        "MOBIUS_INVERT_BOOLEAN",
        "CHAIN_MAP_CHECK",
        "SYMBOLIC_IDENTITY_CHECK",
        "CONDITIONING_RISK_CHECK",
        "STEINER_OFFSET_PREDICT",
        "SEPARATION_ESCALATE",
        "FALSIFY_CANDIDATE",
        "VERIFY_CANDIDATE",
    } <= set(reg)


def test_mobius_round_trip_exact():
    reg = build_operator_registry()
    goal = goals_for("CALIBRATION", "G1")[0]
    cumulative = goal.inputs["cumulative"]
    recovered = reg["MOBIUS_INVERT_BOOLEAN"].execute({"cumulative": cumulative}, ())
    assert not isinstance(recovered, OperatorFailure)
    assert recovered.value == goal.sealed_expected_result
    assert reg["MOBIUS_INVERT_BOOLEAN"].verify((cumulative,), recovered).passed


def test_chain_map_check_catches_corruption():
    reg = build_operator_registry()
    goals = goals_for("CALIBRATION", "G3")
    valid = next(goal for goal in goals if goal.sealed_expected_result["is_chain_map"])
    corrupted = next(goal for goal in goals if not goal.sealed_expected_result["is_chain_map"])
    good = reg["CHAIN_MAP_CHECK"].execute(valid.inputs, ())
    bad = reg["CHAIN_MAP_CHECK"].execute(corrupted.inputs, ())
    assert not isinstance(good, OperatorFailure) and good.value["is_chain_map"] is True
    assert not isinstance(bad, OperatorFailure) and bad.value["is_chain_map"] is False
    residual = reg["CHAIN_RESIDUAL"].execute(corrupted.inputs, ())
    assert not isinstance(residual, OperatorFailure)
    assert any(v != 0 for row in residual.value for v in row)


def test_exact_rank_and_conditioning_guard_agree_on_hilbert_goal():
    reg = build_operator_registry()
    goal = goals_for("CALIBRATION", "G6")[0]
    exact = reg["EXACT_MATRIX_RANK_Q"].execute({"matrix": goal.inputs["exact_matrix"]}, ())
    risk = reg["CONDITIONING_RISK_CHECK"].execute({"matrix": goal.inputs["numeric_matrix"]}, ())
    assert not isinstance(exact, OperatorFailure)
    assert exact.value == goal.sealed_expected_result
    assert not isinstance(risk, OperatorFailure)
    assert risk.value["condition_number"] > 1.0
    assert isinstance(risk.value["requires_exact"], bool)


def test_barcode_to_betti_to_euler_is_executable():
    reg = build_operator_registry()
    goal = goals_for("CALIBRATION", "G4")[0]
    betti = reg["BARCODE_TO_BETTI"].execute({"barcode": goal.inputs["barcode_a"]}, (("time_grid", (0, 1, 2, 3)),))
    assert not isinstance(betti, OperatorFailure)
    euler = reg["BETTI_TO_EULER"].execute({"betti": betti}, ())
    assert not isinstance(euler, OperatorFailure)
    assert len(betti.value) == len(euler.value) == 4


def test_symbolic_identity_and_invariant_checks_close():
    reg = build_operator_registry()
    identity_goal = next(goal for goal in goals_for("CALIBRATION", "G12") if goal.sealed_expected_result is True)
    identity = reg["SYMBOLIC_IDENTITY_CHECK"].execute(identity_goal.inputs, ())
    assert not isinstance(identity, OperatorFailure)
    assert identity.value is True

    invariant_goal = goals_for("CALIBRATION", "G7")[0]
    verdict = reg["POLYNOMIAL_INVARIANT_CHECK"].execute(invariant_goal.inputs, ())
    assert not isinstance(verdict, OperatorFailure)
    assert verdict.value is True


def test_steiner_refuses_nonconvex_control():
    reg = build_operator_registry()
    nonconvex = goals_for("CALIBRATION", "G9")[2]
    app = reg["STEINER_OFFSET_PREDICT"].applicability(nonconvex.inputs, ())
    assert app.verdict == "NOT_APPLICABLE"
    result = reg["STEINER_OFFSET_PREDICT"].execute(nonconvex.inputs, ())
    assert isinstance(result, OperatorFailure)
    assert result.verdict == "NOT_APPLICABLE"


def test_graph_signature_bank_can_separate_simple_pair():
    reg = build_operator_registry()
    goal = next(goal for goal in goals_for("CALIBRATION", "G5") if goal.sealed_expected_result["distinct"])
    signatures = []
    for operator_id in (
        "GRAPH_EULER_BETTI",
        "GRAPH_DEGREE_SIGNATURE",
        "GRAPH_LAPLACIAN_SIGNATURE",
        "GRAPH_WL_SIGNATURE",
    ):
        a = reg[operator_id].execute({"graph": goal.inputs["graph_a"]}, ())
        b = reg[operator_id].execute({"graph": goal.inputs["graph_b"]}, ())
        assert not isinstance(a, OperatorFailure)
        assert not isinstance(b, OperatorFailure)
        signatures.append(a.value != b.value)
    assert any(signatures)


def test_numeric_residual_verifier_obeys_tolerance():
    reg = build_operator_registry()
    candidate = Artifact("cand", "SCALAR", "NUMERICAL", math.pi, "NUMERICAL")
    reference = Artifact("ref", "SCALAR", "NUMERICAL", math.pi + 1e-10, "NUMERICAL")
    result = reg["NUMERIC_RESIDUAL_VERIFY"].execute(
        {"candidate": candidate, "reference": reference}, (("tolerance", 1e-8),)
    )
    assert not isinstance(result, OperatorFailure)
    assert result.value["passed"] is True
    assert result.value["residual"] <= 1e-8
