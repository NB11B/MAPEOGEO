from __future__ import annotations

from dataclasses import asdict, replace
from fractions import Fraction

import sympy as sp
import pytest

from experiments.pct_goal_solver import v0_20_campaign as campaign
from experiments.pct_goal_solver.campaign_oracles import (
    build_independent_oracle,
    candidate_matches_independent_oracle,
)
from experiments.pct_goal_solver.goal_verifiers import verify_historical_goal
from experiments.pct_goal_solver.historical_oracles import (
    historical_candidate_satisfies_reference,
)
from experiments.pct_goal_solver.model import Artifact
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.rigorous_math import certify_cauchy_riemann
from experiments.pct_goal_solver.rigorous_math import QuadraticMeanValueCertificate
from experiments.pct_goal_solver.v0_20_goals import build_case_oracle, build_v0_20_corpus
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry
from experiments.pct_goal_solver.v0_20_verifiers import (
    validate_v0_20_goal_contract,
    verify_v0_20_goal,
)


def _goal(family: str):
    return next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == family
    )


def _trace(family: str):
    goal = _goal(family)
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert trace.final_verdict == "PASS"
    return goal, trace


def test_strict_family_oracles_accept_the_new_root_contracts() -> None:
    for family in ("F1", "F2", "F3", "C1", "C2", "X1"):
        goal = _goal(family)
        oracle = build_independent_oracle(
            family=family,
            inputs={key: artifact.value for key, artifact in goal.inputs.items()},
            constraints=dict(goal.constraints),
            tolerance=goal.allowed_numeric_tolerance,
        )
        assert oracle.authoritative is True, family
        assert oracle.availability == "AVAILABLE", family
        assert oracle.expected_verdict == "PASS", family
        assert oracle.certificate is not None, family


def test_x2_oracle_gap_is_explicit_and_keeps_status_evidence_partial() -> None:
    goal = _goal("X2")
    oracle = build_independent_oracle(
        family=goal.family,
        inputs={key: artifact.value for key, artifact in goal.inputs.items()},
        constraints=dict(goal.constraints),
        tolerance=goal.allowed_numeric_tolerance,
    )
    assert oracle.authoritative is False
    assert oracle.availability == "UNAVAILABLE"
    assert oracle.reason == "NO_INDEPENDENT_X2_ORACLE"

    gates = {key: True for key in campaign.EXPECTED_GATE_KEYS}
    gates["independent_oracles_complete"] = False
    assert campaign.classify_scientific_status(gates) == "EVIDENCE_PARTIAL"


def test_campaign_uses_the_bounded_independent_historical_references() -> None:
    sealed = build_v0_20_corpus()["SEALED_V0_20"]
    historical = [goal for goal in sealed if goal.family.startswith("G")]
    assert len(historical) == 24
    for goal in historical:
        oracle = campaign._build_campaign_oracle(goal)
        assert oracle["authoritative"] is True, goal.goal_id
        assert oracle["oracle_availability"] == "AVAILABLE", goal.goal_id
        assert oracle["expected_verdict"] in {"PASS", "NOT_APPLICABLE"}, goal.goal_id


def test_implementation_manifest_requires_the_strict_evidence_modules() -> None:
    manifest = campaign.build_implementation_manifest()
    paths = {row["path"] for row in manifest["files"]}
    assert manifest["complete"] is True
    assert paths == {
        "experiments/__init__.py",
        "experiments/pct_goal_solver/__init__.py",
        "experiments/pct_goal_solver/model.py",
        "experiments/pct_goal_solver/canonical.py",
        "experiments/pct_goal_solver/lineage.py",
        "experiments/pct_goal_solver/planner.py",
        "experiments/pct_goal_solver/operators.py",
        "experiments/pct_goal_solver/verifiers.py",
        "experiments/pct_goal_solver/compatibility.py",
        "experiments/pct_goal_solver/macros.py",
        "experiments/pct_goal_solver/campaign.py",
        "experiments/pct_goal_solver/goals.py",
        "experiments/pct_goal_solver/goal_verifiers.py",
        "experiments/pct_goal_solver/historical_oracles.py",
        "experiments/pct_goal_solver/bridge_operators.py",
        "experiments/pct_goal_solver/v0_20_goals.py",
        "experiments/pct_goal_solver/v0_20_contracts.py",
        "experiments/pct_goal_solver/v0_20_operators.py",
        "experiments/pct_goal_solver/v0_20_macros.py",
        "experiments/pct_goal_solver/v0_20_verifiers.py",
        "experiments/pct_goal_solver/v0_20_terminal_verification.py",
        "experiments/pct_goal_solver/rigorous_math.py",
        "experiments/pct_goal_solver/elliptic_periods.py",
        "experiments/pct_goal_solver/shortcut_proof.py",
        "experiments/pct_goal_solver/campaign_oracles.py",
        "experiments/pct_goal_solver/repaired_main_binding.py",
        "experiments/pct_goal_solver/v0_20_campaign.py",
        "experiments/pct_goal_solver/generate_v0_20_report.py",
    }


