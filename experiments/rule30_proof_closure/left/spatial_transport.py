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

from ..core.symbolic_constraints import ANFPolynomial, rule30_anf


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


@dataclass(frozen=True)
class SpatiotemporalPhaseRelation:
    """Shift-equivariant spatiotemporal polynomial at depth `d` and phase `phi = t mod P` in terms of
    relative temporal offsets `delta in {0, ..., d - 1}` (`u_delta = y_{t + delta}`).
    """

    depth_d: int
    phase_phi: int
    canonical_offset_anf: str
    active_temporal_offsets: Tuple[int, ...]
    leading_offset: Optional[int]
    leading_offset_is_purely_linear: bool
    polynomial_degree: int
    quadratic_offset_pairs: Tuple[Tuple[int, int], ...]


@dataclass(frozen=True)
class SpatiotemporalAlgebraReport:
    """Section 4 Spatiotemporal Relation Algebra analysis across depths `d = 1 .. max_depth`:
    1. Temporal-support closure & leading-offset linearity,
    2. Operator simplification & PSMSL screening reduction,
    3. Initial-boundary contradiction test against the verified 6-step onset signature
       `(1, 1, 0, s_k, 1, s_k)` (`x_{-k}(k+5) = x_{-k}(k+3)`).
    """

    period_word: Tuple[int, ...]
    max_depth_evaluated: int
    temporal_support_step_law_verified: bool
    leading_offset_purely_linear_all_depths: bool
    unscreened_causal_offset_sum: int
    active_spatiotemporal_offset_sum: int
    psmsl_and_operator_pruning_ratio: float
    onset_signature_unsat_at_transient_t: Dict[str, Optional[int]]
    phase_relations: Tuple[SpatiotemporalPhaseRelation, ...]


