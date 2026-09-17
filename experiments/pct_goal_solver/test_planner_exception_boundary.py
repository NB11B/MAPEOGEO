from __future__ import annotations

from copy import deepcopy as real_deepcopy
from dataclasses import replace

import pytest

from experiments.pct_goal_solver import planner as planner_module
from experiments.pct_goal_solver.compatibility import CompatibilityModel
from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import (
    Applicability,
    Artifact,
    OperatorFailure,
    VerificationResult,
)
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve


class _ToxicTextError(RuntimeError):
    def __str__(self) -> str:
        raise RuntimeError("exception text must not escape the planner boundary")


class _ToxicText:
    def __str__(self) -> str:
        raise RuntimeError("result text must not escape the planner boundary")


@pytest.mark.parametrize(
    ("field", "expected_code"),
    (
        ("applicability", "APPLICABILITY_ERROR"),
        ("execute", "EXECUTION_ERROR"),
        ("verify", "VERIFIER_ERROR"),
    ),
)
def test_unprintable_operator_exception_fails_closed(field: str, expected_code: str):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]

    def raise_unprintable(*args, **kwargs):
        raise _ToxicTextError()

    toxic = replace(original, **{field: raise_unprintable})
    trace = solve(goal, {toxic.operator_id: toxic})

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == expected_code
    assert trace.refusal.reason == "exception message unavailable"


def test_unprintable_root_deepcopy_exception_fails_closed(monkeypatch: pytest.MonkeyPatch):
    goal = goals_for("SEALED", "G1")[0].solver_visible()

    def raise_unprintable(value):
        raise _ToxicTextError()

    monkeypatch.setattr(planner_module, "deepcopy", raise_unprintable)
    trace = solve(goal, build_operator_registry())

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "NONCANONICAL_ROOT"
    assert trace.refusal.reason == "exception message unavailable"


@pytest.mark.parametrize(
    ("boundary", "expected_code"),
    (
        ("applicability_input", "APPLICABILITY_ERROR"),
        ("execution_input", "EXECUTION_ERROR"),
        ("operator_output", "NONCANONICAL_OPERATOR_EVIDENCE"),
        ("verifier_input", "VERIFIER_ERROR"),
    ),
)
def test_unprintable_deepcopy_exception_at_operator_boundaries_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    expected_code: str,
):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]
    top_level_mapping_calls = 0

    def toxic_deepcopy(value):
        nonlocal top_level_mapping_calls
        if type(value) is dict:
            top_level_mapping_calls += 1
            mapping_boundary = {
                2: "applicability_input",
                3: "execution_input",
            }.get(top_level_mapping_calls)
            if mapping_boundary == boundary:
                raise _ToxicTextError()
        if boundary == "operator_output" and type(value) is Artifact:
            raise _ToxicTextError()
        if (
            boundary == "verifier_input"
            and type(value) is tuple
            and value
            and all(type(item) is Artifact for item in value)
        ):
            raise _ToxicTextError()
        return real_deepcopy(value)

    monkeypatch.setattr(planner_module, "deepcopy", toxic_deepcopy)
    trace = solve(goal, {original.operator_id: original})

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == expected_code
    assert "exception message unavailable" in trace.refusal.reason


@pytest.mark.parametrize(
    ("domain", "expected_code"),
    (
        ("pct-applicability-input-v1", "APPLICABILITY_ERROR"),
        ("pct-execution-input-v1", "EXECUTION_ERROR"),
        ("pct-operator-output-evidence-v1", "NONCANONICAL_OPERATOR_EVIDENCE"),
        ("pct-verifier-input-v1", "VERIFIER_ERROR"),
        ("pct-operator-verifier-evidence-v1", "NONCANONICAL_OPERATOR_EVIDENCE"),
    ),
)
def test_unprintable_canonicalization_exception_at_operator_boundaries_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    domain: str,
    expected_code: str,
):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]
    real_digest = planner_module._invocation_digest

    def toxic_digest(value, *, domain: str):
        if domain == target_domain:
            raise _ToxicTextError()
        return real_digest(value, domain=domain)

    target_domain = domain
    monkeypatch.setattr(planner_module, "_invocation_digest", toxic_digest)
    trace = solve(goal, {original.operator_id: original})

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == expected_code
    assert "exception message unavailable" in trace.refusal.reason