def test_historical_terminal_result_is_recomputed_not_trusted_from_trace() -> None:
    goal, trace = _trace("G1")
    forged_value = tuple(trace.candidate_artifact.value[:-1]) + (
        trace.candidate_artifact.value[-1] + 1,
    )
    forged_trace = replace(
        trace,
        candidate_artifact=replace(trace.candidate_artifact, value=forged_value),
    )
    assert forged_trace.verifier_chain == trace.verifier_chain

    case = campaign.evaluate_case(goal, forged_trace, campaign._build_campaign_oracle(goal))
    assert case["observation"]["terminal_authority"]["passed"] is False
    assert case["assessment"]["correct"] is False
    assert case["assessment"]["wrong_positive"] is True


def test_forged_new_family_oracle_certificate_invalidates_assessment() -> None:
    goal, trace = _trace("F1")
    oracle = campaign._build_campaign_oracle(goal)
    assert campaign.evaluate_case(goal, trace, oracle)["assessment"]["correct"] is True

    forged = {**oracle, "certificate": {"forged": True}}
    assessment = campaign.evaluate_case(goal, trace, forged)["assessment"]
    assert assessment["oracle_integrity_valid"] is False
    assert assessment["correct"] is False
    assert assessment["wrong_positive"] is True


def test_historical_g2_accepts_a_distinct_valid_nullspace_basis() -> None:
    goals = [
        goal
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == "G2"
    ]
    registry = build_v0_20_operator_registry()
    for goal in goals:
        trace = solve(goal.solver_visible(), registry)
        basis = trace.candidate_artifact.value["basis"]
        if basis:
            break
    else:
        raise AssertionError("campaign needs a nontrivial G2 nullspace control")

    alternative = {
        **trace.candidate_artifact.value,
        "basis": tuple(
            tuple(Fraction(2) * entry for entry in vector)
            for vector in basis
        ),
    }
    candidate = replace(trace.candidate_artifact, value=alternative)
    assert candidate.value != trace.candidate_artifact.value
    assert verify_historical_goal(goal.solver_visible(), candidate).passed is True
    assert historical_candidate_satisfies_reference(goal.solver_visible(), alternative) is True


def test_new_family_oracle_matching_is_relation_aware_for_f2_and_f3() -> None:
    controls = campaign.build_v0_20_terminal_controls()
    for family in ("F2", "F3"):
        control = next(
            item
            for item in controls
            if item.family == family
            and item.kind.value == "EXTERNAL_VALID_CERTIFICATE"
            and item.is_distinct_alternative
        )
        oracle = build_independent_oracle(
            family=family,
            inputs={key: artifact.value for key, artifact in control.goal.inputs.items()},
            constraints=dict(control.goal.constraints),
            tolerance=control.goal.allowed_numeric_tolerance,
        )
        assert candidate_matches_independent_oracle(
            family=family,
            candidate=asdict(control.candidate.value),
            oracle_certificate=oracle.certificate,
        ) is True


def test_c1_oracle_accepts_exact_real_algebraic_coefficients() -> None:
    base = _goal("C1")
    x, y = base.inputs["coordinates"].value
    coefficient = sp.sqrt(2)
    u, v = coefficient * x, coefficient * y
    goal = replace(
        base,
        inputs={
            **base.inputs,
            "real_part": replace(base.inputs["real_part"], value=u),
            "imag_part": replace(base.inputs["imag_part"], value=v),
        },
    )
    certificate = certify_cauchy_riemann(u, v, x=x, y=y)
    candidate = Artifact(
        artifact_id="external:c1:algebraic",
        semantic_type=goal.target.semantic_type,
        representation_class=goal.target.representation_class,
        value=certificate,
        exactness_class=goal.target.exactness_class,
    )
    oracle = build_independent_oracle(
        family="C1",
        inputs={key: artifact.value for key, artifact in goal.inputs.items()},
        constraints=dict(goal.constraints),
        tolerance=goal.allowed_numeric_tolerance,
    )
    assert verify_v0_20_goal(goal, candidate).passed is True
    assert oracle.authoritative is True
    assert oracle.expected_verdict == "PASS"
    assert candidate_matches_independent_oracle(
        family="C1",
        candidate=asdict(certificate),
        oracle_certificate=oracle.certificate,
    ) is True


