"""Independent mathematical oracles for the v0.20 evidence campaign.

This module deliberately has no dependency on planner, operator, verifier,
certificate-construction, or elliptic-period implementation modules.  Inputs
are plain mathematical values copied out of a goal at the campaign boundary.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
import dis
from fractions import Fraction
import hashlib
import inspect
import math
from pathlib import Path
from types import FunctionType, MappingProxyType, ModuleType
from typing import Any, Mapping

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, PolynomialError


@dataclass(frozen=True)
class IndependentOracle:
    authoritative: bool
    availability: str
    expected_verdict: str
    certificate: Any
    method: str
    reason: str = ""
    independence_receipt: Mapping[str, Any] | None = None


def oracle_dependency_manifest() -> frozenset[str]:
    """Return every source-level import, including ``from`` imports.

    Inspecting module-valued globals is insufficient: ``from .planner import
    solve`` leaves a function, not a module, in the global namespace.  The AST
    manifest is therefore the authority for the dependency surface.
    """

    try:
        source = Path(__file__).read_text(encoding="utf-8")
        rows = _source_import_manifest(source)
        return frozenset(row[2].rsplit(".", 1)[-1] for row in rows)
    except Exception:
        return frozenset({"UNAVAILABLE"})


def _available(verdict: str, certificate: Any, method: str) -> IndependentOracle:
    return IndependentOracle(True, "AVAILABLE", verdict, certificate, method)


def _unavailable(reason: str) -> IndependentOracle:
    return IndependentOracle(False, "UNAVAILABLE", "UNKNOWN", None, "UNAVAILABLE", reason)


def _invalid(reason: str) -> IndependentOracle:
    return _available("INVALID", {"reason": reason}, "EXACT_DOMAIN_VALIDATION")


def _fraction(value: Any) -> Fraction:
    if type(value) is Fraction:
        if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 4096:
            return value
        raise ValueError("exact Fraction exceeds the 4096-bit root bound")
    raise TypeError("value is not an exact Fraction root")


def _bounded_derived_fraction(value: Fraction) -> Fraction:
    if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 4096:
        raise ValueError("derived exact field exceeds the 4096-bit certificate bound")
    return value


def _f1(inputs: Mapping[str, Any]) -> IndependentOracle:
    try:
        lower = _fraction(inputs["lower_bound"])
        upper = _fraction(inputs["upper_bound"])
        lower_gap = lower.numerator**2 - 2 * lower.denominator**2
        upper_gap = upper.numerator**2 - 2 * upper.denominator**2
        if not (0 < lower < upper and lower_gap < 0 < upper_gap):
            return _invalid("INVALID_SQRT2_CUT_BOUNDS")
    except (KeyError, TypeError, ValueError):
        return _invalid("INVALID_SQRT2_CUT_BOUNDS")
    return _available(
        "PASS",
        {"lower": lower, "upper": upper, "lower_gap": lower_gap, "upper_gap": upper_gap},
        "EXACT_INTEGER_SQUARE_ORACLE",
    )


def _f2(inputs: Mapping[str, Any]) -> IndependentOracle:
    try:
        raw_coefficients = inputs["coefficients"]
        if type(raw_coefficients) is not tuple or len(raw_coefficients) != 3:
            return _invalid("INVALID_QUADRATIC_MVT_DOMAIN")
        coefficients = tuple(_fraction(item) for item in raw_coefficients)
        raw_interval = inputs["interval"]
        if type(raw_interval) is not tuple or len(raw_interval) != 2:
            return _invalid("INVALID_QUADRATIC_MVT_DOMAIN")
        interval = tuple(_fraction(item) for item in raw_interval)
        left, right = interval
        if not left < right:
            return _invalid("INVALID_QUADRATIC_MVT_DOMAIN")
        quadratic, linear, _constant = coefficients
        witness = _bounded_derived_fraction((left + right) / 2)
        slope = _bounded_derived_fraction(quadratic * (left + right) + linear)
    except (KeyError, TypeError, ValueError):
        return _invalid("INVALID_QUADRATIC_MVT_DOMAIN")
    return _available(
        "PASS",
        {
            "coefficients": coefficients,
            "interval": interval,
            "witness": witness,
            "secant_slope": slope,
            "derivative_at_witness": slope,
            "verified": True,
        },
        "EXACT_POLYNOMIAL_IDENTITY_ORACLE",
    )


def _extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    old_r, r = abs(a), abs(b)
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_r, old_s if a >= 0 else -old_s, old_t if b >= 0 else -old_t


def _f3(inputs: Mapping[str, Any]) -> IndependentOracle:
    try:
        a, b = inputs["integer_a"], inputs["integer_b"]
        if any(type(item) is not int or abs(item).bit_length() > 4096 for item in (a, b)):
            raise TypeError
        gcd_value, coefficient_a, coefficient_b = _extended_gcd(a, b)
        if gcd_value != math.gcd(a, b) or a * coefficient_a + b * coefficient_b != gcd_value:
            raise ArithmeticError
    except (KeyError, TypeError, ValueError, ArithmeticError):
        return _invalid("INVALID_BEZOUT_DOMAIN")
    return _available(
        "PASS",
        {
            "a": a,
            "b": b,
            "gcd": gcd_value,
            "x": coefficient_a,
            "y": coefficient_b,
            "verified": True,
        },
        "EXACT_EUCLIDEAN_ALGORITHM_ORACLE",
    )


def _c1(inputs: Mapping[str, Any]) -> IndependentOracle:
    try:
        coordinates = inputs["coordinates"]
        if type(coordinates) is not tuple or len(coordinates) != 2:
            raise TypeError
        x, y = coordinates
        if (
            type(x) is not sp.Symbol
            or type(y) is not sp.Symbol
            or x == y
            or x.is_real is not True
            or y.is_real is not True
        ):
            raise TypeError
        u, v = inputs["real_part"], inputs["imag_part"]
        if not isinstance(u, sp.Expr) or not isinstance(v, sp.Expr):
            raise TypeError
        if u.has(sp.nan, sp.oo, -sp.oo, sp.zoo) or v.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
            raise ValueError
        if not (u.free_symbols | v.free_symbols) <= {x, y}:
            raise ValueError
        polynomials = (sp.Poly(u, x, y), sp.Poly(v, x, y))
        coefficients = tuple(
            coefficient
            for polynomial in polynomials
            for coefficient in polynomial.coeffs()
        )
        if any(
            coefficient.atoms(sp.Float)
            or coefficient.is_real is not True
            or coefficient.is_finite is not True
            for coefficient in coefficients
        ):
            raise ValueError
        residuals = (
            sp.cancel(sp.diff(u, x) - sp.diff(v, y)),
            sp.cancel(sp.diff(u, y) + sp.diff(v, x)),
        )
    except (KeyError, TypeError, ValueError, CoercionFailed, PolynomialError):
        return _invalid("INVALID_CAUCHY_RIEMANN_DOMAIN")
    return _available(
        "PASS",
        {
            "u": u,
            "v": v,
            "x": x,
            "y": y,
            "residuals": residuals,
            "holomorphic": residuals == (0, 0),
        },
        "EXACT_FORMAL_DERIVATIVE_ORACLE",
    )


def _c2(inputs: Mapping[str, Any]) -> IndependentOracle:
    try:
        variable = inputs["variable"]
        pole_fraction = _fraction(inputs["pole"])
        pole = sp.Rational(pole_fraction.numerator, pole_fraction.denominator)
        if type(variable) is not sp.Symbol:
            raise TypeError
        raw_expression = inputs["form"]
        if not isinstance(raw_expression, sp.Expr):
            raise TypeError
        expression = sp.cancel(raw_expression)
        if expression.has(sp.nan, sp.oo, -sp.oo, sp.zoo) or expression.free_symbols - {variable}:
            raise ValueError
        numerator_expr, denominator_expr = sp.fraction(expression)
        numerator = sp.Poly(numerator_expr, variable, domain=sp.QQ)
        denominator = sp.Poly(denominator_expr, variable, domain=sp.QQ)
        if denominator.is_zero or denominator.eval(pole) != 0 or numerator.eval(pole) == 0:
            raise ValueError
        factor = sp.Poly(variable - pole, variable, domain=sp.QQ)
        remainder = denominator
        order = 0
        while remainder.eval(pole) == 0:
            remainder, exact_remainder = remainder.div(factor)
            if not exact_remainder.is_zero:
                raise ArithmeticError
            order += 1
        analytic = sp.cancel(numerator.as_expr() / remainder.as_expr())
        residue = sp.cancel(
            sp.diff(analytic, variable, order - 1).subs(variable, pole) / sp.factorial(order - 1)
        )
    except (KeyError, TypeError, ValueError, ArithmeticError, ZeroDivisionError, sp.PolynomialError):
        return _invalid("INVALID_MEROMORPHIC_DOMAIN")
    return _available(
        "PASS",
        {
            "expression": expression,
            "variable": variable,
            "pole": pole,
            "pole_order": order,
            "residue": residue,
            "verified": True,
        },
        "EXACT_LAURENT_COEFFICIENT_ORACLE",
    )


def _x1(inputs: Mapping[str, Any], constraints: Mapping[str, Any], tolerance: float) -> IndependentOracle:
    try:
        raw_coefficients = inputs["coefficients"]
        raw_grid = inputs["grid"]
        if (
            type(raw_coefficients) is not tuple
            or type(raw_grid) is not tuple
            or not raw_coefficients
            or not raw_grid
            or len(raw_coefficients) > 4096
            or len(raw_grid) > 4096
            or len(raw_coefficients) * len(raw_grid) > 100_000
        ):
            raise ValueError
        coefficients = tuple(_fraction(item) for item in raw_coefficients)
        grid = tuple(_fraction(item) for item in raw_grid)
        declared_tolerance = _fraction(constraints["absolute_error_tolerance"])
        if (
            not coefficients
            or not grid
            or declared_tolerance < 0
            or type(tolerance) is not float
            or not math.isfinite(tolerance)
            or tolerance < 0
        ):
            raise ValueError
        def exact_horner(point: Fraction) -> Fraction:
            result = Fraction()
            for coefficient in reversed(coefficients):
                result = _bounded_derived_fraction(result * point + coefficient)
            return result

        values = tuple(exact_horner(point) for point in grid)
    except (KeyError, TypeError, ValueError):
        return _invalid("INVALID_POLYNOMIAL_ENCLOSURE_DOMAIN")
    try:
        numerical_values = tuple(float(value) for value in values)
    except (OverflowError, ValueError):
        return _available(
            "NOT_ESTABLISHED",
            {
                "coefficients": coefficients,
                "grid": grid,
                "exact_values": values,
                "numerical_values": None,
                "point_errors": None,
                "maximum_error": None,
                "tolerance": declared_tolerance,
                "binary64_feasible": False,
                "failure": "BINARY64_OVERFLOW",
            },
            "EXACT_HORNER_BINARY64_FEASIBILITY_ORACLE",
        )
    if any(not math.isfinite(value) for value in numerical_values):
        return _available(
            "NOT_ESTABLISHED",
            {
                "coefficients": coefficients,
                "grid": grid,
                "exact_values": values,
                "numerical_values": numerical_values,
                "point_errors": None,
                "maximum_error": None,
                "tolerance": declared_tolerance,
                "binary64_feasible": False,
                "failure": "NONFINITE_BINARY64_RESULT",
            },
            "EXACT_HORNER_BINARY64_FEASIBILITY_ORACLE",
        )
    point_errors = tuple(
        abs(Fraction.from_float(observed) - exact)
        for observed, exact in zip(numerical_values, values)
    )
    maximum_error = max(point_errors, default=Fraction())
    feasible = maximum_error <= declared_tolerance
    certificate = {
        "coefficients": coefficients,
        "grid": grid,
        "exact_values": values,
        "numerical_values": numerical_values,
        "point_errors": point_errors,
        "maximum_error": maximum_error,
        "tolerance": declared_tolerance,
        "binary64_feasible": feasible,
        "failure": "" if feasible else "NEAREST_BINARY64_EXCEEDS_TOLERANCE",
    }
    if not feasible:
        return _available(
            "NOT_ESTABLISHED",
            certificate,
            "EXACT_HORNER_BINARY64_FEASIBILITY_ORACLE",
        )
    return _available(
        "PASS",
        certificate,
        "EXACT_HORNER_BINARY64_FEASIBILITY_ORACLE",
    )


def _evaluate_independent_oracle(
    *,
    family: str,
    inputs: Mapping[str, Any],
    constraints: Mapping[str, Any],
    tolerance: float,
) -> IndependentOracle:
    """Evaluate the prospective oracle surface after structural admission."""

    if family == "F1":
        return _f1(inputs)
    if family == "F2":
        return _f2(inputs)
    if family == "F3":
        return _f3(inputs)
    if family == "C1":
        return _c1(inputs)
    if family == "C2":
        return _c2(inputs)
    if family == "X1":
        return _x1(inputs, constraints, tolerance)
    if family == "X2":
        return _unavailable("NO_INDEPENDENT_X2_ORACLE")
    return _unavailable("NO_INDEPENDENT_HISTORICAL_ORACLE")


def _exact_symbolic_equal(left: Any, right: Any) -> bool:
    try:
        if not isinstance(left, sp.Basic) or not isinstance(right, sp.Basic):
            return False
        return bool(sp.cancel(left - right) == 0)
    except (TypeError, ValueError, ZeroDivisionError):
        return False


def _exact_symbolic_sequence_equal(left: Any, right: Any) -> bool:
    return bool(
        type(left) is tuple
        and type(right) is tuple
        and len(left) == len(right)
        and all(_exact_symbolic_equal(a, b) for a, b in zip(left, right))
    )


def candidate_matches_independent_oracle(
    *,
    family: str,
    candidate: Mapping[str, Any],
    oracle_certificate: Mapping[str, Any],
) -> bool:
    """Check a candidate projection against an independently derived relation.

    The candidate and oracle inputs are plain mappings so this module remains
    independent of solver certificate classes.  F2 and F3 deliberately check
    their defining relations rather than equality with the oracle's chosen
    witness, because their valid witnesses need not be unique.
    """

    try:
        if type(candidate) is not dict or type(oracle_certificate) is not dict:
            return False
        if family == "F1":
            return bool(
                set(candidate)
                == {"lower", "upper", "lower_square_gap", "upper_square_gap", "verified"}
                and candidate["lower"] == oracle_certificate["lower"]
                and candidate["upper"] == oracle_certificate["upper"]
                and type(candidate["lower_square_gap"]) is int
                and type(candidate["upper_square_gap"]) is int
                and candidate["lower_square_gap"] == oracle_certificate["lower_gap"]
                and candidate["upper_square_gap"] == oracle_certificate["upper_gap"]
                and candidate["verified"] is True
            )
        if family == "F2":
            if set(candidate) != {
                "coefficients",
                "interval",
                "witness",
                "secant_slope",
                "derivative_at_witness",
                "verified",
            }:
                return False
            coefficients = tuple(_fraction(value) for value in candidate["coefficients"])
            interval = tuple(_fraction(value) for value in candidate["interval"])
            if len(coefficients) != 3 or len(interval) != 2:
                return False
            if coefficients != tuple(oracle_certificate["coefficients"]):
                return False
            if interval != tuple(oracle_certificate["interval"]):
                return False
            witness = _fraction(candidate["witness"])
            left, right = interval
            if not left < witness < right:
                return False
            a2, a1, a0 = coefficients
            value = lambda point: a2 * point * point + a1 * point + a0
            secant = (value(right) - value(left)) / (right - left)
            derivative = 2 * a2 * witness + a1
            return bool(
                _fraction(candidate["secant_slope"]) == secant
                and _fraction(candidate["derivative_at_witness"]) == derivative
                and secant == derivative
                and candidate["verified"] is True
            )
        if family == "F3":
            if set(candidate) != {"a", "b", "gcd", "x", "y", "verified"}:
                return False
            if any(type(candidate[key]) is not int for key in ("a", "b", "gcd", "x", "y")):
                return False
            a, b = candidate["a"], candidate["b"]
            gcd_value, x, y = candidate["gcd"], candidate["x"], candidate["y"]
            return bool(
                a == oracle_certificate["a"]
                and b == oracle_certificate["b"]
                and gcd_value == math.gcd(a, b)
                and gcd_value >= 0
                and a * x + b * y == gcd_value
                and candidate["verified"] is True
            )
        if family == "C1":
            if set(candidate) != {"u", "v", "x", "y", "residuals", "holomorphic"}:
                return False
            residuals = candidate["residuals"]
            return bool(
                candidate["x"] == oracle_certificate["x"]
                and candidate["y"] == oracle_certificate["y"]
                and _exact_symbolic_equal(candidate["u"], oracle_certificate["u"])
                and _exact_symbolic_equal(candidate["v"], oracle_certificate["v"])
                and _exact_symbolic_sequence_equal(residuals, oracle_certificate["residuals"])
                and type(candidate["holomorphic"]) is bool
                and candidate["holomorphic"] is oracle_certificate["holomorphic"]
            )
        if family == "C2":
            if set(candidate) != {
                "expression", "variable", "pole", "pole_order", "residue", "verified"
            }:
                return False
            return bool(
                candidate["variable"] == oracle_certificate["variable"]
                and _exact_symbolic_equal(candidate["expression"], oracle_certificate["expression"])
                and _exact_symbolic_equal(candidate["pole"], oracle_certificate["pole"])
                and type(candidate["pole_order"]) is int
                and candidate["pole_order"] == oracle_certificate["pole_order"]
                and _exact_symbolic_equal(candidate["residue"], oracle_certificate["residue"])
                and candidate["verified"] is True
            )
        if family == "X1":
            required = {
                "coefficients",
                "grid",
                "exact_values",
                "numerical_values",
                "point_errors",
                "maximum_error",
                "tolerance",
                "verified",
            }
            return bool(
                set(candidate) == required
                and tuple(candidate["coefficients"]) == tuple(oracle_certificate["coefficients"])
                and tuple(candidate["grid"]) == tuple(oracle_certificate["grid"])
                and tuple(candidate["exact_values"]) == tuple(oracle_certificate["exact_values"])
                and tuple(candidate["numerical_values"])
                == tuple(oracle_certificate["numerical_values"])
                and tuple(candidate["point_errors"])
                == tuple(oracle_certificate["point_errors"])
                and candidate["maximum_error"] == oracle_certificate["maximum_error"]
                and candidate["tolerance"] == oracle_certificate["tolerance"]
                and oracle_certificate["binary64_feasible"] is True
                and candidate["verified"] is True
            )
        return False
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return False


_ORACLE_MODULE_NAME = "experiments.pct_goal_solver.campaign_oracles"
_ORACLE_RECEIPT_METHOD = "prospective-oracle-structural-v1"
_ORACLE_IMPORT_ALLOWLIST = tuple(sorted({
    ("from", 0, "__future__", "annotations", ""),
    ("import", 0, "ast", "ast", ""),
    ("from", 0, "dataclasses", "dataclass", ""),
    ("from", 0, "dataclasses", "replace", ""),
    ("import", 0, "dis", "dis", ""),
    ("from", 0, "fractions", "Fraction", ""),
    ("import", 0, "hashlib", "hashlib", ""),
    ("import", 0, "inspect", "inspect", ""),
    ("import", 0, "math", "math", ""),
    ("from", 0, "pathlib", "Path", ""),
    ("from", 0, "types", "FunctionType", ""),
    ("from", 0, "types", "MappingProxyType", ""),
    ("from", 0, "types", "ModuleType", ""),
    ("from", 0, "typing", "Any", ""),
    ("from", 0, "typing", "Mapping", ""),
    ("import", 0, "sympy", "sympy", "sp"),
    ("from", 0, "sympy.polys.polyerrors", "CoercionFailed", ""),
    ("from", 0, "sympy.polys.polyerrors", "PolynomialError", ""),
}))
_FORBIDDEN_DYNAMIC_GLOBALS = frozenset({"__import__", "eval", "exec"})


def _source_import_manifest(source: str) -> tuple[tuple[str, int, str, str, str], ...]:
    """Extract exact import bindings rather than only imported module objects."""

    rows: list[tuple[str, int, str, str, str]] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            rows.extend(
                ("import", 0, alias.name, alias.name, alias.asname or "")
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            rows.extend(
                (
                    "from",
                    node.level,
                    node.module or "",
                    alias.name,
                    alias.asname or "",
                )
                for alias in node.names
            )
    return tuple(sorted(rows))


def _failed_independence_receipt(reason: str) -> dict[str, Any]:
    return {
        "established": False,
        "method_id": _ORACLE_RECEIPT_METHOD,
        "module": _ORACLE_MODULE_NAME,
        "source_sha256": None,
        "callable_binding_sha256": None,
        "callable_bindings": (),
        "reviewed_imports": (),
        "reviewed_module_attributes": (),
        "live_dependencies": (),
        "reason": reason,
    }


def _assess_oracle_independence_source(
    source: str,
    module_file: Path,
) -> dict[str, Any]:
    """Bind reviewed source imports to the exact live callable graph."""

    imports = _source_import_manifest(source)
    if imports != _ORACLE_IMPORT_ALLOWLIST:
        return _failed_independence_receipt("UNREVIEWED_SOURCE_IMPORTS")

    namespace = globals()
    for name, expected in _EXPECTED_INTERNAL_CALLABLES.items():
        if namespace.get(name) is not expected:
            return _failed_independence_receipt("INTERNAL_CALLABLE_BINDING_MISMATCH")
    for name, expected in _EXPECTED_MODULE_BINDINGS.items():
        if namespace.get(name) is not expected:
            return _failed_independence_receipt("MODULE_BINDING_MISMATCH")
    for (module_name, attribute_name), expected in _EXPECTED_MODULE_ATTRIBUTE_BINDINGS.items():
        module = _EXPECTED_MODULE_BINDINGS[module_name]
        if getattr(module, attribute_name, None) is not expected:
            return _failed_independence_receipt("MODULE_ATTRIBUTE_BINDING_MISMATCH")
    for name, expected in _EXPECTED_EXTERNAL_CALLABLE_BINDINGS.items():
        if namespace.get(name) is not expected:
            return _failed_independence_receipt("EXTERNAL_CALLABLE_BINDING_MISMATCH")
    for (binding_kind, owner, name), expected_code in _EXPECTED_EXTERNAL_CODE_BINDINGS.items():
        dependency = (
            namespace[name]
            if binding_kind == "global"
            else getattr(_EXPECTED_MODULE_BINDINGS[owner], name, None)
        )
        if getattr(dependency, "__code__", None) is not expected_code:
            return _failed_independence_receipt("EXTERNAL_CALLABLE_CODE_MISMATCH")
    if namespace.get("IndependentOracle") is not _EXPECTED_INTERNAL_CLASS:
        return _failed_independence_receipt("INTERNAL_CLASS_BINDING_MISMATCH")

    callable_rows: list[tuple[str, str, str]] = []
    live_dependencies: set[str] = set()
    for name, function in _EXPECTED_INTERNAL_CALLABLES.items():
        if function.__code__ is not _EXPECTED_INTERNAL_CODE_BINDINGS[name]:
            return _failed_independence_receipt("INTERNAL_CALLABLE_CODE_MISMATCH")
        if (
            type(function) is not FunctionType
            or function.__module__ != _ORACLE_MODULE_NAME
            or Path(function.__code__.co_filename).resolve() != module_file
        ):
            return _failed_independence_receipt("INTERNAL_CALLABLE_SOURCE_MISMATCH")
        try:
            callable_source = inspect.getsource(function).encode("utf-8")
        except (OSError, TypeError):
            return _failed_independence_receipt("CALLABLE_SOURCE_UNAVAILABLE")
        callable_rows.append((
            name,
            function.__qualname__,
            hashlib.sha256(callable_source).hexdigest(),
        ))
        if any(
            instruction.opname in {"LOAD_GLOBAL", "LOAD_NAME"}
            and instruction.argval in _FORBIDDEN_DYNAMIC_GLOBALS
            for instruction in dis.get_instructions(function)
        ):
            return _failed_independence_receipt("DYNAMIC_IMPORT_OR_EXECUTION_FORBIDDEN")
        for dependency_name in function.__code__.co_names:
            if dependency_name not in function.__globals__:
                continue
            dependency = function.__globals__[dependency_name]
            if type(dependency) is FunctionType:
                if _EXPECTED_INTERNAL_CALLABLES.get(dependency_name) is dependency:
                    live_dependencies.add(f"callable:{dependency_name}")
                elif _EXPECTED_EXTERNAL_CALLABLE_BINDINGS.get(dependency_name) is dependency:
                    live_dependencies.add(
                        f"external:{dependency.__module__}.{dependency.__qualname__}"
                    )
                else:
                    return _failed_independence_receipt("UNREVIEWED_LIVE_CALLABLE")
            elif isinstance(dependency, ModuleType):
                if _EXPECTED_MODULE_BINDINGS.get(dependency_name) is not dependency:
                    return _failed_independence_receipt("UNREVIEWED_LIVE_MODULE")
                live_dependencies.add(f"module:{dependency.__name__}")
            elif callable(dependency):
                approved = (
                    dependency is _EXPECTED_INTERNAL_CLASS
                    or _EXPECTED_EXTERNAL_CALLABLE_BINDINGS.get(dependency_name)
                    is dependency
                )
                if not approved:
                    return _failed_independence_receipt("UNREVIEWED_EXTERNAL_CALLABLE")
                live_dependencies.add(
                    f"external:{getattr(dependency, '__module__', '')}."
                    f"{getattr(dependency, '__qualname__', dependency_name)}"
                )

    callable_rows.sort()
    source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    callable_binding_sha256 = hashlib.sha256(
        repr(tuple(callable_rows)).encode("utf-8")
    ).hexdigest()
    return {
        "established": True,
        "method_id": _ORACLE_RECEIPT_METHOD,
        "module": _ORACLE_MODULE_NAME,
        "source_sha256": source_sha256,
        "callable_binding_sha256": callable_binding_sha256,
        "callable_bindings": tuple(callable_rows),
        "reviewed_imports": imports,
        "reviewed_module_attributes": tuple(
            f"{module_name}.{attribute_name}"
            for module_name, attribute_name in _EXPECTED_MODULE_ATTRIBUTE_BINDINGS
        ),
        "live_dependencies": tuple(sorted(live_dependencies)),
        "reason": "",
    }


def oracle_independence_receipt() -> dict[str, Any]:
    """Return a fail-closed receipt for source and live dependency independence."""

    try:
        module_file = Path(__file__).resolve()
        if not module_file.is_file():
            return _failed_independence_receipt("ORACLE_SOURCE_UNAVAILABLE")
        source = module_file.read_text(encoding="utf-8")
        return _assess_oracle_independence_source(source, module_file)
    except Exception:
        return _failed_independence_receipt("ORACLE_INDEPENDENCE_CHECK_FAILED")


def build_independent_oracle(
    *,
    family: str,
    inputs: Mapping[str, Any],
    constraints: Mapping[str, Any],
    tolerance: float,
) -> IndependentOracle:
    """Evaluate only when the independent source and live bindings are proven."""

    receipt = oracle_independence_receipt()
    if receipt.get("established") is not True:
        return IndependentOracle(
            authoritative=False,
            availability="UNAVAILABLE",
            expected_verdict="UNKNOWN",
            certificate=None,
            method="UNAVAILABLE",
            reason="ORACLE_INDEPENDENCE_NOT_ESTABLISHED",
            independence_receipt=receipt,
        )
    result = _evaluate_independent_oracle(
        family=family,
        inputs=inputs,
        constraints=constraints,
        tolerance=tolerance,
    )
    return replace(result, independence_receipt=receipt)


_EXPECTED_MODULE_BINDINGS = MappingProxyType({
    "ast": ast,
    "dis": dis,
    "hashlib": hashlib,
    "inspect": inspect,
    "math": math,
    "sp": sp,
})
_EXPECTED_MODULE_ATTRIBUTE_BINDINGS = MappingProxyType({
    ("ast", "Import"): ast.Import,
    ("ast", "ImportFrom"): ast.ImportFrom,
    ("ast", "parse"): ast.parse,
    ("ast", "walk"): ast.walk,
    ("dis", "get_instructions"): dis.get_instructions,
    ("hashlib", "sha256"): hashlib.sha256,
    ("inspect", "getsource"): inspect.getsource,
    ("math", "gcd"): math.gcd,
    ("math", "isfinite"): math.isfinite,
    ("sp", "Basic"): sp.Basic,
    ("sp", "Expr"): sp.Expr,
    ("sp", "Float"): sp.Float,
    ("sp", "Poly"): sp.Poly,
    ("sp", "PolynomialError"): sp.PolynomialError,
    ("sp", "QQ"): sp.QQ,
    ("sp", "Rational"): sp.Rational,
    ("sp", "Symbol"): sp.Symbol,
    ("sp", "cancel"): sp.cancel,
    ("sp", "diff"): sp.diff,
    ("sp", "factorial"): sp.factorial,
    ("sp", "fraction"): sp.fraction,
    ("sp", "nan"): sp.nan,
    ("sp", "oo"): sp.oo,
    ("sp", "zoo"): sp.zoo,
})
_EXPECTED_EXTERNAL_CALLABLE_BINDINGS = MappingProxyType({
    "CoercionFailed": CoercionFailed,
    "Fraction": Fraction,
    "FunctionType": FunctionType,
    "MappingProxyType": MappingProxyType,
    "ModuleType": ModuleType,
    "Path": Path,
    "PolynomialError": PolynomialError,
    "dataclass": dataclass,
    "replace": replace,
})
_EXPECTED_EXTERNAL_CODE_BINDINGS = MappingProxyType({
    **{
        ("global", "", name): dependency.__code__
        for name, dependency in _EXPECTED_EXTERNAL_CALLABLE_BINDINGS.items()
        if type(dependency) is FunctionType
    },
    **{
        ("module", module_name, attribute_name): dependency.__code__
        for (module_name, attribute_name), dependency
        in _EXPECTED_MODULE_ATTRIBUTE_BINDINGS.items()
        if type(dependency) is FunctionType
    },
})
_EXPECTED_INTERNAL_CLASS = IndependentOracle
_EXPECTED_INTERNAL_CALLABLES = MappingProxyType({
    name: value
    for name, value in tuple(globals().items())
    if type(value) is FunctionType and value.__module__ == _ORACLE_MODULE_NAME
})
_EXPECTED_INTERNAL_CODE_BINDINGS = MappingProxyType({
    name: function.__code__
    for name, function in _EXPECTED_INTERNAL_CALLABLES.items()
})
