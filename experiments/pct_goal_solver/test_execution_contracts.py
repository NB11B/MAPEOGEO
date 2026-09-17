from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import (
    Applicability,
    Artifact,
    ArtifactType,
    CandidateLineageObligation,
    InputPort,
    OperatorFailure,
    TargetSpec,
    VerificationResult,
)
from experiments.pct_goal_solver.operators import OperatorSpec, build_operator_registry
from experiments.pct_goal_solver.planner import _registry_digest, enumerate_port_bindings, solve


def _passing_verifier(inputs, output):
    return VerificationResult(True, "TEST_STEP", stage="OPERATOR", subject_id="TEST")


def _always(inputs, bindings):
    return Applicability("APPLICABLE")


def test_operator_ports_are_complete_named_types_and_bind_injectively():
    scalar = ArtifactType("SCALAR", "NUMERICAL", "NUMERICAL")
    spec = OperatorSpec(
        operator_id="PAIR",
        input_ports=(InputPort("left", scalar), InputPort("right", scalar)),
        output=scalar,
        cost=1,
        applicability=_always,
        execute=lambda inputs, bindings: inputs["left"],
        verify=_passing_verifier,
        structural_signature=("PAIR",),
    )
    artifacts = {
        "a": Artifact("a", "SCALAR", "NUMERICAL", 1.0, "NUMERICAL"),
        "b": Artifact("b", "SCALAR", "NUMERICAL", 2.0, "NUMERICAL"),
        "noise": Artifact("noise", "FLOAT_MATRIX", "MATRIX", ((1.0,),), "NUMERICAL"),
    }
    bindings = enumerate_port_bindings(spec, artifacts)
    assert len(bindings) == 2
    assert {tuple(value.artifact_id for value in row.values()) for row in bindings} == {("a", "b"), ("b", "a")}
    assert all(set(row) == {"left", "right"} for row in bindings)
    assert all("noise" not in row for row in bindings)


def test_runtime_output_contract_mismatch_is_rejected_and_recorded():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    registry = build_operator_registry()
    original = registry["MOBIUS_INVERT_BOOLEAN"]

    def wrong_output(inputs, bindings):
        return Artifact("forged", "BOOLEAN_ATOMIC_SIGNAL", "WRONG_REPRESENTATION", (0,) * 16, "EXACT")

    registry[original.operator_id] = replace(original, execute=wrong_output)
    trace = solve(goal, registry, typing_mode="EXPLICIT")
    assert trace.final_verdict != "PASS"
    assert any(event[0] == "OUTPUT_CONTRACT_MISMATCH" for event in trace.falsification_events)
    assert trace.attempted_operator_count > 0
    assert trace.primitive_execution_count > 0


def test_forged_extra_input_and_legacy_evidence_field_are_invalid_contracts():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    forged = Artifact(
        "forged-atomic",
        "BOOLEAN_ATOMIC_SIGNAL",
        "FINITE_LATTICE",
        tuple(range(16)),
        "EXACT",
        provenance=("MOBIUS_INVERT_BOOLEAN", "ZETA_TRANSFORM_BOOLEAN"),
    )
    visible = replace(
        goal,
        inputs={"cumulative": goal.inputs["cumulative"], "forged": forged},
        constraints=goal.constraints + (("required_derived_types", ("BOOLEAN_ZETA_SIGNAL",)),),
    )
    trace = solve(visible, {}, typing_mode="EXPLICIT")
    assert trace.final_verdict == "INVALID"
    assert trace.candidate_artifact is None
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_CONTRACT"


def test_full_target_contract_rejects_wrong_representation_exactness_and_objective():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    registry = build_operator_registry()
    for target in (
        replace(goal.target, representation_class="WRONG"),
        replace(goal.target, exactness_class="NUMERICAL"),
        replace(goal.target, objective="UNDECLARED_OBJECTIVE"),
    ):
        trace = solve(replace(goal, target=target), registry, typing_mode="EXPLICIT")
        assert trace.final_verdict != "PASS"


def test_unknown_required_verifier_class_fails_closed():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    trace = solve(
        replace(goal, required_verifier_class="DOES_NOT_EXIST"),
        build_operator_registry(),
        typing_mode="EXPLICIT",
    )
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "UNKNOWN_VERIFIER_CLASS"


