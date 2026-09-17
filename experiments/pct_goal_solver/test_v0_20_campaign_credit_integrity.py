from __future__ import annotations

from dataclasses import replace
from functools import partial
import math

from experiments.pct_goal_solver import v0_20_campaign as campaign
from experiments.pct_goal_solver import historical_oracles
from experiments.pct_goal_solver.compatibility import CompatibilityModel
from experiments.pct_goal_solver.historical_oracles import HistoricalReference
from experiments.pct_goal_solver.model import (
    Refusal,
    RuntimeMacroBinding,
    VerificationResult,
)
from experiments.pct_goal_solver.operators import OperatorSpec
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v0_20_goals import (
    build_v0_20_corpus,
    build_v0_20_terminal_controls,
)
from experiments.pct_goal_solver.v0_20_operators import (
    build_v0_20_operator_registry,
)


def _sealed(family: str):
    return tuple(
        goal
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == family
    )


def test_forged_pass_execution_receipts_cannot_earn_family_coverage() -> None:
    registry = build_v0_20_operator_registry()
    goals = _sealed("G1")
    traces = tuple(solve(goal.solver_visible(), registry) for goal in goals)
    cases = [
        campaign.evaluate_case(
            goal,
            trace,
            campaign._build_campaign_oracle(goal),
            expected_typing_mode="EXPLICIT",
        )
        for goal, trace in zip(goals, traces)
    ]
    assert all(case["assessment"]["execution_receipt_complete"] for case in cases)
    # A family fragment is not the frozen scored population and earns no gate credit.
    assert campaign._family_coverage({"total": len(cases), "cases": cases}) == 0

    trace = traces[1]
    mutations = {
        "goal": replace(trace, goal_id="forged:goal"),
        "mode": replace(trace, mode="HYBRID/PRIMITIVE"),
        "root": replace(
            trace,
            root_origins=(
                replace(trace.root_origins[0], content_digest="0" * 64),
            ),
        ),
        "derivation": replace(trace, derivations=()),
        "lineage": replace(trace, candidate_lineage=None),
    }
    for label, forged in mutations.items():
        forged_case = campaign.evaluate_case(
            goals[1],
            forged,
            campaign._build_campaign_oracle(goals[1]),
            expected_typing_mode="EXPLICIT",
        )
        assert forged_case["assessment"]["execution_receipt_complete"] is False, label
        assert forged_case["assessment"]["correct"] is False, label
        assert campaign._family_coverage(
            {"cases": [cases[0], forged_case]}
        ) == 0, label


def test_contradictory_pass_metadata_counters_and_events_never_earn_credit() -> None:
    registry = build_v0_20_operator_registry()
    goals = _sealed("G1")
    traces = tuple(solve(goal.solver_visible(), registry) for goal in goals)
    oracle = campaign._build_campaign_oracle(goals[1])
    baseline = campaign.evaluate_case(
        goals[0],
        traces[0],
        campaign._build_campaign_oracle(goals[0]),
        expected_typing_mode="EXPLICIT",
    )
    assert baseline["assessment"]["correct"] is True

    trace = traces[1]
    mutations = {
        "refusal": replace(
            trace,
            refusal=Refusal("FORGED_PASS_REFUSAL", "contradictory PASS refusal"),
        ),
        "failure_reason": replace(trace, failure_reason="contradictory PASS failure"),
        "macro_ids": replace(trace, macro_ids=("FORGED_MACRO",)),
        "macro_bindings": replace(
            trace,
            macro_bindings=(
                RuntimeMacroBinding(
                    macro_id="FORGED_MACRO",
                    primitive_ids=(trace.derivations[0].operator_id,),
                    derivation_step_ids=(trace.derivations[0].step_id,),
                    certificate_digest="0" * 64,
                ),
            ),
        ),
        "expanded_state_count": replace(
            trace,
            expanded_state_count=trace.expanded_state_count + 1,
        ),
        "primitive_execution_count": replace(
            trace,
            primitive_execution_count=trace.primitive_execution_count + 1,
        ),
        "attempted_operator_count": replace(
            trace,
            attempted_operator_count=trace.attempted_operator_count + 1,
        ),
        "verifier_execution_count": replace(
            trace,
            verifier_execution_count=trace.verifier_execution_count + 1,
        ),
        "falsification_events": replace(
            trace,
            falsification_events=trace.falsification_events
            + (("FORGED_EVENT", {"accepted": True}),),
        ),
    }
    for label, forged in mutations.items():
        case = campaign.evaluate_case(
            goals[1],
            forged,
            oracle,
            expected_typing_mode="EXPLICIT",
        )
        assert case["assessment"]["execution_receipt_complete"] is False, label
        assert case["assessment"]["correct"] is False, label
        assert campaign._family_coverage(
            {"cases": [baseline, case]}
        ) == 0, label


