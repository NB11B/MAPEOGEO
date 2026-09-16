from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
from fractions import Fraction
import hashlib
import json
import math
from typing import Any, Mapping

import sympy as sp

from .elliptic_periods import certify_rectangular_periods
from .goals import FAMILIES as V1_FAMILIES, _BUILDERS as V1_BUILDERS, _artifact
from .model import Artifact, ArtifactType, CandidateLineageObligation, GoalSpec, TargetSpec
from .operators import OperatorSpec
from .rigorous_math import (
    certify_bezout,
    certify_cauchy_riemann,
    certify_grid_evaluation,
    certify_quadratic_mean_value,
    certify_residue,
    certify_sqrt2_cut,
)
from .v0_20_contracts import STRICT_V0_20_VERIFIER_CLASS, V0_20_CONTRACTS


FROZEN_FEATURE_BASE_SHA = "32967600a00a5659e49fa3ef056be02567c74efa"
CORE_SPLITS = ("CALIBRATION_V0_20", "VALIDATION_V0_20", "SEALED_V0_20")
CONTROL_SPLIT = "CONTROLS_V0_20"
V0_20_SPLIT_COUNTS = {"CALIBRATION_V0_20": 3, "VALIDATION_V0_20": 1, "SEALED_V0_20": 2}


class TerminalControlKind(str, Enum):
    DOMAIN_REFUSAL = "DOMAIN_REFUSAL"
    VALID_NEGATIVE_RESULT = "VALID_NEGATIVE_RESULT"
    INVALID_TERMINAL_CERTIFICATE = "INVALID_TERMINAL_CERTIFICATE"
    EXTERNAL_VALID_CERTIFICATE = "EXTERNAL_VALID_CERTIFICATE"


REQUIRED_CONTROL_KINDS = tuple(kind.value for kind in TerminalControlKind)

FOUNDATIONAL_FAMILIES = ("F1", "F2", "F3")
COMPLEX_FAMILIES = ("C1", "C2")
CROSS_CLASS_FAMILIES = ("X1", "X2")
NEW_V0_20_FAMILIES = FOUNDATIONAL_FAMILIES + COMPLEX_FAMILIES + CROSS_CLASS_FAMILIES
ALL_V0_20_FAMILIES = tuple(V1_FAMILIES) + NEW_V0_20_FAMILIES
V0_20_EXPECTED_COUNTS = {
    split: len(ALL_V0_20_FAMILIES) * count
    for split, count in V0_20_SPLIT_COUNTS.items()
}
V0_20_TERMINAL_CONTROL_COUNT = 22


@dataclass(frozen=True)
class CaseSignatures:
    exact_sha256: str
    nuisance_sha256: str
    nuisance_relation: str


@dataclass(frozen=True)
class TerminalCandidateControl:
    control_id: str
    family: str
    kind: TerminalControlKind
    goal: GoalSpec
    candidate: Artifact
    expected_verification_pass: bool
    is_distinct_alternative: bool = False
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.control_id or self.family != self.goal.family:
            raise ValueError("terminal control identity/family mismatch")
        if any(
            root is self.candidate or root.artifact_id == self.candidate.artifact_id
            for root in self.goal.inputs.values()
        ):
            raise ValueError("a terminal candidate must remain external to planner roots")
        if self.is_distinct_alternative and self.kind is not TerminalControlKind.EXTERNAL_VALID_CERTIFICATE:
            raise ValueError("only external valid certificates may claim alternative status")

V0_20_REQUIRED_DERIVED_TYPES: dict[str, tuple[str, ...]] = {
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
    **{
        family: dict(V0_20_CONTRACTS[family].constraints)["required_derived_types"]
        for family in NEW_V0_20_FAMILIES
    },
}


