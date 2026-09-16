from __future__ import annotations

from dataclasses import dataclass, replace
import importlib.metadata
import math

import numpy as np
import pytest
import sympy as sp

from experiments.pct_goal_solver import operators as operator_module
from experiments.pct_goal_solver import planner as planner_module
from experiments.pct_goal_solver.canonical import CanonicalizationError, canonical_bytes
from experiments.pct_goal_solver.compatibility import (
    CompatibilityModel,
    _contextual_artifact_descriptors,
)
from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.lineage import derive_artifact, track_roots
from experiments.pct_goal_solver.model import (
    Applicability,
    Artifact,
    ArtifactType,
    CandidateLineageObligation,
    InputPort,
    VerificationResult,
)
from experiments.pct_goal_solver.operators import (
    OperatorSpec,
    build_operator_registry,
    callable_contract_digest,
    operator_registry_digest,
)
from experiments.pct_goal_solver.planner import (
    _candidate_obligations,
    _has_equivalent,
    _registry_digest,
    solve,
)


def _always(inputs, bindings):
    return Applicability("APPLICABLE")


def _passes(inputs, output):
    return VerificationResult(True, "TEST_STEP")


def _artifact(
    artifact_id: str,
    artifact_type: ArtifactType,
    value,
) -> Artifact:
    return Artifact(
        artifact_id,
        artifact_type.semantic_type,
        artifact_type.representation_class,
        value,
        artifact_type.exactness_class,
    )


def test_canonicalization_rejects_builtin_subclasses_and_unapproved_dataclasses():
    class LyingInt(int):
        def __str__(self) -> str:
            return "0"

    @dataclass(frozen=True)
    class UnapprovedEvidence:
        value: int

    assert canonical_bytes(0) != canonical_bytes(99)
    with pytest.raises(CanonicalizationError, match="unsupported evidence type"):
        canonical_bytes(LyingInt(99))
    with pytest.raises(CanonicalizationError, match="unapproved dataclass"):
        canonical_bytes(UnapprovedEvidence(3))


def test_canonicalization_rejects_spoofed_library_scalar_and_symbol_types():
    class FakeNumpyInt(np.int64):
        pass

    class FakeSymbol(sp.Symbol):
        pass

    FakeNumpyInt.__module__ = "numpy"
    FakeSymbol.__module__ = "sympy.core.symbol"

    with pytest.raises(CanonicalizationError, match="unsupported evidence type"):
        canonical_bytes(FakeNumpyInt(3))
    with pytest.raises(CanonicalizationError, match="unsupported evidence type"):
        canonical_bytes(FakeSymbol("x"))