def test_planner_comparison_passes_receive_exact_full_solve_replay() -> None:
    registry = build_v0_20_operator_registry()
    for family in ("G4", "G5"):
        goal = _sealed(family)[0]
        trace = solve(goal.solver_visible(), registry)
        assert any(
            step.operator_id.startswith("PLANNER_COMPARISON_")
            for step in trace.derivations
        )
        assert campaign._execution_receipt_complete(
            goal,
            trace,
            expected_typing_mode="EXPLICIT",
        ), family


def test_forged_cross_class_obligations_and_routing_cannot_earn_credit() -> None:
    registry = build_v0_20_operator_registry()
    goal = _sealed("X1")[0]
    trace = solve(goal.solver_visible(), registry)
    assert trace.derived_obligations

    forged = replace(trace, derived_obligations=trace.derived_obligations[:-1])
    case = campaign.evaluate_case(
        goal,
        forged,
        campaign._build_campaign_oracle(goal),
        expected_typing_mode="EXPLICIT",
    )
    assert case["assessment"]["execution_receipt_complete"] is False
    assert case["assessment"]["correct"] is False


def test_historical_inferred_pass_requires_live_model_bound_routing_receipt() -> None:
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    calibration = tuple(
        goal for goal in corpus["CALIBRATION_V0_20"] if goal.family == "G1"
    )
    calibration_traces = tuple(
        solve(goal.solver_visible(), registry) for goal in calibration
    )
    model = CompatibilityModel.fit(calibration, calibration_traces, registry)
    goal = _sealed("G1")[0]
    trace = solve(
        campaign._blind_input_semantic_types(goal.solver_visible()),
        registry,
        typing_mode="INFERRED",
        compatibility_model=model,
    )
    assert trace.routing_receipt is not None
    case = campaign.evaluate_case(
        goal,
        trace,
        campaign._build_campaign_oracle(goal),
        compatibility_model=model,
        expected_typing_mode="INFERRED",
    )
    assert case["assessment"]["execution_receipt_complete"] is True
    assert case["assessment"]["correct"] is True

    forged = replace(
        trace,
        routing_receipt=replace(trace.routing_receipt, decision_digest="0" * 64),
    )
    forged_case = campaign.evaluate_case(
        goal,
        forged,
        campaign._build_campaign_oracle(goal),
        compatibility_model=model,
        expected_typing_mode="INFERRED",
    )
    assert forged_case["assessment"]["execution_receipt_complete"] is False
    assert forged_case["assessment"]["correct"] is False


def test_g9_not_applicable_refusal_is_replayed_not_string_matched() -> None:
    registry = build_v0_20_operator_registry()
    goal = next(goal for goal in _sealed("G9") if goal.sealed_expected_result == "NOT_APPLICABLE")
    trace = solve(goal.solver_visible(), registry)
    assert trace.refusal is not None

    forged_reason = "plausible but never executed"
    forged = replace(
        trace,
        failure_reason=forged_reason,
        refusal=replace(trace.refusal, reason=forged_reason),
    )
    case = campaign.evaluate_case(
        goal,
        forged,
        campaign._build_campaign_oracle(goal),
        expected_typing_mode="EXPLICIT",
    )
    assert case["assessment"]["refusal_execution_replayed"] is False
    assert case["assessment"]["correct"] is not True


def test_registry_contract_digest_binds_live_callable_implementations() -> None:
    registry = build_v0_20_operator_registry()
    baseline = campaign._registry_contract_digest(registry)
    operator_id, spec = next(iter(registry.items()))

    original_execute = spec.execute

    def same_result(inputs, constraints):
        return original_execute(inputs, constraints)

    tampered = dict(registry)
    tampered[operator_id] = replace(spec, execute=same_result)
    assert isinstance(tampered[operator_id], OperatorSpec)
    assert campaign._registry_contract_digest(tampered) != baseline


