"""Current historical registry plus the two narrow symbolic bridge operators."""

from __future__ import annotations

from typing import Mapping

import sympy as sp

from .model import (
    Applicability,
    Artifact,
    ArtifactType,
    InputPort,
    OperatorFailure,
    VerificationResult,
)
from .operators import Bindings, OperatorSpec, build_operator_registry


_BASE_OPERATOR_COUNT = 33
_BRIDGE_OPERATOR_IDS = frozenset({"NUMERIC_RELATION_SYMBOLIZE", "AREA_SYMBOLIZE"})


def _find_semantic(inputs: Mapping[str, Artifact], semantic_type: str) -> Artifact:
    for artifact in inputs.values():
        if artifact.semantic_type == semantic_type:
            return artifact
    raise KeyError(semantic_type)


def _required(semantic_type: str):
    def applicability(inputs: Mapping[str, Artifact], bindings: Bindings) -> Applicability:
        del bindings
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
    del bindings
    return _symbolic_bridge("NUMERIC_RELATION_SYMBOLIZE", "NUMERIC_RELATION", inputs)


def _exec_area_symbolize(
    inputs: Mapping[str, Artifact], bindings: Bindings
) -> Artifact | OperatorFailure:
    del bindings
    return _symbolic_bridge("AREA_SYMBOLIZE", "AREA", inputs)


def _verify_symbolic_bridge(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    source = next(
        (artifact for artifact in inputs if artifact.semantic_type in {"NUMERIC_RELATION", "AREA"}),
        None,
    )
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


def build_cross_representation_operator_registry() -> dict[str, OperatorSpec]:
    """Return the current 33-operator base plus two registered bridge specs."""
    registry = build_operator_registry()
    if len(registry) != _BASE_OPERATOR_COUNT:
        raise AssertionError(
            f"expected {_BASE_OPERATOR_COUNT} current base operators, got {len(registry)}"
        )
    if _BRIDGE_OPERATOR_IDS & set(registry):
        raise AssertionError("symbolic bridge operator ID collides with the base registry")

    bridges = (
        OperatorSpec(
            operator_id="NUMERIC_RELATION_SYMBOLIZE",
            input_ports=(
                InputPort(
                    "numeric_relation",
                    ArtifactType("NUMERIC_RELATION", "NUMERICAL", "NUMERICAL"),
                ),
            ),
            output=ArtifactType("SYMBOLIC_EXPRESSION", "SYMBOLIC", "SYMBOLIC"),
            cost=1,
            applicability=_required("NUMERIC_RELATION"),
            execute=_exec_numeric_relation_symbolize,
            verify=_verify_symbolic_bridge,
            structural_signature=("NUMERICAL_TO_SYMBOLIC", "NUMERIC_RELATION"),
        ),
        OperatorSpec(
            operator_id="AREA_SYMBOLIZE",
            input_ports=(
                InputPort("area", ArtifactType("AREA", "GEOMETRY", "NUMERICAL")),
            ),
            output=ArtifactType("SYMBOLIC_EXPRESSION", "SYMBOLIC", "SYMBOLIC"),
            cost=1,
            applicability=_required("AREA"),
            execute=_exec_area_symbolize,
            verify=_verify_symbolic_bridge,
            structural_signature=("NUMERICAL_TO_SYMBOLIC", "AREA"),
        ),
    )
    for bridge in bridges:
        registry[bridge.operator_id] = bridge
    return registry
