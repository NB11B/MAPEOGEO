"""Closed, immutable data contracts for the prospective v0.20 families.

This module contains schema only.  It does not know how goals are generated,
how operators search, or how terminal candidates are accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Mapping

import sympy as sp

from .elliptic_periods import PeriodCertificate
from .rigorous_math import (
    BezoutCertificate,
    CauchyRiemannCertificate,
    GridEvaluationCertificate,
    QuadraticMeanValueCertificate,
    ResidueCertificate,
    Sqrt2CutCertificate,
)


NEW_V0_20_FAMILIES = ("F1", "F2", "F3", "C1", "C2", "X1", "X2")
STRICT_V0_20_VERIFIER_CLASS = "PCT_V0_20_STRICT_CERTIFICATE"


@dataclass(frozen=True)
class RootContract:
    key: str
    semantic_type: str
    representation_class: str
    exactness_class: str


@dataclass(frozen=True)
class TargetContract:
    target_id: str
    semantic_type: str
    representation_class: str
    objective: str
    exactness_class: str


@dataclass(frozen=True)
class V020FamilyContract:
    family: str
    contract_id: str
    roots: tuple[RootContract, ...]
    target: TargetContract
    constraints: tuple[tuple[str, Any], ...]
    candidate_type: type
    allowed_numeric_tolerance: float
    search_budget: int


@dataclass(frozen=True)
class V020ArtifactContract:
    semantic_type: str
    representation_class: str
    exactness_class: str


@dataclass(frozen=True)
class SymbolicPolynomial:
    coefficients: tuple[Fraction, ...]
    variable: sp.Symbol
    expression: sp.Expr


@dataclass(frozen=True)
class NumericalPolynomialEvaluation:
    coefficients: tuple[Fraction, ...]
    grid: tuple[Fraction, ...]
    numerical_values: tuple[float, ...]


@dataclass(frozen=True)
class WeierstrassCurve:
    g2: Fraction
    g3: Fraction
    x: sp.Symbol
    y: sp.Symbol
    equation: sp.Expr
    elliptic_discriminant: Fraction
    polynomial_discriminant: Fraction


def _root(
    key: str,
    semantic_type: str,
    representation_class: str,
    exactness_class: str,
) -> RootContract:
    return RootContract(key, semantic_type, representation_class, exactness_class)


def _target(
    target_id: str,
    semantic_type: str,
    representation_class: str,
    objective: str,
    exactness_class: str,
) -> TargetContract:
    return TargetContract(
        target_id,
        semantic_type,
        representation_class,
        objective,
        exactness_class,
    )


def _constraints(
    contract_id: str,
    required_derived_types: tuple[str, ...],
    required_exactness_path: tuple[str, ...],
    *parameters: tuple[str, Any],
) -> tuple[tuple[str, Any], ...]:
    return (
        ("contract_id", contract_id),
        ("required_derived_types", required_derived_types),
        ("required_exactness_path", required_exactness_path),
        *parameters,
    )


def _build_contracts() -> dict[str, V020FamilyContract]:
    """Construct a fresh contract table; no mutable backing alias is retained."""

    return {
    "F1": V020FamilyContract(
        family="F1",
        contract_id="PCT_V0_20_F1_SQRT2_CUT_V1",
        roots=(
            _root("lower_bound", "SQRT2_LOWER_BOUND_EXACT", "RATIONAL_SCALAR", "EXACT"),
            _root("upper_bound", "SQRT2_UPPER_BOUND_EXACT", "RATIONAL_SCALAR", "EXACT"),
        ),
        target=_target(
            "sqrt2_cut_certificate",
            "SQRT2_CUT_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "CERTIFY_SQRT2_CUT",
            "EXACT",
        ),
        constraints=_constraints(
            "PCT_V0_20_F1_SQRT2_CUT_V1",
            ("SQRT2_CUT_CERTIFICATE",),
            ("EXACT",),
        ),
        candidate_type=Sqrt2CutCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=64,
    ),
    "F2": V020FamilyContract(
        family="F2",
        contract_id="PCT_V0_20_F2_QUADRATIC_MVT_V1",
        roots=(
            _root("coefficients", "QUADRATIC_COEFFICIENTS_EXACT", "RATIONAL_TRIPLE", "EXACT"),
            _root("interval", "CLOSED_INTERVAL_EXACT", "RATIONAL_PAIR", "EXACT"),
        ),
        target=_target(
            "mean_value_certificate",
            "QUADRATIC_MEAN_VALUE_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "CERTIFY_MEAN_VALUE_WITNESS",
            "EXACT",
        ),
        constraints=_constraints(
            "PCT_V0_20_F2_QUADRATIC_MVT_V1",
            ("QUADRATIC_MEAN_VALUE_CERTIFICATE",),
            ("EXACT",),
        ),
        candidate_type=QuadraticMeanValueCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=64,
    ),
    "F3": V020FamilyContract(
        family="F3",
        contract_id="PCT_V0_20_F3_BEZOUT_V1",
        roots=(
            _root("integer_a", "INTEGER_A_EXACT", "INTEGER_SCALAR", "EXACT"),
            _root("integer_b", "INTEGER_B_EXACT", "INTEGER_SCALAR", "EXACT"),
        ),
        target=_target(
            "bezout_certificate",
            "BEZOUT_CERTIFICATE",
            "EXACT_CERTIFICATE",
            "CERTIFY_BEZOUT_IDENTITY",
            "EXACT",
        ),
        constraints=_constraints(
            "PCT_V0_20_F3_BEZOUT_V1",
            ("BEZOUT_CERTIFICATE",),
            ("EXACT",),
        ),
        candidate_type=BezoutCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=64,
    ),
    "C1": V020FamilyContract(
        family="C1",
        contract_id="PCT_V0_20_C1_CAUCHY_RIEMANN_V1",
        roots=(
            _root("real_part", "REAL_POLYNOMIAL_POTENTIAL", "SYMBOLIC_EXPRESSION", "SYMBOLIC"),
            _root("imag_part", "IMAG_POLYNOMIAL_POTENTIAL", "SYMBOLIC_EXPRESSION", "SYMBOLIC"),
            _root("coordinates", "REAL_COORDINATE_PAIR", "SYMBOL_PAIR", "SYMBOLIC"),
        ),
        target=_target(
            "cauchy_riemann_certificate",
            "CAUCHY_RIEMANN_CERTIFICATE",
            "SYMBOLIC_CERTIFICATE",
            "CERTIFY_CAUCHY_RIEMANN",
            "SYMBOLIC",
        ),
        constraints=_constraints(
            "PCT_V0_20_C1_CAUCHY_RIEMANN_V1",
            ("CAUCHY_RIEMANN_CERTIFICATE",),
            ("SYMBOLIC",),
        ),
        candidate_type=CauchyRiemannCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=80,
    ),
    "C2": V020FamilyContract(
        family="C2",
        contract_id="PCT_V0_20_C2_RATIONAL_RESIDUE_V1",
        roots=(
            _root("form", "RATIONAL_MEROMORPHIC_FORM", "SYMBOLIC_EXPRESSION", "SYMBOLIC"),
            _root("variable", "COMPLEX_COORDINATE_SYMBOL", "SYMBOL", "SYMBOLIC"),
            _root("pole", "RATIONAL_POLE_EXACT", "RATIONAL_SCALAR", "EXACT"),
        ),
        target=_target(
            "residue_certificate",
            "RESIDUE_CERTIFICATE",
            "SYMBOLIC_CERTIFICATE",
            "CERTIFY_RATIONAL_RESIDUE",
            "SYMBOLIC",
        ),
        constraints=_constraints(
            "PCT_V0_20_C2_RATIONAL_RESIDUE_V1",
            ("RESIDUE_CERTIFICATE",),
            ("SYMBOLIC",),
        ),
        candidate_type=ResidueCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=80,
    ),
    "X1": V020FamilyContract(
        family="X1",
        contract_id="PCT_V0_20_X1_POLYNOMIAL_GRID_V1",
        roots=(
            _root("coefficients", "POLYNOMIAL_COEFFICIENTS_EXACT", "RATIONAL_VECTOR", "EXACT"),
            _root("grid", "EVALUATION_GRID_EXACT", "RATIONAL_VECTOR", "EXACT"),
        ),
        target=_target(
            "grid_evaluation_certificate",
            "GRID_EVALUATION_CERTIFICATE",
            "NUMERICAL_CERTIFICATE",
            "CERTIFY_GRID_APPROXIMATION",
            "NUMERICAL",
        ),
        constraints=_constraints(
            "PCT_V0_20_X1_POLYNOMIAL_GRID_V1",
            (
                "SYMBOLIC_POLYNOMIAL",
                "NUMERICAL_POLYNOMIAL_EVALUATION",
                "GRID_EVALUATION_CERTIFICATE",
            ),
            ("EXACT", "SYMBOLIC", "NUMERICAL"),
            ("absolute_error_tolerance", Fraction(1, 10**12)),
        ),
        candidate_type=GridEvaluationCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=128,
    ),
    "X2": V020FamilyContract(
        family="X2",
        contract_id="PCT_V0_20_X2_RECTANGULAR_PERIOD_V1",
        roots=(
            _root("g2", "WEIERSTRASS_G2_EXACT", "RATIONAL_SCALAR", "EXACT"),
            _root("g3", "WEIERSTRASS_G3_EXACT", "RATIONAL_SCALAR", "EXACT"),
        ),
        target=_target(
            "period_certificate",
            "RECTANGULAR_PERIOD_CERTIFICATE",
            "NUMERICAL_CERTIFICATE",
            "CERTIFY_RECTANGULAR_PERIODS",
            "NUMERICAL",
        ),
        constraints=_constraints(
            "PCT_V0_20_X2_RECTANGULAR_PERIOD_V1",
            ("SYMBOLIC_WEIERSTRASS_CURVE", "RECTANGULAR_PERIOD_CERTIFICATE"),
            ("EXACT", "SYMBOLIC", "NUMERICAL"),
            ("decimal_places", 15),
        ),
        candidate_type=PeriodCertificate,
        allowed_numeric_tolerance=0.0,
        search_budget=128,
    ),
    }


V0_20_CONTRACTS: Mapping[str, V020FamilyContract] = MappingProxyType(_build_contracts())


def _build_artifact_contracts() -> dict[str, V020ArtifactContract]:
    rows: dict[str, V020ArtifactContract] = {}
    for family_contract in V0_20_CONTRACTS.values():
        for root in family_contract.roots:
            rows[root.semantic_type] = V020ArtifactContract(
                root.semantic_type,
                root.representation_class,
                root.exactness_class,
            )
    rows.update(
        {
            "SYMBOLIC_POLYNOMIAL": V020ArtifactContract(
                "SYMBOLIC_POLYNOMIAL",
                "SYMBOLIC_POLYNOMIAL",
                "SYMBOLIC",
            ),
            "NUMERICAL_POLYNOMIAL_EVALUATION": V020ArtifactContract(
                "NUMERICAL_POLYNOMIAL_EVALUATION",
                "NUMERICAL_SERIES",
                "NUMERICAL",
            ),
            "SYMBOLIC_WEIERSTRASS_CURVE": V020ArtifactContract(
                "SYMBOLIC_WEIERSTRASS_CURVE",
                "SYMBOLIC_CURVE",
                "SYMBOLIC",
            ),
        }
    )
    return rows


V0_20_ARTIFACT_CONTRACTS: Mapping[str, V020ArtifactContract] = MappingProxyType(
    _build_artifact_contracts()
)


def materialize_v0_20_artifact_type(semantic_type: str) -> object:
    """Create the core ``ArtifactType`` lazily for strict-core compatibility."""

    from .model import ArtifactType  # type: ignore[attr-defined]

    contract = V0_20_ARTIFACT_CONTRACTS[semantic_type]
    return ArtifactType(
        contract.semantic_type,
        contract.representation_class,
        contract.exactness_class,
    )
