from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import math
from typing import Any, Callable, Mapping

import networkx as nx
import numpy as np
import sympy as sp
from shapely.geometry import MultiPoint, Polygon

from .model import Applicability, Artifact, OperatorFailure, VerificationResult
from .verifiers import exact_value_verifier, finite_numeric, symbolic_equivalent


Bindings = tuple[tuple[str, Any], ...]
ExecuteFn = Callable[[Mapping[str, Artifact], Bindings], Artifact | OperatorFailure]
ApplicabilityFn = Callable[[Mapping[str, Artifact], Bindings], Applicability]
VerifyFn = Callable[[tuple[Artifact, ...], Artifact], VerificationResult]


@dataclass(frozen=True)
class OperatorSpec:
    operator_id: str
    input_types: tuple[str, ...]
    output_type: str
    representation_class: str
    exactness_class: str
    cost: int
    applicability: ApplicabilityFn
    execute: ExecuteFn
    verify: VerifyFn
    structural_signature: tuple[str, ...]


def _bindings(bindings: Bindings) -> dict[str, Any]:
    return dict(bindings)


def _find(inputs: Mapping[str, Artifact], *, key: str | None = None, semantic: str | None = None) -> Artifact:
    if key is not None and key in inputs:
        return inputs[key]
    if semantic is not None:
        for artifact in inputs.values():
            if artifact.semantic_type == semantic:
                return artifact
    raise KeyError(key or semantic or "artifact")


def _provenance(operator_id: str, inputs: Mapping[str, Artifact]) -> tuple[str, ...]:
    chain: list[str] = []
    for artifact in inputs.values():
        chain.extend(artifact.provenance)
        chain.append(artifact.artifact_id)
    chain.append(operator_id)
    return tuple(dict.fromkeys(chain))


def _out(
    operator_id: str,
    inputs: Mapping[str, Artifact],
    semantic_type: str,
    representation_class: str,
    value: Any,
    exactness_class: str,
    metadata: tuple[tuple[str, Any], ...] = (),
) -> Artifact:
    return Artifact(
        artifact_id=f"derived:{operator_id}:{abs(hash((operator_id, repr(value)))):x}",
        semantic_type=semantic_type,
        representation_class=representation_class,
        value=value,
        exactness_class=exactness_class,
        metadata=metadata,
        provenance=_provenance(operator_id, inputs),
    )


def _required(*semantic_types: str) -> ApplicabilityFn:
    required = Counter(semantic_types)

    def check(inputs: Mapping[str, Artifact], bindings: Bindings) -> Applicability:
        available = Counter(artifact.semantic_type for artifact in inputs.values())
        missing = [name for name, count in required.items() if available[name] < count]
        if missing:
            return Applicability("MISSING_PRECONDITION", f"missing semantic inputs: {','.join(sorted(missing))}")
        return Applicability("APPLICABLE")

    return check


def _always(inputs: Mapping[str, Artifact], bindings: Bindings) -> Applicability:
    return Applicability("APPLICABLE")


