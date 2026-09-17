from __future__ import annotations

from dataclasses import replace
from typing import Mapping

import pytest

from experiments.pct_goal_solver.compatibility import CompatibilityModel
from experiments.pct_goal_solver.model import (
    Applicability,
    Artifact,
    DerivedArtifactRecord,
    InputPort,
    SolverVisibleGoal,
    VerificationResult,
)
from experiments.pct_goal_solver.canonical import canonical_sha256
from experiments.pct_goal_solver.operators import Bindings, OperatorSpec
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v0_20_campaign import evaluate_case
from experiments.pct_goal_solver.v0_20_goals import build_v0_20_corpus
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry
from experiments.pct_goal_solver.v0_20_verifiers import verify_v0_20_goal


def _validation_goal(family: str):
    return next(
        goal
        for goal in build_v0_20_corpus()["VALIDATION_V0_20"]
        if goal.family == family
    )


def _always_applicable(
    inputs: Mapping[str, Artifact],
    bindings: Bindings,
) -> Applicability:
    del inputs, bindings
    return Applicability("APPLICABLE")


def _accept_target_shape(
    inputs: tuple[Artifact, ...],
    output: Artifact,
) -> VerificationResult:
    del inputs, output
    return VerificationResult(True, "ADVERSARIAL_TARGET_SHAPE", "target-shaped output")


def _direct_target_operator(
    goal: SolverVisibleGoal,
    mathematically_valid_candidate: Artifact,
) -> OperatorSpec:
    def execute(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact:
        del inputs, bindings
        return mathematically_valid_candidate

    target_type = goal.target.artifact_type
    assert target_type is not None
    return OperatorSpec(
        operator_id=f"MALICIOUS_DIRECT_TARGET_{goal.family}",
        input_ports=tuple(
            InputPort(key, artifact.artifact_type)
            for key, artifact in sorted(goal.inputs.items())
        ),
        output=target_type,
        cost=1,
        applicability=_always_applicable,
        execute=execute,
        verify=_accept_target_shape,
        structural_signature=("ADVERSARIAL", "DIRECT_TARGET", goal.family),
        objectives=(goal.target.objective,),
    )


@pytest.mark.parametrize("family", ("X1", "X2"))
def test_direct_target_operator_cannot_bypass_required_cross_class_stages(
    family: str,
) -> None:
    goal = _validation_goal(family)
    legitimate = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert legitimate.final_verdict == "PASS"
    assert legitimate.candidate_artifact is not None
    assert verify_v0_20_goal(goal, legitimate.candidate_artifact).passed

    malicious = _direct_target_operator(
        goal.solver_visible(),
        legitimate.candidate_artifact,
    )
    trace = solve(goal.solver_visible(), {malicious.operator_id: malicious})

    assert trace.final_verdict != "PASS"
    assert trace.candidate_artifact is None
    assert any(
        event == "CANDIDATE_LINEAGE_REJECTED"
        for event, _ in trace.falsification_events
    )


@pytest.mark.parametrize("family", ("X1", "X2"))
def test_legitimate_receipt_names_exactly_the_selected_stage_artifacts(
    family: str,
) -> None:
    goal = _validation_goal(family)
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())

    assert trace.final_verdict == "PASS"
    assert trace.candidate_lineage is not None
    expected_stage_types = goal.lineage_obligation.ordered_stage_types
    assert trace.candidate_lineage.stage_instance_ids == tuple(
        obligation.artifact_instance_id
        for obligation in trace.derived_obligations
    )
    assert tuple(obligation.order_index for obligation in trace.derived_obligations) == tuple(
        range(len(expected_stage_types))
    )
    assert tuple(obligation.semantic_type for obligation in trace.derived_obligations) == tuple(
        artifact_type.semantic_type for artifact_type in expected_stage_types
    )

    derivations = {step.step_id: step for step in trace.derivations}
    for obligation, expected_type in zip(trace.derived_obligations, expected_stage_types):
        step = derivations[obligation.derivation_step_id]
        assert step.output_instance_id == obligation.artifact_instance_id
        assert step.output_type == expected_type


def _campaign_reports_complete(goal, trace) -> bool:
    result = evaluate_case(
        goal,
        trace,
        {
            "authoritative": False,
            "expected_verdict": None,
            "oracle_availability": "UNAVAILABLE",
        },
    )
    return result["assessment"]["runtime_lineage_complete"]


@pytest.mark.parametrize(
    "mutation",
    ("reordered_receipt", "invented_receipt_id", "reordered_obligations"),
)
def test_campaign_rejects_tampered_or_reordered_lineage_receipts(mutation: str) -> None:
    goal = _validation_goal("X1")
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert trace.final_verdict == "PASS"
    assert trace.candidate_lineage is not None
    assert _campaign_reports_complete(goal, trace)

    if mutation == "reordered_receipt":
        tampered = replace(
            trace,
            candidate_lineage=replace(
                trace.candidate_lineage,
                stage_instance_ids=tuple(reversed(trace.candidate_lineage.stage_instance_ids)),
            ),
        )
    elif mutation == "invented_receipt_id":
        tampered = replace(
            trace,
            candidate_lineage=replace(
                trace.candidate_lineage,
                stage_instance_ids=(
                    "derived:invented-stage-instance",
                    *trace.candidate_lineage.stage_instance_ids[1:],
                ),
            ),
        )
    else:
        tampered = replace(trace, derived_obligations=tuple(reversed(trace.derived_obligations)))

    assert not _campaign_reports_complete(goal, tampered)