def test_public_campaign_result_cannot_poison_cached_evidence(monkeypatch) -> None:
    cached = {"gates": {"stable": True}, "channels": {"cases": [1, 2]}}
    monkeypatch.setattr(campaign, "_execute_v0_20_campaign_cached", lambda: cached)

    first = campaign.execute_v0_20_campaign()
    first["gates"]["stable"] = False
    first["channels"]["cases"].append(3)

    second = campaign.execute_v0_20_campaign()
    assert second == {"gates": {"stable": True}, "channels": {"cases": [1, 2]}}
    assert second is not cached


def test_terminal_control_requires_exact_certifier_semantics(monkeypatch) -> None:
    control = next(
        item
        for item in build_v0_20_terminal_controls()
        if item.kind.value == "EXTERNAL_VALID_CERTIFICATE"
    )
    assert campaign.evaluate_terminal_control(control)["correct"] is True

    monkeypatch.setattr(
        campaign,
        "verify_v0_20_goal",
        lambda goal, candidate: VerificationResult(
            control.expected_verification_pass,
            "FORGED_CERTIFIER",
            "forged",
        ),
    )
    forged = campaign.evaluate_terminal_control(control)
    assert forged["certifier_semantics_valid"] is False
    assert forged["correct"] is False


def test_terminal_control_gate_requires_exact_frozen_manifest() -> None:
    controls = build_v0_20_terminal_controls()
    rows = [campaign.evaluate_terminal_control(control) for control in controls]
    assert campaign._terminal_control_manifest_conforms(controls, rows) is True

    mutated_control = replace(controls[0], expected_verification_pass=True)
    mutated_controls = (mutated_control,) + controls[1:]
    mutated_rows = [
        campaign.evaluate_terminal_control(control) for control in mutated_controls
    ]
    variants = {
        "missing": (controls[:-1], rows[:-1]),
        "extra": (controls + (controls[0],), rows + [rows[0]]),
        "duplicate": (
            controls[:-1] + (controls[0],),
            rows[:-1] + [rows[0]],
        ),
        "mutated": (mutated_controls, mutated_rows),
    }
    for label, (forged_controls, forged_rows) in variants.items():
        assert campaign._terminal_control_manifest_conforms(
            forged_controls,
            forged_rows,
        ) is False, label


def test_historical_reference_flags_are_not_sufficient_for_authority(monkeypatch) -> None:
    goal = _sealed("G1")[0]
    monkeypatch.setattr(
        campaign,
        "build_historical_reference",
        lambda visible: HistoricalReference(
            expected_verdict="PASS",
            candidate_value=goal.sealed_expected_result,
            method_id="unreviewed-default-flags",
            authoritative=True,
            implementation_independent=True,
        ),
    )
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_historical_oracle_live_dependency_substitution_revokes_authority(
    monkeypatch,
) -> None:
    goal = _sealed("G1")[0]
    monkeypatch.setattr(
        historical_oracles,
        "_reference",
        lambda visible: goal.sealed_expected_result,
    )
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_historical_oracle_callable_object_substitution_revokes_authority(
    monkeypatch,
) -> None:
    goal = _sealed("G1")[0]

    class ForgedReference:
        def __call__(self, visible):
            return goal.sealed_expected_result

    monkeypatch.setattr(historical_oracles, "_reference", ForgedReference())
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_historical_oracle_partial_substitution_revokes_authority(monkeypatch) -> None:
    goal = _sealed("G1")[0]

    def forged_reference(visible, *, value):
        return value

    monkeypatch.setattr(
        historical_oracles,
        "_reference",
        partial(forged_reference, value=goal.sealed_expected_result),
    )
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_historical_oracle_module_proxy_substitution_revokes_authority(
    monkeypatch,
) -> None:
    goal = _sealed("G1")[0]

    class MathProxy:
        def __getattr__(self, name):
            return getattr(math, name)

    monkeypatch.setattr(historical_oracles, "math", MathProxy())
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_warm_oracle_cache_detects_in_place_sympy_api_substitution(
    monkeypatch,
) -> None:
    goal = _sealed("G1")[0]
    assert campaign._build_campaign_oracle(goal)["authoritative"] is True
    original = historical_oracles.sp.sympify
    monkeypatch.setattr(
        historical_oracles.sp,
        "sympify",
        lambda value, *args, **kwargs: original(value, *args, **kwargs),
    )
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_warm_oracle_cache_detects_in_place_math_api_substitution(
    monkeypatch,
) -> None:
    goal = _sealed("G1")[0]
    assert campaign._build_campaign_oracle(goal)["authoritative"] is True
    original = historical_oracles.math.isfinite
    monkeypatch.setattr(
        historical_oracles.math,
        "isfinite",
        lambda value: original(value),
    )
    oracle = campaign._build_campaign_oracle(goal)
    assert oracle["authoritative"] is False
    assert oracle["reason"] == "HISTORICAL_REFERENCE_NOT_INDEPENDENT"


