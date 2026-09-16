from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

from .model import Artifact, GoalSpec, TargetSpec


SPLIT_COUNTS = {"CALIBRATION": 3, "VALIDATION": 1, "SEALED": 2}
FAMILIES = tuple(f"G{i}" for i in range(1, 13))


def _artifact(
    goal_id: str,
    name: str,
    semantic_type: str,
    representation_class: str,
    value: Any,
    exactness_class: str,
    **metadata: Any,
) -> Artifact:
    return Artifact(
        artifact_id=f"{goal_id}:{name}",
        semantic_type=semantic_type,
        representation_class=representation_class,
        value=value,
        exactness_class=exactness_class,
        metadata=tuple(sorted(metadata.items())),
    )


def _matrix(rows: list[list[Any]]) -> tuple[tuple[Any, ...], ...]:
    return tuple(tuple(row) for row in rows)


def _boolean_zeta(values: tuple[int, ...]) -> tuple[int, ...]:
    out = []
    for target in range(len(values)):
        out.append(sum(values[source] for source in range(len(values)) if source & target == source))
    return tuple(out)


def _regular_polygon(n: int, phase: float = 0.0) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            math.cos(phase + 2.0 * math.pi * k / n),
            math.sin(phase + 2.0 * math.pi * k / n),
        )
        for k in range(n)
    )