def test_x1_oracle_refuses_when_no_binary64_value_meets_exact_tolerance() -> None:
    base = _goal("X1")
    goal = replace(
        base,
        inputs={
            **base.inputs,
            "coefficients": replace(
                base.inputs["coefficients"],
                value=(Fraction(10**20), Fraction(1, 3)),
            ),
            "grid": replace(base.inputs["grid"], value=(Fraction(1),)),
        },
    )
    oracle = build_independent_oracle(
        family="X1",
        inputs={key: artifact.value for key, artifact in goal.inputs.items()},
        constraints=dict(goal.constraints),
        tolerance=goal.allowed_numeric_tolerance,
    )
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())

    assert oracle.authoritative is True
    assert oracle.expected_verdict == "NOT_ESTABLISHED"
    assert oracle.certificate["binary64_feasible"] is False
    assert oracle.certificate["maximum_error"] == Fraction(1, 3)
    assert oracle.certificate["failure"] == "NEAREST_BINARY64_EXCEEDS_TOLERANCE"
    assert trace.final_verdict == "NOT_ESTABLISHED"


def test_cyclic_rejected_candidate_is_reported_fail_closed() -> None:
    goal, trace = _trace("F2")
    cycle: list[object] = []
    cycle.append(cycle)
    malformed = QuadraticMeanValueCertificate(
        coefficients=cycle,
        interval=(Fraction(0), Fraction(1)),
        witness=Fraction(1, 2),
        secant_slope=Fraction(0),
        derivative_at_witness=Fraction(0),
        verified=True,
    )
    forged = replace(
        trace,
        candidate_artifact=replace(trace.candidate_artifact, value=malformed),
    )
    case = campaign.evaluate_case(goal, forged, campaign._build_campaign_oracle(goal))
    marker = case["observation"]["candidate"]
    assert marker["type"] == "NONCANONICAL_EVIDENCE"
    assert case["observation"]["semantic_certificate"]["complete"] is False
    assert case["assessment"]["correct"] is False
    assert case["assessment"]["wrong_positive"] is True


def test_invalid_numeric_subclasses_and_container_shapes_are_closed_by_contract() -> None:
    class MyFraction(Fraction):
        pass

    class MyInt(int):
        pass

    mutations = []
    f1 = _goal("F1")
    lower = f1.inputs["lower_bound"]
    mutations.append(replace(
        f1,
        inputs={
            **f1.inputs,
            "lower_bound": replace(
                lower,
                value=MyFraction(lower.value.numerator, lower.value.denominator),
            ),
        },
    ))
    f2 = _goal("F2")
    coefficients = f2.inputs["coefficients"]
    mutations.append(replace(
        f2,
        inputs={
            **f2.inputs,
            "coefficients": replace(coefficients, value=list(coefficients.value)),
        },
    ))
    f3 = _goal("F3")
    integer_a = f3.inputs["integer_a"]
    mutations.append(replace(
        f3,
        inputs={
            **f3.inputs,
            "integer_a": replace(integer_a, value=MyInt(integer_a.value)),
        },
    ))
    x1 = _goal("X1")
    grid = x1.inputs["grid"]
    mutations.append(replace(
        x1,
        inputs={**x1.inputs, "grid": replace(grid, value=list(grid.value))},
    ))

    for malformed_goal in mutations:
        assert validate_v0_20_goal_contract(malformed_goal).passed is False
        oracle = build_case_oracle(malformed_goal)
        assert oracle["authoritative"] is False
        assert oracle["authority_kind"] == "INVALID_CHALLENGE_CONTRACT"
        assert oracle["oracle_availability"] == "INVALID_CHALLENGE"
        assert oracle["expected_verdict"] == "INVALID"


def test_f2_oracle_rejects_derived_fields_beyond_exact_bit_bound() -> None:
    base = _goal("F2")
    n = Fraction(2**3000)
    goal = replace(
        base,
        inputs={
            **base.inputs,
            "coefficients": replace(
                base.inputs["coefficients"],
                value=(n, Fraction(0), Fraction(0)),
            ),
            "interval": replace(
                base.inputs["interval"],
                value=(Fraction(0), n),
            ),
        },
    )
    independent = build_independent_oracle(
        family="F2",
        inputs={key: artifact.value for key, artifact in goal.inputs.items()},
        constraints=dict(goal.constraints),
        tolerance=goal.allowed_numeric_tolerance,
    )
    oracle = build_case_oracle(goal)
    assert independent.authoritative is True
    assert independent.expected_verdict == "INVALID"
    assert oracle["expected_verdict"] == "INVALID"


