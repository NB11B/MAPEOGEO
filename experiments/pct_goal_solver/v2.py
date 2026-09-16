from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

import sympy as sp

from .goals import FAMILIES, _BUILDERS
from .model import Applicability, Artifact, GoalSpec, OperatorFailure, VerificationResult
from .operators import Bindings, OperatorSpec, build_operator_registry


V2_SPLIT_COUNTS = {"CALIBRATION_V2": 3, "VALIDATION_V2": 1, "SEALED_V2": 2}
V2_SPLIT_BASES = {"CALIBRATION_V2": 1000, "VALIDATION_V2": 2000, "SEALED_V2": 3000}
V2_REQUIRED_DERIVED_TYPES: dict[str, tuple[str, ...]] = {
    "G1": ("BOOLEAN_ZETA_SIGNAL",),
    "G2": ("MATRIX_RANK",),
    "G3": ("CHAIN_RESIDUAL_MATRIX",),
    "G4": (),
    "G5": (),
    "G6": ("CONDITIONING_RISK",),
    "G7": ("NILPOTENCY_RESULT",),
    "G8": ("SYMBOLIC_EXPRESSION",),
    "G9": ("CONVEXITY_VERDICT", "SYMBOLIC_EXPRESSION"),
    "G10": (),
    "G11": (),
    "G12": ("SYMBOLIC_EXPRESSION",),
}


def _with_v2_contract(goal: GoalSpec) -> GoalSpec:
    inputs = dict(goal.inputs)
    if goal.family == "G2":
        observation = inputs["observation_matrix"]
        inputs["rational_matrix"] = replace(
            observation,
            artifact_id=f"{goal.goal_id}:rational_matrix",
            semantic_type="RATIONAL_MATRIX",
        )
    constraints = tuple(goal.constraints) + (
        ("required_derived_types", V2_REQUIRED_DERIVED_TYPES[goal.family]),
    )
    return replace(goal, inputs=inputs, constraints=constraints)


def build_v2_corpus() -> dict[str, list[GoalSpec]]:
    """Build the fresh V2 calibration/validation/sealed corpus without solving it."""
    corpus: dict[str, list[GoalSpec]] = {split: [] for split in V2_SPLIT_COUNTS}
    for split in ("CALIBRATION_V2", "VALIDATION_V2", "SEALED_V2"):
        base = V2_SPLIT_BASES[split]
        for family_index, family in enumerate(FAMILIES):
            for local_index in range(V2_SPLIT_COUNTS[split]):
                goal_id = f"{split.lower()}:{family.lower()}:{local_index:02d}"
                parameter_index = base + 10 * family_index + local_index
                corpus[split].append(
                    _with_v2_contract(_BUILDERS[family](goal_id, parameter_index))
                )
    return corpus


def _find_semantic(inputs: Mapping[str, Artifact], semantic_type: str) -> Artifact:
    for artifact in inputs.values():
        if artifact.semantic_type == semantic_type:
            return artifact
    raise KeyError(semantic_type)


def _required(semantic_type: str):
    def applicability(inputs: Mapping[str, Artifact], bindings: Bindings) -> Applicability:
        try:
            _find_semantic(inputs, semantic_type)
        except KeyError:
            return Applicability("MISSING_PRECONDITION", f"missing semantic input: {semantic_type}")
        return Applicability("APPLICABLE")

    return applicability


def _symbolic_bridge(
    operator_id: str,
    source_type: str,
    inputs: Mapping[str, Artifact],
) -> Artifact | OperatorFailure:
    try:
        source = _find_semantic(inputs, source_type)
        value = sp.nsimplify(source.value, [sp.pi])
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)
    return Artifact(
        artifact_id=f"derived:{operator_id}:{source.artifact_id}",
        semantic_type="SYMBOLIC_EXPRESSION",
        representation_class="SYMBOLIC",
        value=value,
        exactness_class="SYMBOLIC",
        metadata=(("bridge_source_type", source_type),),
        provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
    )


def _exec_numeric_relation_symbolize(
    inputs: Mapping[str, Artifact], bindings: Bindings
) -> Artifact | OperatorFailure:
    return _symbolic_bridge("NUMERIC_RELATION_SYMBOLIZE", "NUMERIC_RELATION", inputs)


def _exec_area_symbolize(
    inputs: Mapping[str, Artifact], bindings: Bindings
) -> Artifact | OperatorFailure:
    return _symbolic_bridge("AREA_SYMBOLIZE", "AREA", inputs)


def _verify_symbolic_bridge(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    source = next((artifact for artifact in inputs if artifact.semantic_type in {"NUMERIC_RELATION", "AREA"}), None)
    if source is None:
        return VerificationResult(False, "SYMBOLIC_BRIDGE_ROUND_TRIP", "missing numerical source")
    try:
        residual = abs(float(sp.N(output.value, 17)) - float(source.value))
    except Exception as exc:
        return VerificationResult(False, "SYMBOLIC_BRIDGE_ROUND_TRIP", str(exc))
    return VerificationResult(
        residual <= 1e-10,
        "SYMBOLIC_BRIDGE_ROUND_TRIP",
        f"residual={residual}",
        residual=residual,
    )


def build_v2_operator_registry() -> dict[str, OperatorSpec]:
    registry = build_operator_registry()
    bridges = (
        OperatorSpec(
            operator_id="NUMERIC_RELATION_SYMBOLIZE",
            input_types=("NUMERIC_RELATION",),
            output_type="SYMBOLIC_EXPRESSION",
            representation_class="SYMBOLIC",
            exactness_class="SYMBOLIC",
            cost=1,
            applicability=_required("NUMERIC_RELATION"),
            execute=_exec_numeric_relation_symbolize,
            verify=_verify_symbolic_bridge,
            structural_signature=("NUMERICAL_TO_SYMBOLIC", "NUMERIC_RELATION"),
        ),
        OperatorSpec(
            operator_id="AREA_SYMBOLIZE",
            input_types=("AREA",),
            output_type="SYMBOLIC_EXPRESSION",
            representation_class="SYMBOLIC",
            exactness_class="SYMBOLIC",
            cost=1,
            applicability=_required("AREA"),
            execute=_exec_area_symbolize,
            verify=_verify_symbolic_bridge,
            structural_signature=("NUMERICAL_TO_SYMBOLIC", "AREA"),
        ),
    )
    for bridge in bridges:
        registry[bridge.operator_id] = bridge
    if len(registry) != 35:
        raise AssertionError(f"expected 35 V2 operators, got {len(registry)}")
    return registry
