from __future__ import annotations

from fractions import Fraction
import math
import struct
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


_FROZEN_G10_TRIANGLE = (
    (float.fromhex("0x1.f89e910a9febep-1"), float.fromhex("0x1.5a7c46826cf64p-3")),
    (float.fromhex("-0x1.475374cc77ddcp-1"), float.fromhex("0x1.89b3d9960cbefp-1")),
    (float.fromhex("-0x1.6296387c501c8p-2"), float.fromhex("-0x1.e052eb36a7fc5p-1")),
)
_FROZEN_G10_SQUARE = (
    (float.fromhex("0x1.e7984403158a2p-1"), float.fromhex("0x1.38614a8b8c3afp-2")),
    (float.fromhex("-0x1.38614a8b8c3afp-2"), float.fromhex("0x1.e7984403158a2p-1")),
    (float.fromhex("-0x1.e7984403158a2p-1"), float.fromhex("-0x1.38614a8b8c3aep-2")),
    (float.fromhex("0x1.38614a8b8c3a5p-2"), float.fromhex("-0x1.e7984403158a4p-1")),
)
_FROZEN_G10_PENTAGON = (
    (float.fromhex("0x1.f28466d7864c9p-1"), float.fromhex("0x1.d2e5e13e74218p-3")),
    (float.fromhex("0x1.584f3ff892588p-4"), float.fromhex("0x1.fe3018c1fa9d3p-1")),
    (float.fromhex("-0x1.d7eaf61062feap-1"), float.fromhex("0x1.8d2d8bc7aeeaep-2")),
    (float.fromhex("-0x1.4eb32fbc0ea9fp-1"), float.fromhex("-0x1.837401cdae732p-1")),
    (float.fromhex("0x1.090fd6f5d9112p-1"), float.fromhex("-0x1.b60c5527c0a7bp-1")),
)
_FROZEN_G11_PENTAGON = (
    (float.fromhex("0x1.fbae0022edffep-1"), float.fromhex("0x1.097da017f903cp-3")),
    (float.fromhex("0x1.7707a918c71ccp-3"), float.fromhex("0x1.f757a52021e8bp-1")),
    (float.fromhex("-0x1.c1bc004daeb64p-1"), float.fromhex("0x1.e96b861aec7b0p-2")),
    (float.fromhex("-0x1.73b567b1f0ec5p-1"), float.fromhex("-0x1.601a6f55b0d1ap-1")),
    (float.fromhex("0x1.b802fb2cffb6ep-2"), float.fromhex("-0x1.ce5260dde5957p-1")),
)
_FROZEN_G11_PENTAGON_IMAGE = (
    (float.fromhex("0x1.9ea6600aea600p+2"), float.fromhex("-0x1.56845efc41177p+1")),
    (float.fromhex("0x1.1d4c9935ef8e4p+2"), float.fromhex("-0x1.15a4e32fab3a4p-1")),
    (float.fromhex("0x1.cdd4ff9ee59c4p+0"), float.fromhex("-0x1.ce1ccc2f2c332p+0")),
    (float.fromhex("0x1.17ae9f30c96c5p+1"), float.fromhex("-0x1.2e0842cac7418p+2")),
    (float.fromhex("0x1.44c0773f07f49p+2"), float.fromhex("-0x1.5079be4557bebp+2")),
)


def _goal_g1(goal_id: str, index: int) -> GoalSpec:
    atomic = tuple(
        (-1 if (j + index) % 2 else 1) * ((j + 1) * (index + 2) + index * index + 1)
        for j in range(16)
    )
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
    dependent = index % 3 == 1
    a, b = index + 1, index + 2
    p, q = index + 2, -(index + 3)
    rows = [[1, 0, a], [0, 1, b], [p, q, p * a + q * b + (0 if dependent else index + 1)]]
    matrix = _matrix([[Fraction(v) for v in row] for row in rows])
    expected_nullity = 1 if dependent else 0
    inputs = {"observation_matrix": _artifact(goal_id, "matrix", "OBSERVATION_MATRIX", "MATRIX", matrix, "EXACT", field="Q")}
    return GoalSpec(
        goal_id, "G2", inputs,
        TargetSpec("identifiability", "IDENTIFIABILITY_RESULT", "MATRIX", "ESTABLISH_UNIQUENESS", "EXACT"),
        (("require_unique", True),), 0.0, "EXACT_LINEAR_ALGEBRA", 80,
        {
            "unique": expected_nullity == 0,
            "nullity": expected_nullity,
            "basis": ((-a, -b, 1),) if dependent else (),
        },
        ("EXACT_MATRIX_RANK_Q", "EXACT_NULLSPACE_Q", "VERIFY_CANDIDATE"),
    )