def test_scientific_axes_report_evidence_and_capability_independently() -> None:
    axes = campaign.classify_scientific_axes(
        dict(campaign.FROZEN_EXPECTED_GATE_VECTOR)
    )
    assert axes == {
        "engine_validity": "VALID",
        "evidence_completeness": "PARTIAL",
        "capability_support": "NOT_SUPPORTED",
    }


def test_frozen_corpus_manifest_rejects_duplicate_imbalance_and_extra_cross_rows() -> None:
    base = build_v0_20_corpus()
    baseline = campaign._frozen_corpus_manifest_receipt(base)
    assert baseline["valid"] is True
    assert baseline["observed_manifest_sha256"] == campaign._FROZEN_CORPUS_MANIFEST_SHA256

    duplicate = {split: list(goals) for split, goals in base.items()}
    duplicate["SEALED_V0_20"][1] = replace(
        duplicate["SEALED_V0_20"][1],
        goal_id=duplicate["SEALED_V0_20"][0].goal_id,
    )

    imbalance = {split: list(goals) for split, goals in base.items()}
    g2_index = next(
        index
        for index, goal in enumerate(imbalance["SEALED_V0_20"])
        if goal.family == "G2"
    )
    imbalance["SEALED_V0_20"][g2_index] = replace(
        imbalance["SEALED_V0_20"][g2_index],
        family="G1",
    )

    extra_cross = {split: list(goals) for split, goals in base.items()}
    x1 = next(goal for goal in extra_cross["SEALED_V0_20"] if goal.family == "X1")
    extra_cross["SEALED_V0_20"].append(
        replace(x1, goal_id="sealed_v0_20:x1:extra")
    )

    content_drift = {split: list(goals) for split, goals in base.items()}
    drift_goal = content_drift["SEALED_V0_20"][0]
    input_key = next(iter(drift_goal.inputs))
    source = drift_goal.inputs[input_key]
    drift_value = tuple(source.value[:-1]) + (source.value[-1] + 1,)
    content_drift["SEALED_V0_20"][0] = replace(
        drift_goal,
        inputs={**drift_goal.inputs, input_key: replace(source, value=drift_value)},
    )

    for label, forged in {
        "duplicate": duplicate,
        "three-one-imbalance": imbalance,
        "extra-cross-row": extra_cross,
        "content-digest-drift": content_drift,
    }.items():
        receipt = campaign._frozen_corpus_manifest_receipt(forged)
        assert receipt["valid"] is False, label
        invalid = campaign._invalid_corpus_campaign_result(receipt)
        for gate in (
            "closed_challenge_domain_valid",
            "shortcut_proofs_complete",
            "runtime_lineage_receipts_complete",
            "explicit_family_coverage",
            "inferred_family_coverage",
            "hybrid_family_coverage",
        ):
            assert invalid["gates"][gate] is False, (label, gate)
            assert invalid["gate_receipts"][gate]["numerator"] == 0, (label, gate)


def test_frozen_mode_manifest_rejects_missing_duplicate_and_renamed_rows(
    monkeypatch,
) -> None:
    corpus = build_v0_20_corpus()
    original = campaign.MODE_CONFIGS
    variants = {
        "missing": original[:-1],
        "duplicate": original[:-1] + (original[0],),
        "renamed": (("RENAMED/PRIMITIVE", "EXPLICIT", False),) + original[1:],
    }
    for label, forged in variants.items():
        with monkeypatch.context() as context:
            context.setattr(campaign, "MODE_CONFIGS", forged)
            receipt = campaign._frozen_corpus_manifest_receipt(corpus)
            assert receipt["valid"] is False, label
            assert "MODE_CONFIG_MANIFEST_MISMATCH" in receipt["errors"], label
            invalid = campaign._invalid_corpus_campaign_result(receipt)
            assert invalid["gates"]["closed_challenge_domain_valid"] is False