def _canonical(value: Any) -> Any:
    if value is None:
        return {"type": "none"}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": str(value)}
    if isinstance(value, Fraction):
        return {"type": "fraction", "numerator": str(value.numerator), "denominator": str(value.denominator)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite floats are not canonical campaign evidence")
        return {"type": "float", "value": value.hex()}
    if isinstance(value, str):
        return {"type": "str", "value": value}
    if isinstance(value, sp.Basic):
        return {"type": "sympy", "srepr": sp.srepr(value)}
    if isinstance(value, Artifact):
        return {
            "type": "artifact",
            "semantic_type": value.semantic_type,
            "representation_class": value.representation_class,
            "exactness_class": value.exactness_class,
            "value": _canonical(value.value),
            "metadata": _canonical(value.metadata),
        }
    if isinstance(value, TargetSpec):
        return {
            "type": "target",
            "target_id": value.target_id,
            "semantic_type": value.semantic_type,
            "representation_class": value.representation_class,
            "objective": value.objective,
            "exactness_class": value.exactness_class,
            "metadata": _canonical(value.metadata),
        }
    if isinstance(value, Mapping):
        rows = [(_canonical(key), _canonical(item)) for key, item in value.items()]
        rows.sort(key=lambda row: json.dumps(row[0], sort_keys=True, separators=(",", ":")))
        return {"type": "mapping", "items": rows}
    if isinstance(value, tuple):
        return {"type": "tuple", "items": [_canonical(item) for item in value]}
    if isinstance(value, list):
        return {"type": "list", "items": [_canonical(item) for item in value]}
    if isinstance(value, (set, frozenset)):
        items = [_canonical(item) for item in value]
        items.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
        return {"type": "set", "items": items}
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("nonfinite complex values are not canonical campaign evidence")
        return {"type": "complex", "real": value.real.hex(), "imag": value.imag.hex()}
    if is_dataclass(value):
        return {"type": f"dataclass:{type(value).__qualname__}", "value": _canonical(asdict(value))}
    raise TypeError(f"unsupported canonical campaign value: {type(value).__qualname__}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def case_content_fingerprint(goal: GoalSpec) -> str:
    """Hash mathematical and execution-protocol content, excluding identities/answers."""

    payload = {
        "family": goal.family,
        "inputs": {key: artifact for key, artifact in sorted(goal.inputs.items())},
        "target": {
            "semantic_type": goal.target.semantic_type,
            "representation_class": goal.target.representation_class,
            "objective": goal.target.objective,
            "exactness_class": goal.target.exactness_class,
            "metadata": goal.target.metadata,
        },
        "constraints": goal.constraints,
        "allowed_numeric_tolerance": goal.allowed_numeric_tolerance,
        "required_verifier_class": goal.required_verifier_class,
        "search_budget": goal.search_budget,
        "lineage_obligation": goal.lineage_obligation,
    }
    return _digest(payload)


def _projective_rational_matrix(value: Any) -> Any:
    """Normalize only the proven nonzero-scalar nuisance for exact G2 inputs."""

    try:
        matrix = tuple(tuple(_exact_fraction(entry) for entry in row) for row in value)
    except (TypeError, ValueError):
        return value
    pivot = next((entry for row in matrix for entry in row if entry != 0), None)
    if pivot is None:
        return matrix
    return tuple(tuple(entry / pivot for entry in row) for row in matrix)


def case_signatures(goal: GoalSpec) -> CaseSignatures:
    """Return exact identity plus one explicitly named nuisance quotient.

    Exact signatures always retain all mathematical values.  The nuisance
    signature differs only for G2, where multiplication of the entire exact
    matrix by one nonzero rational provably preserves rank and nullity.  No
    scalar, translation, projective, or relabeling invariance is inferred for
    any other family.
    """

    exact = case_content_fingerprint(goal)
    relation = "IDENTITY"
    normalized = goal
    if goal.family == "G2" and "observation_matrix" in goal.inputs:
        relation = "G2_NONZERO_RATIONAL_SCALAR"
        inputs = dict(goal.inputs)
        for key in ("observation_matrix", "rational_matrix"):
            if key in inputs:
                inputs[key] = replace(inputs[key], value=_projective_rational_matrix(inputs[key].value))
        normalized = replace(goal, inputs=inputs)
    nuisance_payload = {
        "relation": relation,
        "normalized_exact_content": case_content_fingerprint(normalized),
    }
    return CaseSignatures(exact, _digest(nuisance_payload), relation)


def _matrix_scale(value: tuple[tuple[Any, ...], ...], scale: Fraction) -> tuple[tuple[Any, ...], ...]:
    return tuple(tuple(scale * entry for entry in row) for row in value)


def _diversify_historical_goal(goal: GoalSpec, variant: int) -> GoalSpec:
    inputs = dict(goal.inputs)
    scale = Fraction(variant + 1)
    if goal.family == "G2":
        source = inputs["observation_matrix"]
        inputs["observation_matrix"] = replace(source, value=_matrix_scale(source.value, scale))
    elif goal.family == "G3":
        for key in ("source_boundary", "target_boundary"):
            source = inputs[key]
            inputs[key] = replace(source, value=_matrix_scale(source.value, scale))
    elif goal.family == "G4":
        translation = 7 * variant
        for key in ("barcode_a", "barcode_b"):
            source = inputs[key]
            shifted = tuple((degree, birth + translation, death + translation) for degree, birth, death in source.value)
            inputs[key] = replace(source, value=shifted)
    elif goal.family == "G5":
        n = 4 + variant
        cycle = tuple((k, (k + 1) % n) for k in range(n))
        if variant % 2 == 0:
            graph_b = tuple((k, k + 1) for k in range(n - 1))
            expected = True
        else:
            graph_b = tuple(tuple(reversed(edge)) for edge in reversed(cycle))
            expected = False
        inputs["graph_a"] = replace(inputs["graph_a"], value=cycle)
        inputs["graph_b"] = replace(inputs["graph_b"], value=graph_b)
        goal = replace(goal, sealed_expected_result=expected)
    elif goal.family == "G6":
        exact = inputs["exact_matrix"]
        scaled = _matrix_scale(exact.value, scale)
        inputs["exact_matrix"] = replace(exact, value=scaled)
        inputs["numeric_matrix"] = replace(inputs["numeric_matrix"], value=tuple(tuple(float(x) for x in row) for row in scaled))
    elif goal.family == "G7":
        factor = variant + 1
        generator = ((0, factor, 0), (0, 0, f"{2 * factor}*pi"), (0, 0, 0))
        inputs["generator"] = replace(inputs["generator"], value=generator)
    return replace(goal, inputs=inputs)


def _closed_goal(
    goal_id: str,
    family: str,
    inputs: Mapping[str, Artifact],
    sealed_expected_result: object,
    sealed_reference_path: tuple[str, ...],
) -> GoalSpec:
    contract = V0_20_CONTRACTS[family]
    target = contract.target
    return GoalSpec(
        goal_id=goal_id,
        family=family,
        inputs=dict(inputs),
        target=TargetSpec(
            target.target_id,
            target.semantic_type,
            target.representation_class,
            target.objective,
            target.exactness_class,
        ),
        constraints=contract.constraints,
        allowed_numeric_tolerance=contract.allowed_numeric_tolerance,
        required_verifier_class=STRICT_V0_20_VERIFIER_CLASS,
        search_budget=contract.search_budget,
        sealed_expected_result=sealed_expected_result,
        sealed_reference_path=sealed_reference_path,
    )


def _goal_f1(goal_id: str, variant: int) -> GoalSpec:
    """Certify a finite exact rational bracket around sqrt(2)."""

    denominator = 10 ** (variant + 3)
    numerator = math.isqrt(2 * denominator * denominator)
    lower, upper = Fraction(numerator, denominator), Fraction(numerator + 1, denominator)
    inputs = {
        "lower_bound": _artifact(
            goal_id, "lower_bound", "SQRT2_LOWER_BOUND_EXACT", "RATIONAL_SCALAR", lower, "EXACT"
        ),
        "upper_bound": _artifact(
            goal_id, "upper_bound", "SQRT2_UPPER_BOUND_EXACT", "RATIONAL_SCALAR", upper, "EXACT"
        ),
    }
    return _closed_goal(
        goal_id,
        "F1",
        inputs,
        certify_sqrt2_cut(lower, upper),
        ("CERTIFY_SQRT2_CUT", "VERIFY_CANDIDATE"),
    )


def _goal_f2(goal_id: str, variant: int) -> GoalSpec:
    problems = (
        ((Fraction(1), Fraction(-2), Fraction(5)), (Fraction(-4), Fraction(7))),
        ((Fraction(-3, 2), Fraction(4), Fraction(0)), (Fraction(-2), Fraction(5))),
        ((Fraction(0), Fraction(-2), Fraction(5)), (Fraction(-7), Fraction(8))),
        ((Fraction(0), Fraction(0), Fraction(3)), (Fraction(-5), Fraction(2))),
        ((Fraction(2, 3), Fraction(1, 5), Fraction(-7)), (Fraction(-3), Fraction(4))),
        ((Fraction(0), Fraction(7, 3), Fraction(-2)), (Fraction(1, 7), Fraction(11, 3))),
    )
    coefficients, (left, right) = problems[variant % len(problems)]
    inputs = {
        "coefficients": _artifact(
            goal_id,
            "coefficients",
            "QUADRATIC_COEFFICIENTS_EXACT",
            "RATIONAL_TRIPLE",
            coefficients,
            "EXACT",
        ),
        "interval": _artifact(
            goal_id, "interval", "CLOSED_INTERVAL_EXACT", "RATIONAL_PAIR", (left, right), "EXACT"
        ),
    }
    return _closed_goal(
        goal_id,
        "F2",
        inputs,
        certify_quadratic_mean_value(coefficients, left, right),
        ("CERTIFY_QUADRATIC_MEAN_VALUE", "VERIFY_CANDIDATE"),
    )


def _goal_f3(goal_id: str, variant: int) -> GoalSpec:
    a, b = 31 + 11 * variant, 18 + 7 * variant
    inputs = {
        "integer_a": _artifact(goal_id, "integer_a", "INTEGER_A_EXACT", "INTEGER_SCALAR", a, "EXACT"),
        "integer_b": _artifact(goal_id, "integer_b", "INTEGER_B_EXACT", "INTEGER_SCALAR", b, "EXACT"),
    }
    return _closed_goal(
        goal_id,
        "F3",
        inputs,
        certify_bezout(a, b),
        ("CERTIFY_BEZOUT", "VERIFY_CANDIDATE"),
    )


def _goal_c1(goal_id: str, variant: int) -> GoalSpec:
    x, y = sp.symbols("x y", real=True)
    c = sp.Integer(variant + 1)
    u, v = x**2 - y**2 + c * x, 2 * x * y + c * y
    inputs = {
        "real_part": _artifact(
            goal_id, "real_part", "REAL_POLYNOMIAL_POTENTIAL", "SYMBOLIC_EXPRESSION", u, "SYMBOLIC"
        ),
        "imag_part": _artifact(
            goal_id, "imag_part", "IMAG_POLYNOMIAL_POTENTIAL", "SYMBOLIC_EXPRESSION", v, "SYMBOLIC"
        ),
        "coordinates": _artifact(
            goal_id, "coordinates", "REAL_COORDINATE_PAIR", "SYMBOL_PAIR", (x, y), "SYMBOLIC"
        ),
    }
    return _closed_goal(
        goal_id,
        "C1",
        inputs,
        certify_cauchy_riemann(u, v, x=x, y=y),
        ("CERTIFY_CAUCHY_RIEMANN", "VERIFY_CANDIDATE"),
    )


def _goal_c2(goal_id: str, variant: int) -> GoalSpec:
    z = sp.Symbol("z")
    pole = Fraction(variant + 1, variant + 2)
    residue = Fraction(variant + 2, variant + 3)
    pole_expr = sp.Rational(pole.numerator, pole.denominator)
    residue_expr = sp.Rational(residue.numerator, residue.denominator)
    expression = residue_expr / (z - pole_expr) + 1 / (z - pole_expr) ** (2 + variant % 3)
    inputs = {
        "form": _artifact(
            goal_id, "form", "RATIONAL_MEROMORPHIC_FORM", "SYMBOLIC_EXPRESSION", expression, "SYMBOLIC"
        ),
        "variable": _artifact(
            goal_id, "variable", "COMPLEX_COORDINATE_SYMBOL", "SYMBOL", z, "SYMBOLIC"
        ),
        "pole": _artifact(
            goal_id, "pole", "RATIONAL_POLE_EXACT", "RATIONAL_SCALAR", pole, "EXACT"
        ),
    }
    return _closed_goal(
        goal_id,
        "C2",
        inputs,
        certify_residue(expression, variable=z, pole=pole),
        ("CERTIFY_RATIONAL_RESIDUE", "VERIFY_CANDIDATE"),
    )


def _goal_x1(goal_id: str, variant: int) -> GoalSpec:
    coefficients = (Fraction(variant + 1, variant + 2), Fraction(-variant - 2, variant + 3), Fraction(1, variant + 5))
    grid = tuple(Fraction(k, variant + 5) for k in range(5))
    values = tuple(sum(coefficient * point**power for power, coefficient in enumerate(coefficients)) for point in grid)
    tolerance = Fraction(1, 10**12)
    inputs = {
        "coefficients": _artifact(
            goal_id,
            "coefficients",
            "POLYNOMIAL_COEFFICIENTS_EXACT",
            "RATIONAL_VECTOR",
            coefficients,
            "EXACT",
        ),
        "grid": _artifact(
            goal_id, "grid", "EVALUATION_GRID_EXACT", "RATIONAL_VECTOR", grid, "EXACT"
        ),
    }
    return _closed_goal(
        goal_id,
        "X1",
        inputs,
        certify_grid_evaluation(coefficients, grid, tuple(float(value) for value in values), tolerance),
        (
            "EXACT_TO_SYMBOLIC_POLYNOMIAL",
            "SYMBOLIC_TO_NUMERICAL_EVALUATION",
            "CERTIFY_GRID_EVALUATION",
            "VERIFY_CANDIDATE",
        ),
    )


def _goal_x2(goal_id: str, variant: int) -> GoalSpec:
    g2, g3 = Fraction(4 + variant), Fraction(1, variant + 1)
    inputs = {
        "g2": _artifact(goal_id, "g2", "WEIERSTRASS_G2_EXACT", "RATIONAL_SCALAR", g2, "EXACT"),
        "g3": _artifact(goal_id, "g3", "WEIERSTRASS_G3_EXACT", "RATIONAL_SCALAR", g3, "EXACT"),
    }
    decimal_places = dict(V0_20_CONTRACTS["X2"].constraints)["decimal_places"]
    return _closed_goal(
        goal_id,
        "X2",
        inputs,
        certify_rectangular_periods(g2, g3, decimal_places=decimal_places),
        (
            "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE",
            "CERTIFY_RECTANGULAR_PERIODS",
            "VERIFY_CANDIDATE",
        ),
    )


_NEW_BUILDERS = {"F1": _goal_f1, "F2": _goal_f2, "F3": _goal_f3, "C1": _goal_c1, "C2": _goal_c2, "X1": _goal_x1, "X2": _goal_x2}


def _with_v0_20_contract(goal: GoalSpec) -> GoalSpec:
    # Historical G1--G12 contracts remain exactly the registered contracts;
    # v0.20 must not add answer-like roots or legacy state-wide evidence lists.
    lineage_obligation = None
    if goal.family == "X1":
        lineage_obligation = CandidateLineageObligation(
            required_input_keys=frozenset({"coefficients", "grid"}),
            ordered_stage_types=(
                ArtifactType("SYMBOLIC_POLYNOMIAL", "SYMBOLIC_POLYNOMIAL", "SYMBOLIC"),
                ArtifactType(
                    "NUMERICAL_POLYNOMIAL_EVALUATION",
                    "NUMERICAL_SERIES",
                    "NUMERICAL",
                ),
            ),
            stage_required_input_keys=(
                frozenset({"coefficients"}),
                frozenset({"coefficients", "grid"}),
            ),
        )
    elif goal.family == "X2":
        lineage_obligation = CandidateLineageObligation(
            required_input_keys=frozenset({"g2", "g3"}),
            ordered_stage_types=(
                ArtifactType("SYMBOLIC_WEIERSTRASS_CURVE", "SYMBOLIC_CURVE", "SYMBOLIC"),
            ),
            stage_required_input_keys=(frozenset({"g2", "g3"}),),
        )
    return replace(goal, lineage_obligation=lineage_obligation)


def _build_goal(goal_id: str, family: str, variant: int) -> GoalSpec:
    if family in _NEW_BUILDERS:
        goal = _NEW_BUILDERS[family](goal_id, variant)
    else:
        # The repaired historical builders already define six genuinely varied
        # cases indexed 0..5.  Reinterpreting their sealed results here would
        # duplicate the oracle and previously encoded obsolete scalar/vertex
        # shortcuts.
        goal = V1_BUILDERS[family](goal_id, variant)
    return _with_v0_20_contract(goal)


def _replace_input(goal: GoalSpec, key: str, value: Any) -> GoalSpec:
    inputs = dict(goal.inputs)
    inputs[key] = replace(inputs[key], value=value)
    return replace(goal, inputs=inputs)


def _exact_fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean is not an exact rational")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, (int, sp.Integer)):
        return Fraction(int(value))
    if isinstance(value, sp.Rational):
        return Fraction(int(value.p), int(value.q))
    raise TypeError("value is not an exact rational")


def build_v0_20_corpus() -> dict[str, list[GoalSpec]]:
    """Build planner inputs only; terminal controls are deliberately separate."""

    corpus: dict[str, list[GoalSpec]] = {split: [] for split in CORE_SPLITS}
    offset = 0
    for split in CORE_SPLITS:
        for family in ALL_V0_20_FAMILIES:
            for local_index in range(V0_20_SPLIT_COUNTS[split]):
                variant = offset + local_index
                goal_id = f"{split.lower()}:{family.lower()}:{local_index:02d}"
                corpus[split].append(_build_goal(goal_id, family, variant))
        offset += V0_20_SPLIT_COUNTS[split]
    return corpus


def _candidate(goal: GoalSpec, suffix: str, value: Any) -> Artifact:
    return Artifact(
        artifact_id=f"terminal-control:{goal.goal_id}:{suffix}",
        semantic_type=goal.target.semantic_type,
        representation_class=goal.target.representation_class,
        value=value,
        exactness_class=goal.target.exactness_class or "EXACT",
        provenance=("EXTERNAL_TERMINAL_CONTROL",),
    )


def _domain_invalid_goal(family: str, variant: int) -> GoalSpec:
    goal = _build_goal(f"terminal-control:{family.lower()}:domain", family, variant)
    if family == "F1":
        return _replace_input(goal, "lower_bound", Fraction(3, 2))
    if family == "F2":
        return _replace_input(goal, "interval", (Fraction(1), Fraction(1)))
    if family == "F3":
        return _replace_input(goal, "integer_a", Fraction(3, 2))
    if family == "C1":
        return _replace_input(goal, "real_part", sp.oo)
    if family == "C2":
        variable = goal.inputs["variable"].value
        return _replace_input(goal, "form", variable + 1)
    if family == "X1":
        return _replace_input(goal, "grid", ())
    if family == "X2":
        return _replace_input(
            _replace_input(goal, "g2", Fraction(3)),
            "g3",
            Fraction(1),
        )
    raise KeyError(family)


def _execute_control_operator(
    registry: Mapping[str, OperatorSpec],
    operator_id: str,
    inputs: Mapping[str, Artifact],
    bindings: tuple[tuple[str, Any], ...] = (),
) -> Artifact:
    """Execute and replay one deterministic producer step for a terminal probe."""

    specification = registry[operator_id]
    output = specification.execute(inputs, bindings)
    if type(output) is not Artifact:
        raise AssertionError(f"{operator_id} refused a valid terminal-control source")
    verification = specification.verify(tuple(inputs.values()), output)
    if not verification.passed:
        raise AssertionError(f"{operator_id} produced an unreplayable terminal-control artifact")
    return output


def _x1_pipeline_candidate(goal: GoalSpec) -> Artifact:
    """Materialize the strict deterministic X1 receipt outside planner search."""

    from .v0_20_operators import build_v0_20_operator_registry

    registry = build_v0_20_operator_registry()
    polynomial = _execute_control_operator(
        registry,
        "EXACT_TO_SYMBOLIC_POLYNOMIAL",
        {"coefficients": goal.inputs["coefficients"]},
    )
    evaluation = _execute_control_operator(
        registry,
        "SYMBOLIC_TO_NUMERICAL_EVALUATION",
        {"polynomial": polynomial, "grid": goal.inputs["grid"]},
    )
    return _execute_control_operator(
        registry,
        "CERTIFY_GRID_EVALUATION",
        {"evaluation": evaluation},
        (("absolute_error_tolerance", dict(goal.constraints)["absolute_error_tolerance"]),),
    )


def _negative_result_control(family: str, variant: int) -> TerminalCandidateControl:
    goal = _build_goal(f"terminal-control:{family.lower()}:negative", family, variant)
    candidate: Artifact
    if family == "F2":
        coefficients = (Fraction(0), Fraction(-5), Fraction(3))
        goal = _replace_input(goal, "coefficients", coefficients)
        left, right = goal.inputs["interval"].value
        value = certify_quadratic_mean_value(coefficients, left, right)
        rationale = "valid affine certificate with a negative slope"
    elif family == "F3":
        goal = _replace_input(_replace_input(goal, "integer_a", 0), "integer_b", 0)
        value = certify_bezout(0, 0)
        rationale = "valid zero result under the total gcd(0,0)=0 convention"
    elif family == "C1":
        x, y = goal.inputs["coordinates"].value
        u, v = x, sp.Integer(0)
        goal = _replace_input(_replace_input(goal, "real_part", u), "imag_part", v)
        value = certify_cauchy_riemann(u, v, x=x, y=y)
        rationale = "valid negative holomorphy result with exact nonzero residual"
    elif family == "C2":
        variable = goal.inputs["variable"].value
        pole = goal.inputs["pole"].value
        expression = 1 / (variable - sp.Rational(pole.numerator, pole.denominator)) ** 2
        goal = _replace_input(goal, "form", expression)
        value = certify_residue(expression, variable=variable, pole=pole)
        rationale = "valid zero-residue result at a second-order pole"
    elif family == "X1":
        goal = _replace_input(goal, "coefficients", (Fraction(-2), Fraction(-1, 3)))
        candidate = _x1_pipeline_candidate(goal)
        rationale = "valid enclosure whose exact numerical values are negative"
    else:
        raise KeyError(family)
    if family != "X1":
        candidate = _candidate(goal, "negative", value)
    return TerminalCandidateControl(
        control_id=f"terminal-control:{family.lower()}:negative",
        family=family,
        kind=TerminalControlKind.VALID_NEGATIVE_RESULT,
        goal=goal,
        candidate=candidate,
        expected_verification_pass=True,
        rationale=rationale,
    )


def _external_alternative_control(family: str, variant: int) -> TerminalCandidateControl:
    goal = _build_goal(f"terminal-control:{family.lower()}:external", family, variant)
    candidate: Artifact
    distinct = True
    if family == "F2":
        coefficients = (Fraction(0), Fraction(5), Fraction(-3))
        goal = _replace_input(goal, "coefficients", coefficients)
        left, right = goal.inputs["interval"].value
        witness = left + (right - left) / 3
        value = replace(
            certify_quadratic_mean_value(coefficients, left, right),
            witness=witness,
        )
        rationale = "affine MVT admits every interior witness; this is not the midpoint"
    elif family == "F3":
        a = goal.inputs["integer_a"].value
        b = goal.inputs["integer_b"].value
        canonical = certify_bezout(a, b)
        step_a, step_b = b // canonical.gcd, a // canonical.gcd
        value = replace(canonical, x=canonical.x + step_a, y=canonical.y - step_b)
        rationale = "Bézout coefficients differ by the exact solution-lattice generator"
    elif family == "X1":
        candidate = _x1_pipeline_candidate(goal)
        distinct = False
        rationale = "independent terminal invocation replays the one strict deterministic X1 receipt"
    else:
        raise KeyError(family)
    if family != "X1":
        candidate = _candidate(goal, "external", value)
    return TerminalCandidateControl(
        control_id=f"terminal-control:{family.lower()}:external",
        family=family,
        kind=TerminalControlKind.EXTERNAL_VALID_CERTIFICATE,
        goal=goal,
        candidate=candidate,
        expected_verification_pass=True,
        is_distinct_alternative=distinct,
        rationale=rationale,
    )


def build_v0_20_terminal_controls() -> tuple[TerminalCandidateControl, ...]:
    """Return external terminal probes; none is ever passed to ``solve`` as a root."""

    controls: list[TerminalCandidateControl] = []
    for index, family in enumerate(NEW_V0_20_FAMILIES):
        invalid_goal = _domain_invalid_goal(family, 60 + index)
        controls.append(TerminalCandidateControl(
            control_id=f"terminal-control:{family.lower()}:domain",
            family=family,
            kind=TerminalControlKind.DOMAIN_REFUSAL,
            goal=invalid_goal,
            candidate=_candidate(invalid_goal, "domain-probe", {"untrusted": "target-shaped"}),
            expected_verification_pass=False,
            rationale="invalid source domain must be rejected by terminal replay",
        ))

        goal = _build_goal(f"terminal-control:{family.lower()}:invalid", family, 70 + index)
        controls.append(TerminalCandidateControl(
            control_id=f"terminal-control:{family.lower()}:invalid",
            family=family,
            kind=TerminalControlKind.INVALID_TERMINAL_CERTIFICATE,
            goal=goal,
            candidate=_candidate(goal, "invalid", {"untrusted": "corrupt-certificate"}),
            expected_verification_pass=False,
            rationale="target metadata cannot launder an invalid terminal payload",
        ))

    for index, family in enumerate(("F2", "F3", "C1", "C2", "X1")):
        controls.append(_negative_result_control(family, 80 + index))
    for index, family in enumerate(("F2", "F3", "X1")):
        controls.append(_external_alternative_control(family, 90 + index))

    if len(controls) != V0_20_TERMINAL_CONTROL_COUNT:
        raise AssertionError("terminal control manifest count drifted")
    identifiers = [control.control_id for control in controls]
    if len(identifiers) != len(set(identifiers)):
        raise AssertionError("terminal control identifiers must be unique")
    return tuple(controls)


def control_kind_for_goal(value: GoalSpec | TerminalCandidateControl) -> str | None:
    if isinstance(value, TerminalCandidateControl):
        return value.kind.value
    return None


def build_case_oracle(goal: GoalSpec) -> dict[str, Any]:
    """Adapt a core goal to the import-independent campaign oracle surface."""

    from .campaign_oracles import build_independent_oracle, oracle_independence_receipt
    from .v0_20_verifiers import validate_v0_20_goal_contract

    validation = validate_v0_20_goal_contract(goal)
    if not validation.passed:
        try:
            signatures = case_signatures(goal)
            exact_fingerprint = signatures.exact_sha256
            nuisance_fingerprint = signatures.nuisance_sha256
            nuisance_relation = signatures.nuisance_relation
        except Exception:
            exact_fingerprint = None
            nuisance_fingerprint = None
            nuisance_relation = "UNAVAILABLE_INVALID_GOAL"
        return {
            "goal_id": goal.goal_id if type(goal.goal_id) is str else "INVALID_GOAL_ID",
            "family": goal.family if type(goal.family) is str else "INVALID_FAMILY",
            "content_fingerprint": exact_fingerprint,
            "nuisance_fingerprint": nuisance_fingerprint,
            "nuisance_relation": nuisance_relation,
            "control_kind": None,
            "authoritative": False,
            "authority_kind": "INVALID_CHALLENGE_CONTRACT",
            "oracle_availability": "INVALID_CHALLENGE",
            "oracle_method": "CLOSED_V0_20_GOAL_CONTRACT",
            "expected_verdict": "INVALID",
            "reason": validation.reason,
            "independence_receipt": None,
            "independence_receipt_sha256": None,
            "certificate": _canonical({"contract_valid": False}),
        }

    adapter_receipt = oracle_independence_receipt()
    oracle = build_independent_oracle(
        family=goal.family,
        inputs={key: artifact.value for key, artifact in goal.inputs.items()},
        constraints=dict(goal.constraints),
        tolerance=goal.allowed_numeric_tolerance,
    )
    receipt_bound = bool(
        type(adapter_receipt) is dict
        and adapter_receipt.get("established") is True
        and type(oracle.independence_receipt) is dict
        and oracle.independence_receipt == adapter_receipt
    )
    authoritative = bool(oracle.authoritative and receipt_bound)
    receipt_digest = _digest(adapter_receipt)
    signatures = case_signatures(goal)
    return {
        "goal_id": goal.goal_id,
        "family": goal.family,
        "content_fingerprint": signatures.exact_sha256,
        "nuisance_fingerprint": signatures.nuisance_sha256,
        "nuisance_relation": signatures.nuisance_relation,
        "control_kind": None,
        "authoritative": authoritative,
        "authority_kind": (
            "INDEPENDENT_MATHEMATICAL_ORACLE"
            if receipt_bound
            else "INDEPENDENCE_NOT_ESTABLISHED"
        ),
        "oracle_availability": oracle.availability if receipt_bound else "UNAVAILABLE",
        "oracle_method": oracle.method,
        "expected_verdict": oracle.expected_verdict,
        "reason": oracle.reason if receipt_bound else "ORACLE_INDEPENDENCE_NOT_ESTABLISHED",
        "independence_receipt": adapter_receipt,
        "independence_receipt_sha256": receipt_digest,
        "certificate": _canonical(oracle.certificate),
    }


def prove_no_same_class_shortcut(goal: GoalSpec, registry: Mapping[str, OperatorSpec]) -> dict[str, Any]:
    """Adapt to the sound proof module and otherwise fail closed."""

    def unavailable(reason: str) -> dict[str, Any]:
        return {
            "status": "UNAVAILABLE",
            "proven_no_shortcut": False,
            "proof_validated": False,
            "proof_digest": None,
            "witness": None,
            "counterexample": None,
            "reason": reason,
        }

    def error(reason: str) -> dict[str, Any]:
        return {
            "status": "ERROR",
            "proven_no_shortcut": False,
            "proof_validated": False,
            "proof_digest": None,
            "witness": None,
            "counterexample": None,
            "reason": reason,
        }

    if type(goal) is not GoalSpec or type(goal.family) is not str:
        return error("GOAL_MUST_BE_AN_EXACT_GOAL_SPEC")
    if goal.family not in CROSS_CLASS_FAMILIES:
        return unavailable("NOT_A_CROSS_CLASS_GOAL")
    if type(registry) is not dict:
        return error("REGISTRY_MUST_BE_AN_EXACT_DICT_SNAPSHOT")
    registry_snapshot = dict(registry)
    if (
        not registry_snapshot
        or any(
            type(operator_id) is not str
            or not operator_id
            or type(specification) is not OperatorSpec
            or type(specification.operator_id) is not str
            or specification.operator_id != operator_id
            for operator_id, specification in registry_snapshot.items()
        )
    ):
        return error("REGISTRY_SNAPSHOT_INVALID")
    try:
        from .shortcut_proof import (
            LineageObligation,
            TypeNode,
            prove_lineage_obligation,
            validate_lineage_proof,
        )
        from .v0_20_verifiers import validate_v0_20_goal_contract
    except ImportError:
        return unavailable("SHORTCUT_PROOF_MODULE_UNAVAILABLE")
    try:
        visible = goal.solver_visible()
        if not validate_v0_20_goal_contract(visible).passed:
            return error("GOAL_CONTRACT_INVALID")
        source_obligation = visible.lineage_obligation
        target_type = visible.target.artifact_type
        if source_obligation is None or target_type is None:
            return error("LINEAGE_CONTRACT_INCOMPLETE")
        obligation = LineageObligation(
            required_input_keys=source_obligation.required_input_keys,
            ordered_stage_types=tuple(
                TypeNode(
                    stage.semantic_type,
                    stage.representation_class,
                    stage.exactness_class,
                )
                for stage in source_obligation.ordered_stage_types
            ),
            stage_required_input_keys=source_obligation.stage_required_input_keys,
        )
        root_types = {
            input_key: artifact.artifact_type
            for input_key, artifact in visible.inputs.items()
        }
        goal_contract = {
            "goal_id": visible.goal_id,
            "family": visible.family,
            "input_types": tuple(
                (
                    input_key,
                    artifact.semantic_type,
                    artifact.representation_class,
                    artifact.exactness_class,
                )
                for input_key, artifact in sorted(visible.inputs.items())
            ),
            "target": (
                visible.target.target_id,
                visible.target.semantic_type,
                visible.target.representation_class,
                visible.target.objective,
                visible.target.exactness_class,
            ),
            "constraints": visible.constraints,
            "allowed_numeric_tolerance": visible.allowed_numeric_tolerance,
            "required_verifier_class": visible.required_verifier_class,
            "search_budget": visible.search_budget,
        }
        result = prove_lineage_obligation(
            root_types=root_types,
            target_type=target_type,
            obligation=obligation,
            registry=registry_snapshot,
            goal_contract=goal_contract,
        )
        if not validate_lineage_proof(
            result,
            root_types=root_types,
            target_type=target_type,
            obligation=obligation,
            registry=registry_snapshot,
            goal_contract=goal_contract,
        ):
            return error("PROOF_REPLAY_VALIDATION_FAILED")
        status = result.status.value
        return {
            "status": status,
            "proven_no_shortcut": status == "PROVED",
            "proof_validated": True,
            "proof_digest": result.proof_digest,
            "registry_digest": result.registry_digest,
            "goal_contract_digest": result.goal_contract_digest,
            "obligation_digest": result.obligation_digest,
            "explored_state_count": result.explored_state_count,
            "witness": _canonical(result.safe_witness) if result.safe_witness is not None else None,
            "counterexample": (
                _canonical(result.counterexample)
                if result.counterexample is not None
                else None
            ),
            "reason": result.reason,
        }
    except Exception as exc:
        return error(type(exc).__name__)