def _goal_g3(goal_id: str, index: int) -> GoalSpec:
    scale = index + 1
    ds = _matrix([[scale * value for value in row] for row in [[-1, 0, 1], [1, -1, 0], [0, 1, -1]]])
    dt = tuple(tuple(scale * (-1 if r == c else 1 if r == (c + 1) % 6 else 0) for c in range(6)) for r in range(6))
    f0 = [[0] * 3 for _ in range(6)]
    for r, c in ((0, 0), (2, 1), (4, 2)):
        f0[r][c] = 1
    f1 = [[0] * 3 for _ in range(6)]
    for r, c in ((0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)):
        f1[r][c] = 1
    corrupted = index % 3 == 1
    if corrupted:
        f1[(2 * index) % 6][index % 3] += index + 1
    residual = tuple(
        tuple(
            sum(dt[r][k] * f1[k][c] for k in range(6))
            - sum(f0[r][k] * ds[k][c] for k in range(3))
            for c in range(3)
        )
        for r in range(6)
    )
    residual_rows = tuple(r for r, row in enumerate(residual) if any(value != 0 for value in row))
    map_columns = tuple(c for c in range(3) if any(residual[r][c] != 0 for r in range(6)))
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
        {
            "is_chain_map": not corrupted,
            "residual": residual,
            "residual_rows": residual_rows,
            "map_columns": map_columns,
            "localized": bool(residual_rows and map_columns),
        },
        ("CHAIN_RESIDUAL", "CHAIN_MAP_CHECK", "INCIDENCE_CORRUPTION_LOCALIZE", "VERIFY_CANDIDATE"),
    )