def analyze_spatiotemporal_relation_algebra(
    word: Sequence[int],
    max_depth: int = 6,
    transients_to_test: Sequence[int] = (1, 2, 3, 4),
) -> SpatiotemporalAlgebraReport:
    """Construct the canonical shift-equivariant spatiotemporal relation algebra
    `R_d = { sum_i a_i y_{t + delta_i} ^ sum_{i<j} b_{ij} y_{t + delta_i} y_{t + delta_j} ^ ... ^ c }`
    and execute the three Section 4 analyses:
    (1) Temporal-support closure, (2) Operator/PSMSL simplification, and (3) Onset boundary contradiction.
    """
    w = tuple(int(b) for b in word)
    p = len(w)
    span = p + max_depth + 10
    c_seq = [w[s % p] for s in range(span + 4)]

    # Build absolute symbolic columns X_{s, -d}(y)
    cols: Dict[int, List[ANFPolynomial]] = {
        0: [ANFPolynomial.const(c_seq[s]) for s in range(span)]
    }
    cols[1] = [
        ANFPolynomial.const(c_seq[s + 1])
        ^ (ANFPolynomial.const(1) if c_seq[s] == 1 else ANFPolynomial.var(f"y_{s}"))
        for s in range(span - 1)
    ]
    for d in range(1, max_depth):
        limit = len(cols[d]) - 1
        cols[d + 1] = [
            cols[d][s + 1] ^ (cols[d][s] | cols[d - 1][s]) for s in range(limit)
        ]

    # Analysis 1 & 2: Extract shift-equivariant relative-offset polynomials at each (d, phi)
    support_map: Dict[Tuple[int, int], set[int]] = {(0, phi): set() for phi in range(p)}
    phase_rels: List[SpatiotemporalPhaseRelation] = []
    step_law_ok = True
    leading_linear_ok = True
    unscreened_sum = 0
    active_sum = 0

    for d in range(1, max_depth + 1):
        for phi in range(p):
            poly_abs = cols[d][phi]
            # Convert absolute variables y_{phi + delta} -> relative offset delta = idx - phi
            rel_monomials = set()
            offsets: set[int] = set()
            quad_pairs: set[Tuple[int, int]] = set()
            for m in poly_abs.monomials:
                rel_m = frozenset(f"u_{int(v.split('_')[1]) - phi}" for v in m)
                rel_monomials.add(rel_m)
                deltas = sorted(int(v.split("_")[1]) - phi for v in m)
                for dl in deltas:
                    offsets.add(dl)
                if len(deltas) >= 2:
                    for i in range(len(deltas)):
                        for j in range(i + 1, len(deltas)):
                            quad_pairs.add((deltas[i], deltas[j]))

            rel_poly = ANFPolynomial(frozenset(rel_monomials))
            support_map[(d, phi)] = offsets
            unscreened_sum += d
            active_sum += len(offsets)

            # Verify Temporal-Support Step Law:
            # Delta(d, phi) <= (Delta(d-1, (phi+1)%P) + 1) U Delta(d-1, phi) U Delta(d-2, phi)
            if d >= 2:
                shifted_prev = {dl + 1 for dl in support_map[(d - 1, (phi + 1) % p)]}
                allowed = shifted_prev | support_map[(d - 1, phi)] | support_map[(d - 2, phi)]
                if not offsets.issubset(allowed):
                    step_law_ok = False

            # Verify Leading-Offset Linearity Theorem:
            # Whenever the apex center step c_{phi + d - 1} == 0, offset delta = d - 1 is present,
            # appears as a singleton linear term u_{d-1}, and has ZERO higher-degree cross-terms!
            lead_off = max(offsets) if offsets else None
            lead_lin = True
            if c_seq[phi + d - 1] == 0:
                target_u = f"u_{d - 1}"
                has_linear = frozenset([target_u]) in rel_poly.monomials
                has_nonlinear = any(
                    target_u in m and len(m) > 1 for m in rel_poly.monomials
                )
                lead_lin = has_linear and (not has_nonlinear) and (lead_off == d - 1)
                if not lead_lin:
                    leading_linear_ok = False
            elif lead_off is not None:
                target_u = f"u_{lead_off}"
                has_nonlinear = any(
                    target_u in m and len(m) > 1 for m in rel_poly.monomials
                )
                lead_lin = not has_nonlinear

            phase_rels.append(
                SpatiotemporalPhaseRelation(
                    depth_d=d,
                    phase_phi=phi,
                    canonical_offset_anf=_format_anf(rel_poly),
                    active_temporal_offsets=tuple(sorted(offsets)),
                    leading_offset=lead_off,
                    leading_offset_is_purely_linear=lead_lin,
                    polynomial_degree=rel_poly.degree,
                    quadratic_offset_pairs=tuple(sorted(quad_pairs)),
                )
            )

    # Analysis 3: Initial-boundary contradiction test against the verified 6-step onset signature
    # universal_column_onset_signature:
    # For depth k >= T, relative to row T at step s = (k - T) + m:
    # m=0 -> 1, m=1 -> 1, m=2 -> 0, m=4 -> 1, and x_{-k}(k+5) ^ x_{-k}(k+3) = 0!
    onset_unsat_by_t: Dict[str, Optional[int]] = {}
    for t_val in transients_to_test:
        # Collect onset constraints across depths k = t_val .. min(max_depth, t_val + 3)
        constraints: List[ANFPolynomial] = []
        all_y_vars: set[str] = set()
        unsat_depth: Optional[int] = None
        for k_depth in range(t_val, min(max_depth, t_val + 3) + 1):
            base_s = k_depth - t_val
            if base_s + 5 >= len(cols[k_depth]):
                break
            # Verified onset constraints from universal_column_onset_signature:
            # 1. cell k (-k) = 1 => X_{base_s + 0, -k} ^ 1 == 0
            # 2. cell (k+1) (-k) = 1 => X_{base_s + 1, -k} ^ 1 == 0
            # 3. cell (k+2) (-k) = 0 => X_{base_s + 2, -k} == 0
            # 4. cell (k+4) (-k) = 1 => X_{base_s + 4, -k} ^ 1 == 0
            # 5. cell (k+5) (-k) = cell (k+3) (-k) => X_{base_s + 5, -k} ^ X_{base_s + 3, -k} == 0
            c_list = [
                cols[k_depth][base_s + 0] ^ ANFPolynomial.one(),
                cols[k_depth][base_s + 1] ^ ANFPolynomial.one(),
                cols[k_depth][base_s + 2],
                cols[k_depth][base_s + 4] ^ ANFPolynomial.one(),
                cols[k_depth][base_s + 5] ^ cols[k_depth][base_s + 3],
            ]
            for cp in c_list:
                constraints.append(cp)
                all_y_vars.update(cp.variables)

            # Check whether the accumulated spatiotemporal onset constraints alone already have no root y
            y_sorted = sorted(all_y_vars)
            n_y = len(y_sorted)
            if any(cp == ANFPolynomial.one() for cp in constraints):
                unsat_depth = k_depth
                break
            if n_y <= 12:
                num_m = 1 << n_y
                all_ones = (1 << num_m) - 1
                v_mask = {
                    vn: sum(1 << mask for mask in range(num_m) if (mask >> bp) & 1)
                    for bp, vn in enumerate(y_sorted)
                }
                cov = 0
                for cp in constraints:
                    cm = 0
                    for m in cp.monomials:
                        mm = all_ones
                        for v in m:
                            mm &= v_mask[v]
                        cm ^= mm
                    cov |= cm
                if cov == all_ones:
                    unsat_depth = k_depth
                    break
        onset_unsat_by_t[f"T={t_val}"] = unsat_depth

    pruning_ratio = round(1.0 - (active_sum / max(1, unscreened_sum)), 4)
    return SpatiotemporalAlgebraReport(
        period_word=w,
        max_depth_evaluated=max_depth,
        temporal_support_step_law_verified=step_law_ok,
        leading_offset_purely_linear_all_depths=leading_linear_ok,
        unscreened_causal_offset_sum=unscreened_sum,
        active_spatiotemporal_offset_sum=active_sum,
        psmsl_and_operator_pruning_ratio=pruning_ratio,
        onset_signature_unsat_at_transient_t=onset_unsat_by_t,
        phase_relations=tuple(phase_rels),
    )