def test_target_like_extra_root_cannot_enter_a_closed_historical_contract():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    bad = Artifact(
        "aaa-bad",
        goal.target.semantic_type,
        goal.target.representation_class,
        tuple(999 for _ in range(16)),
        goal.target.exactness_class or "EXACT",
    )
    trace = solve(replace(goal, inputs={"bad": bad, **goal.inputs}), build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "INVALID"
    assert trace.candidate_artifact is None
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_CONTRACT"


def test_equal_valued_distinct_roots_survive_state_identity():
    goal = next(
        g for g in goals_for("SEALED", "G5")
        if not g.sealed_expected_result["distinct"]
    ).solver_visible()
    trace = solve(goal, build_operator_registry(), typing_mode="EXPLICIT")
    assert {record.input_key for record in trace.root_origins} >= {"graph_a", "graph_b"}
    assert len({record.instance_id for record in trace.root_origins if record.input_key in {"graph_a", "graph_b"}}) == 2


def test_failure_trace_retains_attempted_work_and_structured_causes():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    only = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]

    def fail(inputs, bindings):
        return OperatorFailure("INVALID", "deliberate", only.operator_id)

    trace = solve(goal, {only.operator_id: replace(only, execute=fail)}, typing_mode="EXPLICIT")
    assert trace.final_verdict in {"INVALID", "NOT_ESTABLISHED"}
    assert trace.operator_path == (only.operator_id,)
    assert trace.attempted_operator_count == 1
    assert trace.primitive_execution_count == 1
    assert trace.falsification_events


def test_exact_large_integer_does_not_overflow_finiteness_adapter():
    from experiments.pct_goal_solver.verifiers import finite_numeric

    assert finite_numeric(10**1000)


def test_compatibility_routing_does_not_mutate_blinded_input_mapping():
    from experiments.pct_goal_solver.compatibility import CompatibilityModel
    from experiments.pct_goal_solver.goals import build_goal_corpus

    corpus = build_goal_corpus()
    registry = build_operator_registry()
    calibration_traces = [solve(g.solver_visible(), registry) for g in corpus["CALIBRATION"]]
    model = CompatibilityModel.fit(corpus["CALIBRATION"], calibration_traces, registry)
    visible = goals_for("SEALED", "G8")[0].solver_visible()
    blinded = {
        key: replace(value, semantic_type="BLINDED_INPUT_TYPE")
        for key, value in visible.inputs.items()
    }
    snapshot = dict(blinded)
    decision = model.routing_decision(blinded, registry)
    assert blinded == snapshot
    assert decision.ordered_operator_ids
    assert dict(decision.inferred_root_types)["trajectory"].semantic_type == "NUMERIC_TRAJECTORY"

    forged = {
        key: replace(value, provenance=("FORGED_DERIVATION",))
        for key, value in blinded.items()
    }
    forged_decision = model.routing_decision(forged, registry)
    assert dict(forged_decision.inferred_root_types) == dict(decision.inferred_root_types)


def test_operator_cannot_mutate_root_or_terminal_verification_problem():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = tuple(goal.inputs["cumulative"].value)
    mutable = list(original)
    goal = replace(goal, inputs={"cumulative": replace(goal.inputs["cumulative"], value=mutable)})
    base = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]

    def mutate_input(inputs, bindings):
        inputs["cumulative"].value[:] = [0] * len(inputs["cumulative"].value)
        return OperatorFailure("INVALID", "attempted mutation", "AAA_MUTATE")

    mutator = OperatorSpec(
        operator_id="AAA_MUTATE",
        input_ports=base.input_ports,
        output=ArtifactType("IRRELEVANT", "TEST", "EXACT"),
        cost=1,
        applicability=_always,
        execute=mutate_input,
        verify=_passing_verifier,
        structural_signature=("MUTATION_TEST",),
    )
    trace = solve(goal, {"AAA_MUTATE": mutator, base.operator_id: base})
    assert tuple(mutable) == original
    assert trace.final_verdict == "PASS"
    assert trace.candidate_artifact is not None
    assert tuple(trace.candidate_artifact.value) != (0,) * len(original)


def test_required_verifier_class_cannot_be_relabelled():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    trace = solve(
        replace(goal, required_verifier_class="GRAPH_ISOMORPHISM_CONTROL"),
        build_operator_registry(),
    )
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "VERIFIER_CONTRACT_MISMATCH"