def _verify_internal(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    if not finite_numeric(output.value):
        return VerificationResult(False, "FINITE_OUTPUT", "non-finite output")
    return exact_value_verifier(output)


def _sympy_matrix(value: Any) -> sp.Matrix:
    return sp.Matrix([[sp.sympify(v) for v in row] for row in value])


def _zeta(values: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(values[s] for s in range(len(values)) if s & t == s) for t in range(len(values)))


def _mobius(values: tuple[int, ...]) -> tuple[int, ...]:
    n = int(round(math.log2(len(values))))
    if 2**n != len(values):
        raise ValueError("Boolean signal length must be a power of two")
    out = list(values)
    for bit in range(n):
        for mask in range(len(out)):
            if mask & (1 << bit):
                out[mask] -= out[mask ^ (1 << bit)]
    return tuple(out)


def _exec_exact_rank(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        matrix = _find(inputs, key="matrix") if "matrix" in inputs else next(
            a for a in inputs.values() if a.semantic_type in {"RATIONAL_MATRIX", "OBSERVATION_MATRIX"}
        )
        rank = int(_sympy_matrix(matrix.value).rank())
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "EXACT_MATRIX_RANK_Q")
    return _out("EXACT_MATRIX_RANK_Q", inputs, "MATRIX_RANK", "MATRIX", rank, "EXACT")


def _exec_nullspace(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        matrix = _find(inputs, key="matrix") if "matrix" in inputs else next(
            a for a in inputs.values() if a.semantic_type in {"RATIONAL_MATRIX", "OBSERVATION_MATRIX"}
        )
        m = _sympy_matrix(matrix.value)
        basis = tuple(tuple(sp.simplify(v) for v in vec) for vec in m.nullspace())
        value = {"nullity": len(basis), "basis": basis, "unique": len(basis) == 0}
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "EXACT_NULLSPACE_Q")
    return _out("EXACT_NULLSPACE_Q", inputs, "IDENTIFIABILITY_RESULT", "MATRIX", value, "EXACT")


def _exec_gf2_rank(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        matrix = _find(inputs, key="matrix").value if "matrix" in inputs else next(iter(inputs.values())).value
        rows = [[int(v) & 1 for v in row] for row in matrix]
        rank = 0
        col = 0
        while rows and rank < len(rows) and col < len(rows[0]):
            pivot = next((r for r in range(rank, len(rows)) if rows[r][col]), None)
            if pivot is None:
                col += 1
                continue
            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            for r in range(len(rows)):
                if r != rank and rows[r][col]:
                    rows[r] = [a ^ b for a, b in zip(rows[r], rows[rank])]
            rank += 1
            col += 1
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "GF2_RANK")
    return _out("GF2_RANK", inputs, "MATRIX_RANK", "MATRIX", rank, "EXACT")


def _exec_zeta(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        atomic = _find(inputs, key="atomic") if "atomic" in inputs else _find(inputs, semantic="BOOLEAN_ATOMIC_SIGNAL")
        value = _zeta(tuple(int(v) for v in atomic.value))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "ZETA_TRANSFORM_BOOLEAN")
    return _out("ZETA_TRANSFORM_BOOLEAN", inputs, "BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", value, "EXACT")


def _exec_mobius(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        cumulative = _find(inputs, key="cumulative") if "cumulative" in inputs else _find(inputs, semantic="BOOLEAN_ZETA_SIGNAL")
        value = _mobius(tuple(int(v) for v in cumulative.value))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "MOBIUS_INVERT_BOOLEAN")
    return _out("MOBIUS_INVERT_BOOLEAN", inputs, "BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", value, "EXACT")


def _verify_mobius(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    cumulative = next((a for a in inputs if a.semantic_type == "BOOLEAN_ZETA_SIGNAL"), None)
    if cumulative is None:
        return VerificationResult(False, "EXACT_ROUND_TRIP", "missing cumulative input")
    passed = _zeta(tuple(int(v) for v in output.value)) == tuple(cumulative.value)
    return VerificationResult(passed, "EXACT_ROUND_TRIP", "zeta round trip" if passed else "round trip mismatch")


def _chain_parts(inputs: Mapping[str, Artifact]) -> tuple[sp.Matrix, sp.Matrix, sp.Matrix, sp.Matrix]:
    ds = _sympy_matrix(_find(inputs, key="source_boundary").value)
    dt = _sympy_matrix(_find(inputs, key="target_boundary").value)
    f0 = _sympy_matrix(_find(inputs, key="vertex_map").value)
    f1 = _sympy_matrix(_find(inputs, key="edge_map").value)
    return ds, dt, f0, f1


def _exec_chain_residual(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        ds, dt, f0, f1 = _chain_parts(inputs)
        residual = dt * f1 - f0 * ds
        value = tuple(tuple(int(residual[r, c]) for c in range(residual.cols)) for r in range(residual.rows))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "CHAIN_RESIDUAL")
    return _out("CHAIN_RESIDUAL", inputs, "CHAIN_RESIDUAL_MATRIX", "CHAIN", value, "EXACT")


def _exec_chain_check(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    residual = _exec_chain_residual(inputs, bindings)
    if isinstance(residual, OperatorFailure):
        return residual
    passed = all(v == 0 for row in residual.value for v in row)
    return _out("CHAIN_MAP_CHECK", inputs, "CHAIN_DIAGNOSIS", "CHAIN", passed, "EXACT", (("residual", residual.value),))


def _exec_incidence_localize(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    residual = _exec_chain_residual(inputs, bindings)
    if isinstance(residual, OperatorFailure):
        return residual
    rows = tuple(i for i, row in enumerate(residual.value) if any(v != 0 for v in row))
    cols = tuple(j for j in range(len(residual.value[0]) if residual.value else 0) if any(row[j] != 0 for row in residual.value))
    value = {"residual_rows": rows, "map_columns": cols, "localized": bool(rows and cols)}
    return _out("INCIDENCE_CORRUPTION_LOCALIZE", inputs, "INCIDENCE_FAULT", "CHAIN", value, "EXACT")


def _exec_barcode_to_betti(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        barcode = _find(inputs, key="barcode") if "barcode" in inputs else _find(inputs, semantic="BARCODE")
        opts = _bindings(bindings)
        if "time_grid" in opts:
            grid = tuple(opts["time_grid"])
        else:
            max_death = max((int(d) for _, _, d in barcode.value), default=1)
            grid = tuple(range(max_death))
        values = []
        for t in grid:
            b0 = sum(int(deg) == 0 and b <= t < d for deg, b, d in barcode.value)
            b1 = sum(int(deg) == 1 and b <= t < d for deg, b, d in barcode.value)
            values.append((b0, b1))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "BARCODE_TO_BETTI")
    return _out("BARCODE_TO_BETTI", inputs, "BETTI_CURVE", "PERSISTENCE", tuple(values), "EXACT", (("time_grid", grid),))


def _exec_betti_to_euler(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        betti = _find(inputs, key="betti") if "betti" in inputs else _find(inputs, semantic="BETTI_CURVE")
        value = tuple(int(b0) - int(b1) for b0, b1 in betti.value)
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "BETTI_TO_EULER")
    return _out("BETTI_TO_EULER", inputs, "EULER_CURVE", "PERSISTENCE", value, "EXACT")


def _graph(value: Any) -> nx.Graph:
    graph = nx.Graph()
    graph.add_edges_from(value)
    return graph


def _graph_input(inputs: Mapping[str, Artifact]) -> Artifact:
    if "graph" in inputs:
        return inputs["graph"]
    return next(a for a in inputs.values() if a.semantic_type == "FINITE_GRAPH")


def _exec_graph_euler_betti(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        art = _graph_input(inputs)
        graph = _graph(art.value)
        n, m = graph.number_of_nodes(), graph.number_of_edges()
        b0 = nx.number_connected_components(graph) if n else 0
        value = (n - m, (b0, m - n + b0))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "GRAPH_EULER_BETTI")
    return _out("GRAPH_EULER_BETTI", inputs, "GRAPH_SIGNATURE", "GRAPH", value, "EXACT", (("level", "EULER_BETTI"),))


def _exec_graph_degree(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        graph = _graph(_graph_input(inputs).value)
        value = tuple(sorted(dict(graph.degree()).values()))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "GRAPH_DEGREE_SIGNATURE")
    return _out("GRAPH_DEGREE_SIGNATURE", inputs, "GRAPH_SIGNATURE", "GRAPH", value, "EXACT", (("level", "DEGREE"),))


def _exec_graph_laplacian(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        graph = _graph(_graph_input(inputs).value)
        matrix = nx.laplacian_matrix(graph).toarray().astype(float)
        value = tuple(float(v) for v in np.round(np.linalg.eigvalsh(matrix), 10))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "GRAPH_LAPLACIAN_SIGNATURE")
    return _out("GRAPH_LAPLACIAN_SIGNATURE", inputs, "GRAPH_SIGNATURE", "GRAPH", value, "NUMERICAL", (("level", "LAPLACIAN"),))


def _exec_graph_wl(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        graph = _graph(_graph_input(inputs).value)
        nx.set_node_attributes(graph, "node", "pct_label")
        value = nx.weisfeiler_lehman_graph_hash(graph, node_attr="pct_label", iterations=6)
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "GRAPH_WL_SIGNATURE")
    return _out("GRAPH_WL_SIGNATURE", inputs, "GRAPH_SIGNATURE", "GRAPH", value, "EXACT", (("level", "WL"),))


def _exec_counterexample(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    opts = _bindings(bindings)
    candidates = tuple(opts.get("candidates", ()))
    predicate = opts.get("predicate")
    found = None
    if callable(predicate):
        found = next((candidate for candidate in candidates if not predicate(candidate)), None)
    value = {"counterexample_found": found is not None, "counterexample": found}
    return _out("FINITE_COUNTEREXAMPLE_SEARCH", inputs, "FALSIFICATION_RESULT", "META", value, "EXACT")


def _exec_symbolic_simplify(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        art = next(iter(inputs.values()))
        value = sp.simplify(sp.sympify(art.value))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "SYMBOLIC_SIMPLIFY")
    return _out("SYMBOLIC_SIMPLIFY", inputs, "SYMBOLIC_EXPRESSION", "SYMBOLIC", value, "SYMBOLIC")


def _exec_symbolic_identity(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        lhs = _find(inputs, key="lhs")
        rhs = _find(inputs, key="rhs")
        check = symbolic_equivalent(lhs.value, rhs.value)
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "SYMBOLIC_IDENTITY_CHECK")
    return _out("SYMBOLIC_IDENTITY_CHECK", inputs, "IDENTITY_VERDICT", "SYMBOLIC", check.passed, "SYMBOLIC", (("reason", check.reason),))


def _exec_nilpotency(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        generator = _find(inputs, key="generator") if "generator" in inputs else _find(inputs, semantic="SYMBOLIC_GENERATOR")
        g = _sympy_matrix(generator.value)
        index = None
        power = sp.eye(g.rows)
        for k in range(1, g.rows + 2):
            power = power * g
            if power == sp.zeros(g.rows, g.cols):
                index = k
                break
        value = {"nilpotent": index is not None, "index": index}
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "NILPOTENCY_CHECK")
    return _out("NILPOTENCY_CHECK", inputs, "NILPOTENCY_RESULT", "SYMBOLIC", value, "SYMBOLIC")


def _exec_invariant_check(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        symbols = {name: sp.symbols(name) for name in ("A", "P", "c", "t")}
        A, P, c, t = (symbols[name] for name in ("A", "P", "c", "t"))
        generator = _sympy_matrix(_find(inputs, key="generator").value).subs({sp.Symbol("c"): c})
        state_values = _find(inputs, key="state").value
        state = sp.Matrix([sp.sympify(v, locals=symbols) for v in state_values])
        invariant = sp.sympify(_find(inputs, key="candidate_invariant").value, locals=symbols)
        flow = sp.eye(generator.rows)
        term = sp.eye(generator.rows)
        for k in range(1, generator.rows + 2):
            term = term * generator
            flow += t**k * term / sp.factorial(k)
            if term == sp.zeros(generator.rows, generator.cols):
                break
        moved = sp.simplify(flow * state)
        moved_value = sp.simplify(invariant.subs({A: moved[0], P: moved[1], c: moved[2]}, simultaneous=True))
        base_value = sp.simplify(invariant.subs({A: state[0], P: state[1], c: state[2]}, simultaneous=True))
        passed = sp.simplify(moved_value - base_value) == 0
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "POLYNOMIAL_INVARIANT_CHECK")
    return _out("POLYNOMIAL_INVARIANT_CHECK", inputs, "INVARIANT_VERDICT", "SYMBOLIC", bool(passed), "SYMBOLIC")


def _exec_linear_invariant(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        trajectory = _find(inputs, key="trajectory").value
        matrix = np.asarray([row[1:] for row in trajectory], dtype=float)
        centered = matrix - matrix[0]
        _, _, vh = np.linalg.svd(centered, full_matrices=True)
        coeffs = tuple(float(v) for v in vh[-1])
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "LINEAR_INVARIANT_DISCOVERY")
    return _out("LINEAR_INVARIANT_DISCOVERY", inputs, "NUMERIC_RELATION", "NUMERICAL", coeffs, "NUMERICAL")


def _exec_gaussian_rewrite(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        lhs = _find(inputs, key="lhs")
        value = sp.expand(sp.sympify(lhs.value))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "GAUSSIAN_EXPONENT_REWRITE")
    return _out("GAUSSIAN_EXPONENT_REWRITE", inputs, "SYMBOLIC_EXPRESSION", "SYMBOLIC", value, "SYMBOLIC")


def _exec_numeric_rank(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        art = _find(inputs, key="matrix") if "matrix" in inputs else next(a for a in inputs.values() if a.semantic_type == "FLOAT_MATRIX")
        value = int(np.linalg.matrix_rank(np.asarray(art.value, dtype=float)))
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "NUMERIC_MATRIX_RANK")
    return _out("NUMERIC_MATRIX_RANK", inputs, "MATRIX_RANK", "MATRIX", value, "NUMERICAL")


def _exec_conditioning(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        art = _find(inputs, key="matrix") if "matrix" in inputs else next(a for a in inputs.values() if a.semantic_type == "FLOAT_MATRIX")
        arr = np.asarray(art.value, dtype=float)
        cond = float(np.linalg.cond(arr))
        dtype = art.metadata_dict().get("dtype", "float64")
        threshold = 1e6 if dtype == "float32" else 1e12
        value = {"condition_number": cond, "requires_exact": (not math.isfinite(cond)) or cond > threshold, "threshold": threshold}
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "CONDITIONING_RISK_CHECK")
    return _out("CONDITIONING_RISK_CHECK", inputs, "CONDITIONING_RISK", "NUMERICAL", value, "NUMERICAL")


def _polygon_input(inputs: Mapping[str, Artifact], key: str = "body") -> Polygon:
    art = _find(inputs, key=key) if key in inputs else next(a for a in inputs.values() if a.representation_class == "GEOMETRY")
    return Polygon(art.value)


def _exec_support_sample(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        poly = _polygon_input(inputs)
        samples = int(_bindings(bindings).get("samples", 768))
        coords = np.asarray(list(poly.exterior.coords)[:-1], dtype=float)
        angles = np.arange(samples) * 2 * math.pi / samples
        values = np.max(np.cos(angles)[:, None] * coords[:, 0] + np.sin(angles)[:, None] * coords[:, 1], axis=1)
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "SUPPORT_FUNCTION_SAMPLE")
    return _out("SUPPORT_FUNCTION_SAMPLE", inputs, "SUPPORT_SAMPLES", "NUMERICAL", tuple(float(v) for v in values), "NUMERICAL", (("samples", samples),))


def _exec_support_spectrum(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        samples = _find(inputs, semantic="SUPPORT_SAMPLES")
        arr = np.asarray(samples.value, dtype=float)
        coeff = np.fft.rfft(arr) / len(arr)
        energy = np.abs(coeff) ** 2
        nonzero = energy[1:]
        threshold = max(float(nonzero.max()) * 1e-8, 1e-18) if len(nonzero) else 1e-18
        active = tuple(i for i in range(1, len(energy)) if float(energy[i]) > threshold)
        order = active[0] if active else None
        value = {"order": order, "active_harmonics": active, "energy": tuple(float(v) for v in energy)}
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "SUPPORT_SPECTRUM")
    return _out("SUPPORT_SPECTRUM", inputs, "ROTATIONAL_HARMONIC_ORDER", "NUMERICAL", value, "NUMERICAL")


def _exec_convexity(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        poly = _polygon_input(inputs)
        convex = poly.is_valid and not poly.is_empty and abs(poly.convex_hull.area - poly.area) <= 1e-10
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "CONVEXITY_CHECK")
    return _out("CONVEXITY_CHECK", inputs, "CONVEXITY_VERDICT", "GEOMETRY", bool(convex), "NUMERICAL")


def _steiner_app(inputs: Mapping[str, Artifact], bindings: Bindings) -> Applicability:
    try:
        poly = _polygon_input(inputs)
        if not poly.is_valid or poly.is_empty:
            return Applicability("INVALID_INPUT", "invalid polygon")
        if abs(poly.convex_hull.area - poly.area) > 1e-10:
            return Applicability("NOT_APPLICABLE", "Steiner control restricted to convex bodies")
        _find(inputs, key="offset")
    except Exception as exc:
        return Applicability("MISSING_PRECONDITION", str(exc))
    return Applicability("APPLICABLE")


def _exec_steiner(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    app = _steiner_app(inputs, bindings)
    if not app.applicable:
        verdict = "NOT_APPLICABLE" if app.verdict == "NOT_APPLICABLE" else "INVALID"
        return OperatorFailure(verdict, app.reason, "STEINER_OFFSET_PREDICT")
    poly = _polygon_input(inputs)
    s = float(_find(inputs, key="offset").value)
    value = float(poly.area + poly.length * s + math.pi * s * s)
    return _out("STEINER_OFFSET_PREDICT", inputs, "AREA", "GEOMETRY", value, "NUMERICAL")


def _area_normalized(poly: Polygon) -> Polygon:
    c = poly.centroid
    coords = [(x - c.x, y - c.y) for x, y in list(poly.exterior.coords)[:-1]]
    centered = Polygon(coords)
    scale = 1.0 / math.sqrt(centered.area)
    return Polygon([(x * scale, y * scale) for x, y in coords])


def _exec_mixed_area(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        a = _area_normalized(_polygon_input(inputs, "body_a"))
        b = _area_normalized(_polygon_input(inputs, "body_b"))
        sums = [(x1 + x2, y1 + y2) for x1, y1 in list(a.exterior.coords)[:-1] for x2, y2 in list(b.exterior.coords)[:-1]]
        minkowski = MultiPoint(sums).convex_hull
        mixed = (minkowski.area - a.area - b.area) / 2.0
        defect = mixed * mixed / (a.area * b.area) - 1.0
        value = {"defect": float(defect), "homothetic": abs(defect) <= 1e-8}
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "MIXED_AREA_DEFECT")
    return _out("MIXED_AREA_DEFECT", inputs, "HOMOTHETY_VERDICT", "GEOMETRY", value, "NUMERICAL")


def _exec_relation_fit(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        trajectory = _find(inputs, key="trajectory").value
        _, a0, p0, c0 = trajectory[0]
        dx, dy = [], []
        for _, area, perimeter, c in trajectory[1:]:
            dx.append(perimeter * perimeter - p0 * p0)
            dy.append(c * area - c0 * a0)
        x, y = np.asarray(dx, dtype=float), np.asarray(dy, dtype=float)
        denom = float(np.dot(y, y))
        if denom == 0:
            return OperatorFailure("NOT_APPLICABLE", "degenerate relation fit", "NUMERIC_RELATION_FIT")
        coeff = -float(np.dot(x, y) / denom)
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "NUMERIC_RELATION_FIT")
    return _out("NUMERIC_RELATION_FIT", inputs, "NUMERIC_RELATION", "NUMERICAL", coeff, "NUMERICAL", (("form", "P2_plus_k_cA"),))


def _exec_residual_verify(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    try:
        candidate = _find(inputs, key="candidate")
        reference = _find(inputs, key="reference")
        tolerance = float(_bindings(bindings).get("tolerance", 1e-8))
        residual = abs(float(candidate.value) - float(reference.value))
        value = {"passed": residual <= tolerance, "residual": residual, "tolerance": tolerance}
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), "NUMERIC_RESIDUAL_VERIFY")
    return _out("NUMERIC_RESIDUAL_VERIFY", inputs, "VERIFICATION_RESULT", "NUMERICAL", value, "NUMERICAL")


def _exec_separation(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    values = tuple(artifact.value for artifact in inputs.values())
    distinct = len({repr(value) for value in values}) > 1
    return _out("SEPARATION_ESCALATE", inputs, "REPRESENTATION_SEPARATION", "META", distinct, "EXACT")


def _exec_falsify(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    candidate = inputs.get("candidate") or next(iter(inputs.values()), None)
    if candidate is None:
        return OperatorFailure("INVALID", "missing candidate", "FALSIFY_CANDIDATE")
    counterexample = candidate.metadata_dict().get("counterexample")
    value = {"survived": counterexample is None, "counterexample": counterexample}
    return _out("FALSIFY_CANDIDATE", inputs, "FALSIFICATION_RESULT", "META", value, "EXACT")


def _exec_verify_candidate(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    candidate = inputs.get("candidate") or next(iter(inputs.values()), None)
    if candidate is None:
        return OperatorFailure("INVALID", "missing candidate", "VERIFY_CANDIDATE")
    value = {"passed": finite_numeric(candidate.value), "candidate_id": candidate.artifact_id}
    return _out("VERIFY_CANDIDATE", inputs, "VERIFICATION_RESULT", "META", value, candidate.exactness_class)


def _verify_bool(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    return VerificationResult(bool(output.value), "BOOLEAN_CLOSURE", "true" if bool(output.value) else "false")


def _verify_numeric_result(inputs: tuple[Artifact, ...], output: Artifact) -> VerificationResult:
    passed = finite_numeric(output.value)
    return VerificationResult(passed, "NUMERIC_FINITE", "finite" if passed else "non-finite")


def _spec(
    operator_id: str,
    input_types: tuple[str, ...],
    output_type: str,
    representation_class: str,
    exactness_class: str,
    execute: ExecuteFn,
    *,
    applicability: ApplicabilityFn | None = None,
    verify: VerifyFn = _verify_internal,
    cost: int = 1,
    signature: tuple[str, ...] = (),
) -> OperatorSpec:
    return OperatorSpec(
        operator_id=operator_id,
        input_types=input_types,
        output_type=output_type,
        representation_class=representation_class,
        exactness_class=exactness_class,
        cost=cost,
        applicability=applicability or _required(*input_types),
        execute=execute,
        verify=verify,
        structural_signature=signature or (representation_class, exactness_class, output_type),
    )


def build_operator_registry() -> dict[str, OperatorSpec]:
    specs = [
        _spec("EXACT_MATRIX_RANK_Q", ("RATIONAL_MATRIX",), "MATRIX_RANK", "MATRIX", "EXACT", _exec_exact_rank),
        _spec("EXACT_NULLSPACE_Q", ("OBSERVATION_MATRIX",), "IDENTIFIABILITY_RESULT", "MATRIX", "EXACT", _exec_nullspace),
        _spec("GF2_RANK", ("GF2_MATRIX",), "MATRIX_RANK", "MATRIX", "EXACT", _exec_gf2_rank),
        _spec("ZETA_TRANSFORM_BOOLEAN", ("BOOLEAN_ATOMIC_SIGNAL",), "BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", "EXACT", _exec_zeta),
        _spec("MOBIUS_INVERT_BOOLEAN", ("BOOLEAN_ZETA_SIGNAL",), "BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "EXACT", _exec_mobius, verify=_verify_mobius),
        _spec("CHAIN_RESIDUAL", ("BOUNDARY_OPERATOR", "BOUNDARY_OPERATOR", "CHAIN_MAP_DEGREE_0", "CHAIN_MAP_DEGREE_1"), "CHAIN_RESIDUAL_MATRIX", "CHAIN", "EXACT", _exec_chain_residual),
        _spec("CHAIN_MAP_CHECK", ("BOUNDARY_OPERATOR", "BOUNDARY_OPERATOR", "CHAIN_MAP_DEGREE_0", "CHAIN_MAP_DEGREE_1"), "CHAIN_DIAGNOSIS", "CHAIN", "EXACT", _exec_chain_check),
        _spec("INCIDENCE_CORRUPTION_LOCALIZE", ("BOUNDARY_OPERATOR", "BOUNDARY_OPERATOR", "CHAIN_MAP_DEGREE_0", "CHAIN_MAP_DEGREE_1"), "INCIDENCE_FAULT", "CHAIN", "EXACT", _exec_incidence_localize),
        _spec("BARCODE_TO_BETTI", ("BARCODE",), "BETTI_CURVE", "PERSISTENCE", "EXACT", _exec_barcode_to_betti),
        _spec("BETTI_TO_EULER", ("BETTI_CURVE",), "EULER_CURVE", "PERSISTENCE", "EXACT", _exec_betti_to_euler),
        _spec("GRAPH_EULER_BETTI", ("FINITE_GRAPH",), "GRAPH_SIGNATURE", "GRAPH", "EXACT", _exec_graph_euler_betti),
        _spec("GRAPH_DEGREE_SIGNATURE", ("FINITE_GRAPH",), "GRAPH_SIGNATURE", "GRAPH", "EXACT", _exec_graph_degree),
        _spec("GRAPH_LAPLACIAN_SIGNATURE", ("FINITE_GRAPH",), "GRAPH_SIGNATURE", "GRAPH", "NUMERICAL", _exec_graph_laplacian),
        _spec("GRAPH_WL_SIGNATURE", ("FINITE_GRAPH",), "GRAPH_SIGNATURE", "GRAPH", "EXACT", _exec_graph_wl),
        _spec("FINITE_COUNTEREXAMPLE_SEARCH", (), "FALSIFICATION_RESULT", "META", "EXACT", _exec_counterexample, applicability=_always),
        _spec("SYMBOLIC_SIMPLIFY", ("SYMBOLIC_EXPRESSION",), "SYMBOLIC_EXPRESSION", "SYMBOLIC", "SYMBOLIC", _exec_symbolic_simplify),
        _spec("SYMBOLIC_IDENTITY_CHECK", ("SYMBOLIC_EXPRESSION", "SYMBOLIC_EXPRESSION"), "IDENTITY_VERDICT", "SYMBOLIC", "SYMBOLIC", _exec_symbolic_identity),
        _spec("NILPOTENCY_CHECK", ("SYMBOLIC_GENERATOR",), "NILPOTENCY_RESULT", "SYMBOLIC", "SYMBOLIC", _exec_nilpotency),
        _spec("POLYNOMIAL_INVARIANT_CHECK", ("SYMBOLIC_GENERATOR", "SYMBOLIC_STATE", "SYMBOLIC_EXPRESSION"), "INVARIANT_VERDICT", "SYMBOLIC", "SYMBOLIC", _exec_invariant_check),
        _spec("LINEAR_INVARIANT_DISCOVERY", ("NUMERIC_TRAJECTORY",), "NUMERIC_RELATION", "NUMERICAL", "NUMERICAL", _exec_linear_invariant),
        _spec("GAUSSIAN_EXPONENT_REWRITE", ("SYMBOLIC_EXPRESSION",), "SYMBOLIC_EXPRESSION", "SYMBOLIC", "SYMBOLIC", _exec_gaussian_rewrite),
        _spec("NUMERIC_MATRIX_RANK", ("FLOAT_MATRIX",), "MATRIX_RANK", "MATRIX", "NUMERICAL", _exec_numeric_rank),
        _spec("CONDITIONING_RISK_CHECK", ("FLOAT_MATRIX",), "CONDITIONING_RISK", "NUMERICAL", "NUMERICAL", _exec_conditioning),
        _spec("SUPPORT_FUNCTION_SAMPLE", ("CONVEX_POLYGON",), "SUPPORT_SAMPLES", "NUMERICAL", "NUMERICAL", _exec_support_sample),
        _spec("SUPPORT_SPECTRUM", ("SUPPORT_SAMPLES",), "ROTATIONAL_HARMONIC_ORDER", "NUMERICAL", "NUMERICAL", _exec_support_spectrum),
        _spec("CONVEXITY_CHECK", ("POLYGON",), "CONVEXITY_VERDICT", "GEOMETRY", "NUMERICAL", _exec_convexity),
        _spec("STEINER_OFFSET_PREDICT", ("POLYGON", "SCALAR"), "AREA", "GEOMETRY", "NUMERICAL", _exec_steiner, applicability=_steiner_app, verify=_verify_numeric_result),
        _spec("MIXED_AREA_DEFECT", ("CONVEX_BODY", "CONVEX_BODY"), "HOMOTHETY_VERDICT", "GEOMETRY", "NUMERICAL", _exec_mixed_area, verify=_verify_numeric_result),
        _spec("NUMERIC_RELATION_FIT", ("NUMERIC_TRAJECTORY",), "NUMERIC_RELATION", "NUMERICAL", "NUMERICAL", _exec_relation_fit, verify=_verify_numeric_result),
        _spec("NUMERIC_RESIDUAL_VERIFY", ("SCALAR", "SCALAR"), "VERIFICATION_RESULT", "NUMERICAL", "NUMERICAL", _exec_residual_verify, applicability=_always, verify=_verify_numeric_result),
        _spec("SEPARATION_ESCALATE", (), "REPRESENTATION_SEPARATION", "META", "EXACT", _exec_separation, applicability=_always),
        _spec("FALSIFY_CANDIDATE", (), "FALSIFICATION_RESULT", "META", "EXACT", _exec_falsify, applicability=_always),
        _spec("VERIFY_CANDIDATE", (), "VERIFICATION_RESULT", "META", "EXACT", _exec_verify_candidate, applicability=_always, verify=_verify_bool),
    ]
    registry = {spec.operator_id: spec for spec in specs}
    if len(registry) != 33:
        raise AssertionError(f"expected 33 frozen operators, got {len(registry)}")
    return registry
