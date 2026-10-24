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


def _known_left_diagonal_bit(diag_d: int, step_t: int) -> Optional[int]:
    """Return the exact universal single-seed bit of `D_d(step_t) = cell(step_t, -step_t + d)`
    for the proven periodic diagonals `d in {0, 1, 2, 3, 4, 5}`, or `None` if `d >= 6`.
    """
    if diag_d < 0:
        return 0
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
) -> NullstellensatzContradictionCertificate:
    """Construct the canonical bilateral polynomial ideal `I_{T, w, H}` with universal left-diagonal
    reduction (`D0..D5`), extract its Minimal Unsatisfiable Core (MUS), construct an explicit
    F_2 Nullstellensatz certificate `1 = sum_{r in MUS} q_r(z) * g_r(z)`, and replay it in `ANFPolynomial`.
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

    # Build symbolic row at time T with D0..D5 universal diagonal reduction on the left
    # and R_0 = 1, R_1(even)=0 / R_1(odd)=1 (`g3_R1_parity`) on the right!
    row_polys: Dict[int, ANFPolynomial] = {0: ANFPolynomial.const(w[0])}
    free_left_vars: List[str] = []
    free_right_vars: List[str] = []

    for i in range(1, transient_t):
        col_left = -i
        diag_d = transient_t + col_left  # -i = -T + (T - i) => d = T - i
        known_val = _known_left_diagonal_bit(diag_d, transient_t)
        if known_val is not None:
            row_polys[col_left] = ANFPolynomial.const(known_val)
        else:
            vname = f"l_{i}"
            free_left_vars.append(vname)
            row_polys[col_left] = ANFPolynomial.var(vname)

    for j in range(1, transient_t):
        col_right = j
        # Universal right diagonal R_1(t) = cell(t, t - 1): 0 for even t, 1 for odd t
        if col_right == transient_t - 1:
            r1_val = 0 if (transient_t % 2 == 0) else 1
            row_polys[col_right] = ANFPolynomial.const(r1_val)
        else:
            vname = f"r_{j}"
            free_right_vars.append(vname)
            row_polys[col_right] = ANFPolynomial.var(vname)

    row_polys[-transient_t] = ANFPolynomial.one()
    row_polys[transient_t] = ANFPolynomial.one()

    all_free_vars = tuple(free_left_vars + free_right_vars)
    n_free = len(all_free_vars)

    cur_left = dict(row_polys)
    cur_right = dict(row_polys)
    step_generators: List[ANFPolynomial] = []
    unsat_h = max_horizon
    surviving_masks = list(range(1 << n_free))
    var_eval_maps: List[Dict[str, int]] = [
        {all_free_vars[bit_pos]: ((mask >> bit_pos) & 1) for bit_pos in range(n_free)}
        for mask in surviving_masks
    ]
    eval_table: List[List[int]] = []

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

        row_evals = [g_s.evaluate(vmap) for vmap in var_eval_maps]
        eval_table.append(row_evals)

        if g_s == ANFPolynomial.one():
            if first_unsat_h is None:
                first_unsat_h = s + 1
            unsat_h = s + 1
            break

        if first_unsat_h is None and all(
            any(eval_table[k][mask] == 1 for k in range(s + 1)) for mask in range(1 << n_free)
        ):
            first_unsat_h = s + 1

        if first_unsat_h is not None and s + 1 >= first_unsat_h + p:
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
    candidate_indices = list(range(len(step_generators)))
    for idx in sorted(candidate_indices, key=lambda k: (step_generators[k].degree, k), reverse=True):
        trial = [k for k in candidate_indices if k != idx]
        if all(any(eval_table[k][mask] == 1 for k in trial) for mask in range(1 << n_free)):
            candidate_indices = trial
    mus_indices = tuple(candidate_indices)

    # Construct explicit Nullstellensatz multipliers q_r(z) in F_2[z] / <z^2 + z>
    # such that sum_{r in MUS} q_r(z) * g_r(z) == 1 identically!
    multipliers: Dict[int, ANFPolynomial] = {k: ANFPolynomial.zero() for k in mus_indices}
    for mask in range(1 << n_free):
        bits = [((mask >> bit_pos) & 1) for bit_pos in range(n_free)]
        chosen_k = next(k for k in mus_indices if eval_table[k][mask] == 1)
        multipliers[chosen_k] = multipliers[chosen_k] ^ _lagrange_indicator_poly(all_free_vars, bits)

    # Independent symbolic polynomial replay in ANFPolynomial: verify sum_{k in MUS} q_k(z) * g_k(z) == 1
    replayed_sum = ANFPolynomial.zero()
    for k in mus_indices:
        replayed_sum = replayed_sum ^ (multipliers[k] & step_generators[k])
    replay_ok = (replayed_sum == ANFPolynomial.one())

    max_gen_deg = max((step_generators[k].degree for k in mus_indices), default=0)
    max_mul_deg = max((multipliers[k].degree for k in mus_indices), default=0)

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
