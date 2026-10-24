"""Deliverable 2 — Spatial Relation Transport Grammar & Closure / Time-Dispersion Analysis.

Constructs a certified spatial relation transport operator `Phi_w : R_d -> R_{d+1}` moving one
column outward (`p = -d -> -(d + 1)`) using the 6-case transport grammar proved in Lean
(`Rule30ProofClosure.spatial_transport_step_dichotomy`):
- `T_BLACK_LEFT`: `X_{t, -d} == 1 => X_{t, -(d+1)} = !X_{t+1, -d}`
- `T_BLACK_RIGHT`: `X_{t, -(d-1)} == 1 => X_{t, -(d+1)} = !X_{t+1, -d}`
- `T_WHITE_LEFT`: `X_{t, -d} == 0 => X_{t, -(d+1)} = X_{t+1, -d} XOR X_{t, -(d-1)}`
- `T_WHITE_RIGHT`: `X_{t, -(d-1)} == 0 => X_{t, -(d+1)} = X_{t+1, -d} XOR X_{t, -d}`
- `T_COMP_XOR1`: `X_{t, -d} XOR X_{t, -(d-1)} == 1 => X_{t, -(d+1)} = !X_{t+1, -d}`
- `T_IDEMP_XOR0`: `X_{t, -d} XOR X_{t, -(d-1)} == 0 => X_{t, -(d+1)} = X_{t+1, -d} XOR X_{t, -d}`
- `T_NON_CLOSED_CROSS_TERM`: neither single-column constant nor adjacent-column constant XOR holds,
  spawning a multi-time-step quadratic cross-term `y_{t1} * y_{t2}` (`t1 != t2`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.symbolic_constraints import ANFPolynomial


@dataclass(frozen=True)
class SpatialDepthRelationStep:
    """Symbolic relation certificate at spatial depth `-d` across one period window `s = 0 .. P - 1`."""

    depth_d: int
    transport_rules_applied: Tuple[str, ...]
    column_polynomials_str: Tuple[str, ...]
    adjacent_xor_constants: Tuple[Optional[int], ...]
    max_polynomial_degree: int
    distinct_white_vars_per_cell_max: int
    grammar_closed_at_depth: bool


@dataclass(frozen=True)
class SpatialTransportTrajectoryReport:
    """End-to-end spatial relation transport trace across depths `d = 1 .. max_depth` for a word `w`."""

    period_word: Tuple[int, ...]
    max_depth_evaluated: int
    max_closed_affine_depth: int
    first_non_closed_depth: Optional[int]
    obstruction_mechanism: str
    depth_certificates: Tuple[SpatialDepthRelationStep, ...]


def _format_anf(poly: ANFPolynomial) -> str:
    if not poly.monomials:
        return "0"
    terms: List[str] = []
    for m in sorted(poly.monomials, key=lambda s: (len(s), sorted(s))):
        if not m:
            terms.append("1")
        else:
            terms.append("*".join(sorted(m)))
    return " ^ ".join(terms)


def trace_spatial_relation_transport(
    word: Sequence[int],
    max_depth: int = 6,
) -> SpatialTransportTrajectoryReport:
    """Transport the symbolic relation certificate `R_d` outward from `d = 0` to `d = max_depth`
    and determine the exact depth where the finite relation grammar `{Const, AdjXor}` breaks.
    """
    w = tuple(int(b) for b in word)
    p = len(w)
    span = p + max_depth + 4
    c_seq = [w[s % p] for s in range(span + 2)]

    # Depth 0: X_{s, 0} = c_s
    cols: Dict[int, List[ANFPolynomial]] = {
        0: [ANFPolynomial.const(c_seq[s]) for s in range(span)]
    }
    # Depth 1: X_{s, -1} = c_{s+1} ^ (1 if c_s==1 else y_s)
    cols[1] = [
        ANFPolynomial.const(c_seq[s + 1])
        ^ (ANFPolynomial.const(1) if c_seq[s] == 1 else ANFPolynomial.var(f"y_{s}"))
        for s in range(span - 1)
    ]

    depth_certs: List[SpatialDepthRelationStep] = []
    # Record depth 1 certificate
    adj1: List[Optional[int]] = []
    rules1: List[str] = []
    for s in range(p):
        rules1.append("T_BLACK_RIGHT" if c_seq[s] == 1 else "T_WHITE_RIGHT")
        xor_10 = cols[1][s] ^ cols[0][s]
        if xor_10 == ANFPolynomial.zero():
            adj1.append(0)
        elif xor_10 == ANFPolynomial.one():
            adj1.append(1)
        else:
            adj1.append(None)

    depth_certs.append(
        SpatialDepthRelationStep(
            depth_d=1,
            transport_rules_applied=tuple(rules1),
            column_polynomials_str=tuple(_format_anf(cols[1][s]) for s in range(p)),
            adjacent_xor_constants=tuple(adj1),
            max_polynomial_degree=max(cols[1][s].degree for s in range(p)),
            distinct_white_vars_per_cell_max=max(len(cols[1][s].variables) for s in range(p)),
            grammar_closed_at_depth=True,
        )
    )

    max_closed_d = 1
    first_break_d: Optional[int] = None
    obstruction_reason = "Finite grammar {Const, AdjXor} remains closed through max_depth."

    for d in range(1, max_depth):
        next_col: List[ANFPolynomial] = []
        rules_d: List[str] = []
        limit = len(cols[d]) - 1
        for s in range(limit):
            left_op = cols[d][s]          # X_{s, -d}
            right_op = cols[d - 1][s]     # X_{s, -(d-1)}
            fut_op = cols[d][s + 1]       # X_{s+1, -d}
            xor_pair = left_op ^ right_op

            if left_op == ANFPolynomial.one():
                rule_used = "T_BLACK_LEFT"
                res = ~fut_op
            elif right_op == ANFPolynomial.one():
                rule_used = "T_BLACK_RIGHT"
                res = ~fut_op
            elif left_op == ANFPolynomial.zero():
                rule_used = "T_WHITE_LEFT"
                res = fut_op ^ right_op
            elif right_op == ANFPolynomial.zero():
                rule_used = "T_WHITE_RIGHT"
                res = fut_op ^ left_op
            elif xor_pair == ANFPolynomial.one():
                rule_used = "T_COMP_XOR1"
                res = ~fut_op
            elif xor_pair == ANFPolynomial.zero():
                rule_used = "T_IDEMP_XOR0"
                res = fut_op ^ left_op
            else:
                rule_used = "T_NON_CLOSED_CROSS_TERM"
                res = fut_op ^ (left_op | right_op)

            # Verify exact algebraic identity against full Rule 30 sideways step
            assert res == (fut_op ^ (left_op | right_op))
            next_col.append(res)
            if s < p:
                rules_d.append(rule_used)

        cols[d + 1] = next_col
        adj_next: List[Optional[int]] = []
        for s in range(p):
            xp = cols[d + 1][s] ^ cols[d][s]
            if xp == ANFPolynomial.zero():
                adj_next.append(0)
            elif xp == ANFPolynomial.one():
                adj_next.append(1)
            else:
                adj_next.append(None)

        max_deg = max(cols[d + 1][s].degree for s in range(p))
        max_vars = max(len(cols[d + 1][s].variables) for s in range(p))
        closed_here = all(r != "T_NON_CLOSED_CROSS_TERM" for r in rules_d) and (max_deg <= 1)

        if closed_here and first_break_d is None:
            max_closed_d = d + 1
        elif not closed_here and first_break_d is None:
            first_break_d = d + 1
            obstruction_reason = (
                f"At depth d={d + 1}, adjacent columns X_{{t, -{d}}} and X_{{t, -{d - 1}}} depend on "
                f"distinct time-shifted white-step variables (max {max_vars} variables per cell), "
                f"breaking AdjXor constancy and spawning degree-{max_deg} quadratic cross-terms."
            )

        depth_certs.append(
            SpatialDepthRelationStep(
                depth_d=d + 1,
                transport_rules_applied=tuple(rules_d),
                column_polynomials_str=tuple(_format_anf(cols[d + 1][s]) for s in range(p)),
                adjacent_xor_constants=tuple(adj_next),
                max_polynomial_degree=max_deg,
                distinct_white_vars_per_cell_max=max_vars,
                grammar_closed_at_depth=closed_here,
            )
        )

    return SpatialTransportTrajectoryReport(
        period_word=w,
        max_depth_evaluated=max_depth,
        max_closed_affine_depth=max_closed_d,
        first_non_closed_depth=first_break_d,
        obstruction_mechanism=obstruction_reason,
        depth_certificates=tuple(depth_certs),
    )
