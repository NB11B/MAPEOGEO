"""Typed, fail-closed operators for the seven prospective v0.20 families."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from fractions import Fraction
import hashlib
import inspect
import math
from typing import Any, Mapping

import sympy as sp

from .bridge_operators import build_cross_representation_operator_registry
from .elliptic_periods import (
    PeriodCertificate,
    PeriodCertificationUnavailable,
    certify_rectangular_periods,
    verify_period_certificate,
)
from .model import Artifact, OperatorFailure, VerificationResult
from .operators import Bindings, OperatorSpec, _spec
from .rigorous_math import (
    BezoutCertificate,
    CauchyRiemannCertificate,
    GridEvaluationCertificate,
    QuadraticMeanValueCertificate,
    ResidueCertificate,
    Sqrt2CutCertificate,
    certify_bezout,
    certify_cauchy_riemann,
    certify_grid_evaluation,
    certify_quadratic_mean_value,
    certify_residue,
    certify_sqrt2_cut,
    verify_bezout_certificate,
    verify_cauchy_riemann,
    verify_grid_evaluation,
    verify_quadratic_mean_value,
    verify_residue,
    verify_sqrt2_cut,
)
from .v0_20_contracts import (
    NumericalPolynomialEvaluation,
    SymbolicPolynomial,
    V0_20_CONTRACTS,
    WeierstrassCurve,
    materialize_v0_20_artifact_type,
)


_MAX_OPERATOR_INPUTS = 512
_MAX_BINDINGS = 32
_MAX_LINEAGE_ITEMS = 64
_MAX_IDENTIFIER_LENGTH = 512
_MAX_EXACT_BITS = 4096
_MAX_VECTOR_ITEMS = 4096
_MAX_GRID_WORK = 100_000
_MAX_CANONICAL_NODES = 200_000
_MAX_CANONICAL_TEXT_BYTES = 8_000_000


class _NumericallyUnsafeBridgeError(ValueError):
    """Exact input is valid but cannot be represented safely in binary64."""


_OPERATOR_INPUT_TYPES: dict[str, tuple[str, ...]] = {
    "CERTIFY_SQRT2_CUT": ("SQRT2_LOWER_BOUND_EXACT", "SQRT2_UPPER_BOUND_EXACT"),
    "CERTIFY_QUADRATIC_MEAN_VALUE": (
        "QUADRATIC_COEFFICIENTS_EXACT",
        "CLOSED_INTERVAL_EXACT",
    ),
    "CERTIFY_BEZOUT": ("INTEGER_A_EXACT", "INTEGER_B_EXACT"),
    "CERTIFY_CAUCHY_RIEMANN": (
        "REAL_POLYNOMIAL_POTENTIAL",
        "IMAG_POLYNOMIAL_POTENTIAL",
        "REAL_COORDINATE_PAIR",
    ),
    "CERTIFY_RATIONAL_RESIDUE": (
        "RATIONAL_MEROMORPHIC_FORM",
        "COMPLEX_COORDINATE_SYMBOL",
        "RATIONAL_POLE_EXACT",
    ),
    "EXACT_TO_SYMBOLIC_POLYNOMIAL": ("POLYNOMIAL_COEFFICIENTS_EXACT",),
    "SYMBOLIC_TO_NUMERICAL_EVALUATION": (
        "SYMBOLIC_POLYNOMIAL",
        "EVALUATION_GRID_EXACT",
    ),
    "CERTIFY_GRID_EVALUATION": ("NUMERICAL_POLYNOMIAL_EVALUATION",),
    "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE": (
        "WEIERSTRASS_G2_EXACT",
        "WEIERSTRASS_G3_EXACT",
    ),
    "CERTIFY_RECTANGULAR_PERIODS": ("SYMBOLIC_WEIERSTRASS_CURVE",),
}

_OPERATOR_FAMILIES = {
    "CERTIFY_SQRT2_CUT": "F1",
    "CERTIFY_QUADRATIC_MEAN_VALUE": "F2",
    "CERTIFY_BEZOUT": "F3",
    "CERTIFY_CAUCHY_RIEMANN": "C1",
    "CERTIFY_RATIONAL_RESIDUE": "C2",
    "EXACT_TO_SYMBOLIC_POLYNOMIAL": "X1",
    "SYMBOLIC_TO_NUMERICAL_EVALUATION": "X1",
    "CERTIFY_GRID_EVALUATION": "X1",
    "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE": "X2",
    "CERTIFY_RECTANGULAR_PERIODS": "X2",
}

_OPERATOR_PORT_NAMES = {
    "CERTIFY_SQRT2_CUT": ("lower_bound", "upper_bound"),
    "CERTIFY_QUADRATIC_MEAN_VALUE": ("coefficients", "interval"),
    "CERTIFY_BEZOUT": ("integer_a", "integer_b"),
    "CERTIFY_CAUCHY_RIEMANN": ("real_part", "imag_part", "coordinates"),
    "CERTIFY_RATIONAL_RESIDUE": ("form", "variable", "pole"),
    "EXACT_TO_SYMBOLIC_POLYNOMIAL": ("coefficients",),
    "SYMBOLIC_TO_NUMERICAL_EVALUATION": ("polynomial", "grid"),
    "CERTIFY_GRID_EVALUATION": ("evaluation",),
    "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE": ("g2", "g3"),
    "CERTIFY_RECTANGULAR_PERIODS": ("curve",),
}


def _find_unique(inputs: Mapping[str, Artifact], semantic_type: str) -> Artifact:
    if len(inputs) > _MAX_OPERATOR_INPUTS:
        raise ValueError("operator input count exceeds the resource limit")
    matches = [artifact for artifact in inputs.values() if artifact.semantic_type == semantic_type]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {semantic_type} input")
    return matches[0]


def _find_unique_tuple(inputs: tuple[Artifact, ...], semantic_type: str) -> Artifact:
    if type(inputs) is not tuple or len(inputs) > _MAX_OPERATOR_INPUTS:
        raise ValueError("operator verifier input count exceeds the resource limit")
    matches = [artifact for artifact in inputs if artifact.semantic_type == semantic_type]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {semantic_type} input")
    return matches[0]


def _binding(bindings: Bindings, key: str, expected_type: type) -> Any:
    if type(bindings) is not tuple or len(bindings) > _MAX_BINDINGS:
        raise ValueError("operator bindings exceed the resource limit")
    matches = [value for name, value in bindings if name == key]
    if len(matches) != 1 or type(matches[0]) is not expected_type:
        raise ValueError(f"missing or invalid binding: {key}")
    return matches[0]


def _operator_artifacts(
    operator_id: str,
    inputs: Mapping[str, Artifact] | tuple[Artifact, ...],
) -> tuple[Artifact, ...]:
    required = _OPERATOR_INPUT_TYPES.get(operator_id)
    if required is None:
        raise ValueError("unknown v0.20 operator identity domain")
    if isinstance(inputs, Mapping):
        if len(inputs) > _MAX_OPERATOR_INPUTS:
            raise ValueError("operator input count exceeds the resource limit")
        available = tuple(inputs.values())
    elif type(inputs) is tuple:
        if len(inputs) > _MAX_OPERATOR_INPUTS:
            raise ValueError("operator verifier input count exceeds the resource limit")
        available = inputs
    else:
        raise TypeError("operator inputs must be a mapping or exact tuple")
    if any(type(artifact) is not Artifact for artifact in available):
        raise TypeError("operator inputs must contain exact Artifact values")
    selected: list[Artifact] = []
    for semantic_type in required:
        matches = [artifact for artifact in available if artifact.semantic_type == semantic_type]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {semantic_type} input")
        selected.append(matches[0])
    return tuple(selected)


def _canonical_update(
    digest: Any,
    value: object,
    budget: list[int],
    *,
    depth: int = 0,
) -> None:
    if depth > 64 or budget[0] <= 0:
        raise ValueError("canonical identity exceeds the resource limit")
    budget[0] -= 1

    def emit(tag: bytes, payload: bytes = b"") -> None:
        if len(payload) > _MAX_CANONICAL_TEXT_BYTES:
            raise ValueError("canonical identity text exceeds the resource limit")
        digest.update(tag)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)

    if value is None:
        emit(b"N")
    elif type(value) is bool:
        emit(b"B", b"1" if value else b"0")
    elif type(value) is int:
        emit(b"I", str(value).encode("ascii"))
    elif type(value) is Fraction:
        emit(b"Q")
        _canonical_update(digest, value.numerator, budget, depth=depth + 1)
        _canonical_update(digest, value.denominator, budget, depth=depth + 1)
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite float cannot enter a derived identity")
        emit(b"F", value.hex().encode("ascii"))
    elif type(value) is str:
        emit(b"S", value.encode("utf-8"))
    elif type(value) is tuple:
        emit(b"T", str(len(value)).encode("ascii"))
        for item in value:
            _canonical_update(digest, item, budget, depth=depth + 1)
    elif isinstance(value, sp.Basic):
        emit(b"Y", sp.srepr(value).encode("utf-8"))
    elif is_dataclass(value) and not isinstance(value, type):
        value_type = type(value)
        emit(
            b"D",
            f"{value_type.__module__}.{value_type.__qualname__}".encode("utf-8"),
        )
        for field in fields(value):
            emit(b"K", field.name.encode("utf-8"))
            _canonical_update(digest, getattr(value, field.name), budget, depth=depth + 1)
    else:
        raise TypeError(f"unsupported canonical identity value: {type(value).__name__}")


def _derived_artifact_id(
    operator_id: str,
    inputs: Mapping[str, Artifact] | tuple[Artifact, ...],
    semantic_type: str,
    representation_class: str,
    exactness_class: str,
    value: object,
) -> str:
    digest = hashlib.sha256()
    _canonical_update(
        digest,
        (
            "PCT_V0_20_DERIVED_ARTIFACT_V1",
            operator_id,
            _operator_artifacts(operator_id, inputs),
            semantic_type,
            representation_class,
            exactness_class,
            value,
        ),
        [_MAX_CANONICAL_NODES],
    )
    return f"derived:{operator_id}:{digest.hexdigest()}"


def _lineage(
    operator_id: str,
    inputs: Mapping[str, Artifact] | tuple[Artifact, ...],
) -> tuple[str, ...]:
    rows: list[str] = []
    for artifact in _operator_artifacts(operator_id, inputs):
        if (
            type(artifact) is not Artifact
            or type(artifact.provenance) is not tuple
            or len(artifact.provenance) > _MAX_LINEAGE_ITEMS
            or any(
                type(item) is not str or not item or len(item) > _MAX_IDENTIFIER_LENGTH
                for item in artifact.provenance
            )
            or type(artifact.artifact_id) is not str
            or not artifact.artifact_id
            or len(artifact.artifact_id) > _MAX_IDENTIFIER_LENGTH
        ):
            raise ValueError("input provenance exceeds the resource limit")
        rows.extend(artifact.provenance)
        rows.append(artifact.artifact_id)
    rows.append(operator_id)
    result = tuple(dict.fromkeys(rows))
    if len(result) > _MAX_LINEAGE_ITEMS:
        raise ValueError("derived provenance exceeds the resource limit")
    return result


def _output(
    operator_id: str,
    inputs: Mapping[str, Artifact],
    semantic_type: str,
    representation_class: str,
    exactness_class: str,
    value: object,
) -> Artifact:
    provenance = _lineage(operator_id, inputs)
    return Artifact(
        artifact_id=_derived_artifact_id(
            operator_id,
            inputs,
            semantic_type,
            representation_class,
            exactness_class,
            value,
        ),
        semantic_type=semantic_type,
        representation_class=representation_class,
        value=value,
        exactness_class=exactness_class,
        metadata=(),
        provenance=provenance,
    )


def _failure(operator_id: str) -> OperatorFailure:
    return OperatorFailure("INVALID", "bounded certificate construction rejected input", operator_id)


def _verification(passed: bool, verifier_class: str) -> VerificationResult:
    return VerificationResult(
        passed,
        verifier_class,
        "certificate replay passed" if passed else "certificate replay failed",
    )


def _output_schema(
    output: object,
    *,
    operator_id: str,
    inputs: tuple[Artifact, ...],
    semantic_type: str,
    representation_class: str,
    exactness_class: str,
    value_type: type,
) -> bool:
    if not (
        type(output) is Artifact
        and type(output.artifact_id) is str
        and bool(output.artifact_id)
        and len(output.artifact_id) <= _MAX_IDENTIFIER_LENGTH
        and output.semantic_type == semantic_type
        and output.representation_class == representation_class
        and output.exactness_class == exactness_class
        and type(output.value) is value_type
        and output.metadata == ()
        and type(output.provenance) is tuple
        and len(output.provenance) <= _MAX_LINEAGE_ITEMS
        and all(
            type(item) is str and bool(item) and len(item) <= _MAX_IDENTIFIER_LENGTH
            for item in output.provenance
        )
        and len(set(output.provenance)) == len(output.provenance)
    ):
        return False
    return (
        output.artifact_id
        == _derived_artifact_id(
            operator_id,
            inputs,
            semantic_type,
            representation_class,
            exactness_class,
            output.value,
        )
        and output.provenance == _lineage(operator_id, inputs)
    )


def _execute_sqrt2_cut(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_SQRT2_CUT"
    try:
        lower = _find_unique(inputs, "SQRT2_LOWER_BOUND_EXACT").value
        upper = _find_unique(inputs, "SQRT2_UPPER_BOUND_EXACT").value
        certificate = certify_sqrt2_cut(lower, upper)
        return _output(operator_id, inputs, "SQRT2_CUT_CERTIFICATE", "EXACT_CERTIFICATE", "EXACT", certificate)
    except Exception:
        return _failure(operator_id)


def _verify_sqrt2_cut_step(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        lower = _find_unique_tuple(inputs, "SQRT2_LOWER_BOUND_EXACT").value
        upper = _find_unique_tuple(inputs, "SQRT2_UPPER_BOUND_EXACT").value
        passed = _output_schema(
            output,
            operator_id="CERTIFY_SQRT2_CUT",
            inputs=inputs,
            semantic_type="SQRT2_CUT_CERTIFICATE",
            representation_class="EXACT_CERTIFICATE",
            exactness_class="EXACT",
            value_type=Sqrt2CutCertificate,
        ) and verify_sqrt2_cut(lower, upper, output.value)
    except Exception:
        passed = False
    return _verification(passed, "SQRT2_CUT_REPLAY")


def _execute_quadratic_mvt(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_QUADRATIC_MEAN_VALUE"
    try:
        coefficients = _find_unique(inputs, "QUADRATIC_COEFFICIENTS_EXACT").value
        left, right = _find_unique(inputs, "CLOSED_INTERVAL_EXACT").value
        certificate = certify_quadratic_mean_value(coefficients, left, right)
        return _output(
            operator_id,
            inputs,
            "QUADRATIC_MEAN_VALUE_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "EXACT",
            certificate,
        )
    except Exception:
        return _failure(operator_id)


def _verify_quadratic_mvt_step(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        coefficients = _find_unique_tuple(inputs, "QUADRATIC_COEFFICIENTS_EXACT").value
        left, right = _find_unique_tuple(inputs, "CLOSED_INTERVAL_EXACT").value
        passed = _output_schema(
            output,
            operator_id="CERTIFY_QUADRATIC_MEAN_VALUE",
            inputs=inputs,
            semantic_type="QUADRATIC_MEAN_VALUE_CERTIFICATE",
            representation_class="EXACT_CERTIFICATE",
            exactness_class="EXACT",
            value_type=QuadraticMeanValueCertificate,
        ) and verify_quadratic_mean_value(coefficients, left, right, output.value)
    except Exception:
        passed = False
    return _verification(passed, "QUADRATIC_MVT_REPLAY")


def _execute_bezout(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_BEZOUT"
    try:
        a = _find_unique(inputs, "INTEGER_A_EXACT").value
        b = _find_unique(inputs, "INTEGER_B_EXACT").value
        certificate = certify_bezout(a, b)
        return _output(operator_id, inputs, "BEZOUT_CERTIFICATE", "EXACT_CERTIFICATE", "EXACT", certificate)
    except Exception:
        return _failure(operator_id)


def _verify_bezout_step(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        a = _find_unique_tuple(inputs, "INTEGER_A_EXACT").value
        b = _find_unique_tuple(inputs, "INTEGER_B_EXACT").value
        passed = _output_schema(
            output,
            operator_id="CERTIFY_BEZOUT",
            inputs=inputs,
            semantic_type="BEZOUT_CERTIFICATE",
            representation_class="EXACT_CERTIFICATE",
            exactness_class="EXACT",
            value_type=BezoutCertificate,
        ) and verify_bezout_certificate(a, b, output.value)
    except Exception:
        passed = False
    return _verification(passed, "BEZOUT_REPLAY")


def _materialize_cauchy_riemann_stage(inputs: Mapping[str, Artifact]) -> Artifact:
    u = _find_unique(inputs, "REAL_POLYNOMIAL_POTENTIAL").value
    v = _find_unique(inputs, "IMAG_POLYNOMIAL_POTENTIAL").value
    x, y = _find_unique(inputs, "REAL_COORDINATE_PAIR").value
    certificate = certify_cauchy_riemann(u, v, x=x, y=y)
    return _output(
        "CERTIFY_CAUCHY_RIEMANN",
        inputs,
        "CAUCHY_RIEMANN_CERTIFICATE",
        "SYMBOLIC_CERTIFICATE",
        "SYMBOLIC",
        certificate,
    )


def _execute_cauchy_riemann(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_CAUCHY_RIEMANN"
    try:
        return _materialize_cauchy_riemann_stage(inputs)
    except Exception:
        return _failure(operator_id)


def _verify_cauchy_riemann_step(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        u = _find_unique_tuple(inputs, "REAL_POLYNOMIAL_POTENTIAL").value
        v = _find_unique_tuple(inputs, "IMAG_POLYNOMIAL_POTENTIAL").value
        x, y = _find_unique_tuple(inputs, "REAL_COORDINATE_PAIR").value
        passed = _output_schema(
            output,
            operator_id="CERTIFY_CAUCHY_RIEMANN",
            inputs=inputs,
            semantic_type="CAUCHY_RIEMANN_CERTIFICATE",
            representation_class="SYMBOLIC_CERTIFICATE",
            exactness_class="SYMBOLIC",
            value_type=CauchyRiemannCertificate,
        ) and verify_cauchy_riemann(u, v, output.value, x=x, y=y)
    except Exception:
        passed = False
    return _verification(passed, "CAUCHY_RIEMANN_REPLAY")


def _materialize_residue_stage(inputs: Mapping[str, Artifact]) -> Artifact:
    expression = _find_unique(inputs, "RATIONAL_MEROMORPHIC_FORM").value
    variable = _find_unique(inputs, "COMPLEX_COORDINATE_SYMBOL").value
    pole = _find_unique(inputs, "RATIONAL_POLE_EXACT").value
    certificate = certify_residue(expression, variable=variable, pole=pole)
    return _output(
        "CERTIFY_RATIONAL_RESIDUE",
        inputs,
        "RESIDUE_CERTIFICATE",
        "SYMBOLIC_CERTIFICATE",
        "SYMBOLIC",
        certificate,
    )


def _execute_residue(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_RATIONAL_RESIDUE"
    try:
        return _materialize_residue_stage(inputs)
    except Exception:
        return _failure(operator_id)


def _verify_residue_step(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        expression = _find_unique_tuple(inputs, "RATIONAL_MEROMORPHIC_FORM").value
        variable = _find_unique_tuple(inputs, "COMPLEX_COORDINATE_SYMBOL").value
        pole = _find_unique_tuple(inputs, "RATIONAL_POLE_EXACT").value
        passed = _output_schema(
            output,
            operator_id="CERTIFY_RATIONAL_RESIDUE",
            inputs=inputs,
            semantic_type="RESIDUE_CERTIFICATE",
            representation_class="SYMBOLIC_CERTIFICATE",
            exactness_class="SYMBOLIC",
            value_type=ResidueCertificate,
        ) and verify_residue(expression, output.value, variable=variable, pole=pole)
    except Exception:
        passed = False
    return _verification(passed, "RATIONAL_RESIDUE_REPLAY")


def _symbolic_polynomial(coefficients: tuple[Fraction, ...]) -> SymbolicPolynomial:
    if type(coefficients) is not tuple or not coefficients or any(
        type(value) is not Fraction for value in coefficients
    ):
        raise TypeError("coefficients must be a nonempty exact Fraction tuple")
    if len(coefficients) > _MAX_VECTOR_ITEMS or any(
        max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > _MAX_EXACT_BITS
        for value in coefficients
    ):
        raise ValueError("polynomial coefficients exceed the resource limit")
    x = sp.Symbol("x")
    expression = sp.Add(
        *(
            sp.Rational(coefficient.numerator, coefficient.denominator) * x**power
            for power, coefficient in enumerate(coefficients)
        )
    )
    return SymbolicPolynomial(coefficients, x, expression)


def _materialize_x1_symbolic_stage(coefficients: Artifact) -> Artifact:
    """Build the exact symbolic stage, including its bounded identity receipt."""

    if type(coefficients) is not Artifact:
        raise TypeError("X1 coefficients must be supplied as an exact Artifact")
    inputs = {"coefficients": coefficients}
    value = _symbolic_polynomial(coefficients.value)
    return _output(
        "EXACT_TO_SYMBOLIC_POLYNOMIAL",
        inputs,
        "SYMBOLIC_POLYNOMIAL",
        "SYMBOLIC_POLYNOMIAL",
        "SYMBOLIC",
        value,
    )


def required_stage_receipts_are_admissible(
    family: str,
    inputs: Mapping[str, Artifact],
) -> bool:
    """Check bounded receipt construction shared by goals and operators.

    These families accept symbolic roots or require a symbolic bridge.  Their
    closed goal domain therefore includes the ability to construct the exact
    deterministic artifact receipt, not merely the underlying mathematical
    certificate.  Calling the same materializers here and during execution
    prevents canonical size/node limits from drifting into a later false
    ``INVALID`` result.
    """

    if type(inputs) is not dict:
        return False
    try:
        if family == "C1":
            output = _materialize_cauchy_riemann_stage(inputs)
        elif family == "C2":
            output = _materialize_residue_stage(inputs)
        elif family == "X1":
            output = _materialize_x1_symbolic_stage(inputs["coefficients"])
        else:
            return False
        return type(output) is Artifact
    except Exception:
        return False


def _execute_exact_to_symbolic(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "EXACT_TO_SYMBOLIC_POLYNOMIAL"
    try:
        coefficients = _find_unique(inputs, "POLYNOMIAL_COEFFICIENTS_EXACT")
        return _materialize_x1_symbolic_stage(
            coefficients,
        )
    except Exception:
        return _failure(operator_id)


def _verify_exact_to_symbolic(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        coefficients = _find_unique_tuple(inputs, "POLYNOMIAL_COEFFICIENTS_EXACT").value
        passed = _output_schema(
            output,
            operator_id="EXACT_TO_SYMBOLIC_POLYNOMIAL",
            inputs=inputs,
            semantic_type="SYMBOLIC_POLYNOMIAL",
            representation_class="SYMBOLIC_POLYNOMIAL",
            exactness_class="SYMBOLIC",
            value_type=SymbolicPolynomial,
        ) and output.value == _symbolic_polynomial(coefficients)
    except Exception:
        passed = False
    return _verification(passed, "EXACT_TO_SYMBOLIC_REPLAY")


def _numerical_evaluation(
    polynomial: SymbolicPolynomial,
    grid: tuple[Fraction, ...],
) -> NumericalPolynomialEvaluation:
    if type(polynomial) is not SymbolicPolynomial:
        raise TypeError("symbolic polynomial has the wrong type")
    if polynomial != _symbolic_polynomial(polynomial.coefficients):
        raise ValueError("symbolic polynomial is not bound to its exact coefficients")
    if type(grid) is not tuple or not grid or any(type(value) is not Fraction for value in grid):
        raise TypeError("grid must be a nonempty exact Fraction tuple")
    if (
        len(grid) > _MAX_VECTOR_ITEMS
        or len(polynomial.coefficients) * len(grid) > _MAX_GRID_WORK
        or any(
            max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > _MAX_EXACT_BITS
            for value in grid
        )
    ):
        raise ValueError("numerical polynomial evaluation exceeds the resource limit")
    # Evaluate in exact rational arithmetic first, then perform one explicit
    # IEEE-754 conversion per point.  This makes the numerical bridge's sole
    # rounding step visible to the downstream enclosure certificate and avoids
    # depending on SymPy's evaluation precision heuristics.
    exact_values: list[Fraction] = []
    for point in grid:
        value = Fraction(0)
        for coefficient in reversed(polynomial.coefficients):
            value = value * point + coefficient
            if max(
                abs(value.numerator).bit_length(),
                value.denominator.bit_length(),
            ) > _MAX_EXACT_BITS:
                raise ValueError(
                    "exact polynomial evaluation exceeds the rational resource limit"
                )
        exact_values.append(value)
    try:
        numerical_values = tuple(float(value) for value in exact_values)
    except (OverflowError, ValueError) as exc:
        raise _NumericallyUnsafeBridgeError(
            "exact polynomial value is outside finite binary64 range"
        ) from exc
    if any(type(value) is not float or not math.isfinite(value) for value in numerical_values):
        raise _NumericallyUnsafeBridgeError(
            "exact polynomial value produced a non-finite binary64 result"
        )
    return NumericalPolynomialEvaluation(polynomial.coefficients, grid, numerical_values)


def _execute_symbolic_to_numerical(
    inputs: Mapping[str, Artifact],
    bindings: Bindings,
) -> Artifact | OperatorFailure:
    operator_id = "SYMBOLIC_TO_NUMERICAL_EVALUATION"
    try:
        polynomial = _find_unique(inputs, "SYMBOLIC_POLYNOMIAL").value
        grid = _find_unique(inputs, "EVALUATION_GRID_EXACT").value
        value = _numerical_evaluation(polynomial, grid)
        return _output(
            operator_id,
            inputs,
            "NUMERICAL_POLYNOMIAL_EVALUATION",
            "NUMERICAL_SERIES",
            "NUMERICAL",
            value,
        )
    except _NumericallyUnsafeBridgeError as exc:
        return OperatorFailure("NUMERICALLY_UNSAFE", str(exc), operator_id)
    except Exception:
        return _failure(operator_id)


def _verify_symbolic_to_numerical(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        polynomial = _find_unique_tuple(inputs, "SYMBOLIC_POLYNOMIAL").value
        grid = _find_unique_tuple(inputs, "EVALUATION_GRID_EXACT").value
        passed = _output_schema(
            output,
            operator_id="SYMBOLIC_TO_NUMERICAL_EVALUATION",
            inputs=inputs,
            semantic_type="NUMERICAL_POLYNOMIAL_EVALUATION",
            representation_class="NUMERICAL_SERIES",
            exactness_class="NUMERICAL",
            value_type=NumericalPolynomialEvaluation,
        ) and output.value == _numerical_evaluation(polynomial, grid)
    except Exception:
        passed = False
    return _verification(passed, "SYMBOLIC_TO_NUMERICAL_REPLAY")


def _execute_grid_certificate(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_GRID_EVALUATION"
    try:
        evaluation = _find_unique(inputs, "NUMERICAL_POLYNOMIAL_EVALUATION").value
        if type(evaluation) is not NumericalPolynomialEvaluation:
            raise TypeError("numerical evaluation has the wrong type")
        tolerance = _binding(bindings, "absolute_error_tolerance", Fraction)
        certificate = certify_grid_evaluation(
            evaluation.coefficients,
            evaluation.grid,
            evaluation.numerical_values,
            tolerance,
        )
        return _output(
            operator_id,
            inputs,
            "GRID_EVALUATION_CERTIFICATE",
            "NUMERICAL_CERTIFICATE",
            "NUMERICAL",
            certificate,
        )
    except Exception:
        return _failure(operator_id)


def _verify_grid_certificate(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        evaluation = _find_unique_tuple(inputs, "NUMERICAL_POLYNOMIAL_EVALUATION").value
        certificate = output.value
        passed = (
            type(evaluation) is NumericalPolynomialEvaluation
            and _output_schema(
                output,
                operator_id="CERTIFY_GRID_EVALUATION",
                inputs=inputs,
                semantic_type="GRID_EVALUATION_CERTIFICATE",
                representation_class="NUMERICAL_CERTIFICATE",
                exactness_class="NUMERICAL",
                value_type=GridEvaluationCertificate,
            )
            and certificate.coefficients == evaluation.coefficients
            and certificate.grid == evaluation.grid
            and certificate.numerical_values == evaluation.numerical_values
            and verify_grid_evaluation(certificate)
        )
    except Exception:
        passed = False
    return _verification(passed, "GRID_EVALUATION_REPLAY")


def _weierstrass_curve(g2: Fraction, g3: Fraction) -> WeierstrassCurve:
    if type(g2) is not Fraction or type(g3) is not Fraction:
        raise TypeError("Weierstrass invariants must be exact Fraction values")
    if any(
        max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 1024
        for value in (g2, g3)
    ):
        raise ValueError("Weierstrass invariants exceed the resource limit")
    x, y = sp.symbols("x y")
    g2_expr = sp.Rational(g2.numerator, g2.denominator)
    g3_expr = sp.Rational(g3.numerator, g3.denominator)
    equation = y**2 - (4 * x**3 - g2_expr * x - g3_expr)
    elliptic_discriminant = g2**3 - 27 * g3**2
    if elliptic_discriminant <= 0:
        raise ValueError("v0.20 period domain requires positive discriminant")
    return WeierstrassCurve(
        g2=g2,
        g3=g3,
        x=x,
        y=y,
        equation=equation,
        elliptic_discriminant=elliptic_discriminant,
        polynomial_discriminant=16 * elliptic_discriminant,
    )


def _execute_invariants_to_curve(
    inputs: Mapping[str, Artifact],
    bindings: Bindings,
) -> Artifact | OperatorFailure:
    operator_id = "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE"
    try:
        g2 = _find_unique(inputs, "WEIERSTRASS_G2_EXACT").value
        g3 = _find_unique(inputs, "WEIERSTRASS_G3_EXACT").value
        curve = _weierstrass_curve(g2, g3)
        return _output(
            operator_id,
            inputs,
            "SYMBOLIC_WEIERSTRASS_CURVE",
            "SYMBOLIC_CURVE",
            "SYMBOLIC",
            curve,
        )
    except Exception:
        return _failure(operator_id)


def _verify_invariants_to_curve(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        g2 = _find_unique_tuple(inputs, "WEIERSTRASS_G2_EXACT").value
        g3 = _find_unique_tuple(inputs, "WEIERSTRASS_G3_EXACT").value
        passed = _output_schema(
            output,
            operator_id="EXACT_INVARIANTS_TO_SYMBOLIC_CURVE",
            inputs=inputs,
            semantic_type="SYMBOLIC_WEIERSTRASS_CURVE",
            representation_class="SYMBOLIC_CURVE",
            exactness_class="SYMBOLIC",
            value_type=WeierstrassCurve,
        ) and output.value == _weierstrass_curve(g2, g3)
    except Exception:
        passed = False
    return _verification(passed, "WEIERSTRASS_CURVE_REPLAY")


def _execute_period_certificate(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CERTIFY_RECTANGULAR_PERIODS"
    try:
        curve = _find_unique(inputs, "SYMBOLIC_WEIERSTRASS_CURVE").value
        if type(curve) is not WeierstrassCurve:
            raise TypeError("symbolic curve has the wrong type")
        if curve != _weierstrass_curve(curve.g2, curve.g3):
            raise ValueError("symbolic curve is not bound to its exact invariants")
        decimal_places = _binding(bindings, "decimal_places", int)
        certificate = certify_rectangular_periods(curve.g2, curve.g3, decimal_places=decimal_places)
        return _output(
            operator_id,
            inputs,
            "RECTANGULAR_PERIOD_CERTIFICATE",
            "NUMERICAL_CERTIFICATE",
            "NUMERICAL",
            certificate,
        )
    except PeriodCertificationUnavailable as exc:
        return OperatorFailure("NUMERICALLY_UNSAFE", str(exc), operator_id)
    except ArithmeticError as exc:
        return OperatorFailure("NUMERICALLY_UNSAFE", str(exc), operator_id)
    except Exception:
        return _failure(operator_id)


def _verify_period_certificate_step(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    try:
        curve = _find_unique_tuple(inputs, "SYMBOLIC_WEIERSTRASS_CURVE").value
        certificate = output.value
        passed = (
            type(curve) is WeierstrassCurve
            and curve == _weierstrass_curve(curve.g2, curve.g3)
            and _output_schema(
                output,
                operator_id="CERTIFY_RECTANGULAR_PERIODS",
                inputs=inputs,
                semantic_type="RECTANGULAR_PERIOD_CERTIFICATE",
                representation_class="NUMERICAL_CERTIFICATE",
                exactness_class="NUMERICAL",
                value_type=PeriodCertificate,
            )
            and certificate.g2 == curve.g2
            and certificate.g3 == curve.g3
            and verify_period_certificate(certificate)
        )
    except Exception:
        passed = False
    return _verification(passed, "RECTANGULAR_PERIOD_REPLAY")


def verify_cross_class_pipeline_receipt(
    family: str,
    inputs: Mapping[str, Artifact],
    candidate: Artifact,
) -> bool:
    """Replay the deterministic X1/X2 producer chain and its artifact receipt.

    Artifact provenance is evidence of the declared producer chain, not proof
    that an untrusted process actually executed it.  This replay nevertheless
    prevents a bare certificate or a receipt borrowed from another source from
    satisfying the campaign's cross-class candidate contract.
    """

    try:
        if family == "X1":
            coefficients = _find_unique(inputs, "POLYNOMIAL_COEFFICIENTS_EXACT")
            grid = _find_unique(inputs, "EVALUATION_GRID_EXACT")
            polynomial_value = _symbolic_polynomial(coefficients.value)
            polynomial = _output(
                "EXACT_TO_SYMBOLIC_POLYNOMIAL",
                {"coefficients": coefficients},
                "SYMBOLIC_POLYNOMIAL",
                "SYMBOLIC_POLYNOMIAL",
                "SYMBOLIC",
                polynomial_value,
            )
            evaluation_value = _numerical_evaluation(polynomial_value, grid.value)
            evaluation = _output(
                "SYMBOLIC_TO_NUMERICAL_EVALUATION",
                {"polynomial": polynomial, "grid": grid},
                "NUMERICAL_POLYNOMIAL_EVALUATION",
                "NUMERICAL_SERIES",
                "NUMERICAL",
                evaluation_value,
            )
            return _verify_grid_certificate((evaluation,), candidate).passed
        if family == "X2":
            g2 = _find_unique(inputs, "WEIERSTRASS_G2_EXACT")
            g3 = _find_unique(inputs, "WEIERSTRASS_G3_EXACT")
            curve = _output(
                "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE",
                {"g2": g2, "g3": g3},
                "SYMBOLIC_WEIERSTRASS_CURVE",
                "SYMBOLIC_CURVE",
                "SYMBOLIC",
                _weierstrass_curve(g2.value, g3.value),
            )
            return _verify_period_certificate_step((curve,), candidate).passed
    except Exception:
        return False
    return False


def _closed_spec(
    operator_id: str,
    input_types: tuple[str, ...],
    output_type: str,
    representation_class: str,
    exactness_class: str,
    execute: Any,
    *,
    verify: Any,
    cost: int = 1,
) -> OperatorSpec:
    """Build a spec with complete ports/objectives on the strict core.

    The feature branch predates the core's typed-port fields, so the keyword
    extension is detected once at construction time.  On the strict integrated
    core every v0.20 spec receives explicit contracts and a nonempty objective.
    """

    parameters = inspect.signature(_spec).parameters
    options: dict[str, object] = {"verify": verify, "cost": cost}
    if "input_contracts" in parameters:
        options["input_contracts"] = tuple(
            materialize_v0_20_artifact_type(semantic_type)
            for semantic_type in input_types
        )
    if "port_names" in parameters:
        options["port_names"] = _OPERATOR_PORT_NAMES[operator_id]
    if "objectives" in parameters:
        family = _OPERATOR_FAMILIES[operator_id]
        options["objectives"] = (V0_20_CONTRACTS[family].target.objective,)
    return _spec(
        operator_id,
        input_types,
        output_type,
        representation_class,
        exactness_class,
        execute,
        **options,
    )


def build_v0_20_operator_registry() -> dict[str, OperatorSpec]:
    """Return the historical registry plus the closed v0.20 certificate paths."""

    registry = dict(build_cross_representation_operator_registry())
    specifications = (
        _closed_spec(
            "CERTIFY_SQRT2_CUT",
            ("SQRT2_LOWER_BOUND_EXACT", "SQRT2_UPPER_BOUND_EXACT"),
            "SQRT2_CUT_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "EXACT",
            _execute_sqrt2_cut,
            verify=_verify_sqrt2_cut_step,
        ),
        _closed_spec(
            "CERTIFY_QUADRATIC_MEAN_VALUE",
            ("QUADRATIC_COEFFICIENTS_EXACT", "CLOSED_INTERVAL_EXACT"),
            "QUADRATIC_MEAN_VALUE_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "EXACT",
            _execute_quadratic_mvt,
            verify=_verify_quadratic_mvt_step,
        ),
        _closed_spec(
            "CERTIFY_BEZOUT",
            ("INTEGER_A_EXACT", "INTEGER_B_EXACT"),
            "BEZOUT_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "EXACT",
            _execute_bezout,
            verify=_verify_bezout_step,
        ),
        _closed_spec(
            "CERTIFY_CAUCHY_RIEMANN",
            (
                "REAL_POLYNOMIAL_POTENTIAL",
                "IMAG_POLYNOMIAL_POTENTIAL",
                "REAL_COORDINATE_PAIR",
            ),
            "CAUCHY_RIEMANN_CERTIFICATE",
            "SYMBOLIC_CERTIFICATE",
            "SYMBOLIC",
            _execute_cauchy_riemann,
            verify=_verify_cauchy_riemann_step,
            cost=2,
        ),
        _closed_spec(
            "CERTIFY_RATIONAL_RESIDUE",
            (
                "RATIONAL_MEROMORPHIC_FORM",
                "COMPLEX_COORDINATE_SYMBOL",
                "RATIONAL_POLE_EXACT",
            ),
            "RESIDUE_CERTIFICATE",
            "SYMBOLIC_CERTIFICATE",
            "SYMBOLIC",
            _execute_residue,
            verify=_verify_residue_step,
            cost=2,
        ),
        _closed_spec(
            "EXACT_TO_SYMBOLIC_POLYNOMIAL",
            ("POLYNOMIAL_COEFFICIENTS_EXACT",),
            "SYMBOLIC_POLYNOMIAL",
            "SYMBOLIC_POLYNOMIAL",
            "SYMBOLIC",
            _execute_exact_to_symbolic,
            verify=_verify_exact_to_symbolic,
            cost=2,
        ),
        _closed_spec(
            "SYMBOLIC_TO_NUMERICAL_EVALUATION",
            ("SYMBOLIC_POLYNOMIAL", "EVALUATION_GRID_EXACT"),
            "NUMERICAL_POLYNOMIAL_EVALUATION",
            "NUMERICAL_SERIES",
            "NUMERICAL",
            _execute_symbolic_to_numerical,
            verify=_verify_symbolic_to_numerical,
            cost=3,
        ),
        _closed_spec(
            "CERTIFY_GRID_EVALUATION",
            ("NUMERICAL_POLYNOMIAL_EVALUATION",),
            "GRID_EVALUATION_CERTIFICATE",
            "NUMERICAL_CERTIFICATE",
            "NUMERICAL",
            _execute_grid_certificate,
            verify=_verify_grid_certificate,
        ),
        _closed_spec(
            "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE",
            ("WEIERSTRASS_G2_EXACT", "WEIERSTRASS_G3_EXACT"),
            "SYMBOLIC_WEIERSTRASS_CURVE",
            "SYMBOLIC_CURVE",
            "SYMBOLIC",
            _execute_invariants_to_curve,
            verify=_verify_invariants_to_curve,
            cost=2,
        ),
        _closed_spec(
            "CERTIFY_RECTANGULAR_PERIODS",
            ("SYMBOLIC_WEIERSTRASS_CURVE",),
            "RECTANGULAR_PERIOD_CERTIFICATE",
            "NUMERICAL_CERTIFICATE",
            "NUMERICAL",
            _execute_period_certificate,
            verify=_verify_period_certificate_step,
            cost=3,
        ),
    )
    for specification in specifications:
        registry[specification.operator_id] = specification
    return registry