def test_callable_contract_binds_closure_cells_live_code_helpers_and_dependency_versions(
    monkeypatch: pytest.MonkeyPatch,
):
    def factory(value: int):
        def execute(inputs, bindings):
            return value

        return execute

    assert callable_contract_digest(factory(1), implementation_id="same") != callable_contract_digest(
        factory(99), implementation_id="same"
    )

    def external_helper_a():
        return 1

    def external_helper_b():
        return 2

    def use_helper(helper):
        def execute(inputs, bindings):
            return helper()

        return execute

    external_helper_a.__module__ = "third_party_fake"
    wrapped = use_helper(external_helper_a)
    before_external_code_change = callable_contract_digest(wrapped, implementation_id="external")
    original_external_code = external_helper_a.__code__
    try:
        external_helper_a.__code__ = external_helper_b.__code__
        assert callable_contract_digest(wrapped, implementation_id="external") != before_external_code_change
    finally:
        external_helper_a.__code__ = original_external_code

    baseline = _registry_digest(build_operator_registry())
    original_mobius = operator_module._mobius
    monkeypatch.setattr(
        operator_module,
        "_mobius",
        lambda values: tuple(0 for _ in original_mobius(values)),
    )
    assert _registry_digest(build_operator_registry()) != baseline
    monkeypatch.setattr(operator_module, "_mobius", original_mobius)

    baseline = _registry_digest(build_operator_registry())
    original_comparison_verifier = planner_module._verify_comparison_candidate
    monkeypatch.setattr(
        planner_module,
        "_verify_comparison_candidate",
        lambda goal, artifacts, output: VerificationResult(False, "TAMPERED"),
    )
    assert _registry_digest(build_operator_registry()) != baseline
    monkeypatch.setattr(
        planner_module,
        "_verify_comparison_candidate",
        original_comparison_verifier,
    )

    scalar = ArtifactType("SCALAR", "TEST", "EXACT")

    def execute_a(inputs, bindings):
        return _artifact("a", scalar, 1)

    def execute_b(inputs, bindings):
        return _artifact("b", scalar, 2)

    spec = OperatorSpec("LIVE", (), scalar, 1, _always, execute_a, _passes, ("LIVE",))
    live_registry = {spec.operator_id: spec}
    before_code_change = operator_registry_digest(live_registry)
    original_code = execute_a.__code__
    try:
        execute_a.__code__ = execute_b.__code__
        assert operator_registry_digest(live_registry) != before_code_change
    finally:
        execute_a.__code__ = original_code

    baseline = operator_registry_digest(build_operator_registry())
    real_version = importlib.metadata.version
    monkeypatch.setattr(
        importlib.metadata,
        "version",
        lambda name: "0+tampered" if name == "numpy" else real_version(name),
    )
    assert operator_registry_digest(build_operator_registry()) != baseline


def test_lineage_stages_must_form_one_ancestral_dag_path():
    root_type = ArtifactType("ROOT", "TEST", "EXACT")
    stage_a_type = ArtifactType("STAGE_A", "TEST", "EXACT")
    stage_b_type = ArtifactType("STAGE_B", "TEST", "EXACT")
    terminal_type = ArtifactType("TERMINAL", "TEST", "EXACT")
    root = dict(track_roots({"root": _artifact("root", root_type, 1)}))["root"]
    verified = VerificationResult(True, "TEST", stage="OPERATOR", subject_id="TEST")
    stage_a, step_a = derive_artifact(
        operator_id="A",
        output=_artifact("a", stage_a_type, 1),
        bound_inputs={"root": root},
        verifier=verified,
    )
    stage_b, step_b = derive_artifact(
        operator_id="B",
        output=_artifact("b", stage_b_type, 1),
        bound_inputs={"root": root},
        verifier=verified,
    )
    joined, step_join = derive_artifact(
        operator_id="JOIN",
        output=_artifact("joined", terminal_type, 1),
        bound_inputs={"a": stage_a, "b": stage_b},
        verifier=verified,
    )
    goal = replace(
        goals_for("SEALED", "G1")[0].solver_visible(),
        lineage_obligation=CandidateLineageObligation(
            required_input_keys=frozenset({"root"}),
            ordered_stage_types=(stage_a_type, stage_b_type),
            stage_required_input_keys=(frozenset({"root"}), frozenset({"root"})),
        ),
    )
    assert _candidate_obligations(goal, joined, (step_a, step_b, step_join)) is None


