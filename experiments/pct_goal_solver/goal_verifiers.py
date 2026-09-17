"""Root-recomputed, fail-closed terminal verification for G1--G12 goals.

Only original goal roots are used: no operator, sealed answer, intermediate label,
or candidate assertion supplies the reference. Dispatch is closed over an exact
(family, required_verifier_class) pair and a fixed target contract.

The supported symbolic language is rational expressions (polynomials for G7),
not executable Python. Geometry roots are finite simple convex polygons. G10
uses enclosed finite-order rotation residuals at the declared numeric tolerance;
G11 uses the dimensionless Minkowski homothety defect at that tolerance. Neither
numerical verdict purports to prove exact equality of arbitrary real inputs.

HistoricalGoalContract records bind complete targets, roots, constraints,
candidate schemas, tolerance metrics, and deterministic resource ceilings. G8
identifies its coefficient by exact rational least squares and checks a separate
normalized fit residual and excitation floor. G5's edge-list graph domain has
no isolated vertices; the empty edge list denotes the graph of order zero.
G5 signature-level and G10 spectrum diagnostics are outside these certificates
and are rejected, rather than preserved as unchecked claims.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
import keyword
from math import isfinite, isqrt
import re
import struct
from types import MappingProxyType
from typing import Any, Callable

import networkx as nx
import sympy as sp

from .model import Artifact, SolverVisibleGoal, TargetSpec, VerificationResult


VERIFIER_VERSION = "historical-root-v2"
_TARGETS = {
    "G1": ("BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "EXACT", "EXACT_EQUALITY"),
    "G2": ("IDENTIFIABILITY_RESULT", "MATRIX", "EXACT", "EXACT_LINEAR_ALGEBRA"),
    "G3": ("CHAIN_DIAGNOSIS", "CHAIN", "EXACT", "CHAIN_RESIDUAL"),
    "G4": ("REPRESENTATION_SEPARATION", "PERSISTENCE", "EXACT", "EXACT_EQUALITY"),
    "G5": ("GRAPH_DISTINGUISHABILITY", "GRAPH", "EXACT", "GRAPH_ISOMORPHISM_CONTROL"),
    "G6": ("MATRIX_RANK", "MATRIX", "EXACT", "EXACT_LINEAR_ALGEBRA"),
    "G7": ("INVARIANT_VERDICT", "SYMBOLIC", "SYMBOLIC", "SYMBOLIC_IDENTITY"),
    "G8": ("NUMERIC_RELATION", "NUMERICAL", "NUMERICAL", "NUMERIC_THEN_SYMBOLIC"),
    "G9": ("AREA", "GEOMETRY", "NUMERICAL", "GEOMETRIC_NUMERICAL"),
    "G10": ("ROTATIONAL_HARMONIC_ORDER", "NUMERICAL", "NUMERICAL", "SPECTRAL_NUMERICAL"),
    "G11": ("HOMOTHETY_VERDICT", "GEOMETRY", "NUMERICAL", "GEOMETRIC_NUMERICAL"),
    "G12": ("IDENTITY_VERDICT", "SYMBOLIC", "SYMBOLIC", "SYMBOLIC_IDENTITY"),
}


@dataclass(frozen=True)
class ResourceLimits:
    max_scalar_bits: int = 4096
    max_sequence_items: int = 1024
    max_payload_nodes: int = 8192
    max_payload_depth: int = 32
    max_matrix_dimension: int = 16
    max_matrix_bit_work: int = 200_000
    max_boolean_cardinality: int = 256
    max_barcode_intervals: int = 64
    max_graph_vertices: int = 12
    max_graph_edges: int = 66
    max_graph_search_nodes: int = 100_000
    max_polygon_vertices: int = 32
    max_polygon_product: int = 1024
    max_trajectory_rows: int = 128
    max_symbol_count: int = 4
    max_expression_chars: int = 4096
    max_expression_nodes: int = 256
    max_expression_depth: int = 24
    max_expression_exponent: int = 16
    max_expression_degree: int = 32
    max_expanded_terms: int = 2048
    max_search_budget: int = 100_000


@dataclass(frozen=True)
class FieldContract:
    name: str
    kind: str
    values: tuple = ()
    required: bool = True


@dataclass(frozen=True)
class RootContract:
    key: str
    semantic_type: str
    representation_class: str
    exactness_class: str
    metadata: tuple[FieldContract, ...] = ()
    domain: str = "family-validated-root"


@dataclass(frozen=True)
class CandidateSchema:
    kind: str
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class TolerancePolicy:
    metric: str = "exact-equality"
    maximum: Fraction = Fraction()
    fit_tolerance: Fraction = Fraction()
    conditioning_floor: Fraction = Fraction()


@dataclass(frozen=True)
class HistoricalGoalContract:
    family: str
    verifier_class: str
    target: TargetSpec
    roots: tuple[RootContract, ...]
    constraints: tuple[FieldContract, ...]
    candidate_schema: CandidateSchema
    tolerance_policy: TolerancePolicy
    resource_limits: ResourceLimits


_LIMITS = ResourceLimits()
# The public float spelling 0.001 is included, without rounding input tolerances.
_MAX_NUMERIC_TOLERANCE = Fraction(0.001)
_CHAIN_FIELDS = ("residual", "residual_rows", "map_columns", "localized")
_CONTRACT_ROWS = (
    ("G1", "atomic", "RECOVER", (RootContract("cumulative", "BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", "EXACT", (FieldContract("rank", "lattice-rank"),)),),
     (FieldContract("lattice_rank", "lattice-rank"),), CandidateSchema("integer-sequence"), TolerancePolicy()),
    ("G2", "identifiability", "ESTABLISH_UNIQUENESS", (RootContract("observation_matrix", "OBSERVATION_MATRIX", "MATRIX", "EXACT", (FieldContract("field", "literal", ("Q",)),)),),
     (FieldContract("require_unique", "literal", (True,)),), CandidateSchema("mapping", ("unique", "nullity", "basis")), TolerancePolicy()),
    ("G3", "chain_diagnosis", "VERIFY_AND_LOCALIZE", (
        RootContract("source_boundary", "BOUNDARY_OPERATOR", "CHAIN", "EXACT", (FieldContract("role", "literal", ("source",)),)),
        RootContract("target_boundary", "BOUNDARY_OPERATOR", "CHAIN", "EXACT", (FieldContract("role", "literal", ("target",)),)),
        RootContract("vertex_map", "CHAIN_MAP_DEGREE_0", "CHAIN", "EXACT"), RootContract("edge_map", "CHAIN_MAP_DEGREE_1", "CHAIN", "EXACT")),
     (FieldContract("localize_if_invalid", "literal", (True,)),), CandidateSchema("chain-diagnosis", ("is_chain_map",), _CHAIN_FIELDS, _CHAIN_FIELDS), TolerancePolicy()),
    ("G4", "separation_level", "FIND_FINEST_NEEDED", tuple(RootContract(key, "BARCODE", "PERSISTENCE", "EXACT") for key in ("barcode_a", "barcode_b")),
     (FieldContract("levels", "literal", (("BARCODE", "BETTI", "EULER"),)),), CandidateSchema("mapping", ("level", "distinct")), TolerancePolicy()),
    ("G5", "distinguish", "DISTINGUISH", tuple(RootContract(key, "FINITE_GRAPH", "GRAPH", "EXACT", domain="simple-undirected-edge-list-with-no-isolated-vertices") for key in ("graph_a", "graph_b")),
     (FieldContract("signature_bank", "literal", (("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL"),)),), CandidateSchema("mapping", ("distinct",)), TolerancePolicy()),
    ("G6", "rank", "SAFE_RANK", (
        RootContract("exact_matrix", "RATIONAL_MATRIX", "MATRIX", "EXACT", (FieldContract("field", "literal", ("Q",)),)),
        RootContract("numeric_matrix", "FLOAT_MATRIX", "MATRIX", "NUMERICAL", (FieldContract("dtype", "literal", ("float32", "float64")),))),
     (FieldContract("allow_exact_escalation", "literal", (True,)),), CandidateSchema("integer"), TolerancePolicy()),
    ("G7", "conserved", "VERIFY_CONSERVATION", (
        RootContract("generator", "SYMBOLIC_GENERATOR", "SYMBOLIC", "SYMBOLIC", (FieldContract("nilpotency_bound", "symbol-count"),)),
        RootContract("state", "SYMBOLIC_STATE", "SYMBOLIC", "SYMBOLIC"), RootContract("candidate_invariant", "SYMBOLIC_EXPRESSION", "SYMBOLIC", "SYMBOLIC")),
     (FieldContract("flow_parameter", "literal", ("t",)),), CandidateSchema("boolean"), TolerancePolicy()),
    ("G8", "invariant_coefficient", "DISCOVER_AND_VERIFY", (RootContract("trajectory", "NUMERIC_TRAJECTORY", "NUMERICAL", "NUMERICAL", (FieldContract("model", "literal", ("anchored_quadratic_relation_v1",)),)),),
     (FieldContract("relation_form", "literal", ("P2_plus_k_cA",)),), CandidateSchema("real"),
     TolerancePolicy("absolute-least-squares-coefficient-error", _MAX_NUMERIC_TOLERANCE, Fraction(1, 10**10), Fraction(1, 10**12))),
    ("G9", "offset_area", "PREDICT", (RootContract("body", "POLYGON", "GEOMETRY", "NUMERICAL"), RootContract("offset", "SCALAR", "NUMERICAL", "NUMERICAL")),
     (FieldContract("requires_convexity", "literal", (True,)),), CandidateSchema("real"), TolerancePolicy("absolute-Steiner-area-error", _MAX_NUMERIC_TOLERANCE)),
    ("G10", "harmonic_order", "INFER", (RootContract("body", "CONVEX_POLYGON", "GEOMETRY", "NUMERICAL"),),
     (FieldContract("samples", "literal", (768,)),), CandidateSchema("mapping", ("order",)), TolerancePolicy("normalized-Euclidean-residual-at-2*pi/order", _MAX_NUMERIC_TOLERANCE)),
    ("G11", "homothetic", "DISCRIMINATE", tuple(RootContract(key, "CONVEX_BODY", "GEOMETRY", "NUMERICAL") for key in ("body_a", "body_b")),
     (FieldContract("area_normalize", "literal", (True,)),), CandidateSchema("mapping", ("homothetic", "defect")), TolerancePolicy("dimensionless-Minkowski-defect", _MAX_NUMERIC_TOLERANCE)),
    ("G12", "equivalent", "PROVE_IDENTITY", tuple(RootContract(key, "SYMBOLIC_EXPRESSION", "SYMBOLIC", "SYMBOLIC") for key in ("lhs", "rhs")),
     (FieldContract("symbols", "symbols"),), CandidateSchema("boolean"), TolerancePolicy()),
)
HISTORICAL_GOAL_CONTRACTS = MappingProxyType({
    family: HistoricalGoalContract(family, _TARGETS[family][3],
        TargetSpec(target_id, _TARGETS[family][0], _TARGETS[family][1], objective, _TARGETS[family][2]),
        roots, constraints, schema, policy, _LIMITS)
    for family, target_id, objective, roots, constraints, schema, policy in _CONTRACT_ROWS
})
del _CONTRACT_ROWS

_SYMPY_INTEGER_TYPES = frozenset({sp.Integer, type(sp.S.Zero), type(sp.S.One), type(sp.S.NegativeOne)})
_SYMPY_RATIONAL_TYPES = _SYMPY_INTEGER_TYPES | {sp.Rational, type(sp.S.Half)}


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _sequence(value: Any, length: int | None = None) -> tuple:
    _require(type(value) in {tuple, list}, "expected an exact list/tuple")
    _require(len(value) <= _LIMITS.max_sequence_items, "sequence exceeds resource limit")
    if length is not None:
        _require(len(value) == length, "incorrect sequence dimension")
    return tuple(value)


def _integer(value: Any) -> int:
    _require(type(value) is int or type(value) in _SYMPY_INTEGER_TYPES, "expected an exact integer, not bool/float/subclass")
    result = int(value)
    _require(result.bit_length() <= _LIMITS.max_scalar_bits, "integer exceeds resource limit")
    return result


def _rational(value: Any) -> Fraction:
    if type(value) in {int, Fraction}:
        result = Fraction(value)
    elif type(value) in _SYMPY_RATIONAL_TYPES:
        result = Fraction(int(value.p), int(value.q))
    else:
        raise ValueError("expected a finite exact rational, not bool/subclass")
    _require(max(result.numerator.bit_length(), result.denominator.bit_length()) <= _LIMITS.max_scalar_bits,
             "rational exceeds resource limit")
    return result


def _real(value: Any) -> Fraction:
    if type(value) is float:
        _require(isfinite(value), "nonfinite numerical input")
        return Fraction(value)
    if type(value) is sp.Float:
        _require(value.is_finite is True, "nonfinite symbolic float")
        _, mantissa, exponent, _ = value._mpf_
        _require(max(mantissa.bit_length() + max(exponent, 0), max(-exponent, 0) + 1) <= _LIMITS.max_scalar_bits,
                 "symbolic float exceeds exact-conversion resource limit")
        return _rational(sp.Rational(value))
    return _rational(value)


def _mapping(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    _require(type(value) is dict, "certificate must be a dictionary")
    _require(required <= value.keys() and value.keys() <= required | optional, "incomplete or unknown certificate fields")
    return value


def _pairs(value: Any) -> dict:
    rows = _sequence(value)
    result = {}
    for row in rows:
        key, item = _sequence(row, 2)
        _require(type(key) is str and key not in result, "duplicate or malformed metadata/constraint key")
        result[key] = item
    return result


def _root(goal: SolverVisibleGoal, key: str) -> Any:
    artifact = goal.inputs[key]
    _require(type(artifact) is Artifact, "root must be an exact Artifact")
    return artifact.value


def _matrix(value: Any) -> sp.Matrix:
    rows = _sequence(value)
    _require(bool(rows), "empty matrix is outside the supported domain")
    width = len(_sequence(rows[0]))
    _require(width > 0, "matrix must have columns")
    _require(max(len(rows), width) <= _LIMITS.max_matrix_dimension, "matrix exceeds resource limit")
    parsed = [[_rational(x) for x in _sequence(row, width)] for row in rows]
    maximum_bits = max(
        max(item.numerator.bit_length(), item.denominator.bit_length())
        for row in parsed
        for item in row
    )
    work = len(parsed) * width * max(len(parsed), width) * maximum_bits
    _require(work <= _LIMITS.max_matrix_bit_work, "matrix exact-arithmetic work exceeds resource limit")
    return sp.Matrix(parsed)


def _same_literal(value: Any, expected: Any) -> bool:
    if type(value) is not type(expected):
        return False
    if type(value) is tuple:
        return len(value) == len(expected) and all(_same_literal(a, b) for a, b in zip(value, expected))
    return value == expected


def _validate_fields(value: Any, rules: tuple[FieldContract, ...]) -> dict:
    _require(type(value) is tuple, "metadata and constraints require exact tuples")
    supplied = _pairs(value)
    allowed = {rule.name for rule in rules}
    required = {rule.name for rule in rules if rule.required}
    _require(required <= supplied.keys() <= allowed, "missing or extra metadata/constraint fields")
    for rule in rules:
        if rule.name not in supplied:
            continue
        item = supplied[rule.name]
        if rule.kind == "literal":
            _require(any(_same_literal(item, expected) for expected in rule.values), "unregistered metadata/constraint value")
        elif rule.kind == "symbols":
            _require(type(item) is tuple, "symbol declarations require a tuple")
            _symbols(item)
        else:
            upper = {"lattice-rank": 8, "symbol-count": _LIMITS.max_symbol_count,
                     "polygon-count": _LIMITS.max_polygon_vertices}[rule.kind]
            minimum = 0 if rule.kind == "lattice-rank" else 1
            _require(type(item) is int and minimum <= item <= upper, "invalid bounded metadata/constraint integer")
    return supplied


def _bounded_payload(value: Any) -> None:
    """Reject cycles, opaque/subclass payloads and oversized work before algebra."""
    visited = 0
    active: set[int] = set()
    def walk(item: Any, depth: int) -> None:
        nonlocal visited
        visited += 1
        _require(visited <= _LIMITS.max_payload_nodes and depth <= _LIMITS.max_payload_depth,
                 "payload exceeds node/depth resource limit")
        kind = type(item)
        if item is None or kind is bool:
            return
        if kind in {int, Fraction, float, sp.Float} or kind in _SYMPY_RATIONAL_TYPES:
            _real(item)
            return
        if kind is str:
            _require(len(item) <= _LIMITS.max_expression_chars, "text exceeds resource limit")
            return
        if isinstance(item, sp.Expr):
            _expression_tree_budget(item)
            return
        _require(kind in {tuple, list, dict}, "unsupported payload type or subclass")
        _require(len(item) <= _LIMITS.max_sequence_items and id(item) not in active,
                 "cyclic or oversized payload")
        active.add(id(item))
        for child in (tuple(item.keys()) + tuple(item.values()) if kind is dict else item):
            walk(child, depth + 1)
        active.remove(id(item))
    walk(value, 0)


def _validate_artifact(artifact: Artifact) -> None:
    _require(type(artifact) is Artifact, "artifact subclasses are not certificate evidence")
    for item in (artifact.artifact_id, artifact.semantic_type, artifact.representation_class, artifact.exactness_class):
        _require(type(item) is str and 0 < len(item) <= 256, "invalid artifact identity/type field")
    _require(type(artifact.provenance) is tuple and len(artifact.provenance) <= 128
             and all(type(item) is str and 0 < len(item) <= 256 for item in artifact.provenance),
             "invalid nonauthoritative provenance")
    _bounded_payload((artifact.value, artifact.metadata))


def _validate_goal_contract(
    goal: SolverVisibleGoal,
    candidate: Artifact | None,
    contract: HistoricalGoalContract,
) -> None:
    _require(type(goal) is SolverVisibleGoal and type(goal.target) is TargetSpec, "unsupported goal/target subclass")
    _require(type(goal.goal_id) is str and 0 < len(goal.goal_id) <= 256, "invalid goal identity")
    _require(type(goal.search_budget) is int and 0 <= goal.search_budget <= contract.resource_limits.max_search_budget,
             "invalid bounded search budget")
    for item in (goal.target.target_id, goal.target.semantic_type, goal.target.representation_class,
                 goal.target.objective, goal.target.exactness_class):
        _require(type(item) is str, "target fields require exact strings")
    _validate_fields(goal.target.metadata, ())
    _require(goal.target == contract.target, "target violates complete historical contract")
    _require(type(goal.inputs) is dict and set(goal.inputs) == {root.key for root in contract.roots},
             "missing or extra historical root keys")
    _require(all(type(key) is str for key in goal.inputs), "root keys require exact strings")
    ids = set()
    for root in contract.roots:
        artifact = goal.inputs[root.key]
        _validate_artifact(artifact)
        _require(artifact.artifact_id not in ids, "duplicate root artifact identity")
        ids.add(artifact.artifact_id)
        _require((artifact.semantic_type, artifact.representation_class, artifact.exactness_class)
                 == (root.semantic_type, root.representation_class, root.exactness_class), "root violates artifact contract")
        _validate_fields(artifact.metadata, root.metadata)
    _bounded_payload(goal.constraints)
    constraints = _validate_fields(goal.constraints, contract.constraints)
    if goal.family == "G1":
        _require(_pairs(goal.inputs["cumulative"].metadata)["rank"] == constraints["lattice_rank"],
                 "root rank and goal lattice rank disagree")
    tolerance = _real(goal.allowed_numeric_tolerance)
    policy = contract.tolerance_policy
    _require(tolerance == 0 if policy.maximum == 0 else 0 < tolerance <= policy.maximum,
             "numeric tolerance violates declared policy")
    if candidate is None:
        _validate_historical_root_domain(goal)
        return
    _validate_artifact(candidate)
    _require((candidate.semantic_type, candidate.representation_class, candidate.exactness_class)
             == (contract.target.semantic_type, contract.target.representation_class, contract.target.exactness_class),
             "candidate violates target semantic/representation/exactness contract")
    _require(type(candidate.metadata) is tuple, "candidate metadata requires a tuple")
    metadata = _pairs(candidate.metadata)
    schema = contract.candidate_schema
    _require(metadata.keys() <= set(schema.metadata_fields), "unregistered candidate metadata")
    if schema.kind == "mapping" or (schema.kind == "chain-diagnosis" and type(candidate.value) is not bool):
        _mapping(candidate.value, set(schema.required_fields), set(schema.optional_fields))
    elif schema.kind in {"boolean", "chain-diagnosis"}:
        _require(type(candidate.value) is bool, "candidate must be boolean")
    elif schema.kind == "integer":
        _integer(candidate.value)
    elif schema.kind == "real":
        _real(candidate.value)
    elif schema.kind == "integer-sequence":
        for item in _sequence(candidate.value):
            _integer(item)


def validate_historical_goal_contract(goal: SolverVisibleGoal) -> VerificationResult:
    """Validate the complete registered problem statement without a candidate."""
    try:
        _require(type(goal) is SolverVisibleGoal and type(goal.family) is str,
                 "invalid goal/dispatch schema")
        contract = HISTORICAL_GOAL_CONTRACTS.get(goal.family)
        _require(contract is not None, "unsupported historical family")
        _require((goal.family, goal.required_verifier_class) in HISTORICAL_VERIFIER_DISPATCH,
                 "unsupported family/verifier-class pair")
        _validate_goal_contract(goal, None, contract)
        return VerificationResult(
            True,
            goal.required_verifier_class,
            "complete historical goal contract accepted",
            evidence=(("verifier_version", VERIFIER_VERSION),),
        )
    except Exception as exc:
        return VerificationResult(
            False,
            "UNSUPPORTED_TERMINAL_VERIFIER",
            f"rejected: {type(exc).__name__}: {exc}",
            evidence=(("verifier_version", VERIFIER_VERSION),),
        )


def _result(goal: SolverVisibleGoal, passed: bool, reason: str,
            residual: Fraction | None = None, evidence: tuple = ()) -> VerificationResult:
    measured = None
    if residual is not None:
        try:
            measured = float(residual)
        except OverflowError:
            measured = None
    return VerificationResult(bool(passed), goal.required_verifier_class, reason,
                              measured, (("verifier_version", VERIFIER_VERSION),
                              ("tolerance_metric", HISTORICAL_GOAL_CONTRACTS[goal.family].tolerance_policy.metric)) + evidence)


def _g1_roots(goal: SolverVisibleGoal) -> tuple[int, ...]:
    cumulative = tuple(_integer(v) for v in _sequence(_root(goal, "cumulative")))
    size = len(cumulative)
    _require(size > 0 and size & (size - 1) == 0, "Boolean lattice cardinality must be a positive power of two")
    _require(size <= _LIMITS.max_boolean_cardinality, "Boolean lattice exceeds resource limit")
    rank = _pairs(goal.constraints).get("lattice_rank")
    if rank is not None:
        _require(_integer(rank) == size.bit_length() - 1, "lattice rank disagrees with signal size")
    return cumulative


def _g1(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    cumulative = _g1_roots(goal)
    atomic = tuple(_integer(v) for v in _sequence(candidate.value, len(cumulative)))
    size = len(cumulative)
    reconstructed = tuple(sum(atomic[s] for s in range(size) if s & t == s) for t in range(size))
    return _result(goal, reconstructed == cumulative, "independent exact Boolean-zeta round trip")


def _g2(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    matrix = _matrix(_root(goal, "observation_matrix"))
    value = _mapping(candidate.value, {"unique", "nullity", "basis"})
    _require(type(value["unique"]) is bool, "unique must be boolean")
    nullity = matrix.cols - matrix.rank()
    reported = _integer(value["nullity"])
    basis = _sequence(value["basis"], nullity)
    vectors = [sp.Matrix([_rational(v) for v in _sequence(vector, matrix.cols)]) for vector in basis]
    full_basis = not vectors or sp.Matrix.hstack(*vectors).rank() == nullity
    annihilated = all(matrix * vector == sp.zeros(matrix.rows, 1) for vector in vectors)
    return _result(goal, reported == nullity and value["unique"] == (nullity == 0) and full_basis and annihilated,
                   "independent full nullspace basis, rank, and uniqueness", evidence=(("nullity", int(nullity)),))


def _g3_roots(goal: SolverVisibleGoal) -> tuple[sp.Matrix, sp.Matrix, sp.Matrix, sp.Matrix]:
    ds, dt, f0, f1 = (_matrix(_root(goal, key)) for key in ("source_boundary", "target_boundary", "vertex_map", "edge_map"))
    _require(f0.shape == (dt.rows, ds.rows) and f1.shape == (dt.cols, ds.cols), "incompatible chain-map dimensions")
    return ds, dt, f0, f1


def _g3(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    ds, dt, f0, f1 = _g3_roots(goal)
    residual = dt * f1 - f0 * ds
    expected = residual == sp.zeros(*residual.shape)
    metadata = _pairs(candidate.metadata)
    if type(candidate.value) is bool:
        observed = candidate.value
        proof = metadata
    else:
        value = _mapping(candidate.value, {"is_chain_map"}, {"residual", "residual_rows", "map_columns", "localized"})
        observed = value["is_chain_map"]
        _require(not (metadata.keys() & value.keys()), "duplicate chain evidence fields are forbidden")
        proof = {**metadata, **value}
    _require(type(observed) is bool, "chain-map verdict must be boolean")
    if "residual" in proof:
        _require(_matrix(proof["residual"]) == residual, "reported chain residual is incorrect")
    localize = _pairs(goal.constraints).get("localize_if_invalid", False)
    _require(type(localize) is bool, "localization constraint must be boolean")
    rows = tuple(i for i in range(residual.rows) if any(residual[i, j] != 0 for j in range(residual.cols)))
    cols = tuple(j for j in range(residual.cols) if any(residual[i, j] != 0 for i in range(residual.rows)))
    if localize and not expected:
        _require({"residual", "residual_rows", "map_columns"} <= proof.keys(), "invalid chain requires residual and complete fault localization")
    for name, required in (("residual_rows", rows), ("map_columns", cols)):
        if name in proof:
            supplied = tuple(_integer(v) for v in _sequence(proof[name]))
            _require(len(set(supplied)) == len(supplied) and set(supplied) == set(required), "incorrect fault localization")
    if "localized" in proof:
        _require(type(proof["localized"]) is bool and proof["localized"] == bool(rows and cols), "incorrect localized flag")
    return _result(goal, observed == expected, "independent chain commutation and requested localization")


def normalize_historical_barcode(
    value: Any,
) -> tuple[tuple[int, Fraction, Fraction], ...]:
    """Validate and canonicalize a G4 barcode under its frozen exact domain."""
    rows = []
    _require(len(_sequence(value)) <= _LIMITS.max_barcode_intervals, "barcode exceeds resource limit")
    for row in _sequence(value):
        degree, birth, death = _sequence(row, 3)
        degree, birth, death = _integer(degree), _rational(birth), _rational(death)
        _require(degree >= 0 and birth < death, "invalid finite half-open persistence interval")
        rows.append((degree, birth, death))
    return tuple(sorted(rows))


def _g4(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    a, b = (normalize_historical_barcode(_root(goal, key)) for key in ("barcode_a", "barcode_b"))
    grid = sorted({endpoint for barcode in (a, b) for _, birth, death in barcode for endpoint in (birth, death)})
    degrees = sorted({degree for barcode in (a, b) for degree, _, _ in barcode})
    def betti(barcode):
        return tuple(tuple(sum(d == degree and birth <= t < death for d, birth, death in barcode) for degree in degrees) for t in grid)
    ba, bb = betti(a), betti(b)
    ea = tuple(sum((-1) ** d * n for d, n in zip(degrees, row)) for row in ba)
    eb = tuple(sum((-1) ** d * n for d, n in zip(degrees, row)) for row in bb)
    expected = "EULER" if ea != eb else "BETTI" if ba != bb else "BARCODE" if a != b else "NONE"
    value = _mapping(candidate.value, {"level", "distinct"})
    _require(type(value["distinct"]) is bool and type(value["level"]) is str, "invalid separation schema")
    return _result(goal, value["level"] == expected and value["distinct"] == (expected != "NONE"),
                   "independent common-grid persistence information order", evidence=(("level", expected),))


def _graph(value: Any) -> nx.Graph:
    """The edge-only domain contains no isolated vertices (empty means order 0)."""
    graph = nx.Graph()
    _require(len(_sequence(value)) <= _LIMITS.max_graph_edges, "graph edges exceed resource limit")
    for edge in _sequence(value):
        a, b = _sequence(edge, 2)
        _require(all(type(v) in {str, int} for v in (a, b)) and a != b, "supported graph requires finite integer/string vertices and no loops")
        _require(not graph.has_edge(a, b), "duplicate undirected edge")
        graph.add_edge(a, b)
        _require(len(graph) <= _LIMITS.max_graph_vertices, "graph vertices exceed resource limit")
    return graph


def _bounded_graph_isomorphic(a: nx.Graph, b: nx.Graph) -> bool:
    """Exact adjacency-preserving bijection with a deterministic search budget."""
    if len(a) != len(b) or a.number_of_edges() != b.number_of_edges():
        return False
    signature = lambda graph, vertex: (graph.degree[vertex], tuple(sorted(graph.degree[n] for n in graph[vertex])))
    sa = {v: signature(a, v) for v in a}
    sb = {v: signature(b, v) for v in b}
    if sorted(sa.values()) != sorted(sb.values()):
        return False
    order_key = lambda v: (type(v).__name__, str(v))
    candidates = {v: tuple(sorted((w for w in b if sa[v] == sb[w]), key=order_key)) for v in a}
    order = sorted(a, key=lambda v: (len(candidates[v]), -a.degree[v], order_key(v)))
    assignment = {}
    used = set()
    attempts = 0
    def search(index):
        nonlocal attempts
        if index == len(order):
            return True
        v = order[index]
        for w in candidates[v]:
            attempts += 1
            _require(attempts <= _LIMITS.max_graph_search_nodes, "graph isomorphism search exceeds resource limit")
            if w in used or any(a.has_edge(v, old) != b.has_edge(w, mapped) for old, mapped in assignment.items()):
                continue
            assignment[v] = w
            used.add(w)
            if search(index + 1):
                return True
            used.remove(w)
            del assignment[v]
        return False
    return search(0)


def _g5(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    a, b = (_graph(_root(goal, key)) for key in ("graph_a", "graph_b"))
    value = _mapping(candidate.value, {"distinct"})
    _require(type(value["distinct"]) is bool, "distinct must be boolean")
    return _result(goal, value["distinct"] == (not _bounded_graph_isomorphic(a, b)),
                   "independent graph-isomorphism decision in the no-isolated-vertices edge-list domain")


def _round_ratio_nearest_ties_even(numerator: int, denominator: int) -> int:
    """Round a nonnegative exact ratio to an integer under IEEE ties-to-even."""
    quotient, remainder = divmod(numerator, denominator)
    comparison = 2 * remainder - denominator
    return quotient + int(comparison > 0 or (comparison == 0 and quotient & 1 == 1))


def _fraction_to_binary32(value: Fraction) -> float:
    """Correctly round an exact rational directly to IEEE-754 binary32.

    Converting through Python ``float`` would first round to binary64 and can
    therefore double-round values close to a binary32 midpoint.
    """
    value = _rational(value)
    if value == 0:
        bits = 0
    else:
        sign = int(value < 0)
        magnitude = abs(value)
        numerator, denominator = magnitude.numerator, magnitude.denominator

        # This initial difference is either floor(log2(x)) or one too large.
        exponent = numerator.bit_length() - denominator.bit_length()
        below_power = (
            numerator < denominator << exponent
            if exponent >= 0
            else numerator << -exponent < denominator
        )
        if below_power:
            exponent -= 1

        if exponent < -126:
            # All binary32 subnormals are integer multiples of 2**-149.
            significand = _round_ratio_nearest_ties_even(numerator << 149, denominator)
            if significand == 0:
                bits = sign << 31
            elif significand < 1 << 23:
                bits = (sign << 31) | significand
            else:
                # Rounding the largest subnormal interval upward gives the
                # smallest normal number, exponent field 1 and fraction 0.
                _require(significand == 1 << 23, "binary32 subnormal rounding overflow")
                bits = (sign << 31) | (1 << 23)
        else:
            shift = 23 - exponent
            scaled_numerator = numerator << shift if shift >= 0 else numerator
            scaled_denominator = denominator if shift >= 0 else denominator << -shift
            significand = _round_ratio_nearest_ties_even(scaled_numerator, scaled_denominator)
            if significand == 1 << 24:
                significand >>= 1
                exponent += 1
            if exponent > 127:
                # Round-to-nearest overflow has the signed infinity encoding.
                bits = (sign << 31) | (0xFF << 23)
            else:
                _require(1 << 23 <= significand < 1 << 24, "invalid binary32 normal significand")
                bits = (sign << 31) | ((exponent + 127) << 23) | (significand - (1 << 23))
    return struct.unpack("!f", bits.to_bytes(4, "big"))[0]


def _same_binary64(left: float, right: float) -> bool:
    """Compare finite/infinite float values including the sign of zero."""
    return struct.pack("!d", left) == struct.pack("!d", right)


def _g6_roots(goal: SolverVisibleGoal) -> sp.Matrix:
    matrix = _matrix(_root(goal, "exact_matrix"))
    numerical = _sequence(_root(goal, "numeric_matrix"), matrix.rows)
    dtype = _pairs(goal.inputs["numeric_matrix"].metadata)["dtype"]
    for row_index, row in enumerate(numerical):
        for column_index, item in enumerate(_sequence(row, matrix.cols)):
            _require(type(item) is float and isfinite(item), "numeric matrix entries must be finite exact Python floats")
            exact = _rational(matrix[row_index, column_index])
            reference = _fraction_to_binary32(exact) if dtype == "float32" else float(exact)
            _require(_same_binary64(item, reference), "numeric matrix is not the declared dtype view of exact_matrix")
    return matrix


def _g6(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    matrix = _g6_roots(goal)
    observed = _integer(candidate.value)
    return _result(goal, observed == matrix.rank(), "independent rational-matrix rank")


def _symbol_name(name: Any) -> None:
    _require(type(name) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}", name) is not None
             and not keyword.iskeyword(name)
             and name not in {"pi", "E", "I", "oo", "zoo", "nan", "inf", "Infinity", "True", "False", "None"},
             "invalid or reserved symbolic variable")


def _symbols(value: Any) -> tuple[sp.Symbol, ...]:
    result = []
    _require(len(_sequence(value)) <= _LIMITS.max_symbol_count, "too many symbolic variables")
    for item in _sequence(value):
        if type(item) is str:
            _symbol_name(item)
            symbol = sp.Symbol(item)
        else:
            _require(type(item) is sp.Symbol, "state entries must be exact named symbols")
            _symbol_name(item.name)
            symbol = item
        _require(str(symbol) not in {str(s) for s in result}, "duplicate symbolic variable name")
        result.append(symbol)
    return tuple(result)


def _expression_tree_budget(expression: sp.Expr, symbols: tuple[sp.Symbol, ...] | None = None) -> None:
    """One exact grammar for parsed strings and caller-supplied SymPy trees.

    Degree/term bounds account for rational numerator and denominator expansion;
    no simplification, differentiation or cancellation precedes this check.
    """
    count = 0
    def visit(node, depth):
        nonlocal count
        count += 1
        _require(count <= _LIMITS.max_expression_nodes and depth <= _LIMITS.max_expression_depth,
                 "symbolic tree exceeds node/depth resource limit")
        kind = type(node)
        if kind in _SYMPY_RATIONAL_TYPES:
            _rational(node)
            return (0, 0, 1, 1)
        if kind is sp.Symbol:
            _symbol_name(node.name)
            _require(symbols is None or node in symbols, "undeclared symbol or mismatched assumptions")
            return (1, 0, 1, 1)
        if kind is type(sp.pi):
            return (1, 0, 1, 1)
        _require(kind in {sp.Add, sp.Mul, sp.Pow}, "unsupported exact symbolic grammar")
        rows = [visit(arg, depth + 1) for arg in node.args]
        if kind is sp.Pow:
            _require(type(node.exp) in _SYMPY_INTEGER_TYPES, "symbolic exponent must be an exact integer")
            exponent = _integer(node.exp)
            _require(abs(exponent) <= _LIMITS.max_expression_exponent, "symbolic exponent exceeds resource limit")
            n, d, nt, dt = rows[0]
            if exponent < 0:
                _require(sp.cancel(node.base) != 0, "identically zero symbolic denominator")
                n, d, nt, dt = d, n, dt, nt
            power = abs(exponent)
            result = n * power, d * power, nt ** power, dt ** power
        else:
            n, d, nt, dt = rows[0]
            for rn, rd, rnt, rdt in rows[1:]:
                if kind is sp.Mul:
                    n, d, nt, dt = n + rn, d + rd, nt * rnt, dt * rdt
                else:
                    n, d, nt, dt = max(n + rd, rn + d), d + rd, nt * rdt + rnt * dt, dt * rdt
                _require(max(n, d) <= _LIMITS.max_expression_degree and max(nt, dt) <= _LIMITS.max_expanded_terms,
                         "symbolic expansion exceeds resource limit")
            result = n, d, nt, dt
        _require(max(result[:2]) <= _LIMITS.max_expression_degree and max(result[2:]) <= _LIMITS.max_expanded_terms,
                 "symbolic expansion exceeds resource limit")
        return result
    visit(expression, 0)


def _expression(value: Any, symbols: tuple[sp.Symbol, ...]) -> sp.Expr:
    names = {str(symbol): symbol for symbol in symbols}
    names["pi"] = sp.pi
    source = value.strip() if type(value) is str else ""
    def parse(node, depth=0):
        _require(depth <= _LIMITS.max_expression_depth, "symbolic AST exceeds depth resource limit")
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            # The AST stores floats rounded to binary64 (possibly infinity).
            # Parse the already-whitelisted numeric token instead so authored
            # decimal/exponent literals remain exact, finite rationals.
            literal = node.value
            if type(literal) is float:
                token = ast.get_source_segment(source, node).replace("_", "")
                exponent = re.search(r"[eE]([+-]?\d+)$", token)
                _require(exponent is None or abs(int(exponent.group(1))) <= 1200, "decimal exponent exceeds resource limit")
                literal = Fraction(token)
            return sp.Rational(_rational(literal))
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            item = parse(node.operand, depth + 1)
            return item if isinstance(node.op, ast.UAdd) else sp.Mul(-1, item, evaluate=False)
        if isinstance(node, ast.BinOp):
            lhs, rhs = parse(node.left, depth + 1), parse(node.right, depth + 1)
            if isinstance(node.op, ast.Add): return sp.Add(lhs, rhs, evaluate=False)
            if isinstance(node.op, ast.Sub): return sp.Add(lhs, sp.Mul(-1, rhs, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Mult): return sp.Mul(lhs, rhs, evaluate=False)
            if isinstance(node.op, ast.Div): return sp.Mul(lhs, sp.Pow(rhs, -1, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Pow):
                # Unary +/- integer exponents are accepted without evaluating a
                # general expression in the exponent position.
                if isinstance(node.right, ast.UnaryOp) and isinstance(node.right.operand, ast.Constant) and type(node.right.operand.value) is int:
                    rhs = sp.Integer(node.right.operand.value * (-1 if isinstance(node.right.op, ast.USub) else 1))
                _require(type(rhs) in _SYMPY_INTEGER_TYPES and abs(rhs) <= _LIMITS.max_expression_exponent, "unsupported exponent")
                return sp.Pow(lhs, rhs, evaluate=False)
        raise ValueError("unsupported or unsafe symbolic syntax")
    if type(value) is str:
        _require(len(value) <= _LIMITS.max_expression_chars, "symbolic input exceeds supported size")
        tree = ast.parse(source, mode="eval")
        _require(sum(1 for _ in ast.walk(tree)) <= _LIMITS.max_expression_nodes, "symbolic AST exceeds node resource limit")
        expression = parse(tree.body)
    elif isinstance(value, sp.Expr):
        expression = value
    else:
        expression = sp.Rational(_rational(value))
    _expression_tree_budget(expression, symbols)
    expression = sp.cancel(expression)
    # String parsing preserves authored syntax until the first budget check,
    # whereas caller-supplied SymPy expressions may already be canonicalized.
    # Recheck the shared canonical representation so neither path can exceed
    # the declared degree/exponent/term policy after cancellation.
    _expression_tree_budget(expression, symbols)
    _require(not expression.has(sp.oo, -sp.oo, sp.zoo, sp.nan) and expression.free_symbols <= set(symbols), "undefined expression or undeclared symbol")
    _require(expression.is_rational_function(*symbols) is True, "unsupported non-rational expression")
    return expression


def _g7_roots(goal: SolverVisibleGoal) -> tuple[tuple[sp.Symbol, ...], sp.Matrix, sp.Expr]:
    symbols = _symbols(_root(goal, "state"))
    _require(bool(symbols), "empty symbolic state")
    rows = _sequence(_root(goal, "generator"), len(symbols))
    # The registered family is a nilpotent *linear* generator.  Matrix entries
    # are constants (exact rationals and pi), never hidden state-dependent
    # nonlinear vector fields.
    generator = sp.Matrix([[_expression(v, ()) for v in _sequence(row, len(symbols))] for row in rows])
    bound = _pairs(goal.inputs["generator"].metadata)["nilpotency_bound"]
    _require(all(entry == 0 for entry in generator ** bound), "generator is not nilpotent at the declared bound")
    if bound > 1:
        _require(any(entry != 0 for entry in generator ** (bound - 1)), "nilpotency bound is not minimal")
    invariant = _expression(_root(goal, "candidate_invariant"), symbols)
    _require(invariant.is_polynomial(*symbols), "invariant must be polynomial in the supplied state")
    return symbols, generator, invariant


def _g7(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    _require(type(candidate.value) is bool, "invariant verdict must be boolean")
    symbols, generator, invariant = _g7_roots(goal)
    vector_field = generator * sp.Matrix(symbols)
    derivative = sp.cancel(sum(sp.diff(invariant, symbol) * component for symbol, component in zip(symbols, vector_field)))
    expected = derivative == 0
    return _result(goal, candidate.value == expected, "independent Lie derivative of supplied generator", evidence=(("lie_derivative", str(derivative)),))


def _g8_roots(goal: SolverVisibleGoal) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    _require(len(_sequence(_root(goal, "trajectory"))) <= _LIMITS.max_trajectory_rows, "trajectory exceeds resource limit")
    rows = tuple(tuple(_real(v) for v in _sequence(row, 4)) for row in _sequence(_root(goal, "trajectory")))
    _require(len(rows) >= 4 and all(b[0] > a[0] for a, b in zip(rows, rows[1:])), "relation data require at least four increasing finite times")
    _require(all(row[3] == rows[0][3] and row[3] != 0 for row in rows), "relation data require one constant nonzero c")
    products = tuple(area * c for _, area, _, c in rows)
    squares = tuple(perimeter * perimeter for _, _, perimeter, _ in rows)
    # Fit on a proper training prefix and reserve the final row as a holdout.
    x = tuple(value - products[0] for value in products[1:-1])
    y = tuple(value - squares[0] for value in squares[1:-1])
    denominator = sum(value * value for value in x)
    excitation = denominator / (len(x) * max(Fraction(1), *(abs(value) for value in products)) ** 2)
    policy = HISTORICAL_GOAL_CONTRACTS["G8"].tolerance_policy
    _require(excitation >= policy.conditioning_floor, "coefficient identification is degenerate or ill-conditioned")
    reference = -sum(a * b for a, b in zip(x, y)) / denominator
    scale = max(Fraction(1), *(abs(value) for value in y), *(abs(reference * value) for value in x))
    fit_residual = max(abs(b + reference * a) for a, b in zip(x, y)) / scale
    holdout_x = products[-1] - products[0]
    holdout_y = squares[-1] - squares[0]
    holdout_scale = max(Fraction(1), abs(holdout_y), abs(reference * holdout_x))
    holdout_residual = abs(holdout_y + reference * holdout_x) / holdout_scale
    return reference, fit_residual, holdout_residual, excitation


def _g8(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    coefficient = _real(candidate.value)
    reference, fit_residual, holdout_residual, excitation = _g8_roots(goal)
    policy = HISTORICAL_GOAL_CONTRACTS["G8"].tolerance_policy
    coefficient_error = abs(coefficient - reference)
    passed = (
        coefficient_error <= _real(goal.allowed_numeric_tolerance)
        and fit_residual <= policy.fit_tolerance
        and holdout_residual <= policy.fit_tolerance
    )
    return _result(goal, passed, "exact-rational training fit with a separately checked holdout", coefficient_error,
                   (("reference_coefficient", str(reference)), ("normalized_fit_residual", str(fit_residual)),
                    ("normalized_holdout_residual", str(holdout_residual)),
                    ("fit_tolerance", str(policy.fit_tolerance)), ("normalized_excitation", str(excitation)),
                    ("conditioning_floor", str(policy.conditioning_floor))))


Point = tuple[Fraction, Fraction]


def _cross(a: Point, b: Point, c: Point) -> Fraction:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _hull(points: tuple[Point, ...]) -> tuple[Point, ...]:
    ordered = sorted(set(points))
    halves = []
    for sequence in (ordered, list(reversed(ordered))):
        half = []
        for point in sequence:
            while len(half) >= 2 and _cross(half[-2], half[-1], point) <= 0:
                half.pop()
            half.append(point)
        halves.append(half[:-1])
    return tuple(halves[0] + halves[1])


def _cycle(points: tuple[Point, ...]) -> tuple[Point, ...]:
    first = min(range(len(points)), key=points.__getitem__)
    return points[first:] + points[:first]


def _polygon_vertices(value: Any) -> tuple[Point, ...]:
    """Parse the finite exact vertex-list domain shared by G9--G11."""
    _require(len(_sequence(value)) <= _LIMITS.max_polygon_vertices, "polygon exceeds resource limit")
    points = tuple(tuple(_real(v) for v in _sequence(point, 2)) for point in _sequence(value))
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    _require(len(points) >= 3 and len(set(points)) == len(points), "polygon requires distinct vertices and positive area")
    return points


def _simple_polygon(value: Any) -> tuple[Point, ...]:
    """Validate an exact simple polygon without imposing convexity."""
    points = _polygon_vertices(value)
    size = len(points)

    def on_segment(a: Point, b: Point, point: Point) -> bool:
        return (
            _cross(a, b, point) == 0
            and min(a[0], b[0]) <= point[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= point[1] <= max(a[1], b[1])
        )

    def intersects(a: Point, b: Point, c: Point, d: Point) -> bool:
        orientations = (_cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b))
        if ((orientations[0] > 0 > orientations[1] or orientations[0] < 0 < orientations[1])
                and (orientations[2] > 0 > orientations[3] or orientations[2] < 0 < orientations[3])):
            return True
        return any((turn == 0 and on_segment(start, end, point)) for turn, start, end, point in (
            (orientations[0], a, b, c), (orientations[1], a, b, d),
            (orientations[2], c, d, a), (orientations[3], c, d, b),
        ))

    # Adjacent collinear edges may continue along a boundary but may not
    # reverse and overlap. Nonadjacent edges may not touch or cross.
    for index, point in enumerate(points):
        before, after = points[index - 1], points[(index + 1) % size]
        if _cross(before, point, after) == 0:
            incoming = (point[0] - before[0], point[1] - before[1])
            outgoing = (after[0] - point[0], after[1] - point[1])
            _require(sum(a * b for a, b in zip(incoming, outgoing)) > 0, "overlapping polygon boundary")
    for first in range(size):
        a, b = points[first], points[(first + 1) % size]
        for second in range(first + 1, size):
            if second in {first, (first + 1) % size} or first == (second + 1) % size:
                continue
            c, d = points[second], points[(second + 1) % size]
            _require(not intersects(a, b, c, d), "self-intersecting polygon boundary")
    _require(_area(points) > 0, "polygon requires positive area")
    return points


def _polygon(value: Any) -> tuple[Point, ...]:
    points = _simple_polygon(value)
    hull = _hull(points)
    _require(len(hull) >= 3, "degenerate polygon")
    simplified = tuple(p for i, p in enumerate(points) if _cross(points[i - 1], p, points[(i + 1) % len(points)]) != 0)
    _require(len(simplified) == len(hull) and (_cycle(simplified) == _cycle(hull) or _cycle(tuple(reversed(simplified))) == _cycle(hull)),
             "supported domain is simple convex polygons in boundary order")
    # Collinear omitted vertices must actually lie on the corresponding boundary,
    # not make an out-and-back excursion along an edge.
    for i, point in enumerate(points):
        before, after = points[i - 1], points[(i + 1) % len(points)]
        if _cross(before, point, after) == 0:
            _require(all(min(a, b) <= v <= max(a, b) for a, v, b in zip(before, point, after)), "backtracking polygon edge")
    return hull


def _area(points: tuple[Point, ...]) -> Fraction:
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))) / 2


def _sqrt_interval(value: Fraction) -> tuple[Fraction, Fraction]:
    scale = 10 ** 80
    lower_integer = isqrt(value.numerator * scale * scale // value.denominator)
    lower = Fraction(lower_integer, scale)
    return lower, lower if lower * lower == value else Fraction(lower_integer + 1, scale)


@lru_cache(maxsize=1)
def _pi_interval() -> tuple[Fraction, Fraction]:
    # Machin's identity and the alternating-series remainder theorem. All
    # endpoints are exact rationals; no floating library constants are trusted.
    def atan_inverse(q):
        terms = 80
        partial = sum((Fraction((-1) ** k, (2 * k + 1) * q ** (2 * k + 1)) for k in range(terms)), Fraction())
        next_term = Fraction(1, (2 * terms + 1) * q ** (2 * terms + 1))
        return partial, partial + next_term
    a_low, a_high = atan_inverse(5)
    b_low, b_high = atan_inverse(239)
    return 16 * a_low - 4 * b_high, 16 * a_high - 4 * b_low


def _g9_reference(goal: SolverVisibleGoal) -> tuple[Fraction, Fraction]:
    polygon = _polygon(_root(goal, "body"))
    offset = _real(_root(goal, "offset"))
    _require(offset >= 0, "Steiner expansion requires nonnegative offset")
    bounds = [_sqrt_interval((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) for a, b in zip(polygon, polygon[1:] + polygon[:1])]
    pi_low, pi_high = _pi_interval()
    area = _area(polygon)
    lower = area + offset * sum(low for low, _ in bounds) + offset * offset * pi_low
    upper = area + offset * sum(high for _, high in bounds) + offset * offset * pi_high
    return lower, upper


def _g9(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    observed, tolerance = _real(candidate.value), _real(goal.allowed_numeric_tolerance)
    lower, upper = _g9_reference(goal)
    residual_bound = max(abs(observed - lower), abs(observed - upper))
    return _result(goal, residual_bound <= tolerance, "rational interval enclosure of convex Steiner area", residual_bound,
                   (("reference_lower", str(lower)), ("reference_upper", str(upper)), ("bound_method", "shoelace+integer-sqrt+Machin-alternating")))


@lru_cache(maxsize=64)
def _rotation_coefficients(order: int) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    """Enclose cos(2*pi/order), sin(2*pi/order) with rational Taylor bounds."""
    if order == 2:
        return (Fraction(-1), Fraction(-1)), (Fraction(), Fraction())
    if order == 4:
        return (Fraction(), Fraction()), (Fraction(1), Fraction(1))
    pi_low, pi_high = _pi_interval()
    # Round outward before Taylor evaluation to keep rational arithmetic small.
    scale = 10 ** 50
    low = Fraction(pi_low.numerator * scale // pi_low.denominator, scale) * 2 / order
    high = Fraction(pi_high.numerator * scale // pi_high.denominator + 1, scale) * 2 / order
    angle, angle_error = (low + high) / 2, (high - low) / 2
    cosine, sine = Fraction(), Fraction()
    cos_term, sin_term = Fraction(1), angle
    for k in range(40):
        cosine += cos_term
        sine += sin_term
        cos_term *= -angle * angle / ((2 * k + 1) * (2 * k + 2))
        sin_term *= -angle * angle / ((2 * k + 2) * (2 * k + 3))
    # Alternating tails decrease for these real angles in [0, pi]. Both
    # trigonometric functions are 1-Lipschitz, covering pi/angle uncertainty.
    cos_error, sin_error = abs(cos_term) + angle_error, abs(sin_term) + angle_error
    return (cosine - cos_error, cosine + cos_error), (sine - sin_error, sine + sin_error)


def _scaled_interval(interval: tuple[Fraction, Fraction], scalar: Fraction) -> tuple[Fraction, Fraction]:
    a, b = interval[0] * scalar, interval[1] * scalar
    return min(a, b), max(a, b)


def _interval_square(interval: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction]:
    lower, upper = interval
    minimum = Fraction() if lower <= 0 <= upper else min(lower * lower, upper * upper)
    return minimum, max(lower * lower, upper * upper)


def _rotation_order(polygon: tuple[Point, ...], tolerance: Fraction) -> tuple[int, Fraction]:
    n = len(polygon)
    center = tuple(sum(point[axis] for point in polygon) / n for axis in (0, 1))
    centered = tuple((x - center[0], y - center[1]) for x, y in polygon)
    scale_squared = max(x * x + y * y for x, y in centered)
    _require(scale_squared > 0, "rotation normalization requires positive Euclidean radius")
    tolerance_squared = tolerance * tolerance
    for order in range(n, 1, -1):
        if n % order:
            continue
        shift = n // order
        cosine, sine = _rotation_coefficients(order)
        lower_errors, upper_errors = [], []
        for i, (a, b) in enumerate(centered):
            target = centered[(i + shift) % n]
            ca, sb = _scaled_interval(cosine, a), _scaled_interval(sine, b)
            sa, cb = _scaled_interval(sine, a), _scaled_interval(cosine, b)
            dx = (ca[0] - sb[1] - target[0], ca[1] - sb[0] - target[0])
            dy = (sa[0] + cb[0] - target[1], sa[1] + cb[1] - target[1])
            dx2, dy2 = _interval_square(dx), _interval_square(dy)
            lower_errors.append((dx2[0] + dy2[0]) / scale_squared)
            upper_errors.append((dx2[1] + dy2[1]) / scale_squared)
        lower_squared, upper_squared = max(lower_errors), max(upper_errors)
        if upper_squared <= tolerance_squared:
            return order, _sqrt_interval(upper_squared)[1]
        _require(lower_squared > tolerance_squared, "rotational order is indeterminate at the interval/tolerance boundary")
    return 1, Fraction()


def _g10_reference(goal: SolverVisibleGoal) -> tuple[int, Fraction]:
    polygon = _polygon(_root(goal, "body"))
    return _rotation_order(polygon, _real(goal.allowed_numeric_tolerance))


def _g10(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    value = _mapping(candidate.value, {"order"})
    observed = _integer(value["order"])
    _require(observed > 0, "rotation order must be positive")
    expected, residual = _g10_reference(goal)
    return _result(goal, observed == expected, "independent enclosed finite-order polygon rotation", residual,
                   (("rotation_order", expected), ("numeric_contract", "normalized-Euclidean-residual-at-2*pi/order")))


def _g11_reference(goal: SolverVisibleGoal) -> Fraction:
    a, b = (_polygon(_root(goal, key)) for key in ("body_a", "body_b"))
    _require(len(a) * len(b) <= _LIMITS.max_polygon_product, "Minkowski product exceeds resource limit")
    sums = tuple((ax + bx, ay + by) for ax, ay in a for bx, by in b)
    area_a, area_b, area_sum = _area(a), _area(b), _area(_hull(sums))
    mixed = (area_sum - area_a - area_b) / 2
    defect = mixed * mixed / (area_a * area_b) - 1
    _require(defect >= 0, "invalid negative Minkowski defect")
    return defect


def _g11(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    value = _mapping(candidate.value, {"homothetic", "defect"})
    _require(type(value["homothetic"]) is bool, "homothety verdict must be boolean")
    observed_defect = _real(value["defect"])
    defect = _g11_reference(goal)
    tolerance = _real(goal.allowed_numeric_tolerance)
    expected = defect <= tolerance
    residual = abs(observed_defect - defect)
    return _result(goal, value["homothetic"] == expected and residual <= tolerance,
                   "independent exact-rational Minkowski area and bounded positive-homothety defect", residual,
                   (("exact_defect", str(defect)), ("numeric_contract", "dimensionless-Minkowski-defect")))


def _g12_difference(goal: SolverVisibleGoal) -> sp.Expr:
    symbols = _symbols(_pairs(goal.constraints).get("symbols", ()))
    lhs, rhs = (_expression(_root(goal, key), symbols) for key in ("lhs", "rhs"))
    return sp.cancel(lhs - rhs)


def _g12(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    _require(type(candidate.value) is bool, "identity verdict must be boolean")
    difference = _g12_difference(goal)
    return _result(goal, candidate.value == (difference == 0), "independent rational-function identity on its common defined domain")


def _validate_historical_root_domain(goal: SolverVisibleGoal) -> None:
    """Validate all candidate-independent mathematics before planner search."""
    if goal.family == "G1":
        _g1_roots(goal)
    elif goal.family == "G2":
        _matrix(_root(goal, "observation_matrix"))
    elif goal.family == "G3":
        _g3_roots(goal)
    elif goal.family == "G4":
        normalize_historical_barcode(_root(goal, "barcode_a"))
        normalize_historical_barcode(_root(goal, "barcode_b"))
    elif goal.family == "G5":
        _graph(_root(goal, "graph_a"))
        _graph(_root(goal, "graph_b"))
    elif goal.family == "G6":
        _g6_roots(goal)
    elif goal.family == "G7":
        _g7_roots(goal)
    elif goal.family == "G8":
        _g8_roots(goal)
    elif goal.family == "G9":
        # Convexity is an operator applicability condition: the frozen corpus
        # intentionally includes a well-formed nonconvex NOT_APPLICABLE case.
        _simple_polygon(_root(goal, "body"))
        _require(_real(_root(goal, "offset")) >= 0, "Steiner expansion requires nonnegative offset")
    elif goal.family == "G10":
        _g10_reference(goal)
    elif goal.family == "G11":
        _g11_reference(goal)
    elif goal.family == "G12":
        _g12_difference(goal)
    else:  # The structural dispatcher should already make this unreachable.
        raise ValueError("unsupported historical family")


_FUNCTIONS: dict[str, Callable[[SolverVisibleGoal, Artifact], VerificationResult]] = {
    "G1": _g1, "G2": _g2, "G3": _g3, "G4": _g4, "G5": _g5, "G6": _g6,
    "G7": _g7, "G8": _g8, "G9": _g9, "G10": _g10, "G11": _g11, "G12": _g12,
}
HISTORICAL_VERIFIER_DISPATCH = MappingProxyType({(family, contract[3]): _FUNCTIONS[family] for family, contract in _TARGETS.items()})


def verify_historical_goal(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    """Validate a historical candidate, returning a failed result on any bad input.

    The dispatch table is exact, with no family-only, type-only, or truthiness
    fallback. G2 requires a complete basis. Invalid G3 diagnoses must include
    ``residual``, ``residual_rows`` and ``map_columns`` when localization was
    requested; those fields may be in the candidate dictionary or metadata.
    """
    try:
        _require(type(goal) is SolverVisibleGoal and type(goal.family) is str and type(goal.required_verifier_class) is str,
                 "invalid goal/dispatch schema")
        verifier = HISTORICAL_VERIFIER_DISPATCH.get((goal.family, goal.required_verifier_class))
        _require(verifier is not None, "unsupported family/verifier-class pair")
        _validate_goal_contract(goal, candidate, HISTORICAL_GOAL_CONTRACTS[goal.family])
        return verifier(goal, candidate)
    except Exception as exc:
        return VerificationResult(False, "UNSUPPORTED_TERMINAL_VERIFIER",
                                  f"rejected: {type(exc).__name__}: {exc}",
                                  evidence=(("verifier_version", VERIFIER_VERSION),))