def test_candidate_cannot_borrow_derived_obligation_from_unrelated_root():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    evidence_type = ArtifactType("EVIDENCE", "CERTIFICATE", "EXACT")
    evidence = OperatorSpec(
        operator_id="UNRELATED_EVIDENCE",
        input_ports=(InputPort("noise", ArtifactType("SCALAR", "NUMERICAL", "NUMERICAL")),),
        output=evidence_type,
        cost=1,
        applicability=_always,
        execute=lambda inputs, bindings: Artifact("evidence", "EVIDENCE", "CERTIFICATE", True, "EXACT"),
        verify=_passing_verifier,
        structural_signature=("UNRELATED",),
    )
    visible = replace(
        goal,
        inputs={**goal.inputs, "noise": Artifact("noise", "SCALAR", "NUMERICAL", 7.0, "NUMERICAL")},
        constraints=goal.constraints + (("required_derived_types", ("EVIDENCE",)),),
        lineage_obligation=CandidateLineageObligation(
            required_input_keys=frozenset({"cumulative"}),
            ordered_stage_types=(evidence_type,),
        ),
        search_budget=100,
    )
    mobius = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]
    trace = solve(visible, {mobius.operator_id: mobius, evidence.operator_id: evidence})
    assert trace.final_verdict != "PASS"
    assert trace.candidate_artifact is None


