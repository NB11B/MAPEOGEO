from __future__ import annotations

import math
from typing import Any

import sympy as sp

from .model import Artifact, VerificationResult


def exact_value_verifier(output: Artifact) -> VerificationResult:
    return VerificationResult(True, "EXACT_INTERNAL", evidence=(("artifact_id", output.artifact_id),))


def exact_compare(actual: Any, expected: Any, verifier_class: str = "EXACT_EQUALITY") -> VerificationResult:
    passed = actual == expected
    return VerificationResult(passed, verifier_class, "equal" if passed else "mismatch")


def numeric_compare(actual: float, expected: float, tolerance: float, verifier_class: str = "NUMERIC_RESIDUAL") -> VerificationResult:
    residual = abs(float(actual) - float(expected))
    return VerificationResult(
        residual <= tolerance,
        verifier_class,
        "within tolerance" if residual <= tolerance else "residual exceeds tolerance",
        residual=residual,
        evidence=(("tolerance", tolerance),),
    )


def symbolic_equivalent(lhs: Any, rhs: Any) -> VerificationResult:
    try:
        diff = sp.simplify(sp.sympify(lhs) - sp.sympify(rhs))
    except Exception as exc:  # pragma: no cover - defensive adapter boundary
        return VerificationResult(False, "SYMBOLIC_IDENTITY", f"symbolic parse failed: {exc}")
    passed = diff == 0
    return VerificationResult(passed, "SYMBOLIC_IDENTITY", "identity closed" if passed else f"residual={diff}")


def finite_numeric(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, dict):
        return all(finite_numeric(v) for v in value.values() if isinstance(v, (int, float, dict, tuple, list)))
    if isinstance(value, (tuple, list)):
        return all(finite_numeric(v) for v in value)
    return True