def test_campaign_replays_materialized_outputs_instead_of_trusting_rehashed_lineage() -> None:
    """Self-consistent public hashes cannot launder a forged operator output."""

    goal = _validation_goal("X1")
    trace = solve(goal.solver_visible(), build_v0_20_operator_registry())
    assert trace.final_verdict == "PASS"
    assert trace.candidate_lineage is not None
    assert _campaign_reports_complete(goal, trace)

    instance_ids: dict[str, str] = {}
    step_ids: dict[str, str] = {}
    forged_steps = []
    forged_records = []
    records_by_step = {
        record.derivation_step_id: record for record in trace.derived_artifacts
    }
    for index, step in enumerate(trace.derivations):
        original_record = records_by_step[step.step_id]
        artifact = original_record.artifact
        if index == 0:
            artifact = replace(
                artifact,
                metadata=artifact.metadata + (("forged_intermediate", True),),
            )
        bindings = tuple(
            (port, instance_ids.get(parent, parent))
            for port, parent in step.input_bindings
        )
        output_instance_id = "derived:" + canonical_sha256(
            {
                "operator_id": step.operator_id,
                "parents": bindings,
                "artifact": {
                    "artifact_id": artifact.artifact_id,
                    "artifact_type": artifact.artifact_type,
                    "value": artifact.value,
                    "metadata": artifact.metadata,
                },
            },
            domain="pct-derived-instance-v1",
        )
        forged_step = replace(
            step,
            input_bindings=bindings,
            output_instance_id=output_instance_id,
        )
        forged_step = replace(
            forged_step,
            step_id="step:" + canonical_sha256(
                {
                    "operator_id": forged_step.operator_id,
                    "parents": forged_step.input_bindings,
                    "output_instance_id": forged_step.output_instance_id,
                    "verifier": forged_step.verifier,
                },
                domain="pct-derivation-step-v1",
            ),
        )
        instance_ids[step.output_instance_id] = forged_step.output_instance_id
        step_ids[step.step_id] = forged_step.step_id
        forged_steps.append(forged_step)
        forged_records.append(
            DerivedArtifactRecord(
                instance_id=forged_step.output_instance_id,
                derivation_step_id=forged_step.step_id,
                artifact=artifact,
            )
        )

    forged_obligations = tuple(
        replace(
            obligation,
            artifact_instance_id=instance_ids[obligation.artifact_instance_id],
            derivation_step_id=step_ids[obligation.derivation_step_id],
        )
        for obligation in trace.derived_obligations
    )
    forged_receipt = replace(
        trace.candidate_lineage,
        candidate_instance_id=instance_ids[trace.candidate_lineage.candidate_instance_id],
        stage_instance_ids=tuple(
            instance_ids[instance_id]
            for instance_id in trace.candidate_lineage.stage_instance_ids
        ),
    )
    forged = replace(
        trace,
        derivations=tuple(forged_steps),
        derived_artifacts=tuple(forged_records),
        derived_obligations=forged_obligations,
        candidate_lineage=forged_receipt,
    )

    assert not _campaign_reports_complete(goal, forged)


def test_campaign_rejects_rehashed_routing_not_derived_from_fitted_model() -> None:
    """A self-consistent receipt hash is identity, not routing authority."""

    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    calibration = next(
        goal
        for goal in corpus["CALIBRATION_V0_20"]
        if goal.family == "X1"
    )
    calibration_trace = solve(calibration.solver_visible(), registry)
    model = CompatibilityModel.fit(
        (calibration,),
        (calibration_trace,),
        registry,
    )
    goal = _validation_goal("X1")
    blinded = replace(
        goal.solver_visible(),
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in goal.inputs.items()
        },
    )
    trace = solve(
        blinded,
        registry,
        typing_mode="INFERRED",
        compatibility_model=model,
    )
    assert trace.final_verdict == "PASS"
    assert trace.routing_receipt is not None

    oracle = {
        "authoritative": False,
        "expected_verdict": None,
        "oracle_availability": "UNAVAILABLE",
    }
    baseline = evaluate_case(
        goal,
        trace,
        oracle,
        compatibility_model=model,
    )
    assert baseline["assessment"]["runtime_lineage_complete"] is True

    receipt = trace.routing_receipt
    forged_receipts = (
        replace(receipt, compatibility_model_digest="1" * 64),
        replace(
            receipt,
            ordered_operator_ids=tuple(reversed(receipt.ordered_operator_ids)),
        ),
    )
    for forged_receipt in forged_receipts:
        forged_receipt = replace(
            forged_receipt,
            decision_digest=canonical_sha256(
                {
                    "inferred_root_types": forged_receipt.inferred_root_types,
                    "ordered_operator_ids": forged_receipt.ordered_operator_ids,
                    "ambiguous_input_keys": forged_receipt.ambiguous_input_keys,
                    "compatibility_model_digest": forged_receipt.compatibility_model_digest,
                },
                domain="pct-routing-decision-v1",
            ),
        )
        assessment = evaluate_case(
            goal,
            replace(trace, routing_receipt=forged_receipt),
            oracle,
            compatibility_model=model,
        )
        assert assessment["assessment"]["runtime_lineage_complete"] is False