def test_lineage_obligation_cannot_smuggle_an_undeclared_root_into_a_closed_goal():
    import math

    goal = goals_for("SEALED", "G1")[0].solver_visible()
    mid_type = ArtifactType("MID", "SYMBOLIC", "SYMBOLIC")
    zeta_type = ArtifactType("BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", "EXACT")
    atomic_type = ArtifactType("BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "EXACT")

    def unrelated_mid(inputs, bindings):
        return Artifact("mid", "MID", "SYMBOLIC", inputs["noise"].value, "SYMBOLIC")

    def terminal(inputs, bindings):
        values = list(inputs["zeta"].value)
        rank = int(round(math.log2(len(values))))
        for bit in range(rank):
            for mask in range(len(values)):
                if mask & (1 << bit):
                    values[mask] -= values[mask ^ (1 << bit)]
        return Artifact("answer", "BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", tuple(values), "EXACT")

    registry = {
        "UNRELATED_MID": OperatorSpec(
            "UNRELATED_MID",
            (InputPort("noise", ArtifactType("SCALAR", "NUMERICAL", "NUMERICAL")),),
            mid_type,
            1,
            _always,
            unrelated_mid,
            _passing_verifier,
            ("MID",),
        ),
        "LATE_JOIN_TERMINAL": OperatorSpec(
            "LATE_JOIN_TERMINAL",
            (InputPort("mid", mid_type), InputPort("zeta", zeta_type)),
            atomic_type,
            1,
            _always,
            terminal,
            _passing_verifier,
            ("TERMINAL",),
            objectives=("RECOVER",),
        ),
    }
    visible = replace(
        goal,
        inputs={**goal.inputs, "noise": Artifact("noise", "SCALAR", "NUMERICAL", 3.0, "NUMERICAL")},
        lineage_obligation=CandidateLineageObligation(
            required_input_keys=frozenset({"cumulative"}),
            ordered_stage_types=(mid_type,),
            stage_required_input_keys=(frozenset({"cumulative"}),),
        ),
        search_budget=32,
    )
    trace = solve(visible, registry)
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_CONTRACT"


def test_uncertified_macro_is_ignored_by_authoritative_execution():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    registry = build_operator_registry()
    fake = SimpleNamespace(macro_id="FORGED", primitive_ids=("MOBIUS_INVERT_BOOLEAN",))
    primitive = solve(goal, registry)
    assert solve(goal, registry, macros=(fake,)) == primitive


def test_macro_cannot_rescue_path_beyond_primitive_search_budget():
    import math

    mid = ArtifactType("MID", "SYMBOLIC", "SYMBOLIC")
    zeta = ArtifactType("BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", "EXACT")
    atomic = ArtifactType("BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "EXACT")

    def lift(inputs, bindings):
        return Artifact("mid", "MID", "SYMBOLIC", tuple(inputs["zeta"].value), "SYMBOLIC")

    def finish(inputs, bindings):
        values = list(inputs["mid"].value)
        rank = int(round(math.log2(len(values))))
        for bit in range(rank):
            for mask in range(len(values)):
                if mask & (1 << bit):
                    values[mask] -= values[mask ^ (1 << bit)]
        return Artifact("answer", "BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", tuple(values), "EXACT")

    registry = {
        "LIFT": OperatorSpec("LIFT", (InputPort("zeta", zeta),), mid, 1, _always, lift, _passing_verifier, ("LIFT",)),
        "FINISH": OperatorSpec(
            "FINISH",
            (InputPort("mid", mid),),
            atomic,
            1,
            _always,
            finish,
            _passing_verifier,
            ("FINISH",),
            objectives=("RECOVER",),
        ),
    }
    goal = replace(goals_for("SEALED", "G1")[0].solver_visible(), search_budget=2)
    primitive = solve(goal, registry)
    fake = SimpleNamespace(macro_id="FORGED", primitive_ids=("LIFT", "FINISH"))
    synthesized = solve(goal, registry, macros=(fake,))
    assert primitive.final_verdict == "NOT_ESTABLISHED"
    assert synthesized == primitive


def test_inferred_tie_is_permutation_invariant_fail_closed():
    from experiments.pct_goal_solver.compatibility import CompatibilityModel
    from experiments.pct_goal_solver.goals import build_goal_corpus

    corpus = build_goal_corpus()
    registry = build_operator_registry()
    model = CompatibilityModel.fit(
        corpus["CALIBRATION"],
        [solve(goal.solver_visible(), registry) for goal in corpus["CALIBRATION"]],
        registry,
    )
    goal = goals_for("SEALED", "G3")[0].solver_visible()
    blinded = {key: replace(value, semantic_type="BLINDED_INPUT_TYPE") for key, value in goal.inputs.items()}
    traces = [
        solve(replace(goal, inputs=inputs), registry, typing_mode="INFERRED", compatibility_model=model)
        for inputs in (blinded, dict(reversed(tuple(blinded.items()))))
    ]
    assert [trace.final_verdict for trace in traces] == ["INVALID", "INVALID"]
    assert [trace.refusal.code for trace in traces if trace.refusal] == [
        "AMBIGUOUS_TYPE_INFERENCE",
        "AMBIGUOUS_TYPE_INFERENCE",
    ]
    assert traces[0].routing_receipt == traces[1].routing_receipt


def test_registry_digest_binds_callable_implementations():
    registry = build_operator_registry()
    tampered = dict(registry)
    original = tampered["MOBIUS_INVERT_BOOLEAN"]
    tampered[original.operator_id] = replace(
        original,
        execute=lambda inputs, bindings: OperatorFailure("ERROR", "tampered", original.operator_id),
    )
    assert _registry_digest(registry) != _registry_digest(tampered)


def test_comparison_candidates_have_verified_derivation_steps():
    registry = build_operator_registry()
    for family in ("G4", "G5"):
        trace = solve(goals_for("SEALED", family)[0].solver_visible(), registry)
        assert trace.final_verdict == "PASS"
        assert trace.candidate_lineage is not None
        assert trace.candidate_lineage.stage_instance_ids == ()
        assert trace.derived_obligations == ()
        assert any(
            step.output_instance_id == trace.candidate_lineage.candidate_instance_id
            for step in trace.derivations
        )


def test_structured_refusals_preserve_precise_code_and_operator():
    goal = goals_for("SEALED", "G1")[0].solver_visible()
    original = build_operator_registry()["MOBIUS_INVERT_BOOLEAN"]
    unsafe = replace(
        original,
        execute=lambda inputs, bindings: OperatorFailure("NUMERICALLY_UNSAFE", "unstable", original.operator_id),
    )
    trace = solve(goal, {unsafe.operator_id: unsafe})
    assert trace.final_verdict == "NOT_ESTABLISHED"
    assert trace.refusal is not None
    assert trace.refusal.code == "NUMERICALLY_UNSAFE"
    assert trace.refusal.operator_id == unsafe.operator_id

    broken = replace(original, applicability=lambda inputs, bindings: (_ for _ in ()).throw(RuntimeError("boom")))
    trace = solve(goal, {broken.operator_id: broken})
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "APPLICABILITY_ERROR"
    assert trace.refusal.operator_id == broken.operator_id


def test_noncanonical_root_is_a_structured_invalid_result_not_an_exception():
    import sympy as sp

    goal = goals_for("SEALED", "G12")[0].solver_visible()
    inputs = dict(goal.inputs)
    inputs["lhs"] = replace(inputs["lhs"], value=sp.oo)
    trace = solve(replace(goal, inputs=inputs), build_operator_registry())
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "NONCANONICAL_ROOT"