def _goal_g4(goal_id: str, index: int) -> GoalSpec:
    shift = 10 * index
    kind = ("EULER", "BETTI", "BARCODE", "NONE", "EULER", "BETTI")[index % 6]
    if kind == "EULER":
        a = ((0, shift, shift + 2 + index // 4),)
        b = ((0, shift, shift + 1),)
    elif kind == "BETTI":
        a = ((0, shift, shift + 2), (1, shift, shift + 2))
        b = ()
    elif kind == "BARCODE":
        a = ((0, shift, shift + 3), (0, shift + 1, shift + 2))
        b = ((0, shift, shift + 2), (0, shift + 1, shift + 3))
    else:
        a = ((0, shift, shift + 2), (1, shift + 1, shift + 3))
        b = tuple(reversed(a))
    inputs = {
        "barcode_a": _artifact(goal_id, "a", "BARCODE", "PERSISTENCE", a, "EXACT"),
        "barcode_b": _artifact(goal_id, "b", "BARCODE", "PERSISTENCE", b, "EXACT"),
    }
    return GoalSpec(
        goal_id, "G4", inputs,
        TargetSpec("separation_level", "REPRESENTATION_SEPARATION", "PERSISTENCE", "FIND_FINEST_NEEDED", "EXACT"),
        (("levels", ("BARCODE", "BETTI", "EULER")),), 0.0, "EXACT_EQUALITY", 96,
        {"level": kind, "distinct": kind != "NONE"},
        ("BARCODE_TO_BETTI", "BETTI_TO_EULER", "SEPARATION_ESCALATE", "VERIFY_CANDIDATE"),
    )


def _goal_g5(goal_id: str, index: int) -> GoalSpec:
    cases = (
        (((0, 1), (1, 2), (2, 3), (3, 0)), ((10, 11), (11, 12), (12, 13), (13, 10)), False),
        (((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)), ((0, 1), (1, 2), (2, 3), (3, 4)), True),
        (((0, 1), (1, 2), (2, 0)), ((7, 9), (9, 8), (8, 7)), False),
        (((0, 1), (0, 2), (0, 3)), ((4, 5), (5, 6), (6, 7)), True),
        (((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)), ((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)), True),
        (((0, 1), (1, 2), (2, 3), (3, 4), (4, 5)), ((15, 14), (14, 13), (13, 12), (12, 11), (11, 10)), False),
    )
    graph_a, graph_b, expected = cases[index % len(cases)]
    inputs = {
        "graph_a": _artifact(goal_id, "ga", "FINITE_GRAPH", "GRAPH", graph_a, "EXACT"),
        "graph_b": _artifact(goal_id, "gb", "FINITE_GRAPH", "GRAPH", graph_b, "EXACT"),
    }
    return GoalSpec(
        goal_id, "G5", inputs,
        TargetSpec("distinguish", "GRAPH_DISTINGUISHABILITY", "GRAPH", "DISTINGUISH", "EXACT"),
        (("signature_bank", ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL")),), 0.0, "GRAPH_ISOMORPHISM_CONTROL", 128,
        {"distinct": expected},
        ("GRAPH_EULER_BETTI", "GRAPH_DEGREE_SIGNATURE", "GRAPH_LAPLACIAN_SIGNATURE", "GRAPH_WL_SIGNATURE", "SEPARATION_ESCALATE", "VERIFY_CANDIDATE"),
    )


def _goal_g6(goal_id: str, index: int) -> GoalSpec:
    matrices = (
        ((1, 2), (3, 5)),
        ((1, 2, 3), (2, 4, 6)),
        ((1, 0, 2), (0, 1, 3), (2, 1, 0)),
        ((1, 2, 3), (0, 1, 1), (1, 3, 4)),
        ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1)),
        ((0, 0), (0, 0)),
    )
    exact = tuple(tuple(Fraction(value) for value in row) for row in matrices[index % len(matrices)])
    expected_rank = (2, 1, 3, 2, 3, 0)[index % 6]
    dtype = "float32" if index % 2 else "float64"
    def cast(value: Fraction) -> float:
        result = float(value)
        return struct.unpack("!f", struct.pack("!f", result))[0] if dtype == "float32" else result
    numeric = tuple(tuple(cast(v) for v in row) for row in exact)
    inputs = {
        "exact_matrix": _artifact(goal_id, "exact", "RATIONAL_MATRIX", "MATRIX", exact, "EXACT", field="Q"),
        "numeric_matrix": _artifact(goal_id, "numeric", "FLOAT_MATRIX", "MATRIX", numeric, "NUMERICAL", dtype=dtype),
    }
    return GoalSpec(
        goal_id, "G6", inputs,
        TargetSpec("rank", "MATRIX_RANK", "MATRIX", "SAFE_RANK", "EXACT"),
        (("allow_exact_escalation", True),), 0.0, "EXACT_LINEAR_ALGEBRA", 96,
        expected_rank,
        ("NUMERIC_MATRIX_RANK", "CONDITIONING_RISK_CHECK", "EXACT_MATRIX_RANK_Q", "VERIFY_CANDIDATE"),
    )


def _goal_g7(goal_id: str, index: int) -> GoalSpec:
    # E21 generator acts on [A, P, c] as A'=P, P'=2*pi*c, c'=0.
    # The polynomial P**2 - 4*pi*c*A is therefore exactly conserved.
    scale = index + 1
    generator = ((0, scale, 0), (0, 0, f"{2 * scale}*pi"), (0, 0, 0))
    state = ("A", "P", "c")
    conserved = index % 2 == 0
    invariant = "P**2 - 4*pi*c*A" if conserved else "P**2 - 4*pi*c*A + A"
    inputs = {
        "generator": _artifact(goal_id, "generator", "SYMBOLIC_GENERATOR", "SYMBOLIC", generator, "SYMBOLIC", nilpotency_bound=3),
        "state": _artifact(goal_id, "state", "SYMBOLIC_STATE", "SYMBOLIC", state, "SYMBOLIC"),
        "candidate_invariant": _artifact(goal_id, "invariant", "SYMBOLIC_EXPRESSION", "SYMBOLIC", invariant, "SYMBOLIC"),
    }
    return GoalSpec(
        goal_id, "G7", inputs,
        TargetSpec("conserved", "INVARIANT_VERDICT", "SYMBOLIC", "VERIFY_CONSERVATION", "SYMBOLIC"),
        (("flow_parameter", "t"),), 0.0, "SYMBOLIC_IDENTITY", 96,
        conserved,
        ("NILPOTENCY_CHECK", "POLYNOMIAL_INVARIANT_CHECK", "SYMBOLIC_IDENTITY_CHECK", "VERIFY_CANDIDATE"),
    )


def _goal_g8(goal_id: str, index: int) -> GoalSpec:
    c = Fraction(index + 1)
    coefficient = Fraction(-(index + 2), index + 1)
    constant = Fraction(100 + 11 * index)
    perimeter_values = tuple(Fraction(index + 2 + step) for step in range(5))
    trajectory = tuple(
        (
            Fraction(step, index + 1),
            (constant - perimeter * perimeter) / (coefficient * c),
            perimeter,
            c,
        )
        for step, perimeter in enumerate(perimeter_values)
    )
    inputs = {"trajectory": _artifact(goal_id, "trajectory", "NUMERIC_TRAJECTORY", "NUMERICAL", trajectory, "NUMERICAL", model="anchored_quadratic_relation_v1")}
    return GoalSpec(
        goal_id, "G8", inputs,
        TargetSpec("invariant_coefficient", "NUMERIC_RELATION", "NUMERICAL", "DISCOVER_AND_VERIFY", "NUMERICAL"),
        (("relation_form", "P2_plus_k_cA"),), 1e-8, "NUMERIC_THEN_SYMBOLIC", 128,
        coefficient,
        ("NUMERIC_RELATION_FIT", "NUMERIC_RESIDUAL_VERIFY", "SYMBOLIC_IDENTITY_CHECK", "VERIFY_CANDIDATE"),
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
    cases = (
        (_FROZEN_G10_TRIANGLE, 3),
        (((-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0)), 2),
        (_FROZEN_G10_SQUARE, 4),
        (((0.0, 0.0), (3.0, 0.0), (2.0, 2.0), (0.0, 1.0)), 1),
        (_FROZEN_G10_PENTAGON, 5),
        (((2.0, 0.0), (1.0, 1.0), (-1.0, 2.0), (-2.0, 0.0), (-1.0, -1.0), (1.0, -2.0)), 2),
    )
    polygon, n = cases[index % len(cases)]
    inputs = {"body": _artifact(goal_id, "body", "CONVEX_POLYGON", "GEOMETRY", polygon, "NUMERICAL")}
    return GoalSpec(
        goal_id, "G10", inputs,
        TargetSpec("harmonic_order", "ROTATIONAL_HARMONIC_ORDER", "NUMERICAL", "INFER", "NUMERICAL"),
        (("samples", 768),), 1e-8, "SPECTRAL_NUMERICAL", 128,
        {"order": n}, ("SUPPORT_FUNCTION_SAMPLE", "SUPPORT_SPECTRUM", "NUMERIC_RESIDUAL_VERIFY", "VERIFY_CANDIDATE"),
    )


def _goal_g11(goal_id: str, index: int) -> GoalSpec:
    cases = (
        (((0, 0), (2, 0), (2, 2), (0, 2)), ((3, 5), (9, 5), (9, 11), (3, 11)), True, 0.0),
        (((0, 0), (2, 0), (2, 2), (0, 2)), ((0, 0), (4, 0), (4, 2), (0, 2)), False, 0.125),
        (((0, 0), (2, 0), (0, 2)), ((5, 7), (9, 7), (5, 11)), True, 0.0),
        (((0, 0), (3, 0), (3, 2), (0, 2)), ((0, 0), (9, 0), (9, 2), (0, 2)), False, 1.0 / 3.0),
        (_FROZEN_G11_PENTAGON, _FROZEN_G11_PENTAGON_IMAGE, True, 0.0),
        (((0, 0), (4, 0), (4, 1), (0, 1)), ((0, 0), (1, 0), (1, 4), (0, 4)), False, 225.0 / 64.0),
    )
    a, b, same, defect = cases[index % len(cases)]
    inputs = {
        "body_a": _artifact(goal_id, "a", "CONVEX_BODY", "GEOMETRY", a, "NUMERICAL"),
        "body_b": _artifact(goal_id, "b", "CONVEX_BODY", "GEOMETRY", b, "NUMERICAL"),
    }
    return GoalSpec(
        goal_id, "G11", inputs,
        TargetSpec("homothetic", "HOMOTHETY_VERDICT", "GEOMETRY", "DISCRIMINATE", "NUMERICAL"),
        (("area_normalize", True),), 1e-5, "GEOMETRIC_NUMERICAL", 96,
        {"homothetic": same, "defect": defect},
        ("MIXED_AREA_DEFECT", "NUMERIC_RESIDUAL_VERIFY", "VERIFY_CANDIDATE"),
    )


def _goal_g12(goal_id: str, index: int) -> GoalSpec:
    sigma = index + 1
    lhs = f"-(nx+ny-2*dot)/(2*{sigma}**2)"
    equivalent = index % 2 == 0
    rhs = f"dot/{sigma}**2-nx/(2*{sigma}**2)-ny/(2*{sigma}**2"
    rhs += ")" if equivalent else f")+1/{sigma + 1}"
    inputs = {
        "lhs": _artifact(goal_id, "lhs", "SYMBOLIC_EXPRESSION", "SYMBOLIC", lhs, "SYMBOLIC"),
        "rhs": _artifact(goal_id, "rhs", "SYMBOLIC_EXPRESSION", "SYMBOLIC", rhs, "SYMBOLIC"),
    }
    return GoalSpec(
        goal_id, "G12", inputs,
        TargetSpec("equivalent", "IDENTITY_VERDICT", "SYMBOLIC", "PROVE_IDENTITY", "SYMBOLIC"),
        (("symbols", ("nx", "ny", "dot")),), 0.0, "SYMBOLIC_IDENTITY", 64,
        equivalent,
        ("GAUSSIAN_EXPONENT_REWRITE", "SYMBOLIC_SIMPLIFY", "SYMBOLIC_IDENTITY_CHECK", "VERIFY_CANDIDATE"),
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
