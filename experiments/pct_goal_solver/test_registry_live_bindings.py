from __future__ import annotations

import math

import pytest

from experiments.pct_goal_solver import v0_20_operators as v0_20_operator_module
from experiments.pct_goal_solver.operators import (
    callable_contract_digest,
    operator_registry_digest,
)


def _nested_math_reference(values: tuple[float, ...]) -> tuple[bool, ...]:
    return tuple(math.isfinite(value) for value in values)


def test_registry_digest_changes_after_warm_sympy_attribute_substitution(
    monkeypatch: pytest.MonkeyPatch,
):
    registry = v0_20_operator_module.build_v0_20_operator_registry()
    before = operator_registry_digest(registry)
    assert operator_registry_digest(registry) == before
    original = v0_20_operator_module.sp.srepr

    with monkeypatch.context() as patch:
        patch.setattr(
            v0_20_operator_module.sp,
            "srepr",
            lambda value: f"tampered:{original(value)}",
        )
        after = operator_registry_digest(registry)

    assert after != before
    assert operator_registry_digest(registry) == before


def test_registry_digest_changes_after_warm_math_attribute_substitution(
    monkeypatch: pytest.MonkeyPatch,
):
    registry = v0_20_operator_module.build_v0_20_operator_registry()
    before = operator_registry_digest(registry)
    assert operator_registry_digest(registry) == before

    with monkeypatch.context() as patch:
        patch.setattr(v0_20_operator_module.math, "isfinite", lambda value: True)
        after = operator_registry_digest(registry)

    assert after != before
    assert operator_registry_digest(registry) == before


def test_registry_digest_binds_external_python_attribute_code_in_place():
    registry = v0_20_operator_module.build_v0_20_operator_registry()
    before = operator_registry_digest(registry)
    callable_type = type(v0_20_operator_module.sp.srepr)
    original_code = callable_type.__call__.__code__

    def forged_call(self, *args, **kwargs):
        return "tampered"

    try:
        callable_type.__call__.__code__ = forged_call.__code__
        after = operator_registry_digest(registry)
    finally:
        callable_type.__call__.__code__ = original_code

    assert after != before
    assert operator_registry_digest(registry) == before


def test_nested_code_module_attribute_binding_is_live_and_deterministic(
    monkeypatch: pytest.MonkeyPatch,
):
    implementation_id = "test.nested-math-reference.v1"
    before = callable_contract_digest(
        _nested_math_reference,
        implementation_id=implementation_id,
    )
    assert callable_contract_digest(
        _nested_math_reference,
        implementation_id=implementation_id,
    ) == before

    with monkeypatch.context() as patch:
        patch.setattr(math, "isfinite", lambda value: True)
        after = callable_contract_digest(
            _nested_math_reference,
            implementation_id=implementation_id,
        )

    assert after != before
    assert callable_contract_digest(
        _nested_math_reference,
        implementation_id=implementation_id,
    ) == before


def test_campaign_execution_authority_rejects_a_stale_registry_receipt(
    monkeypatch: pytest.MonkeyPatch,
):
    from experiments.pct_goal_solver import v0_20_campaign as campaign
    from experiments.pct_goal_solver.planner import solve
    from experiments.pct_goal_solver.v0_20_goals import build_v0_20_corpus

    goal = next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == "C1"
    )
    registry = v0_20_operator_module.build_v0_20_operator_registry()
    trace = solve(goal.solver_visible(), registry)
    assert trace.final_verdict == "PASS"
    assert trace.candidate_lineage is not None
    assert campaign._execution_receipt_complete(goal, trace) is True
    stale_registry_digest = trace.candidate_lineage.registry_digest
    original = v0_20_operator_module.sp.srepr

    with monkeypatch.context() as patch:
        patch.setattr(
            v0_20_operator_module.sp,
            "srepr",
            lambda value: f"tampered:{original(value)}",
        )
        live_registry_digest = campaign._planner_registry_digest(
            campaign._authoritative_registry()
        )
        authority_preserved = campaign._execution_receipt_complete(goal, trace)

    assert live_registry_digest != stale_registry_digest
    assert authority_preserved is False