@dataclass(frozen=True)
class RightCoupledFluxVerificationReport:
    """Combines the arbitrary-depth characteristic-flux onset laws (`k >= T`, zero left-cone variables)
    with the right-half evolution `Y_s(r_1, ..., r_{max(0, T-2)})` from the finite-support single-seed
    right slice (`R_0(T) = 1`, `R_1(T) = T mod 2`, `cell(T, p) = 0` for `p > T`).
    """

    transients_tested: Tuple[int, ...]
    periods_tested: Tuple[int, ...]
    total_hypotheses_tested: int
    pure_left_onset_unsat_count: int
    law_l4_and_exact_d3_zero_cone_unsat_count: int
    right_coupled_flux_unsat_count: int
    white_run_cases_closed_by_right_correlation: Tuple[str, ...]
    max_free_right_variables_at_t6: int


def analyze_right_coupled_characteristic_flux(
    transients: Sequence[int] = (1, 2, 3, 4, 5, 6),
    periods: Sequence[int] = (2, 3),
    max_depth: int = 8,
) -> RightCoupledFluxVerificationReport:
    """Evaluate all mixed-word hypotheses across `transients` and `periods` at depths `k >= T`
    (where sideways characteristic rays reach the left wavefront `D_0..D_5` without touching row `T`
    on the left), both before and after substituting the right-half transition polynomials
    `y_s = Y_s(r_1, ..., r_{max(0, T-2)})` generated from the finite-support right boundary, as well
    as under the zero-cone local Law L4 + exact D_3 parity (`universal_column_onset_exact_6step` +
    `double_white_step_depth2_forcing`).
    """
    import itertools

    mixed_words = [
        tuple(w)
        for p_val in periods
        for w in itertools.product((0, 1), repeat=p_val)
        if (0 in w and 1 in w)
    ]

    total_tested = 0
    pure_left_unsat = 0
    law_l4_zero_cone_unsat = 0
    right_coupled_unsat = 0
    closed_by_right: List[str] = []

    for w in mixed_words:
        p = len(w)
        st_rep = analyze_spatiotemporal_relation_algebra(
            w, max_depth=max_depth, transients_to_test=transients
        )
        for t_val in transients:
            total_tested += 1
            left_only_k = st_rep.onset_signature_unsat_at_transient_t.get(f"T={t_val}")
            if left_only_k is not None:
                pure_left_unsat += 1
                law_l4_zero_cone_unsat += 1
                right_coupled_unsat += 1
                continue

            # Test zero-cone local Law L4 (c_s=0 & c_{s+1}=0 => y_s*(1 ^ y_{s+1}) = 0) + exact D_3(k+3) parity
            # using ONLY boundary variables y_s (zero left-cone variables l_i and zero right-cone variables r_j)
            horizon = 2 * max_depth + 4
            c_seq = [w[s % p] for s in range(horizon + 4)]
            y_vars = [ANFPolynomial.var(f"y_{s}") for s in range(horizon + 2)]
            cols_y: Dict[int, List[ANFPolynomial]] = {
                0: [ANFPolynomial.const(c_seq[s]) for s in range(horizon + 2)]
            }
            cols_y[1] = [
                ANFPolynomial.const(c_seq[s + 1])
                ^ (ANFPolynomial.const(1) if c_seq[s] == 1 else y_vars[s])
                for s in range(horizon + 1)
            ]
            for d in range(1, max_depth):
                limit = len(cols_y[d]) - 1
                cols_y[d + 1] = [
                    cols_y[d][s + 1] ^ (cols_y[d][s] | cols_y[d - 1][s]) for s in range(limit)
                ]
            l4_constraints: List[ANFPolynomial] = []
            l4_y_set: set[str] = set()
            for s in range(horizon):
                if c_seq[s] == 0 and c_seq[s + 1] == 0:
                    # Law L4: y_s == 1 => y_{s+1} == 1, i.e., y_s & (1 ^ y_{s+1}) == 0
                    cp_l4 = y_vars[s] & (ANFPolynomial.one() ^ y_vars[s + 1])
                    l4_constraints.append(cp_l4)
            for k_depth in range(t_val, max_depth + 1):
                base_s = k_depth - t_val
                if base_s + 5 >= len(cols_y[k_depth]):
                    break
                d3_target = ANFPolynomial.const(1 if (k_depth % 2 == 0) else 0)
                c_list_exact = [
                    cols_y[k_depth][base_s + 0] ^ ANFPolynomial.one(),
                    cols_y[k_depth][base_s + 1] ^ ANFPolynomial.one(),
                    cols_y[k_depth][base_s + 2],
                    cols_y[k_depth][base_s + 3] ^ d3_target,
                    cols_y[k_depth][base_s + 4] ^ ANFPolynomial.one(),
                    cols_y[k_depth][base_s + 5] ^ d3_target,
                ]
                for cp in c_list_exact:
                    l4_constraints.append(cp)
                    l4_y_set.update(cp.variables)
                active_l4 = [
                    cp for cp in l4_constraints if cp.variables.issubset(l4_y_set) and len(cp.variables) > 0
                ]
                if any(cp == ANFPolynomial.one() for cp in l4_constraints):
                    law_l4_zero_cone_unsat += 1
                    break
                y_sorted = sorted(l4_y_set)
                n_y = len(y_sorted)
                if n_y <= 14:
                    num_m_y = 1 << n_y
                    all_ones_y = (1 << num_m_y) - 1
                    v_mask_y = {
                        vn: sum(1 << mask for mask in range(num_m_y) if (mask >> bp) & 1)
                        for bp, vn in enumerate(y_sorted)
                    }
                    cov_y = 0
                    for cp in active_l4:
                        cm = 0
                        for m in cp.monomials:
                            mm = all_ones_y
                            for v in m:
                                mm &= v_mask_y[v]
                            cm ^= mm
                        cov_y |= cm
                    if cov_y == all_ones_y:
                        law_l4_zero_cone_unsat += 1
                        break

            # For any case where pure left-onset (unconstrained y_s) had a surviving assignment,
            # evolve the right-half polynomial system from the finite-support initial condition at row T
            # (R_0(T) = 1, R_1(T) = T % 2, cell(T, q) = 0 for q > T) and test compatibility with
            # the characteristic-flux onset equations!
            horizon = 2 * max_depth + 4
            c_seq = [w[s % p] for s in range(horizon + 4)]
            right_vars = [f"r_{j}" for j in range(1, max(1, t_val - 1))]
            cur_right: Dict[int, ANFPolynomial] = {}
            for j in range(1, t_val):
                if j == t_val - 1:
                    cur_right[j] = ANFPolynomial.const(0 if (t_val % 2 == 0) else 1)
                else:
                    cur_right[j] = ANFPolynomial.var(f"r_{j}")
            cur_right[t_val] = ANFPolynomial.one()

            y_polys: List[ANFPolynomial] = []
            for s in range(horizon + 2):
                y_polys.append(cur_right.get(1, ANFPolynomial.zero()))
                c_poly = ANFPolynomial.const(c_seq[s])
                extent = t_val + s + 1
                nxt_right: Dict[int, ANFPolynomial] = {}
                for col in range(1, extent + 1):
                    lp = cur_right.get(col - 1, ANFPolynomial.zero()) if col - 1 >= 1 else c_poly
                    cp = cur_right.get(col, ANFPolynomial.zero())
                    rp = cur_right.get(col + 1, ANFPolynomial.zero())
                    nxt_right[col] = rule30_anf(lp, cp, rp)
                cur_right = nxt_right

            # Reconstruct left columns X_{s, -d}(r) directly using y_s = y_polys[s]
            cols_r: Dict[int, List[ANFPolynomial]] = {
                0: [ANFPolynomial.const(c_seq[s]) for s in range(horizon + 2)]
            }
            cols_r[1] = [
                ANFPolynomial.const(c_seq[s + 1])
                ^ (ANFPolynomial.const(1) if c_seq[s] == 1 else y_polys[s])
                for s in range(horizon + 1)
            ]
            for d in range(1, max_depth):
                limit = len(cols_r[d]) - 1
                cols_r[d + 1] = [
                    cols_r[d][s + 1] ^ (cols_r[d][s] | cols_r[d - 1][s]) for s in range(limit)
                ]

            n_r = len(right_vars)
            num_m = 1 << n_r
            all_ones = (1 << num_m) - 1
            v_mask = {
                vn: sum(1 << mask for mask in range(num_m) if (mask >> bp) & 1)
                for bp, vn in enumerate(right_vars)
            }
            cov = 0
            coupled_ok = False
            for k_depth in range(t_val, max_depth + 1):
                base_s = k_depth - t_val
                if base_s + 5 >= len(cols_r[k_depth]):
                    break
                c_list = [
                    cols_r[k_depth][base_s + 0] ^ ANFPolynomial.one(),
                    cols_r[k_depth][base_s + 1] ^ ANFPolynomial.one(),
                    cols_r[k_depth][base_s + 2],
                    cols_r[k_depth][base_s + 4] ^ ANFPolynomial.one(),
                    cols_r[k_depth][base_s + 5] ^ cols_r[k_depth][base_s + 3],
                ]
                for cp in c_list:
                    cm = 0
                    for m in cp.monomials:
                        mm = all_ones
                        for v in m:
                            mm &= v_mask[v]
                        cm ^= mm
                    cov |= cm
                if cov == all_ones:
                    coupled_ok = True
                    closed_by_right.append(
                        f"T={t_val}, w={list(w)} -> refuted at k={k_depth} by right-half correlation (n_right_vars={n_r})"
                    )
                    break
            if coupled_ok:
                right_coupled_unsat += 1

    return RightCoupledFluxVerificationReport(
        transients_tested=tuple(transients),
        periods_tested=tuple(periods),
        total_hypotheses_tested=total_tested,
        pure_left_onset_unsat_count=pure_left_unsat,
        law_l4_and_exact_d3_zero_cone_unsat_count=law_l4_zero_cone_unsat,
        right_coupled_flux_unsat_count=right_coupled_unsat,
        white_run_cases_closed_by_right_correlation=tuple(closed_by_right),
        max_free_right_variables_at_t6=max(0, max(transients) - 2),
    )
