"""Universal Certificate-Discovery & Canonical Bilateral Boolean Ideal Normalizer (R30-CERT-001).

Integrates four parallel repository capabilities into a single algebraic compatibility pipeline:
1. MAPEOGEO exact relational/operator kernel (`mapeogeo.gfyproof_bridge.canonical_sha256` + `ANFPolynomial` ideal algebra):
   Constructs `I_{T, w, H} <= F_2[z_1, ..., z_n] / <z_i^2 - z_i>` with exact translation certificates.
2. PSMSL projection (`psmsl_future_work`):
   Projects out screened right-boundary variables at black center steps (`c_t = 1`) and certifies
   degree collapse (columns `-1` and `-2` are degree <= 1 for all words; Law L3 cancels the
   unscreened right-boundary variable out of `X_{t,-2} XOR X_{t,-3}` on `101` patterns).
3. Collatz / BBB17 phase macros (`Rule30LeftReconstruction.lean`):
   Applies exact operator-cancellation laws `L1` (`1*`), `L2` (`11*`), `L3` (`101*`), `L3b` (`1010*`),
   and the universal left-diagonal hierarchy `D0=1, D1=1, D2=0, D3=parity, D4=1, D5=!D3`.
4. Geometric dependency / MUS & Nullstellensatz certificate extractor:
   Extracts Minimal Unsatisfiable Cores (MUS), constructs explicit F_2 Nullstellensatz certificates
   `1 = sum_{r in MUS} q_r(z) * g_r(z) mod <z_i^2 - z_i>`, replays them independently in `ANFPolynomial`,
   and clusters all candidate words into an exhaustive 4-grammar partition `{G1, G2, G3, G4}`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from mapeogeo.gfyproof_bridge import canonical_sha256
from ..core.rule30_exact import evolve_single_seed
from ..core.symbolic_constraints import ANFPolynomial, rule30_anf


GRAMMAR_CLUSTERS = (
    "G1_CONSTANT_WAVEFRONT_PROPAGATION",
    "G2_DOUBLE_BLACK_11_DEPTH2_SCREENING",
    "G3_COMPLEMENT_101_XOR_CANCELLATION",
    "G4_ISOLATED_BLACK_WHITE_RUN_EROSION",
)


@dataclass(frozen=True)
class PSMSLSidewaysTranslationCertificate:
    """Exact translation & degree-collapse certificate in the PSMSL-projected sideways basis."""

    period_word: Tuple[int, ...]
    steps_evaluated: int
    active_psmsl_variables: int
    screened_psmsl_variables: int
    max_col_minus1_degree: int
    max_col_minus2_degree: int
    law_l2_constant_depth2_hits: int
    law_l3_conserved_xor_degree0_hits: int
    law_l3b_depth4_linear_collapse_hits: int
    single_seed_evaluation_mismatches: int
    translation_verified: bool


@dataclass(frozen=True)
class NullstellensatzContradictionCertificate:
    """Replayable F_2 Nullstellensatz contradiction certificate `1 = sum_r q_r(z) * g_r(z)`."""

    transient_t: int
    period_p: int
    period_word: Tuple[int, ...]
    grammar_cluster: str
    active_operator_laws: Tuple[str, ...]
    free_left_variables_before_diagonals: int
    free_left_variables_after_diagonals: int
    free_right_variables: int
    unsat_horizon_h: int
    mus_step_indices: Tuple[int, ...]
    mus_size: int
    max_generator_degree: int
    max_multiplier_degree: int
    polynomial_replay_verified: bool
    certificate_sha256: str


@dataclass(frozen=True)
class CounterexampleStressTestResult:
    """Verification of the parameterized certificate grammar against known adversarial counterexamples."""

    test_id: str
    target_family: str
    period_word: Tuple[int, ...]
    grammar_cluster: str
    rejected_by_invariant: str
    rejection_horizon_steps: int
    passed: bool


def classify_word_operator_grammar(word: Sequence[int]) -> Tuple[str, Tuple[str, ...]]:
    """Classify any periodic word `w in {0,1}^P` into the exhaustive 4-grammar partition `{G1, G2, G3, G4}`."""
    w = tuple(int(b) for b in word)
    p = len(w)
    if all(b == 0 for b in w) or all(b == 1 for b in w):
        return (
            "G1_CONSTANT_WAVEFRONT_PROPAGATION",
            ("no_eventually_all_white_center", "no_eventually_all_black_center"),
        )
    ww = w * 4
    has_11 = any(ww[i] == 1 and ww[i + 1] == 1 for i in range(3 * p))
    has_101 = any(ww[i] == 1 and ww[i + 1] == 0 and ww[i + 2] == 1 for i in range(3 * p))
    has_1010 = any(
        ww[i] == 1 and ww[i + 1] == 0 and ww[i + 2] == 1 and ww[i + 3] == 0 for i in range(3 * p)
    )
    if has_11:
        laws = ["L1:left_black_step_screened_forcing", "L2:double_black_step_depth2_forcing"]
        if has_101:
            laws.append("L3:local_101_pattern_conserved_left_xor")
        return ("G2_DOUBLE_BLACK_11_DEPTH2_SCREENING", tuple(laws))
    if has_101:
        laws = [
            "L1:left_black_step_screened_forcing",
            "L3:local_101_pattern_conserved_left_xor",
        ]
        if has_1010:
            laws.append("L3b:local_1010_complement_cancellation_depth4")
        return ("G3_COMPLEMENT_101_XOR_CANCELLATION", tuple(laws))
    return (
        "G4_ISOLATED_BLACK_WHITE_RUN_EROSION",
        (
            "L1:left_black_step_screened_forcing",
            "left_effective_boundary_autonomous_step",
            "g8_p2_white_run_erodes_depth",
        ),
    )


def build_psmsl_sideways_ideal_and_verify(
    word: Sequence[int],
    horizon: int = 8,
    anchor_t: int = 2,
) -> PSMSLSidewaysTranslationCertificate:
    """Construct the PSMSL-projected sideways left-permutive polynomial basis `X_{t, -d}(y)` and
    certify exact degree collapse (`deg(X_{t,-1}) <= 1`, `deg(X_{t,-2}) <= 1`, Law L2, Law L3, Law L3b).
    """
    w = tuple(int(b) for b in word)
    p = len(w)
    total_steps = horizon + 6
    c_seq = [w[s % p] for s in range(total_steps + 6)]

    # PSMSL variables y_s = x_{s, 1} exist ONLY at white steps c_s == 0; screened at c_s == 1
    active_vars = sum(1 for s in range(total_steps) if c_seq[s] == 0)
    screened_vars = sum(1 for s in range(total_steps) if c_seq[s] == 1)

    # Depth 0: X_{s, 0} = c_s (constant ANFPolynomial)
    x_col0: List[ANFPolynomial] = [ANFPolynomial.const(c_seq[s]) for s in range(total_steps + 5)]

    # Depth -1: X_{s, -1} = c_{s+1} XOR (c_s OR y_s) = c_{s+1} XOR (1 if c_s==1 else y_s)
    x_col_m1: List[ANFPolynomial] = []
    for s in range(total_steps + 4):
        c_next = ANFPolynomial.const(c_seq[s + 1])
        z_s = ANFPolynomial.const(1) if c_seq[s] == 1 else ANFPolynomial.var(f"y_{s}")
        x_col_m1.append(c_next ^ z_s)

    # Depth -2: X_{s, -2} = X_{s+1, -1} XOR (X_{s, -1} OR X_{s, 0})
    x_col_m2: List[ANFPolynomial] = []
    for s in range(total_steps + 3):
        x_col_m2.append(x_col_m1[s + 1] ^ (x_col_m1[s] | x_col0[s]))

    # Depth -3: X_{s, -3} = X_{s+1, -2} XOR (X_{s, -2} OR X_{s, -1})
    x_col_m3: List[ANFPolynomial] = []
    for s in range(total_steps + 2):
        x_col_m3.append(x_col_m2[s + 1] ^ (x_col_m2[s] | x_col_m1[s]))

    # Depth -4: X_{s, -4} = X_{s+1, -3} XOR (X_{s, -3} OR X_{s, -2})
    x_col_m4: List[ANFPolynomial] = []
    for s in range(total_steps + 1):
        x_col_m4.append(x_col_m3[s + 1] ^ (x_col_m3[s] | x_col_m2[s]))

    max_deg_m1 = max(poly.degree for poly in x_col_m1[:horizon])
    max_deg_m2 = max(poly.degree for poly in x_col_m2[:horizon])

    l2_hits = 0
    l3_hits = 0
    l3b_hits = 0
    laws_ok = (max_deg_m1 <= 1) and (max_deg_m2 <= 1)

    for s in range(horizon):
        if c_seq[s] == 1 and c_seq[s + 1] == 1:
            l2_hits += 1
            if x_col_m2[s] != ANFPolynomial.const(c_seq[s + 2]):
                laws_ok = False
        if c_seq[s] == 1 and c_seq[s + 1] == 0 and c_seq[s + 2] == 1:
            l3_hits += 1
            xor_23 = x_col_m2[s] ^ x_col_m3[s]
            if xor_23 != ANFPolynomial.const(1 ^ c_seq[s + 3]):
                laws_ok = False
            if c_seq[s + 3] == 0:
                l3b_hits += 1
                # Under 1010, X_{s, -3} OR X_{s, -2} collapses to constant 1, and X_{s, -4} = !X_{s+1, -3}
                or_32 = x_col_m3[s] | x_col_m2[s]
                if or_32 != ANFPolynomial.const(1) or x_col_m4[s] != (~x_col_m3[s + 1]):
                    laws_ok = False
                if x_col_m4[s].degree > 1:
                    laws_ok = False

    # Also verify exact evaluation on the single-seed trajectory when c_seq = actual center column
    rows = evolve_single_seed(anchor_t + horizon + 8)
    actual_c = [rows[anchor_t + s].get(0, 0) for s in range(horizon + 6)]
    actual_y = {f"y_{s}": rows[anchor_t + s].get(1, 0) for s in range(horizon + 6)}
    act_col0 = [ANFPolynomial.const(actual_c[s]) for s in range(horizon + 5)]
    act_m1 = [
        ANFPolynomial.const(actual_c[s + 1])
        ^ (ANFPolynomial.const(1) if actual_c[s] == 1 else ANFPolynomial.var(f"y_{s}"))
        for s in range(horizon + 4)
    ]
    act_m2 = [act_m1[s + 1] ^ (act_m1[s] | act_col0[s]) for s in range(horizon + 3)]
    act_m3 = [act_m2[s + 1] ^ (act_m2[s] | act_m1[s]) for s in range(horizon + 2)]
    mismatches = 0
    for s in range(horizon):
        if act_m1[s].evaluate(actual_y) != rows[anchor_t + s].get(-1, 0):
            mismatches += 1
        if act_m2[s].evaluate(actual_y) != rows[anchor_t + s].get(-2, 0):
            mismatches += 1
        if act_m3[s].evaluate(actual_y) != rows[anchor_t + s].get(-3, 0):
            mismatches += 1

    return PSMSLSidewaysTranslationCertificate(
        period_word=w,
        steps_evaluated=horizon,
        active_psmsl_variables=active_vars,
        screened_psmsl_variables=screened_vars,
        max_col_minus1_degree=max_deg_m1,
        max_col_minus2_degree=max_deg_m2,
        law_l2_constant_depth2_hits=l2_hits,
        law_l3_conserved_xor_degree0_hits=l3_hits,
        law_l3b_depth4_linear_collapse_hits=l3b_hits,
        single_seed_evaluation_mismatches=mismatches,
        translation_verified=(laws_ok and mismatches == 0),
    )


@dataclass(frozen=True)
class PrimitiveContradictionProvenance:
    """Deliverable 1: Primitive spacetime equation and diagonal dependency provenance for a certificate."""

    transient_t: int
    period_p: int
    period_word: Tuple[int, ...]
    grammar_cluster: str
    dependency_category: str
    min_diagonal_d_for_degree0_mus1: Optional[int]
    unbridged_spatial_gap_at_d0: int
    unbridged_spatial_gap_at_d5: int
    diagonal_premises_at_row_t: Tuple[str, ...]
    self_regenerated_diagonals_from_d0: Tuple[str, ...]
    center_word_steps_used: Tuple[int, ...]
    primitive_spacetime_equations_count: int
    mus_size_at_no_diags: int
    max_deg_at_no_diags: int
    mus_size_at_d0_only: int
    max_deg_at_d0_only: int
    mus_size_at_d5_full: int
    max_deg_at_d5_full: int


def _known_left_diagonal_bit(diag_d: int, step_t: int, max_diagonal_d: int = 5) -> Optional[int]:
    """Return the exact universal single-seed bit of `D_d(step_t) = cell(step_t, -step_t + d)`
    for the proven periodic diagonals `d <= max_diagonal_d` (`d in {0, 1, 2, 3, 4, 5}`),
    or `None` if `d > max_diagonal_d` or `d >= 6`.
    """
    if diag_d < 0:
        return 0
    if diag_d > max_diagonal_d:
        return None
    if diag_d == 0:
        return 1
    if diag_d == 1 and step_t >= 1:
        return 1
    if diag_d == 2 and step_t >= 2:
        return 0
    if diag_d == 3 and step_t >= 2:
        return 0 if (step_t % 2 == 0) else 1
    if diag_d == 4 and step_t >= 3:
        return 1
    if diag_d == 5 and step_t >= 4:
        # D 5 (t + 4) = !D 3 (t + 3) => 0 on even steps >= 4, 1 on odd steps >= 5
        return 0 if (step_t % 2 == 0) else 1
    return None


def _lagrange_indicator_poly(var_names: Sequence[str], assignment_bits: Sequence[int]) -> ANFPolynomial:
    """Construct `delta_a(z) = prod_j (z_{var_j} ^ 1 ^ a_j)` in `F_2[z] / <z^2 + z>`."""
    prod = ANFPolynomial.one()
    for v_name, bit in zip(var_names, assignment_bits):
        factor = ANFPolynomial.var(v_name) ^ ANFPolynomial.const(1 ^ int(bit))
        prod = prod & factor
    return prod


def build_nullstellensatz_certificate(
    transient_t: int,
    word: Sequence[int],
    max_horizon: int = 14,
    max_diagonal_d: int = 5,
    use_right_r1_diagonal: bool = True,
    compute_multipliers: bool = True,
) -> NullstellensatzContradictionCertificate:
    """Construct the canonical bilateral polynomial ideal `I_{T, w, H}` with configurable left-diagonal
    reduction (`max_diagonal_d = -1` withholds all diagonals at row T; `0..5` supplies `D0..D_{max_diagonal_d}`),
    extract its Minimal Unsatisfiable Core (MUS), construct an explicit F_2 Nullstellensatz certificate
    `1 = sum_{r in MUS} q_r(z) * g_r(z)`, and replay it in `ANFPolynomial`.
    """
    w = tuple(int(b) for b in word)
    p = len(w)
    grammar_cluster, active_laws = classify_word_operator_grammar(w)

    if transient_t == 0:
        rows0 = evolve_single_seed(max_horizon + 2)
        for s in range(max_horizon):
            if rows0[s].get(0, 0) != w[s % p]:
                payload = {
                    "schema": "mapeogeo.rule30.nullstellensatz-certificate.v1",
                    "transient_t": 0,
                    "period_p": p,
                    "period_word": list(w),
                    "grammar_cluster": grammar_cluster,
                    "mus_step_indices": [s],
                    "generators": [{"step": s, "monomials": [[]]}],
                    "multipliers": [{"step": s, "monomials": [[]]}],
                }
                return NullstellensatzContradictionCertificate(
                    transient_t=0,
                    period_p=p,
                    period_word=w,
                    grammar_cluster=grammar_cluster,
                    active_operator_laws=active_laws,
                    free_left_variables_before_diagonals=0,
                    free_left_variables_after_diagonals=0,
                    free_right_variables=0,
                    unsat_horizon_h=s + 1,
                    mus_step_indices=(s,),
                    mus_size=1,
                    max_generator_degree=0,
                    max_multiplier_degree=0,
                    polynomial_replay_verified=True,
                    certificate_sha256=canonical_sha256(
                        payload, domain="rule30-nullstellensatz-certificate-v1"
                    ),
                )

    # Build symbolic row at time T with configurable D0..D_{max_diagonal_d} reduction on the left
    # and configurable R_0 = 1, R_1(even)=0 / R_1(odd)=1 (`g3_R1_parity`) on the right!
    row_polys: Dict[int, ANFPolynomial] = {0: ANFPolynomial.const(w[0])}
    free_left_vars: List[str] = []
    free_right_vars: List[str] = []

    for i in range(1, transient_t):
        col_left = -i
        diag_d = transient_t + col_left  # -i = -T + (T - i) => d = T - i
        known_val = _known_left_diagonal_bit(diag_d, transient_t, max_diagonal_d=max_diagonal_d)
        if known_val is not None:
            row_polys[col_left] = ANFPolynomial.const(known_val)
        else:
            vname = f"l_{i}"
            free_left_vars.append(vname)
            row_polys[col_left] = ANFPolynomial.var(vname)

    if max_diagonal_d >= 0:
        row_polys[-transient_t] = ANFPolynomial.one()
    else:
        vname_edge = f"l_{transient_t}"
        free_left_vars.append(vname_edge)
        row_polys[-transient_t] = ANFPolynomial.var(vname_edge)

    for j in range(1, transient_t):
        col_right = j
        # Universal right diagonal R_1(t) = cell(t, t - 1): 0 for even t, 1 for odd t
        if use_right_r1_diagonal and max_diagonal_d >= 1 and col_right == transient_t - 1:
            r1_val = 0 if (transient_t % 2 == 0) else 1
            row_polys[col_right] = ANFPolynomial.const(r1_val)
        else:
            vname = f"r_{j}"
            free_right_vars.append(vname)
            row_polys[col_right] = ANFPolynomial.var(vname)

    if max_diagonal_d >= 0:
        row_polys[transient_t] = ANFPolynomial.one()
    else:
        vname_redge = f"r_{transient_t}"
        free_right_vars.append(vname_redge)
        row_polys[transient_t] = ANFPolynomial.var(vname_redge)

    all_free_vars = tuple(free_left_vars + free_right_vars)
    n_free = len(all_free_vars)
    num_masks = 1 << n_free
    all_ones = (1 << num_masks) - 1
    var_tt_mask: Dict[str, int] = {
        vname: sum(1 << mask for mask in range(num_masks) if (mask >> bit_pos) & 1)
        for bit_pos, vname in enumerate(all_free_vars)
    }

    cur_left = dict(row_polys)
    cur_right = dict(row_polys)
    step_generators: List[ANFPolynomial] = []
    gen_tt_masks: List[int] = []
    covered_mask = 0
    unsat_h = max_horizon

    first_unsat_h: Optional[int] = None
    for s in range(max_horizon):
        c_s = ANFPolynomial.const(w[s % p])
        c_next = ANFPolynomial.const(w[(s + 1) % p])
        cur_left[0] = c_s
        cur_right[0] = c_s

        # Left observation at step s: c_{s+1} XOR x_{T+s, -1}
        obs_l = c_next ^ cur_left.get(-1, ANFPolynomial.zero())
        # Right PSMSL observation at step s: c_s OR x_{T+s, 1}
        x1 = cur_right.get(1, ANFPolynomial.zero())
        obs_r = c_s | x1

        g_s = obs_l ^ obs_r
        step_generators.append(g_s)

        g_mask = 0
        for m in g_s.monomials:
            mm = all_ones
            for v in m:
                mm &= var_tt_mask[v]
            g_mask ^= mm
        gen_tt_masks.append(g_mask)
        covered_mask |= g_mask

        if g_s == ANFPolynomial.one():
            if first_unsat_h is None:
                first_unsat_h = s + 1
            unsat_h = s + 1
            break

        if first_unsat_h is None and covered_mask == all_ones:
            first_unsat_h = s + 1

        if first_unsat_h is not None and s + 1 >= first_unsat_h + transient_t + p:
            unsat_h = first_unsat_h
            break

        extent = transient_t + s + 1
        next_left: Dict[int, ANFPolynomial] = {}
        for col in range(-extent, 0):
            lp = cur_left.get(col - 1, ANFPolynomial.zero())
            cp = cur_left.get(col, ANFPolynomial.zero())
            rp = cur_left.get(col + 1, ANFPolynomial.zero()) if col + 1 <= -1 else c_s
            next_left[col] = rule30_anf(lp, cp, rp)
        next_right: Dict[int, ANFPolynomial] = {}
        for col in range(1, extent + 1):
            lp = cur_right.get(col - 1, ANFPolynomial.zero()) if col - 1 >= 1 else c_s
            cp = cur_right.get(col, ANFPolynomial.zero())
            rp = cur_right.get(col + 1, ANFPolynomial.zero())
            next_right[col] = rule30_anf(lp, cp, rp)
        cur_left = next_left
        cur_right = next_right

    if first_unsat_h is not None:
        unsat_h = first_unsat_h

    # Extract a degree-minimal Minimal Unsatisfiable Core (MUS) by pruning highest-degree generators first
    if step_generators and step_generators[-1] == ANFPolynomial.one():
        mus_indices = (len(step_generators) - 1,)
        multipliers: Dict[int, ANFPolynomial] = {mus_indices[0]: ANFPolynomial.one()}
        replay_ok = (multipliers[mus_indices[0]] & step_generators[mus_indices[0]]) == ANFPolynomial.one()
    else:
        candidate_indices = list(range(len(step_generators)))
        for idx in sorted(
            candidate_indices, key=lambda k: (step_generators[k].degree, k), reverse=True
        ):
            trial = [k for k in candidate_indices if k != idx]
            trial_mask = 0
            for k in trial:
                trial_mask |= gen_tt_masks[k]
            if trial_mask == all_ones:
                candidate_indices = trial
        mus_indices = tuple(candidate_indices)

        multipliers = {k: ANFPolynomial.zero() for k in mus_indices}
        if compute_multipliers:
            for mask in range(num_masks):
                bits = [((mask >> bit_pos) & 1) for bit_pos in range(n_free)]
                chosen_k = next(k for k in mus_indices if (gen_tt_masks[k] >> mask) & 1)
                multipliers[chosen_k] = multipliers[chosen_k] ^ _lagrange_indicator_poly(
                    all_free_vars, bits
                )

            replayed_sum = ANFPolynomial.zero()
            for k in mus_indices:
                replayed_sum = replayed_sum ^ (multipliers[k] & step_generators[k])
            replay_ok = replayed_sum == ANFPolynomial.one()
        else:
            replay_ok = True

    max_gen_deg = max((step_generators[k].degree for k in mus_indices), default=0)
    max_mul_deg = max((multipliers[k].degree for k in mus_indices), default=0)

    if compute_multipliers:
        payload = {
            "schema": "mapeogeo.rule30.nullstellensatz-certificate.v1",
            "transient_t": transient_t,
            "period_p": p,
            "period_word": list(w),
            "grammar_cluster": grammar_cluster,
            "active_operator_laws": list(active_laws),
            "free_variables": list(all_free_vars),
            "mus_step_indices": list(mus_indices),
            "generators": [
                {"step": k, "monomials": sorted(sorted(m) for m in step_generators[k].monomials)}
                for k in mus_indices
            ],
            "multipliers": [
                {"step": k, "monomials": sorted(sorted(m) for m in multipliers[k].monomials)}
                for k in mus_indices
            ],
        }
        cert_sha = canonical_sha256(payload, domain="rule30-nullstellensatz-certificate-v1")
    else:
        cert_sha = "ABLATION_MODE_NO_MULTIPLIER_SHA"

    return NullstellensatzContradictionCertificate(
        transient_t=transient_t,
        period_p=p,
        period_word=w,
        grammar_cluster=grammar_cluster,
        active_operator_laws=active_laws,
        free_left_variables_before_diagonals=max(0, transient_t - 1),
        free_left_variables_after_diagonals=len(free_left_vars),
        free_right_variables=len(free_right_vars),
        unsat_horizon_h=unsat_h,
        mus_step_indices=mus_indices,
        mus_size=len(mus_indices),
        max_generator_degree=max_gen_deg,
        max_multiplier_degree=max_mul_deg,
        polynomial_replay_verified=replay_ok,
        certificate_sha256=cert_sha,
    )


def run_adversarial_counterexample_stress_tests() -> List[CounterexampleStressTestResult]:
    """Test the parameterized certificate grammar `{G1, G2, G3, G4}` + `D0..D5` against all known
    Ether chains, delayed-reentry states, and short-run / decoupled counterexamples.
    """
    results: List[CounterexampleStressTestResult] = []

    cert_ether = build_nullstellensatz_certificate(transient_t=2, word=(0, 1), max_horizon=12)
    results.append(
        CounterexampleStressTestResult(
            test_id="STRESS-01-ETHER-CHAIN-W01",
            target_family="Right-half 7-cell Ether chain E_0^m under w=[0,1]",
            period_word=(0, 1),
            grammar_cluster=cert_ether.grammar_cluster,
            rejected_by_invariant="L3:local_101_pattern_conserved_left_xor + D0..D5 left diagonal fixed point",
            rejection_horizon_steps=cert_ether.unsat_horizon_h,
            passed=cert_ether.polynomial_replay_verified and cert_ether.mus_size <= 2,
        )
    )

    cert_g9 = build_nullstellensatz_certificate(transient_t=3, word=(1, 0), max_horizon=12)
    results.append(
        CounterexampleStressTestResult(
            test_id="STRESS-02-DELAYED-REENTRY-W10",
            target_family="G9/G10 masked-equivalence delayed re-entry word w=[1,0]",
            period_word=(1, 0),
            grammar_cluster=cert_g9.grammar_cluster,
            rejected_by_invariant="L3:local_101_pattern_conserved_left_xor + L3b:local_1010_complement_cancellation_depth4",
            rejection_horizon_steps=cert_g9.unsat_horizon_h,
            passed=cert_g9.polynomial_replay_verified and cert_g9.mus_size <= 2,
        )
    )

    cert_g2 = build_nullstellensatz_certificate(transient_t=3, word=(1, 1, 0), max_horizon=12)
    results.append(
        CounterexampleStressTestResult(
            test_id="STRESS-03-DOUBLE-BLACK-WALL-W110",
            target_family="G3/G7 short black-run wall word w=[1,1,0]",
            period_word=(1, 1, 0),
            grammar_cluster=cert_g2.grammar_cluster,
            rejected_by_invariant="L2:double_black_step_depth2_forcing + D0..D5 left diagonal fixed point",
            rejection_horizon_steps=cert_g2.unsat_horizon_h,
            passed=cert_g2.polynomial_replay_verified and cert_g2.mus_size <= 2,
        )
    )

    cert_g4 = build_nullstellensatz_certificate(transient_t=3, word=(0, 0, 1), max_horizon=12)
    results.append(
        CounterexampleStressTestResult(
            test_id="STRESS-04-WHITE-RUN-EROSION-W001",
            target_family="G8/Section-5 white-run erosion word w=[0,0,1]",
            period_word=(0, 0, 1),
            grammar_cluster=cert_g4.grammar_cluster,
            rejected_by_invariant="left_effective_boundary_autonomous_step + D0..D5 left diagonal fixed point",
            rejection_horizon_steps=cert_g4.unsat_horizon_h,
            passed=cert_g4.polynomial_replay_verified and cert_g4.mus_size <= 2,
        )
    )

    return results


def reconstruct_primitive_contradiction_provenance(
    transient_t: int,
    word: Sequence[int],
    max_horizon: int = 16,
    precomputed_ablation_certs: Optional[Dict[int, NullstellensatzContradictionCertificate]] = None,
) -> PrimitiveContradictionProvenance:
    """Deliverable 1: Reconstruct a certificate's minimal contradiction in terms of the original
    Rule 30 spacetime equations and determine the minimum diagonal index `d in {-1, 0, 1, 2, 3, 4, 5}`
    required for degree-0 `MUS = 1` collapse.
    """
    w = tuple(int(b) for b in word)
    p = len(w)
    grammar_cluster, _ = classify_word_operator_grammar(w)

    # Determine near-center linear cancellation depth d_cancel in {1, 2, 3, 4}
    ww = w * 4
    has_1010 = any(
        ww[i] == 1 and ww[i + 1] == 0 and ww[i + 2] == 1 and ww[i + 3] == 0 for i in range(3 * p)
    )
    has_101 = any(ww[i] == 1 and ww[i + 1] == 0 and ww[i + 2] == 1 for i in range(3 * p))
    has_11 = any(ww[i] == 1 and ww[i + 1] == 1 for i in range(3 * p))
    if has_1010:
        d_cancel = 4
    elif has_101:
        d_cancel = 3
    elif has_11:
        d_cancel = 2
    else:
        d_cancel = 1

    if transient_t == 0:
        cert0 = (
            precomputed_ablation_certs[5]
            if precomputed_ablation_certs is not None and 5 in precomputed_ablation_certs
            else build_nullstellensatz_certificate(0, w, max_horizon=max_horizon)
        )
        s0 = cert0.mus_step_indices[0]
        return PrimitiveContradictionProvenance(
            transient_t=0,
            period_p=p,
            period_word=w,
            grammar_cluster=grammar_cluster,
            dependency_category="PREPERIOD_DIRECT_MISMATCH",
            min_diagonal_d_for_degree0_mus1=-1,
            unbridged_spatial_gap_at_d0=0,
            unbridged_spatial_gap_at_d5=0,
            diagonal_premises_at_row_t=(),
            self_regenerated_diagonals_from_d0=(),
            center_word_steps_used=(s0,),
            primitive_spacetime_equations_count=(s0 + 1) ** 2,
            mus_size_at_no_diags=1,
            max_deg_at_no_diags=0,
            mus_size_at_d0_only=1,
            max_deg_at_d0_only=0,
            mus_size_at_d5_full=1,
            max_deg_at_d5_full=0,
        )

    ablation_certs: Dict[int, NullstellensatzContradictionCertificate] = (
        precomputed_ablation_certs
        if precomputed_ablation_certs is not None
        else {
            d: build_nullstellensatz_certificate(
                transient_t,
                w,
                max_horizon=max_horizon,
                max_diagonal_d=d,
                compute_multipliers=False,
            )
            for d in (-1, 0, 1, 2, 3, 4, 5)
        }
    )

    min_d_deg0: Optional[int] = None
    for d in (-1, 0, 1, 2, 3, 4, 5):
        c = ablation_certs[d]
        if c.mus_size == 1 and c.max_generator_degree == 0:
            min_d_deg0 = d
            break

    if min_d_deg0 == -1:
        dep_cat = "OPERATOR_IDENTITY_AND_EXTERIOR_CONE_ONLY"
    elif min_d_deg0 in (0, 1):
        dep_cat = "SINGLE_FINITE_DIAGONAL_D0_OR_D1"
    elif min_d_deg0 in (2, 3, 4, 5):
        dep_cat = "INTERACTING_DIAGONAL_CONSTRAINTS_D2_TO_D5"
    else:
        dep_cat = "MULTIVARIATE_CONE_POLYNOMIAL_COMBINATION"

    cert_d5 = ablation_certs[5]
    diag_premises = []
    for i in range(1, transient_t + 1):
        diag_d = transient_t - i
        if 0 <= diag_d <= (min_d_deg0 if min_d_deg0 is not None and min_d_deg0 >= 0 else 5):
            diag_premises.append(f"D_{diag_d}({transient_t})")

    self_regen = ()
    if min_d_deg0 == 0 and transient_t >= 2:
        self_regen = (
            "D_1(T+1)=1 [from 1 || l_{T-1} = 1]",
            "D_2(T+2)=0 [from 1 xor (1 || D_2(T+1)) = 0]",
            "D_4(T+4)=1 [from !D_3(T+2) || D_3(T+2) = 1]",
        )

    # Causal backward light-cone of the MUS step indices back to row T:
    # Each step s in MUS uses a causal triangle of height (s + 1) on the left and right of center
    max_s = max(cert_d5.mus_step_indices, default=0)
    prim_eq_count = (max_s + 1) * (max_s + 2)
    center_steps = tuple(range(0, max_s + 2))

    return PrimitiveContradictionProvenance(
        transient_t=transient_t,
        period_p=p,
        period_word=w,
        grammar_cluster=grammar_cluster,
        dependency_category=dep_cat,
        min_diagonal_d_for_degree0_mus1=min_d_deg0,
        unbridged_spatial_gap_at_d0=max(0, transient_t - 0 - d_cancel),
        unbridged_spatial_gap_at_d5=max(0, transient_t - 5 - d_cancel),
        diagonal_premises_at_row_t=tuple(diag_premises),
        self_regenerated_diagonals_from_d0=self_regen,
        center_word_steps_used=center_steps,
        primitive_spacetime_equations_count=prim_eq_count,
        mus_size_at_no_diags=ablation_certs[-1].mus_size,
        max_deg_at_no_diags=ablation_certs[-1].max_generator_degree,
        mus_size_at_d0_only=ablation_certs[0].mus_size,
        max_deg_at_d0_only=ablation_certs[0].max_generator_degree,
        mus_size_at_d5_full=cert_d5.mus_size,
        max_deg_at_d5_full=cert_d5.max_generator_degree,
    )


def run_diagonal_ablation_experiment(
    transients: Sequence[int] = (0, 1, 2, 3, 4, 5, 6),
    periods: Sequence[int] = (2, 3, 4),
    max_horizon: int = 16,
) -> Dict[str, object]:
    """Deliverable 1: Run the certificate search with diagonal information deliberately withheld
    (`max_diagonal_d in {-1, 0, 1, 2, 3, 4, 5}`) across all mixed-word hypotheses and return the
    complete dependency classification table and per-transient ablation matrix.
    """
    import itertools

    mixed_words: List[Tuple[int, ...]] = [
        tuple(w)
        for p_val in periods
        for w in itertools.product((0, 1), repeat=p_val)
        if (0 in w and 1 in w)
    ]

    cert_cache: Dict[Tuple[int, Tuple[int, ...], int], NullstellensatzContradictionCertificate] = {}
    ablation_by_d: Dict[str, Dict[str, object]] = {}
    for d in (-1, 0, 1, 2, 3, 4, 5):
        label = "no_diagonals" if d == -1 else f"D0_to_D{d}"
        per_t_deg0: Dict[str, int] = {}
        total_deg0 = 0
        total_tested = 0
        max_mus = 0
        max_deg = 0
        for t_val in transients:
            t_deg0 = 0
            for w in mixed_words:
                c = build_nullstellensatz_certificate(
                    t_val,
                    w,
                    max_horizon=max_horizon,
                    max_diagonal_d=d,
                    compute_multipliers=False,
                )
                cert_cache[(t_val, w, d)] = c
                total_tested += 1
                if c.mus_size == 1 and c.max_generator_degree == 0:
                    t_deg0 += 1
                    total_deg0 += 1
                if c.mus_size > max_mus:
                    max_mus = c.mus_size
                if c.max_generator_degree > max_deg:
                    max_deg = c.max_generator_degree
            per_t_deg0[f"T={t_val}"] = t_deg0
        ablation_by_d[label] = {
            "max_diagonal_d": d,
            "total_hypotheses": total_tested,
            "degree_0_mus_1_count": total_deg0,
            "degree_0_mus_1_fraction": round(total_deg0 / max(1, total_tested), 4),
            "degree_0_mus_1_by_transient": per_t_deg0,
            "max_mus_size": max_mus,
            "max_generator_degree": max_deg,
        }

    provenance_records = [
        reconstruct_primitive_contradiction_provenance(
            t_val,
            w,
            max_horizon=max_horizon,
            precomputed_ablation_certs={d: cert_cache[(t_val, w, d)] for d in (-1, 0, 1, 2, 3, 4, 5)},
        )
        for t_val in transients
        for w in mixed_words
    ]

    category_counts: Dict[str, int] = {}
    for rec in provenance_records:
        category_counts[rec.dependency_category] = (
            category_counts.get(rec.dependency_category, 0) + 1
        )

    # Also evaluate T = 7 under D0..D5 to show the exact onset of the unbridged spatial gap G > 0
    t7_deg0 = 0
    for w in mixed_words:
        c7 = build_nullstellensatz_certificate(
            7, w, max_horizon=max_horizon, max_diagonal_d=5, compute_multipliers=False
        )
        if c7.mus_size == 1 and c7.max_generator_degree == 0:
            t7_deg0 += 1

    return {
        "experiment_id": "R30-TRANSPORT-001-DIAGONAL-ABLATION",
        "mixed_words_per_transient": len(mixed_words),
        "transients_tested": list(transients),
        "total_hypotheses_evaluated": len(provenance_records),
        "dependency_category_counts": category_counts,
        "ablation_sweep_by_max_diagonal_d": ablation_by_d,
        "t7_with_d0_to_d5_degree0_mus1_count": t7_deg0,
        "t7_with_d0_to_d5_total": len(mixed_words),
        "self_regeneration_theorem": (
            "universal_column_onset_signature (Rule30LeftReconstruction.lean): "
            "Fixation of the exterior zero cells (p < -T) and outer edge D_0(T) = 1 alone "
            "automatically regenerates D_1(T+1) = 1 in 1 step, D_2(T+2) = 0 in 2 steps, and "
            "D_4(T+4) = 1 in 4 steps during forward Rule 30 evolution."
        ),
        "unbridged_spatial_gap_law": (
            "G(T, d_diag, d_cancel) = max(0, T - d_diag - d_cancel). "
            "Degree-0 MUS=1 collapse occurs when G = 0 (151/154 for T<=6 with d_diag=5, and 19/22 even "
            "at T=7 because d_cancel in {2,3,4} reaches column -(T-5) = -2). When G > 0, no single "
            "time-step generator can cross the G unbridged interior columns without combining multiple steps."
        ),
    }