def test_dedup_lineage_progress_uses_a_real_dag_path_not_flattened_siblings():
    root_type = ArtifactType("ROOT", "TEST", "EXACT")
    stage_a_type = ArtifactType("STAGE_A", "TEST", "EXACT")
    stage_b_type = ArtifactType("STAGE_B", "TEST", "EXACT")
    terminal_type = ArtifactType("TERMINAL", "TEST", "EXACT")
    root = dict(track_roots({"root": _artifact("root", root_type, 1)}))["root"]
    verified = VerificationResult(True, "TEST", stage="OPERATOR", subject_id="TEST")
    stage_a, _ = derive_artifact(
        operator_id="A",
        output=_artifact("a", stage_a_type, 1),
        bound_inputs={"root": root},
        verifier=verified,
    )
    sibling_b, _ = derive_artifact(
        operator_id="B_SIBLING",
        output=_artifact("b-sibling", stage_b_type, 1),
        bound_inputs={"root": root},
        verifier=verified,
    )
    false_progress, _ = derive_artifact(
        operator_id="JOIN",
        output=_artifact("same-output-a", terminal_type, 1),
        bound_inputs={"a": stage_a, "b": sibling_b},
        verifier=verified,
    )
    chained_b, _ = derive_artifact(
        operator_id="B_CHAINED",
        output=_artifact("b-chained", stage_b_type, 1),
        bound_inputs={"a": stage_a},
        verifier=verified,
    )
    real_progress, _ = derive_artifact(
        operator_id="FINISH",
        output=_artifact("same-output-b", terminal_type, 1),
        bound_inputs={"b": chained_b},
        verifier=verified,
    )
    goal = replace(
        goals_for("SEALED", "G1")[0].solver_visible(),
        lineage_obligation=CandidateLineageObligation(
            required_input_keys=frozenset({"root"}),
            ordered_stage_types=(stage_a_type, stage_b_type),
            stage_required_input_keys=(frozenset({"root"}), frozenset({"root"})),
        ),
    )
    state = {
        "root": root,
        "a": stage_a,
        "b-sibling": sibling_b,
        "false-progress": false_progress,
        "b-chained": chained_b,
    }
    assert not _has_equivalent(goal, real_progress, state)


