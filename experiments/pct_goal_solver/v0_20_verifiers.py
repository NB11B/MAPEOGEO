"""Authoritative terminal verification for the seven prospective v0.20 families."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

import sympy as sp

from .elliptic_periods import PeriodCertificate, verify_period_certificate
from .model import (
    Artifact,
    ArtifactType,
    CandidateLineageObligation,
    GoalSpec,
    SolverVisibleGoal,
    TargetSpec,
    VerificationResult,
)
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
    STRICT_V0_20_VERIFIER_CLASS,
    V0_20_CONTRACTS,
    V020FamilyContract,
)
from .v0_20_operators import (
    required_stage_receipts_are_admissible,
    verify_cross_class_pipeline_receipt,
)


_MAX_IDENTIFIER_LENGTH = 512
_MAX_PROVENANCE_ITEMS = 64


def _result(passed: bool, reason: str, *, family: str | None = None) -> VerificationResult:
    evidence = (("family", family),) if passed and family is not None else ()
    return VerificationResult(passed, STRICT_V0_20_VERIFIER_CLASS, reason, evidence=evidence)


def _failure(reason: str) -> VerificationResult:
    return _result(False, reason)


def _valid_identifier(value: object) -> bool:
    return type(value) is str and bool(value) and len(value) <= _MAX_IDENTIFIER_LENGTH


def _expected_lineage(family: str) -> CandidateLineageObligation | None:
    if family == "X1":
        return CandidateLineageObligation(
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
    if family == "X2":
        return CandidateLineageObligation(
            required_input_keys=frozenset({"g2", "g3"}),
            ordered_stage_types=(
                ArtifactType("SYMBOLIC_WEIERSTRASS_CURVE", "SYMBOLIC_CURVE", "SYMBOLIC"),
            ),
            stage_required_input_keys=(frozenset({"g2", "g3"}),),
        )
    return None


def _root_artifact_schema(goal_id: str, artifact: object, root: Any) -> bool:
    return (
        type(artifact) is Artifact
        and artifact.artifact_id == f"{goal_id}:{root.key}"
        and artifact.semantic_type == root.semantic_type
        and artifact.representation_class == root.representation_class
        and artifact.exactness_class == root.exactness_class
        and artifact.metadata == ()
        and artifact.provenance == ()
    )


def _root_values_are_admissible(
    family: str,
    inputs: Mapping[str, Artifact],
    constraints: tuple[tuple[str, Any], ...],
) -> bool:
    """Validate only the source domain; no expected answer is read or emitted."""

    parameters = dict(constraints)
    try:
        if family == "F1":
            lower = inputs["lower_bound"].value
            upper = inputs["upper_bound"].value
            return (
                type(lower) is Fraction
                and type(upper) is Fraction
                and bool(certify_sqrt2_cut(lower, upper).verified)
            )
        if family == "F2":
            coefficients = inputs["coefficients"].value
            interval = inputs["interval"].value
            if (
                type(coefficients) is not tuple
                or len(coefficients) != 3
                or any(type(value) is not Fraction for value in coefficients)
                or type(interval) is not tuple
                or len(interval) != 2
                or any(type(value) is not Fraction for value in interval)
            ):
                return False
            return bool(certify_quadratic_mean_value(coefficients, interval[0], interval[1]).verified)
        if family == "F3":
            a = inputs["integer_a"].value
            b = inputs["integer_b"].value
            return type(a) is int and type(b) is int and bool(certify_bezout(a, b).verified)
        if family == "C1":
            u = inputs["real_part"].value
            v = inputs["imag_part"].value
            coordinates = inputs["coordinates"].value
            if (
                not isinstance(u, sp.Expr)
                or not isinstance(v, sp.Expr)
                or type(coordinates) is not tuple
                or len(coordinates) != 2
                or any(type(value) is not sp.Symbol for value in coordinates)
            ):
                return False
            certificate = certify_cauchy_riemann(
                u,
                v,
                x=coordinates[0],
                y=coordinates[1],
            )
            return (
                type(certificate.holomorphic) is bool
                and required_stage_receipts_are_admissible(family, inputs)
            )
        if family == "C2":
            expression = inputs["form"].value
            variable = inputs["variable"].value
            pole = inputs["pole"].value
            if (
                not isinstance(expression, sp.Expr)
                or type(variable) is not sp.Symbol
                or type(pole) is not Fraction
            ):
                return False
            certificate = certify_residue(
                expression,
                variable=variable,
                pole=pole,
            )
            return (
                certificate.verified is True
                and required_stage_receipts_are_admissible(family, inputs)
            )
        if family == "X1":
            coefficients = inputs["coefficients"].value
            grid = inputs["grid"].value
            tolerance = parameters.get("absolute_error_tolerance")
            if (
                type(coefficients) is not tuple
                or not coefficients
                or any(type(value) is not Fraction for value in coefficients)
                or type(grid) is not tuple
                or not grid
                or any(type(value) is not Fraction for value in grid)
                or type(tolerance) is not Fraction
            ):
                return False
            if not required_stage_receipts_are_admissible(family, inputs):
                return False
            probe = certify_grid_evaluation(
                coefficients,
                grid,
                (0.0 for _ in grid),
                tolerance,
            )
            return type(probe) is GridEvaluationCertificate
        if family == "X2":
            g2 = inputs["g2"].value
            g3 = inputs["g3"].value
            decimal_places = parameters.get("decimal_places")
            if type(g2) is not Fraction or type(g3) is not Fraction or type(decimal_places) is not int:
                return False
            bounded = all(
                max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 1024
                for value in (g2, g3)
            )
            return bounded and 10 <= decimal_places <= 64 and g2**3 - 27 * g3**2 > 0
    except (ArithmeticError, AssertionError, TypeError, ValueError):
        return False
    return False


def _goal_schema(goal: object) -> tuple[V020FamilyContract, Mapping[str, Artifact]] | None:
    if type(goal) not in (SolverVisibleGoal, GoalSpec):
        return None
    if not _valid_identifier(goal.goal_id) or type(goal.family) is not str:
        return None
    contract = V0_20_CONTRACTS.get(goal.family)
    if contract is None:
        return None
    if type(goal.target) is not TargetSpec:
        return None
    target = contract.target
    if (
        goal.target.target_id != target.target_id
        or goal.target.semantic_type != target.semantic_type
        or goal.target.representation_class != target.representation_class
        or goal.target.objective != target.objective
        or goal.target.exactness_class != target.exactness_class
        or goal.target.metadata != ()
        or type(goal.constraints) is not tuple
        or goal.constraints != contract.constraints
        or type(goal.allowed_numeric_tolerance) is not float
        or goal.allowed_numeric_tolerance != contract.allowed_numeric_tolerance
        or goal.required_verifier_class != STRICT_V0_20_VERIFIER_CLASS
        or type(goal.search_budget) is not int
        or goal.search_budget != contract.search_budget
        or goal.lineage_obligation != _expected_lineage(goal.family)
        or type(goal.inputs) is not dict
    ):
        return None
    expected_keys = tuple(root.key for root in contract.roots)
    if len(goal.inputs) != len(expected_keys) or set(goal.inputs) != set(expected_keys):
        return None
    for root in contract.roots:
        if not _root_artifact_schema(goal.goal_id, goal.inputs.get(root.key), root):
            return None
    if not _root_values_are_admissible(goal.family, goal.inputs, goal.constraints):
        return None
    return contract, goal.inputs


def validate_v0_20_goal_contract(goal: SolverVisibleGoal | GoalSpec) -> VerificationResult:
    """Validate the complete public goal schema without consulting sealed data."""

    try:
        schema = _goal_schema(goal)
    except Exception:
        return _failure("GOAL_CONTRACT_EXCEPTION")
    if schema is None:
        return _failure("GOAL_CONTRACT_MISMATCH")
    contract, _ = schema
    return _result(True, "GOAL_CONTRACT_VALID", family=contract.family)


def _candidate_schema(candidate: object, contract: V020FamilyContract) -> bool:
    if type(candidate) is not Artifact:
        return False
    provenance = candidate.provenance
    return (
        _valid_identifier(candidate.artifact_id)
        and candidate.semantic_type == contract.target.semantic_type
        and candidate.representation_class == contract.target.representation_class
        and candidate.exactness_class == contract.target.exactness_class
        and type(candidate.value) is contract.candidate_type
        and candidate.metadata == ()
        and type(provenance) is tuple
        and len(provenance) <= _MAX_PROVENANCE_ITEMS
        and all(_valid_identifier(item) for item in provenance)
        and len(set(provenance)) == len(provenance)
    )


def _verify_candidate_value(
    family: str,
    inputs: Mapping[str, Artifact],
    constraints: tuple[tuple[str, Any], ...],
    value: object,
) -> bool:
    parameters = dict(constraints)
    if family == "F1" and type(value) is Sqrt2CutCertificate:
        return verify_sqrt2_cut(
            inputs["lower_bound"].value,
            inputs["upper_bound"].value,
            value,
        )
    if family == "F2" and type(value) is QuadraticMeanValueCertificate:
        left, right = inputs["interval"].value
        return verify_quadratic_mean_value(
            inputs["coefficients"].value,
            left,
            right,
            value,
        )
    if family == "F3" and type(value) is BezoutCertificate:
        return verify_bezout_certificate(
            inputs["integer_a"].value,
            inputs["integer_b"].value,
            value,
        )
    if family == "C1" and type(value) is CauchyRiemannCertificate:
        x, y = inputs["coordinates"].value
        return verify_cauchy_riemann(
            inputs["real_part"].value,
            inputs["imag_part"].value,
            value,
            x=x,
            y=y,
        )
    if family == "C2" and type(value) is ResidueCertificate:
        return verify_residue(
            inputs["form"].value,
            value,
            variable=inputs["variable"].value,
            pole=inputs["pole"].value,
        )
    if family == "X1" and type(value) is GridEvaluationCertificate:
        return (
            value.coefficients == inputs["coefficients"].value
            and value.grid == inputs["grid"].value
            and value.tolerance == parameters["absolute_error_tolerance"]
            and verify_grid_evaluation(value)
        )
    if family == "X2" and type(value) is PeriodCertificate:
        return (
            value.g2 == inputs["g2"].value
            and value.g3 == inputs["g3"].value
            and value.decimal_places == parameters["decimal_places"]
            and verify_period_certificate(value)
        )
    return False


def verify_v0_20_goal(
    goal: SolverVisibleGoal | GoalSpec,
    candidate: Artifact,
) -> VerificationResult:
    """Fail-closed, source-bound verification for an untrusted candidate artifact."""

    try:
        schema = _goal_schema(goal)
        if schema is None:
            return _failure("GOAL_CONTRACT_MISMATCH")
        contract, inputs = schema
        if not _candidate_schema(candidate, contract):
            return _failure("CANDIDATE_SCHEMA_MISMATCH")
        passed = _verify_candidate_value(
            contract.family,
            inputs,
            goal.constraints,
            candidate.value,
        )
        if not passed:
            return _failure("CERTIFICATE_REPLAY_FAILED")
        if contract.family in {"X1", "X2"} and not verify_cross_class_pipeline_receipt(
            contract.family,
            inputs,
            candidate,
        ):
            return _failure("CROSS_CLASS_RECEIPT_REPLAY_FAILED")
        return _result(True, "CERTIFICATE_REPLAY_PASSED", family=contract.family)
    except Exception:
        return _failure("TERMINAL_VERIFIER_EXCEPTION")
