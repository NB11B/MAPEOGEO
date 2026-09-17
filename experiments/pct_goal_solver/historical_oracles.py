"""Reference calculations for the finite historical G1--G12 campaign.

This module is deliberately outside the planner, operator registry, and strict
terminal verifier.  It consumes only solver-visible mathematical roots and
returns a reference outcome.  The algorithms are small, bounded alternatives
used for campaign assessment; they do not authorize planner execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations
import math
from typing import Any, Mapping

import sympy as sp

from .model import SolverVisibleGoal


@dataclass(frozen=True)
class HistoricalReference:
    expected_verdict: str
    candidate_value: Any | None
    method_id: str
    authoritative: bool = True
    implementation_independent: bool = True


def _fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("boolean is not a scalar")
    if type(value) is Fraction:
        return value
    if type(value) is int:
        return Fraction(value)
    if type(value) is float and math.isfinite(value):
        return Fraction(value)
    if isinstance(value, sp.Rational):
        return Fraction(int(value.p), int(value.q))
    raise ValueError("unsupported scalar")


def _rank_and_nullspace(value: Any) -> tuple[int, tuple[tuple[Fraction, ...], ...]]:
    rows = [[_fraction(item) for item in row] for row in value]
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("invalid matrix")
    height, width = len(rows), len(rows[0])
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(width):
        pivot = next((row for row in range(pivot_row, height) if rows[row][column]), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        divisor = rows[pivot_row][column]
        rows[pivot_row] = [item / divisor for item in rows[pivot_row]]
        for row in range(height):
            if row == pivot_row or rows[row][column] == 0:
                continue
            multiplier = rows[row][column]
            rows[row] = [a - multiplier * b for a, b in zip(rows[row], rows[pivot_row])]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == height:
            break
    free_columns = [column for column in range(width) if column not in pivot_columns]
    basis = []
    for free in free_columns:
        vector = [Fraction() for _ in range(width)]
        vector[free] = Fraction(1)
        for row, pivot in enumerate(pivot_columns):
            vector[pivot] = -rows[row][free]
        basis.append(tuple(vector))
    return len(pivot_columns), tuple(basis)


def _matmul(left: Any, right: Any) -> tuple[tuple[Fraction, ...], ...]:
    a = [[_fraction(item) for item in row] for row in left]
    b = [[_fraction(item) for item in row] for row in right]
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("incompatible matrices")
    return tuple(
        tuple(
            sum(
                (a[row][k] * b[k][column] for k in range(len(b))),
                Fraction(),
            )
            for column in range(len(b[0]))
        )
        for row in range(len(a))
    )


def _subtract(left: Any, right: Any) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(_fraction(a) - _fraction(b) for a, b in zip(arow, brow)) for arow, brow in zip(left, right))


def _graph(value: Any) -> tuple[tuple[Any, ...], frozenset[frozenset[Any]]]:
    edges = tuple(tuple(edge) for edge in value)
    vertices = tuple(sorted({vertex for edge in edges for vertex in edge}, key=lambda item: (type(item).__name__, repr(item))))
    return vertices, frozenset(frozenset(edge) for edge in edges)


def _isomorphic(left: Any, right: Any) -> bool:
    va, ea = _graph(left)
    vb, eb = _graph(right)
    if len(va) != len(vb) or len(ea) != len(eb):
        return False
    if len(va) > 8:
        raise ValueError("reference permutation bound exceeded")
    for image in permutations(vb):
        mapping = dict(zip(va, image))
        if frozenset(frozenset((mapping[a], mapping[b])) for a, b in (tuple(edge) for edge in ea)) == eb:
            return True
    return False


def _points(value: Any) -> tuple[tuple[Fraction, Fraction], ...]:
    return tuple((_fraction(x), _fraction(y)) for x, y in value)


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _convex(points) -> bool:
    if len(points) < 3:
        return False
    signs = [_cross(points[i - 1], points[i], points[(i + 1) % len(points)]) for i in range(len(points))]
    return all(value > 0 for value in signs) or all(value < 0 for value in signs)


def _area(points) -> Fraction:
    return abs(
        sum(
            (a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1])),
            Fraction(),
        )
    ) / 2


def _hull(points):
    ordered = sorted(set(points))
    halves = []
    for sequence in (ordered, tuple(reversed(ordered))):
        half = []
        for point in sequence:
            while len(half) >= 2 and _cross(half[-2], half[-1], point) <= 0:
                half.pop()
            half.append(point)
        halves.append(half[:-1])
    return tuple(halves[0] + halves[1])


def _rotation_order(value: Any, tolerance: float) -> int:
    points = tuple((float(_fraction(x)), float(_fraction(y))) for x, y in value)
    n = len(points)
    cx = sum(x for x, _ in points) / n
    cy = sum(y for _, y in points) / n
    centered = tuple((x - cx, y - cy) for x, y in points)
    scale = max(math.hypot(x, y) for x, y in centered)
    for order in range(n, 1, -1):
        if n % order:
            continue
        shift = n // order
        source = next(point for point in centered if math.hypot(*point) > 0)
        target = centered[(centered.index(source) + shift) % n]
        denominator = source[0] ** 2 + source[1] ** 2
        cosine = (source[0] * target[0] + source[1] * target[1]) / denominator
        sine = (source[0] * target[1] - source[1] * target[0]) / denominator
        residual = max(
            math.hypot(cosine * x - sine * y - centered[(i + shift) % n][0],
                       sine * x + cosine * y - centered[(i + shift) % n][1]) / scale
            for i, (x, y) in enumerate(centered)
        )
        if residual <= tolerance:
            return order
    return 1


def _reference(goal: SolverVisibleGoal) -> Any:
    roots = {key: artifact.value for key, artifact in goal.inputs.items()}
    family = goal.family
    if family == "G1":
        zeta = tuple(int(value) for value in roots["cumulative"])
        return tuple(
            sum((-1) ** (target.bit_count() - source.bit_count()) * zeta[source]
                for source in range(len(zeta)) if source & target == source)
            for target in range(len(zeta))
        )
    if family == "G2":
        rank, basis = _rank_and_nullspace(roots["observation_matrix"])
        nullity = len(roots["observation_matrix"][0]) - rank
        return {"unique": nullity == 0, "nullity": nullity, "basis": basis}
    if family == "G3":
        residual = _subtract(_matmul(roots["target_boundary"], roots["edge_map"]),
                             _matmul(roots["vertex_map"], roots["source_boundary"]))
        rows = tuple(index for index, row in enumerate(residual) if any(row))
        columns = tuple(index for index in range(len(residual[0])) if any(row[index] for row in residual))
        return {"is_chain_map": not rows, "residual": residual, "residual_rows": rows,
                "map_columns": columns, "localized": bool(rows and columns)}
    if family == "G4":
        barcodes = tuple(tuple(sorted(tuple(row) for row in roots[key])) for key in ("barcode_a", "barcode_b"))
        grid = sorted({point for barcode in barcodes for _, birth, death in barcode for point in (birth, death)})
        degrees = sorted({degree for barcode in barcodes for degree, _, _ in barcode})
        def betti(barcode):
            return tuple(tuple(sum(degree == d and birth <= t < death for d, birth, death in barcode)
                               for degree in degrees) for t in grid)
        curves = tuple(betti(barcode) for barcode in barcodes)
        euler = tuple(tuple(sum((-1) ** degree * count for degree, count in zip(degrees, row)) for row in curve)
                      for curve in curves)
        level = "EULER" if euler[0] != euler[1] else "BETTI" if curves[0] != curves[1] else "BARCODE" if barcodes[0] != barcodes[1] else "NONE"
        return {"level": level, "distinct": level != "NONE"}
    if family == "G5":
        return {"distinct": not _isomorphic(roots["graph_a"], roots["graph_b"])}
    if family == "G6":
        return _rank_and_nullspace(roots["exact_matrix"])[0]
    if family == "G7":
        symbols = tuple(sp.Symbol(str(item)) if type(item) is str else item for item in roots["state"])
        names = {str(symbol): symbol for symbol in symbols} | {"pi": sp.pi}
        generator = sp.Matrix([[sp.sympify(item, locals=names) for item in row] for row in roots["generator"]])
        invariant = sp.sympify(roots["candidate_invariant"], locals=names)
        derivative = sum(sp.diff(invariant, symbol) * component
                         for symbol, component in zip(symbols, generator * sp.Matrix(symbols)))
        return bool(sp.expand(derivative) == 0)
    if family == "G8":
        rows = tuple(tuple(_fraction(item) for item in row) for row in roots["trajectory"])
        products = tuple(area * c for _, area, _, c in rows)
        squares = tuple(perimeter * perimeter for _, _, perimeter, _ in rows)
        x = tuple(item - products[0] for item in products[1:-1])
        y = tuple(item - squares[0] for item in squares[1:-1])
        return -sum(a * b for a, b in zip(x, y)) / sum(a * a for a in x)
    if family == "G9":
        polygon = _points(roots["body"])
        if not _convex(polygon):
            raise ValueError("NOT_APPLICABLE")
        offset = float(_fraction(roots["offset"]))
        perimeter = sum(math.hypot(float(b[0] - a[0]), float(b[1] - a[1]))
                        for a, b in zip(polygon, polygon[1:] + polygon[:1]))
        return float(_area(polygon)) + perimeter * offset + math.pi * offset * offset
    if family == "G10":
        return {"order": _rotation_order(roots["body"], float(goal.allowed_numeric_tolerance))}
    if family == "G11":
        a, b = (_points(roots[key]) for key in ("body_a", "body_b"))
        sums = tuple((x1 + x2, y1 + y2) for x1, y1 in a for x2, y2 in b)
        area_a, area_b = _area(_hull(a)), _area(_hull(b))
        mixed = (_area(_hull(sums)) - area_a - area_b) / 2
        defect = mixed * mixed / (area_a * area_b) - 1
        tolerance = _fraction(goal.allowed_numeric_tolerance)
        return {"homothetic": defect <= tolerance, "defect": defect}
    if family == "G12":
        declared = dict(goal.constraints)["symbols"]
        symbols = {str(name): sp.Symbol(str(name)) for name in declared}
        lhs = sp.sympify(roots["lhs"], locals=symbols)
        rhs = sp.sympify(roots["rhs"], locals=symbols)
        return bool(sp.cancel(lhs - rhs) == 0)
    raise ValueError(f"unsupported family: {family}")


def build_historical_reference(goal: SolverVisibleGoal) -> HistoricalReference:
    try:
        value = _reference(goal)
    except ValueError as error:
        if str(error) == "NOT_APPLICABLE":
            return HistoricalReference("NOT_APPLICABLE", None, "bounded-reference-v1")
        return HistoricalReference("INVALID", None, "bounded-reference-v1")
    return HistoricalReference("PASS", value, "bounded-reference-v1")


def _reference_equivalent(observed: Any, expected: Any, tolerance: float) -> bool:
    """Compare a solver value with the bounded reference without engine code."""

    if type(observed) is bool or type(expected) is bool:
        return type(observed) is bool and type(expected) is bool and observed is expected
    exact_numeric = (int, Fraction)
    if type(observed) in exact_numeric or isinstance(observed, sp.Rational):
        if type(expected) in exact_numeric or isinstance(expected, sp.Rational):
            try:
                return _fraction(observed) == _fraction(expected)
            except ValueError:
                return False
    if type(observed) is float or type(expected) is float:
        try:
            left, right = float(observed), float(expected)
        except (TypeError, ValueError, OverflowError):
            return False
        if not math.isfinite(left) or not math.isfinite(right):
            return False
        return abs(left - right) <= tolerance * max(1.0, abs(right))
    if isinstance(observed, sp.Basic) or isinstance(expected, sp.Basic):
        try:
            return bool(sp.simplify(sp.sympify(observed) - sp.sympify(expected)) == 0)
        except (TypeError, ValueError):
            return False
    if isinstance(observed, Mapping) and isinstance(expected, Mapping):
        return set(observed) == set(expected) and all(
            _reference_equivalent(observed[key], expected[key], tolerance)
            for key in expected
        )
    if type(observed) in (tuple, list) and type(expected) in (tuple, list):
        return len(observed) == len(expected) and all(
            _reference_equivalent(left, right, tolerance)
            for left, right in zip(observed, expected)
        )
    return type(observed) is type(expected) and observed == expected


def historical_candidate_satisfies_reference(
    goal: SolverVisibleGoal,
    candidate_value: Any,
) -> bool:
    """Check family-specific reference invariants without choosing one witness.

    Several historical outputs admit non-unique evidence (most notably a G2
    nullspace basis).  This assessment therefore checks the mathematical
    relation for each family instead of comparing every candidate with the
    deterministic witness emitted by :func:`_reference`.
    """

    try:
        reference = build_historical_reference(goal)
        if reference.expected_verdict != "PASS":
            return False
        tolerance = goal.allowed_numeric_tolerance
        if type(tolerance) is not float or not math.isfinite(tolerance) or tolerance < 0:
            return False
        expected = reference.candidate_value
        family = goal.family
        if family == "G1":
            return tuple(int(value) for value in candidate_value) == tuple(expected)
        if family == "G2":
            if type(candidate_value) is not dict or set(candidate_value) != {
                "unique", "nullity", "basis"
            }:
                return False
            if type(candidate_value["unique"]) is not bool:
                return False
            reported_nullity = _fraction(candidate_value["nullity"])
            if reported_nullity.denominator != 1:
                return False
            expected_nullity = expected["nullity"]
            basis = tuple(
                tuple(_fraction(entry) for entry in vector)
                for vector in candidate_value["basis"]
            )
            matrix = tuple(
                tuple(_fraction(entry) for entry in row)
                for row in goal.inputs["observation_matrix"].value
            )
            width = len(matrix[0])
            if any(len(vector) != width for vector in basis):
                return False
            independent_rank = 0 if not basis else _rank_and_nullspace(basis)[0]
            annihilated = all(
                sum((row[index] * vector[index] for index in range(width)), Fraction()) == 0
                for vector in basis
                for row in matrix
            )
            return bool(
                reported_nullity == expected_nullity
                and candidate_value["unique"] is (expected_nullity == 0)
                and len(basis) == expected_nullity
                and independent_rank == expected_nullity
                and annihilated
            )
        if family == "G3":
            observed = (
                candidate_value
                if type(candidate_value) is bool
                else candidate_value.get("is_chain_map")
                if type(candidate_value) is dict
                else None
            )
            return type(observed) is bool and observed is expected["is_chain_map"]
        if family in {"G4", "G5", "G10"}:
            return type(candidate_value) is dict and _reference_equivalent(
                candidate_value, expected, tolerance
            )
        if family == "G6":
            observed_rank = _fraction(candidate_value)
            return observed_rank.denominator == 1 and observed_rank == expected
        if family in {"G7", "G12"}:
            return type(candidate_value) is bool and candidate_value is expected
        if family == "G8":
            observed = _fraction(candidate_value)
            return abs(observed - expected) <= Fraction(tolerance)
        if family == "G9":
            observed = float(candidate_value)
            return math.isfinite(observed) and abs(observed - float(expected)) <= tolerance
        if family == "G11":
            if type(candidate_value) is not dict or set(candidate_value) != {"homothetic", "defect"}:
                return False
            observed_defect = _fraction(candidate_value["defect"])
            return bool(
                type(candidate_value["homothetic"]) is bool
                and candidate_value["homothetic"] is expected["homothetic"]
                and abs(observed_defect - _fraction(expected["defect"])) <= Fraction(tolerance)
            )
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return False
    return False


# Compatibility alias for callers from the pre-hardening branch.  Its behavior
# is relation-aware despite the historical name.
historical_candidate_matches_reference = historical_candidate_satisfies_reference