def test_x1_oracle_bounds_every_exact_horner_intermediate() -> None:
    base = _goal("X1")
    large = Fraction(2**3000)
    goal = replace(
        base,
        inputs={
            **base.inputs,
            "coefficients": replace(
                base.inputs["coefficients"],
                value=(large, large),
            ),
            "grid": replace(base.inputs["grid"], value=(large,)),
        },
    )
    independent = build_independent_oracle(
        family="X1",
        inputs={key: artifact.value for key, artifact in goal.inputs.items()},
        constraints=dict(goal.constraints),
        tolerance=goal.allowed_numeric_tolerance,
    )
    oracle = build_case_oracle(goal)

    assert independent.authoritative is True
    assert independent.expected_verdict == "INVALID"
    assert independent.method == "EXACT_DOMAIN_VALIDATION"
    assert validate_v0_20_goal_contract(goal).passed is False
    assert oracle["authoritative"] is False
    assert oracle["authority_kind"] == "INVALID_CHALLENGE_CONTRACT"
    assert oracle["expected_verdict"] == "INVALID"


def test_lineage_binds_goal_mode_registry_and_full_verifier_chain() -> None:
    goal, trace = _trace("X1")
    assert campaign._lineage_complete(goal, trace) is True
    assert campaign._lineage_complete(
        goal,
        replace(trace, goal_id="forged:goal"),
    ) is False
    assert campaign._lineage_complete(
        goal,
        replace(trace, mode="INFERRED/PRIMITIVE"),
    ) is False
    assert campaign._lineage_complete(
        goal,
        replace(trace, verifier_chain=(trace.verifier_chain[-1],)),
    ) is False
    forged_terminal = replace(trace.verifier_chain[-1], reason="forged terminal receipt")
    assert campaign._lineage_complete(
        goal,
        replace(trace, verifier_chain=trace.verifier_chain[:-1] + (forged_terminal,)),
    ) is False

    registry = campaign._authoritative_registry()
    with pytest.raises(TypeError):
        registry["FORGED"] = next(iter(registry.values()))


def test_runtime_lineage_is_replayed_from_authoritative_derivation_dag() -> None:
    for family in ("X1", "X2"):
        goal, trace = _trace(family)
        assert campaign._lineage_complete(goal, trace) is True


def test_terminal_lineage_receipt_alone_cannot_satisfy_runtime_gate() -> None:
    goal, trace = _trace("X1")
    assert trace.candidate_lineage is not None
    tampered = replace(trace, derivations=(), derived_obligations=())
    assert campaign._lineage_complete(goal, tampered) is False

    wrong_registry = replace(
        trace,
        candidate_lineage=replace(trace.candidate_lineage, registry_digest="0" * 64),
    )
    assert campaign._lineage_complete(goal, wrong_registry) is False


def test_runtime_lineage_rejects_obligation_and_dag_tampering() -> None:
    goal, trace = _trace("X1")
    obligations = list(trace.derived_obligations)
    obligations[0] = replace(obligations[0], semantic_type="FORGED_STAGE")
    assert campaign._lineage_complete(
        goal,
        replace(trace, derived_obligations=tuple(obligations)),
    ) is False

    derivations = list(trace.derivations)
    second = derivations[1]
    root_instance = trace.root_origins[0].instance_id
    derivations[1] = replace(
        second,
        input_bindings=tuple(
            (port, root_instance if port == "polynomial" else instance_id)
            for port, instance_id in second.input_bindings
        ),
    )
    assert campaign._lineage_complete(
        goal,
        replace(trace, derivations=tuple(derivations)),
    ) is False


def test_runtime_lineage_rejects_failed_step_or_missing_candidate_derivation() -> None:
    goal, trace = _trace("X1")
    derivations = list(trace.derivations)
    derivations[0] = replace(
        derivations[0],
        verifier=replace(derivations[0].verifier, passed=False),
    )
    assert campaign._lineage_complete(
        goal,
        replace(trace, derivations=tuple(derivations)),
    ) is False
    assert campaign._lineage_complete(
        goal,
        replace(trace, derivations=trace.derivations[:-1]),
    ) is False

    forged_steps = list(trace.derivations)
    forged_steps[0] = replace(forged_steps[0], step_id="step:" + "0" * 64)
    assert campaign._lineage_complete(
        goal,
        replace(trace, derivations=tuple(forged_steps)),
    ) is False