def _synthetic_credited_sealed_mode() -> dict:
    cases = []
    for goal in build_v0_20_corpus()["SEALED_V0_20"]:
        signatures = campaign.case_signatures(goal)
        cases.append({
            "goal_id": goal.goal_id,
            "family": goal.family,
            "exact_content_sha256": signatures.exact_sha256,
            "nuisance_content_sha256": signatures.nuisance_sha256,
            "nuisance_relation": signatures.nuisance_relation,
            "assessment": {
                "challenge_contract_valid": True,
                "oracle_available": True,
                "correct": True,
                "credit_eligible_execution": True,
            },
            "oracle": {
                "authority_kind": "INDEPENDENT_MATHEMATICAL_ORACLE",
            },
        })
    return {"total": len(cases), "cases": cases}


def test_family_coverage_requires_exact_unique_frozen_scored_mode_manifest() -> None:
    mode = _synthetic_credited_sealed_mode()
    receipt = campaign._scored_mode_manifest_receipt(mode)
    assert receipt["valid"] is True
    assert receipt["observed_manifest_sha256"] == (
        campaign._FROZEN_SEALED_CASE_MANIFEST_SHA256
    )
    assert campaign._family_coverage(mode) == len(campaign._FROZEN_CAMPAIGN_FAMILIES)

    duplicated = {"total": mode["total"], "cases": list(mode["cases"])}
    duplicated["cases"][1] = duplicated["cases"][0]
    duplicate_receipt = campaign._scored_mode_manifest_receipt(duplicated)
    assert duplicate_receipt["valid"] is False
    assert "DUPLICATE_SEALED_GOAL_ID" in duplicate_receipt["errors"]
    assert campaign._family_coverage(duplicated) == 0

    content_drift = {"total": mode["total"], "cases": list(mode["cases"])}
    content_drift["cases"][0] = {
        **content_drift["cases"][0],
        "exact_content_sha256": "0" * 64,
    }
    assert campaign._scored_mode_manifest_receipt(content_drift)["valid"] is False
    assert campaign._family_coverage(content_drift) == 0


def _conserving_macro_analysis() -> dict:
    pairs = (
        ("EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED"),
        ("INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED"),
        ("HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED"),
    )
    evaluations = [
        {
            "goal_id": goal_id,
            "family": family,
            "mode_pair": list(pair),
            "macro_used": True,
            "macro_rescue": False,
            "exact_conservation": True,
            "unauthorized_macro_claim": False,
        }
        for goal_id, family in campaign._FROZEN_EXPECTED_SEALED_GOAL_ROWS
        for pair in pairs
    ]
    return {
        "total_comparisons": len(evaluations),
        "macro_use_count": len(evaluations),
        "unauthorized_macro_claim_count": 0,
        "macro_rescue_count": 0,
        "exact_conservation_count": len(evaluations),
        "evaluations": evaluations,
    }


def test_macro_gate_credit_requires_exact_comparison_manifest_and_macro_use() -> None:
    analysis = _conserving_macro_analysis()
    denominator = campaign.GATE_DENOMINATORS["zero_macro_rescues"]
    assert campaign._macro_gate_credit_counts(analysis) == (denominator, denominator)

    extra = {**analysis, "evaluations": list(analysis["evaluations"])}
    extra["evaluations"].append(dict(extra["evaluations"][0]))
    extra["total_comparisons"] += 1
    extra["macro_rescue_count"] = 1
    assert campaign._macro_gate_credit_counts(extra) == (0, 0)

    missing = {**analysis, "evaluations": list(analysis["evaluations"][:-1])}
    missing["total_comparisons"] -= 1
    missing["macro_use_count"] -= 1
    missing["exact_conservation_count"] -= 1
    assert campaign._macro_gate_credit_counts(missing) == (0, 0)

    duplicate = {**analysis, "evaluations": list(analysis["evaluations"])}
    duplicate["evaluations"][-1] = dict(duplicate["evaluations"][0])
    assert campaign._macro_gate_credit_counts(duplicate) == (0, 0)

    unused = {**analysis, "evaluations": list(analysis["evaluations"])}
    unused["evaluations"][0] = {
        **unused["evaluations"][0],
        "macro_used": False,
    }
    unused["macro_use_count"] -= 1
    assert campaign._macro_gate_credit_counts(unused) == (denominator, 0)


def test_cross_class_family_selector_is_frozen_authority(monkeypatch) -> None:
    monkeypatch.setattr(campaign, "CROSS_CLASS_FAMILIES", ("X1", "X2", "F1"))
    receipt = campaign._frozen_corpus_manifest_receipt(build_v0_20_corpus())
    assert receipt["valid"] is False
    assert "CROSS_CLASS_FAMILY_MANIFEST_MISMATCH" in receipt["errors"]