@pytest.mark.parametrize("family", ["G4", "G5"])
def test_planner_comparison_contract_cannot_be_relabelled(family: str):
    goal = goals_for("SEALED", family)[0].solver_visible()
    relabelled = replace(
        goal,
        target=replace(
            goal.target,
            semantic_type="ARBITRARY_UNREGISTERED_TARGET",
            objective="UNDECLARED_OBJECTIVE",
        ),
    )
    trace = solve(relabelled, build_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "GOAL_TARGET_CONTRACT_MISMATCH"


@pytest.mark.parametrize("search_budget", [2.5, True, "8"])
def test_goal_schema_rejects_non_integer_search_budgets_without_raising(search_budget):
    goal = replace(goals_for("SEALED", "G1")[0].solver_visible(), search_budget=search_budget)
    trace = solve(goal, build_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


def test_goal_schema_is_checked_before_snapshot_normalization():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    for malformed in (
        replace(goal, inputs=list(goal.inputs.items())),
        replace(goal, constraints=list(goal.constraints)),
    ):
        trace = solve(malformed, build_operator_registry())
        assert trace.final_verdict == "INVALID"
        assert trace.refusal is not None
        assert trace.refusal.code == "INVALID_GOAL_SCHEMA"

    trace = solve(object(), build_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


def test_goal_schema_rejects_tampered_exactness_and_lineage_shapes():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    bad_input = replace(goal.inputs["cumulative"])
    object.__setattr__(bad_input, "exactness_class", "UNREGISTERED")
    bad_target = replace(goal.target)
    object.__setattr__(bad_target, "exactness_class", 3)
    obligation = CandidateLineageObligation(
        required_input_keys=frozenset({"cumulative"}),
        ordered_stage_types=(ArtifactType("MID", "TEST", "EXACT"),),
    )
    object.__setattr__(
        obligation,
        "stage_required_input_keys",
        (frozenset({"cumulative"}), frozenset({"cumulative"})),
    )
    for malformed in (
        replace(goal, inputs={"cumulative": bad_input}),
        replace(goal, target=bad_target),
        replace(goal, lineage_obligation=obligation),
    ):
        trace = solve(malformed, build_operator_registry())
        assert trace.final_verdict == "INVALID"
        assert trace.refusal is not None
        assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


@pytest.mark.parametrize("tolerance", [float("inf"), float("-inf"), float("nan"), -1.0])
def test_goal_schema_rejects_nonfinite_or_negative_tolerance(tolerance: float):
    goal = replace(goals_for("SEALED", "G1")[0].solver_visible(), allowed_numeric_tolerance=tolerance)
    trace = solve(goal, build_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


@pytest.mark.parametrize(
    "metadata",
    [
        (("duplicate", 1), ("duplicate", 2)),
        (("opaque", object()),),
        (("callable", lambda: None),),
    ],
)
def test_goal_schema_rejects_duplicate_or_noncanonical_target_metadata(metadata):
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    trace = solve(
        replace(goal, target=replace(goal.target, metadata=metadata)),
        build_operator_registry(),
    )
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


@pytest.mark.parametrize(
    "constraint",
    [
        ("required_derived_types", 3),
        ("required_derived_types", ("MID", 3)),
        ("samples", True),
        ("tolerance", float("inf")),
        ("levels", ("BARCODE", 3)),
    ],
)
def test_goal_schema_rejects_malformed_known_constraints_without_raising(constraint):
    goal = replace(
        goals_for("SEALED", "G1")[0].solver_visible(),
        constraints=(constraint,),
    )
    trace = solve(goal, build_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


def test_infinite_tolerance_cannot_turn_an_unbounded_g8_candidate_into_pass():
    goal = replace(
        goals_for("SEALED", "G8")[0].solver_visible(),
        allowed_numeric_tolerance=float("inf"),
    )
    original = build_operator_registry()["NUMERIC_RELATION_FIT"]
    forged = replace(
        original,
        execute=lambda inputs, bindings: _artifact("forged", original.output, 1e100),
        verify=_passes,
    )
    trace = solve(goal, {forged.operator_id: forged})
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_SCHEMA"


def test_equivalent_artifact_is_retained_when_it_advances_repeated_lineage_stage():
    zeta_type = ArtifactType("BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", "EXACT")
    mid_type = ArtifactType("MID", "TEST", "EXACT")
    other_type = ArtifactType("OTHER", "TEST", "EXACT")
    atomic_type = ArtifactType("BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "EXACT")

    def copy_as(operator_id: str, output_type: ArtifactType, input_port: str):
        def execute(inputs, bindings):
            return _artifact(operator_id, output_type, tuple(inputs[input_port].value))

        return execute

    def finish(inputs, bindings):
        values = list(inputs["mid"].value)
        rank = int(round(math.log2(len(values))))
        for bit in range(rank):
            for mask in range(len(values)):
                if mask & (1 << bit):
                    values[mask] -= values[mask ^ (1 << bit)]
        return _artifact("answer", atomic_type, tuple(values))

    registry = {
        "A_TO_MID": OperatorSpec(
            "A_TO_MID", (InputPort("zeta", zeta_type),), mid_type, 1, _always,
            copy_as("mid-1", mid_type, "zeta"), _passes, ("MID",),
        ),
        "MID_TO_OTHER": OperatorSpec(
            "MID_TO_OTHER", (InputPort("mid", mid_type),), other_type, 1, _always,
            copy_as("other", other_type, "mid"), _passes, ("OTHER",),
        ),
        "OTHER_TO_MID": OperatorSpec(
            "OTHER_TO_MID", (InputPort("other", other_type),), mid_type, 1, _always,
            copy_as("mid-2", mid_type, "other"), _passes, ("MID",),
        ),
        "MID_TO_ANSWER": OperatorSpec(
            "MID_TO_ANSWER", (InputPort("mid", mid_type),), atomic_type, 1, _always,
            finish, _passes, ("ANSWER",), objectives=("RECOVER",),
        ),
    }
    goal = replace(
        goals_for("SEALED", "G1")[0].solver_visible(),
        lineage_obligation=CandidateLineageObligation(
            required_input_keys=frozenset({"cumulative"}),
            ordered_stage_types=(mid_type, other_type, mid_type),
            stage_required_input_keys=(
                frozenset({"cumulative"}),
                frozenset({"cumulative"}),
                frozenset({"cumulative"}),
            ),
        ),
        search_budget=128,
    )
    trace = solve(goal, registry)
    assert trace.final_verdict == "PASS"
    assert [row.semantic_type for row in trace.derived_obligations] == ["MID", "OTHER", "MID"]


def test_joint_capacity_assignment_reports_equal_optimum_ambiguity_permutation_invariant():
    roots = {
        "left": Artifact("left", "BLINDED_INPUT_TYPE", "TEST", 1, "EXACT"),
        "right": Artifact("right", "BLINDED_INPUT_TYPE", "TEST", 1, "EXACT"),
    }
    descriptor = _contextual_artifact_descriptors(roots["left"], roots)
    model = CompatibilityModel(
        goal_ids=frozenset({"calibration"}),
        operator_contexts={},
        operator_support={},
        type_contexts={"TYPE_A": (descriptor,), "TYPE_B": (descriptor | {"extra"},)},
        type_support={"TYPE_A": 1, "TYPE_B": 1},
        type_max_count={"TYPE_A": 1, "TYPE_B": 1},
    )
    first = model.routing_decision(roots, {})
    second = model.routing_decision(dict(reversed(tuple(roots.items()))), {})
    assert first.ambiguous_input_keys == ("left", "right")
    assert first == second


def test_empty_compatibility_model_refuses_inference_instead_of_reusing_labels():
    model = CompatibilityModel(frozenset(), {}, {}, {}, {}, {})
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    trace = solve(
        goal,
        build_operator_registry(),
        typing_mode="INFERRED",
        compatibility_model=model,
    )
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INFEASIBLE_TYPE_INFERENCE"


def test_comparison_work_is_included_in_all_trace_counters(monkeypatch: pytest.MonkeyPatch):
    counts = {
        "primitive_attempts": 0,
        "primitive_executions": 0,
        "primitive_verifiers": 0,
        "comparison_attempts": 0,
        "comparison_outputs": 0,
        "terminal_verifiers": 0,
    }

    def wrap_spec(spec: OperatorSpec) -> OperatorSpec:
        applicability = spec.applicability
        execute = spec.execute
        verify = spec.verify

        def counted_applicability(inputs, bindings):
            counts["primitive_attempts"] += 1
            return applicability(inputs, bindings)

        def counted_execute(inputs, bindings):
            counts["primitive_executions"] += 1
            return execute(inputs, bindings)

        def counted_verify(inputs, output):
            counts["primitive_verifiers"] += 1
            return verify(inputs, output)

        return replace(
            spec,
            applicability=counted_applicability,
            execute=counted_execute,
            verify=counted_verify,
        )

    registry = {key: wrap_spec(spec) for key, spec in build_operator_registry().items()}
    original_comparison = planner_module._comparison_candidate
    original_terminal = planner_module._verify_goal

    def counted_comparison(goal, artifacts):
        counts["comparison_attempts"] += 1
        result = original_comparison(goal, artifacts)
        counts["comparison_outputs"] += result is not None
        return result

    def counted_terminal(goal, candidate):
        counts["terminal_verifiers"] += 1
        return original_terminal(goal, candidate)

    monkeypatch.setattr(planner_module, "_comparison_candidate", counted_comparison)
    monkeypatch.setattr(planner_module, "_verify_goal", counted_terminal)
    trace = solve(goals_for("SEALED", "G5")[0].solver_visible(), registry)
    assert trace.final_verdict == "PASS"
    assert trace.attempted_operator_count == (
        counts["primitive_attempts"] + counts["comparison_attempts"]
    )
    assert trace.primitive_execution_count == (
        counts["primitive_executions"] + counts["comparison_outputs"]
    )
    assert trace.verifier_execution_count == (
        counts["primitive_verifiers"]
        + counts["comparison_outputs"]
        + counts["terminal_verifiers"]
    )


def test_noncanonical_operator_output_is_a_structured_invalid_refusal():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]
    forged = replace(
        original,
        execute=lambda inputs, bindings: _artifact("opaque", original.output, object()),
        verify=_passes,
    )
    trace = solve(goal, {forged.operator_id: forged})
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "NONCANONICAL_OPERATOR_EVIDENCE"
    assert trace.refusal.operator_id == forged.operator_id