def test_unprintable_terminal_verifier_exception_fails_closed(monkeypatch: pytest.MonkeyPatch):
    goal = goals_for("SEALED", "G1")[0].solver_visible()

    def raise_unprintable(*args, **kwargs):
        raise _ToxicTextError()

    monkeypatch.setattr(planner_module, "_verify_goal", raise_unprintable)
    trace = solve(goal, build_operator_registry())

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "TERMINAL_VERIFIER_ERROR"
    assert trace.refusal.reason == "exception message unavailable"


def test_unprintable_routing_exception_and_refusal_code_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    model = CompatibilityModel(frozenset(), {}, {}, {}, {}, {})

    class ToxicRoutingError(_ToxicTextError):
        @property
        def refusal_code(self):
            raise _ToxicTextError()

    def raise_unprintable(self, inputs, registry):
        raise ToxicRoutingError()

    monkeypatch.setattr(CompatibilityModel, "routing_decision", raise_unprintable)
    trace = solve(
        goal,
        build_operator_registry(),
        typing_mode="INFERRED",
        compatibility_model=model,
    )

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "ROUTING_ERROR"
    assert trace.refusal.reason == "exception message unavailable"


def test_exception_text_is_bounded():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]

    def raise_long_message(*args, **kwargs):
        raise RuntimeError("x" * 10_000)

    toxic = replace(original, execute=raise_long_message)
    trace = solve(goal, {toxic.operator_id: toxic})

    assert trace.refusal is not None
    assert len(trace.refusal.reason) == planner_module._MAX_EXCEPTION_TEXT_LENGTH
    assert trace.refusal.reason.endswith("...[truncated]")


@pytest.mark.parametrize(
    ("field", "result_factory", "expected_code"),
    (
        (
            "applicability",
            lambda operator_id: Applicability("NOT_APPLICABLE", _ToxicText()),
            "APPLICABILITY_ERROR",
        ),
        (
            "execute",
            lambda operator_id: OperatorFailure(
                "NOT_APPLICABLE",
                _ToxicText(),
                operator_id,
            ),
            "EXECUTION_INVALID",
        ),
        (
            "verify",
            lambda operator_id: VerificationResult(
                False,
                "TEST_VERIFIER",
                _ToxicText(),
            ),
            "VERIFIER_ERROR",
        ),
    ),
)
def test_unprintable_operator_result_fields_fail_closed(
    field: str,
    result_factory,
    expected_code: str,
):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]

    def toxic_result(*args, **kwargs):
        return result_factory(original.operator_id)

    toxic = replace(original, **{field: toxic_result})
    trace = solve(goal, {toxic.operator_id: toxic})

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == expected_code
    assert type(trace.refusal.reason) is str


def test_unprintable_terminal_verifier_result_fields_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    monkeypatch.setattr(
        planner_module,
        "_verify_goal",
        lambda goal, candidate: VerificationResult(
            False,
            "TEST_TERMINAL",
            _ToxicText(),
        ),
    )

    trace = solve(goal, build_operator_registry())

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "TERMINAL_VERIFIER_ERROR"
    assert trace.refusal.reason == "invalid terminal verifier result fields"


def test_oversized_untrusted_result_text_is_rejected():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]
    toxic = replace(
        original,
        applicability=lambda inputs, bindings: Applicability(
            "NOT_APPLICABLE",
            "x" * 10_000,
        ),
    )

    trace = solve(goal, {toxic.operator_id: toxic})

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "APPLICABILITY_ERROR"
    assert trace.refusal.reason == "invalid applicability result fields"