def _goal_g1(goal_id: str, index: int) -> GoalSpec:
    atomic = tuple(((j + 1) * (index + 2)) % 9 - 4 for j in range(16))
    cumulative = _boolean_zeta(atomic)
    inputs = {
        "cumulative": _artifact(goal_id, "cumulative", "BOOLEAN_ZETA_SIGNAL", "FINITE_LATTICE", cumulative, "EXACT", rank=4)
    }
    return GoalSpec(
        goal_id, "G1", inputs,
        TargetSpec("atomic", "BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "RECOVER", "EXACT"),
        (("lattice_rank", 4),), 0.0, "EXACT_EQUALITY", 64,
        atomic, ("MOBIUS_INVERT_BOOLEAN", "ZETA_TRANSFORM_BOOLEAN", "VERIFY_CANDIDATE"),
    )


def _goal_g2(goal_id: str, index: int) -> GoalSpec:
    dependent = index % 2 == 1
    rows = [[1, 0, 1], [0, 1, 1], [1, 1, 2 if dependent else 3]]
    matrix = _matrix([[Fraction(v) for v in row] for row in rows])
    expected_nullity = 1 if dependent else 0
    inputs = {"observation_matrix": _artifact(goal_id, "matrix", "OBSERVATION_MATRIX", "MATRIX", matrix, "EXACT", field="Q")}
    return GoalSpec(
        goal_id, "G2", inputs,
        TargetSpec("identifiability", "IDENTIFIABILITY_RESULT", "MATRIX", "ESTABLISH_UNIQUENESS", "EXACT"),
        (("require_unique", True),), 0.0, "EXACT_LINEAR_ALGEBRA", 80,
        {"unique": expected_nullity == 0, "nullity": expected_nullity},
        ("EXACT_MATRIX_RANK_Q", "EXACT_NULLSPACE_Q", "VERIFY_CANDIDATE"),
    )


def _goal_g3(goal_id: str, index: int) -> GoalSpec:
    ds = _matrix([[-1, 0, 1], [1, -1, 0], [0, 1, -1]])
    dt = tuple(tuple((-1 if r == c else 1 if r == (c + 1) % 6 else 0) for c in range(6)) for r in range(6))
    f0 = [[0] * 3 for _ in range(6)]
    for r, c in ((0, 0), (2, 1), (4, 2)):
        f0[r][c] = 1
    f1 = [[0] * 3 for _ in range(6)]
    for r, c in ((0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)):
        f1[r][c] = 1
    corrupted = index % 3 == 2
    if corrupted:
        f1[0][0] = -1
    inputs = {
        "source_boundary": _artifact(goal_id, "ds", "BOUNDARY_OPERATOR", "CHAIN", ds, "EXACT", role="source"),
        "target_boundary": _artifact(goal_id, "dt", "BOUNDARY_OPERATOR", "CHAIN", dt, "EXACT", role="target"),
        "vertex_map": _artifact(goal_id, "f0", "CHAIN_MAP_DEGREE_0", "CHAIN", _matrix(f0), "EXACT"),
        "edge_map": _artifact(goal_id, "f1", "CHAIN_MAP_DEGREE_1", "CHAIN", _matrix(f1), "EXACT"),
    }
    return GoalSpec(
        goal_id, "G3", inputs,
        TargetSpec("chain_diagnosis", "CHAIN_DIAGNOSIS", "CHAIN", "VERIFY_AND_LOCALIZE", "EXACT"),
        (("localize_if_invalid", True),), 0.0, "CHAIN_RESIDUAL", 96,
        {"is_chain_map": not corrupted, "fault_expected": corrupted},
        ("CHAIN_RESIDUAL", "CHAIN_MAP_CHECK", "INCIDENCE_CORRUPTION_LOCALIZE", "VERIFY_CANDIDATE"),
    )


def _goal_g4(goal_id: str, index: int) -> GoalSpec:
    shift = index % 2
    a = ((0, 0, 3), (1, 1 + shift, 3 + shift))
    b = ((0, 0, 3), (1, 2 + shift, 4 + shift))
    inputs = {
        "barcode_a": _artifact(goal_id, "a", "BARCODE", "PERSISTENCE", a, "EXACT"),
        "barcode_b": _artifact(goal_id, "b", "BARCODE", "PERSISTENCE", b, "EXACT"),
    }
    return GoalSpec(
        goal_id, "G4", inputs,
        TargetSpec("separation_level", "REPRESENTATION_SEPARATION", "PERSISTENCE", "FIND_FINEST_NEEDED", "EXACT"),
        (("levels", ("BARCODE", "BETTI", "EULER")),), 0.0, "EXACT_EQUALITY", 96,
        "BETTI_OR_BARCODE", ("BARCODE_TO_BETTI", "BETTI_TO_EULER", "SEPARATION_ESCALATE", "VERIFY_CANDIDATE"),
    )


def _goal_g5(goal_id: str, index: int) -> GoalSpec:
    if index % 2 == 0:
        graph_a = ((0, 1), (1, 2), (2, 3), (3, 0))
        graph_b = ((0, 1), (1, 2), (2, 3))
        expected = True
    else:
        graph_a = ((0, 1), (1, 2), (2, 0))
        graph_b = ((0, 1), (1, 2), (2, 0))
        expected = False
    inputs = {
        "graph_a": _artifact(goal_id, "ga", "FINITE_GRAPH", "GRAPH", graph_a, "EXACT"),
        "graph_b": _artifact(goal_id, "gb", "FINITE_GRAPH", "GRAPH", graph_b, "EXACT"),
    }
    return GoalSpec(
        goal_id, "G5", inputs,
        TargetSpec("distinguish", "GRAPH_DISTINGUISHABILITY", "GRAPH", "DISTINGUISH", "EXACT"),
        (("signature_bank", ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL")),), 0.0, "GRAPH_ISOMORPHISM_CONTROL", 128,
        expected, ("GRAPH_EULER_BETTI", "GRAPH_DEGREE_SIGNATURE", "GRAPH_LAPLACIAN_SIGNATURE", "GRAPH_WL_SIGNATURE", "SEPARATION_ESCALATE", "VERIFY_CANDIDATE"),
    )


def _goal_g6(goal_id: str, index: int) -> GoalSpec:
    n = 6 + (index % 4)
    exact = tuple(tuple(Fraction(1, r + c + 1) for c in range(n)) for r in range(n))
    numeric = tuple(tuple(float(v) for v in row) for row in exact)
    inputs = {
        "exact_matrix": _artifact(goal_id, "exact", "RATIONAL_MATRIX", "MATRIX", exact, "EXACT", field="Q"),
        "numeric_matrix": _artifact(goal_id, "numeric", "FLOAT_MATRIX", "MATRIX", numeric, "NUMERICAL", dtype="float32" if index % 2 else "float64"),
    }
    return GoalSpec(
        goal_id, "G6", inputs,
        TargetSpec("rank", "MATRIX_RANK", "MATRIX", "SAFE_RANK", "EXACT"),
        (("allow_exact_escalation", True),), 0.0, "EXACT_LINEAR_ALGEBRA", 96,
        n, ("NUMERIC_MATRIX_RANK", "CONDITIONING_RISK_CHECK", "EXACT_MATRIX_RANK_Q", "VERIFY_CANDIDATE"),
    )


def _goal_g7(goal_id: str, index: int) -> GoalSpec:
    scale = index + 1
    generator = ((0, 1, 0), (0, 0, f"2*pi*{scale}"), (0, 0, 0))
    state = (f"A{index}", f"P{index}", "1")
    invariant = "P**2 - 4*pi*c*A"
    inputs = {
        "generator": _artifact(goal_id, "generator", "SYMBOLIC_GENERATOR", "SYMBOLIC", generator, "SYMBOLIC", nilpotency_bound=3),
        "state": _artifact(goal_id, "state", "SYMBOLIC_STATE", "SYMBOLIC", state, "SYMBOLIC"),
        "candidate_invariant": _artifact(goal_id, "invariant", "SYMBOLIC_EXPRESSION", "SYMBOLIC", invariant, "SYMBOLIC"),
    }
    return GoalSpec(
        goal_id, "G7", inputs,
        TargetSpec("conserved", "INVARIANT_VERDICT", "SYMBOLIC", "VERIFY_CONSERVATION", "SYMBOLIC"),
        (("flow_parameter", "t"),), 0.0, "SYMBOLIC_IDENTITY", 96,
        True, ("NILPOTENCY_CHECK", "POLYNOMIAL_INVARIANT_CHECK", "SYMBOLIC_IDENTITY_CHECK", "VERIFY_CANDIDATE"),
    )


def _goal_g8(goal_id: str, index: int) -> GoalSpec:
    c = (index % 4) + 1
    a0 = 1.0 + 0.25 * index
    p0 = 2.5 + 0.1 * index
    ts = (0.0, 0.1, 0.25, 0.5, 0.9)
    trajectory = tuple((t, a0 + p0 * t + math.pi * c * t * t, p0 + 2 * math.pi * c * t, float(c)) for t in ts)
    inputs = {"trajectory": _artifact(goal_id, "trajectory", "NUMERIC_TRAJECTORY", "NUMERICAL", trajectory, "NUMERICAL", model="parallel_body_2d")}
    return GoalSpec(
        goal_id, "G8", inputs,
        TargetSpec("invariant_coefficient", "NUMERIC_RELATION", "NUMERICAL", "DISCOVER_AND_VERIFY", "NUMERICAL"),
        (("relation_form", "P2_plus_k_cA"),), 1e-8, "NUMERIC_THEN_SYMBOLIC", 128,
        -4.0 * math.pi, ("NUMERIC_RELATION_FIT", "NUMERIC_RESIDUAL_VERIFY", "SYMBOLIC_IDENTITY_CHECK", "VERIFY_CANDIDATE"),
    )


def _goal_g9(goal_id: str, index: int) -> GoalSpec:
    nonconvex = index % 3 == 2
    if nonconvex:
        polygon = ((0.0, 0.0), (2.0, 0.0), (1.0, 0.5), (2.0, 2.0), (0.0, 2.0))
    else:
        polygon = ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0))
    offset = 0.1 + 0.02 * index
    inputs = {
        "body": _artifact(goal_id, "body", "POLYGON", "GEOMETRY", polygon, "NUMERICAL"),
        "offset": _artifact(goal_id, "offset", "SCALAR", "NUMERICAL", offset, "NUMERICAL"),
    }
    expected = "NOT_APPLICABLE" if nonconvex else 4.0 + 8.0 * offset + math.pi * offset * offset
    return GoalSpec(
        goal_id, "G9", inputs,
        TargetSpec("offset_area", "AREA", "GEOMETRY", "PREDICT", "NUMERICAL"),
        (("requires_convexity", True),), 5e-5, "GEOMETRIC_NUMERICAL", 96,
        expected, ("CONVEXITY_CHECK", "STEINER_OFFSET_PREDICT", "NUMERIC_RESIDUAL_VERIFY", "VERIFY_CANDIDATE"),
    )


def _goal_g10(goal_id: str, index: int) -> GoalSpec:
    n = (3, 4, 5, 6, 8, 10)[index % 6]
    polygon = _regular_polygon(n, math.pi / (2 * n))
    inputs = {"body": _artifact(goal_id, "body", "CONVEX_POLYGON", "GEOMETRY", polygon, "NUMERICAL", rotational_order=n)}
    return GoalSpec(
        goal_id, "G10", inputs,
        TargetSpec("harmonic_order", "ROTATIONAL_HARMONIC_ORDER", "NUMERICAL", "INFER", "NUMERICAL"),
        (("samples", 768),), 1e-8, "SPECTRAL_NUMERICAL", 128,
        n, ("SUPPORT_FUNCTION_SAMPLE", "SUPPORT_SPECTRUM", "NUMERIC_RESIDUAL_VERIFY", "VERIFY_CANDIDATE"),
    )


def _goal_g11(goal_id: str, index: int) -> GoalSpec:
    same = index % 2 == 0
    a = _regular_polygon(4, math.pi / 4)
    b = _regular_polygon(4, math.pi / 4) if same else _regular_polygon(6)
    inputs = {
        "body_a": _artifact(goal_id, "a", "CONVEX_BODY", "GEOMETRY", a, "NUMERICAL"),
        "body_b": _artifact(goal_id, "b", "CONVEX_BODY", "GEOMETRY", b, "NUMERICAL"),
    }
    return GoalSpec(
        goal_id, "G11", inputs,
        TargetSpec("homothetic", "HOMOTHETY_VERDICT", "GEOMETRY", "DISCRIMINATE", "NUMERICAL"),
        (("area_normalize", True),), 1e-5, "GEOMETRIC_NUMERICAL", 96,
        same, ("MIXED_AREA_DEFECT", "NUMERIC_RESIDUAL_VERIFY", "VERIFY_CANDIDATE"),
    )


def _goal_g12(goal_id: str, index: int) -> GoalSpec:
    sigma = index + 1
    lhs = f"-(nx+ny-2*dot)/(2*{sigma}**2)"
    rhs = f"dot/{sigma}**2-nx/(2*{sigma}**2)-ny/(2*{sigma}**2)"
    inputs = {
        "lhs": _artifact(goal_id, "lhs", "SYMBOLIC_EXPRESSION", "SYMBOLIC", lhs, "SYMBOLIC"),
        "rhs": _artifact(goal_id, "rhs", "SYMBOLIC_EXPRESSION", "SYMBOLIC", rhs, "SYMBOLIC"),
    }
    return GoalSpec(
        goal_id, "G12", inputs,
        TargetSpec("equivalent", "IDENTITY_VERDICT", "SYMBOLIC", "PROVE_IDENTITY", "SYMBOLIC"),
        (("symbols", ("nx", "ny", "dot")),), 0.0, "SYMBOLIC_IDENTITY", 64,
        True, ("GAUSSIAN_EXPONENT_REWRITE", "SYMBOLIC_SIMPLIFY", "SYMBOLIC_IDENTITY_CHECK", "VERIFY_CANDIDATE"),
    )


_BUILDERS = {
    "G1": _goal_g1,
    "G2": _goal_g2,
    "G3": _goal_g3,
    "G4": _goal_g4,
    "G5": _goal_g5,
    "G6": _goal_g6,
    "G7": _goal_g7,
    "G8": _goal_g8,
    "G9": _goal_g9,
    "G10": _goal_g10,
    "G11": _goal_g11,
    "G12": _goal_g12,
}


def build_goal_corpus() -> dict[str, list[GoalSpec]]:
    """Build the deterministic calibration/validation/sealed mixed-domain corpus."""
    corpus: dict[str, list[GoalSpec]] = {split: [] for split in SPLIT_COUNTS}
    global_index = 0
    for split in ("CALIBRATION", "VALIDATION", "SEALED"):
        for family in FAMILIES:
            for local_index in range(SPLIT_COUNTS[split]):
                goal_id = f"{split.lower()}:{family.lower()}:{local_index:02d}"
                corpus[split].append(_BUILDERS[family](goal_id, global_index + local_index))
            global_index += SPLIT_COUNTS[split]
    return corpus


def goals_for(split: str, family: str | None = None) -> tuple[GoalSpec, ...]:
    corpus = build_goal_corpus()
    rows = corpus[split]
    if family is not None:
        rows = [goal for goal in rows if goal.family == family]
    return tuple(rows)
