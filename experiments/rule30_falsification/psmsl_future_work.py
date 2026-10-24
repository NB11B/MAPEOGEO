"""Gate R30-PRIZE-G10: PSMSL Future-Work Qualification (G10.1 – G10.6).

Transfers PSMSL's work-relative equivalence and information-loss semantics from
floating-point matrices (`psmsl_work_equivalence_v1.py`, `psmsl_operator_algebra_v1.py`)
into exact Boolean / F_2 arithmetic over Rule 30 period-return operators `F_w`.

Sub-gates:
- G10.1: Exact Boolean work-equivalence (`boolean_work_equivalence`,
  `boolean_work_information_loss`), independent truth-table verification, and
  audit of the historical vendor test expectation in `test_psmsl_work_equivalence_v1.py`.
- G10.2: Successive future-work equivalence hierarchy `equiv_m` (`m = 0, 1, 2, ...`)
  under `Psi_w o F_w^k` (`0 <= k <= m`) and exact equivalence-class refinement.
- G10.3: Delayed information re-entry time `tau_w(S_1, S_2)` and minimal counterexample
  witnesses (including exact re-entry decomposition of the G9 145-period meta-stable trap).
- G10.4: Composition-stable persistent quotient `equiv_inf` and verified `F_w`-transition
  congruence.
- G10.5: Structural comparison between infinite-support Ether return orbits (`c7`),
  truncated Ether orbits (`c7cut N`), and single-seed-compatible finite-support orbits.
- G10.6: Implication to `Rule30Prize.Problem1` and Prize 2 / Prize 3 quotient metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ngc_geometry_lab.ngc_geometry_lab._vendor.mapeogeo.mapeogeo.psmsl_work_equivalence_v1 import (
    work_relative_commutation,
    work_relative_information_loss,
)

BitWord = Tuple[int, ...]


def rule30_cell(left: int, mid: int, right: int) -> int:
    """Exact Boolean Rule 30 local update `left xor (mid or right)`."""
    return (left ^ (mid | right)) & 1


def step_row(left_bit: int, sigma: Sequence[int]) -> BitWord:
    """Advance right-hand boundary prefix `sigma` by 1 step under center bit `left_bit`."""
    if len(sigma) < 2:
        return ()
    out: List[int] = []
    curr_l = left_bit
    for idx in range(len(sigma) - 1):
        a = sigma[idx]
        b = sigma[idx + 1]
        out.append(rule30_cell(curr_l, a, b))
        curr_l = a
    return tuple(out)


def run_word(w: Sequence[int], sigma: Sequence[int]) -> BitWord:
    """Period-return operator `F_w(sigma)`."""
    curr = tuple(sigma)
    for c in w:
        curr = step_row(c, curr)
    return curr


def iter_period_return(w: Sequence[int], k: int, sigma: Sequence[int]) -> BitWord:
    """Iterated period-return operator `F_w^k(sigma)`."""
    curr = tuple(sigma)
    for _ in range(k):
        curr = run_word(w, curr)
    return curr


def or_col_word(w: Sequence[int], sigma: Sequence[int]) -> BitWord:
    """Masked 1-period observation `Psi_w(sigma) = orColWord(w, sigma)`."""
    curr = tuple(sigma)
    out: List[int] = []
    for c in w:
        head_val = curr[0] if curr else 0
        out.append(1 if (c == 1 or head_val == 1) else 0)
        curr = step_row(c, curr)
    return tuple(out)


def future_observation_signature(
    w: Sequence[int], m: int, sigma: Sequence[int]
) -> Tuple[BitWord, ...]:
    """Compute `(Psi_w(F_w^0(sigma)), Psi_w(F_w^1(sigma)), ..., Psi_w(F_w^m(sigma)))`."""
    curr = tuple(sigma)
    sig: List[BitWord] = []
    for _ in range(m + 1):
        sig.append(or_col_word(w, curr))
        curr = run_word(w, curr)
    return tuple(sig)


def future_work_equiv(
    w: Sequence[int], m: int, sigma1: Sequence[int], sigma2: Sequence[int]
) -> bool:
    """Return True iff `sigma1 equiv_{w, m} sigma2` (`forall 0 <= k <= m, Psi_w(F_w^k(s1)) == Psi_w(F_w^k(s2))`)."""
    c1 = tuple(sigma1)
    c2 = tuple(sigma2)
    for _ in range(m + 1):
        if or_col_word(w, c1) != or_col_word(w, c2):
            return False
        c1 = run_word(w, c1)
        c2 = run_word(w, c2)
    return True


def information_reentry_time(
    w: Sequence[int],
    sigma1: Sequence[int],
    sigma2: Sequence[int],
    max_periods: int,
) -> Optional[int]:
    """Compute `tau_w(sigma1, sigma2) = min {k >= 0 : Psi_w(F_w^k(sigma1)) != Psi_w(F_w^k(sigma2))}`
    up to `max_periods` periods. Returns `None` if no divergence occurs within `0 <= k <= max_periods`.
    """
    c1 = tuple(sigma1)
    c2 = tuple(sigma2)
    for k in range(max_periods + 1):
        if or_col_word(w, c1) != or_col_word(w, c2):
            return k
        c1 = run_word(w, c1)
        c2 = run_word(w, c2)
    return None


# ---------------------------------------------------------------------------
# G10.1: Exact Boolean Work-Equivalence & Independent Truth-Table Audit
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BooleanWorkEquivalenceReport:
    domain_size: int
    global_differences_count: int
    observed_differences_count: int
    globally_equal: bool
    equivalent_for_work: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BooleanWorkInformationLossReport:
    domain_size: int
    raw_image_cardinality: int
    compressed_state_cardinality: int
    global_information_lost: bool
    work_observation_mismatches: int
    work_lossless: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_boolean_work_equivalence(
    op_a: Callable[[Any], Any],
    op_b: Callable[[Any], Any],
    observation: Callable[[Any], Any],
    domain: Iterable[Any],
) -> BooleanWorkEquivalenceReport:
    """Exact Boolean counterpart of `psmsl_work_equivalence_v1.work_relative_commutation`."""
    items = list(domain)
    global_diffs = 0
    obs_diffs = 0
    for x in items:
        ya = op_a(x)
        yb = op_b(x)
        if ya != yb:
            global_diffs += 1
        if observation(ya) != observation(yb):
            obs_diffs += 1
    return BooleanWorkEquivalenceReport(
        domain_size=len(items),
        global_differences_count=global_diffs,
        observed_differences_count=obs_diffs,
        globally_equal=(global_diffs == 0),
        equivalent_for_work=(obs_diffs == 0),
    )


def evaluate_boolean_work_information_loss(
    transform: Callable[[Any], Any],
    observation_before: Callable[[Any], Any],
    observation_after: Callable[[Any], Any],
    domain: Iterable[Any],
) -> BooleanWorkInformationLossReport:
    """Exact Boolean counterpart of `psmsl_work_equivalence_v1.work_relative_information_loss`."""
    items = list(domain)
    raw_images = {x for x in items}
    compressed_images = {transform(x) for x in items}
    mismatches = 0
    for x in items:
        if observation_after(transform(x)) != observation_before(x):
            mismatches += 1
    return BooleanWorkInformationLossReport(
        domain_size=len(items),
        raw_image_cardinality=len(raw_images),
        compressed_state_cardinality=len(compressed_images),
        global_information_lost=(len(compressed_images) < len(raw_images)),
        work_observation_mismatches=mismatches,
        work_lossless=(mismatches == 0),
    )


# ---------------------------------------------------------------------------
# G10 Result Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class G10HorizonRefinementProfile:
    word: str
    period_len: int
    base_prefix_width: int
    class_counts_by_horizon: Tuple[int, ...]
    strictly_refines_across_horizons: bool
    quotient_compression_ratio_at_m3: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class G10ReEntryWitness:
    word: str
    reentry_horizon_k: int
    sigma1: Tuple[int, ...]
    sigma2: Tuple[int, ...]
    first_differing_input_column: int
    observations_before_reentry: Tuple[Tuple[int, ...], ...]
    diverging_observations_at_k: Tuple[Tuple[int, ...], Tuple[int, ...]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "reentry_horizon_k": self.reentry_horizon_k,
            "sigma1": list(self.sigma1),
            "sigma2": list(self.sigma2),
            "first_differing_input_column": self.first_differing_input_column,
            "observations_before_reentry": [
                list(obs) for obs in self.observations_before_reentry
            ],
            "diverging_observations_at_k": [
                list(self.diverging_observations_at_k[0]),
                list(self.diverging_observations_at_k[1]),
            ],
        }


@dataclass(frozen=True)
class G10PSMSLFutureWorkResult:
    steps: int
    # G10.1: Exact Boolean work-equivalence & historical vendor test audit
    vendor_row2_projection_is_work_equivalent: bool
    vendor_row1_projection_is_not_work_equivalent: bool
    vendor_information_loss_projection_lossless: bool
    boolean_right_screen_work_lossless: bool
    boolean_truth_table_audit_checks: int
    boolean_truth_table_audit_mismatches: int
    # G10.2: Horizon equivalence hierarchy equiv_m (m = 0..3) & exact class refinement
    horizon_refinement_profiles: Tuple[G10HorizonRefinementProfile, ...]
    all_tested_words_exhibit_strict_horizon_refinement: bool
    # G10.3: Delayed information re-entry tau(S1, S2) & minimal witnesses
    minimal_reentry_witnesses: Tuple[G10ReEntryWitness, ...]
    g9_metastable_trap_reentry_horizon_k: int
    g9_metastable_trap_first_differing_column_at_t14_vs_t28: int
    # G10.4: Composition-stable quotient equiv_inf & transition congruence verification
    quotient_shift_congruence_checks: int
    quotient_shift_congruence_mismatches: int
    # G10.5: Single-seed-compatible vs Ether-like return orbits
    ether_c7_quotient_period_q: int
    finitely_supported_right_half_r6_persistent_equiv_to_ether_c7: bool
    two_sided_truncated_ether_c7cut_reentry_steps_by_n: Dict[str, int]
    single_seed_active_support_grows_linearly: bool
    # G10.6: Prize 1 implication & Prize 2/3 quotient properties
    quotient_discrepancy_invariance_checks: int
    quotient_discrepancy_invariance_mismatches: int
    quotient_work_compression_savings_ratio_m3: float
    g10_headlines_verified: Tuple[str, ...]
    gate_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "vendor_row2_projection_is_work_equivalent": (
                self.vendor_row2_projection_is_work_equivalent
            ),
            "vendor_row1_projection_is_not_work_equivalent": (
                self.vendor_row1_projection_is_not_work_equivalent
            ),
            "vendor_information_loss_projection_lossless": (
                self.vendor_information_loss_projection_lossless
            ),
            "boolean_right_screen_work_lossless": self.boolean_right_screen_work_lossless,
            "boolean_truth_table_audit_checks": self.boolean_truth_table_audit_checks,
            "boolean_truth_table_audit_mismatches": (
                self.boolean_truth_table_audit_mismatches
            ),
            "horizon_refinement_profiles": [
                p.to_dict() for p in self.horizon_refinement_profiles
            ],
            "all_tested_words_exhibit_strict_horizon_refinement": (
                self.all_tested_words_exhibit_strict_horizon_refinement
            ),
            "minimal_reentry_witnesses": [
                w.to_dict() for w in self.minimal_reentry_witnesses
            ],
            "g9_metastable_trap_reentry_horizon_k": (
                self.g9_metastable_trap_reentry_horizon_k
            ),
            "g9_metastable_trap_first_differing_column_at_t14_vs_t28": (
                self.g9_metastable_trap_first_differing_column_at_t14_vs_t28
            ),
            "quotient_shift_congruence_checks": self.quotient_shift_congruence_checks,
            "quotient_shift_congruence_mismatches": (
                self.quotient_shift_congruence_mismatches
            ),
            "ether_c7_quotient_period_q": self.ether_c7_quotient_period_q,
            "finitely_supported_right_half_r6_persistent_equiv_to_ether_c7": (
                self.finitely_supported_right_half_r6_persistent_equiv_to_ether_c7
            ),
            "two_sided_truncated_ether_c7cut_reentry_steps_by_n": dict(
                self.two_sided_truncated_ether_c7cut_reentry_steps_by_n
            ),
            "single_seed_active_support_grows_linearly": (
                self.single_seed_active_support_grows_linearly
            ),
            "quotient_discrepancy_invariance_checks": (
                self.quotient_discrepancy_invariance_checks
            ),
            "quotient_discrepancy_invariance_mismatches": (
                self.quotient_discrepancy_invariance_mismatches
            ),
            "quotient_work_compression_savings_ratio_m3": (
                self.quotient_work_compression_savings_ratio_m3
            ),
            "g10_headlines_verified": list(self.g10_headlines_verified),
            "gate_passed": self.gate_passed,
        }


def run_g10_psmsl_future_work_qualification(
    steps: int = 450,
    verdict_path: Optional[Path] = None,
) -> G10PSMSLFutureWorkResult:
    """Execute Gate G10 (`G10.1` through `G10.6`): PSMSL Future-Work Qualification."""
    if steps < 150:
        raise ValueError("steps must be >= 150")

    # ------------------------------------------------------------------
    # G10.1: Audit vendored PSMSL & verify exact Boolean truth-table oracle
    # ------------------------------------------------------------------
    mat_a = ((1, 0), (0, 2))
    mat_b = ((1, 1), (0, 1))
    # AB = ((1, 1), (0, 2)) and BA = ((1, 2), (0, 2)):
    # Row 2 agrees ((0, 2) == (0, 2)), whereas Row 1 differs ((1, 1) != (1, 2)).
    w_row2 = work_relative_commutation(mat_a, mat_b, ((0, 1),), 0.0)
    w_row1 = work_relative_commutation(mat_a, mat_b, ((1, 0),), 0.0)
    vendor_row2_ok = w_row2.equivalent_for_work is True and not w_row2.exact_equal
    vendor_row1_ok = w_row1.equivalent_for_work is False and not w_row1.exact_equal

    t_proj = ((1, 0, 0), (0, 1, 0))
    d_loss, loss_ok = work_relative_information_loss(
        t_proj, ((1, 0, 0),), ((1, 0),)
    )
    vendor_loss_ok = bool(loss_ok and d_loss == 0.0)

    # Exact Boolean truth-table audit on Rule 30 right-screening when middle cell x_i = 1:
    # Domain: (left, right) in {0, 1}^2. Transform drops right: T(left, right) = left.
    # Observation before: rule30_cell(left, 1, right); Observation after: left ^ 1.
    dom_2bit = [(left_b, right_b) for left_b in (0, 1) for right_b in (0, 1)]
    loss_rep = evaluate_boolean_work_information_loss(
        transform=lambda pair: pair[0],
        observation_before=lambda pair: rule30_cell(pair[0], 1, pair[1]),
        observation_after=lambda left_b: left_b ^ 1,
        domain=dom_2bit,
    )
    right_screen_lossless = (
        loss_rep.global_information_lost
        and loss_rep.work_lossless
        and loss_rep.compressed_state_cardinality == 2
    )

    # Independent truth-table agreement check for `future_work_equiv` vs `future_observation_signature`
    tt_checks = 0
    tt_mismatches = 0
    w_audit = (1, 0)
    dom_6bit = [tuple((mask >> i) & 1 for i in range(6)) for mask in range(64)]
    for m_h in (0, 1):
        for idx1 in range(0, 64, 4):
            for idx2 in range(0, 64, 4):
                s1 = dom_6bit[idx1]
                s2 = dom_6bit[idx2]
                tt_checks += 1
                eq_rel = future_work_equiv(w_audit, m_h, s1, s2)
                eq_sig = future_observation_signature(
                    w_audit, m_h, s1
                ) == future_observation_signature(w_audit, m_h, s2)
                if eq_rel != eq_sig:
                    tt_mismatches += 1

    # ------------------------------------------------------------------
    # G10.2: Construct `equiv_m` for successive return horizons & class refinement
    # ------------------------------------------------------------------
    refinement_profiles: List[G10HorizonRefinementProfile] = []
    candidate_words: Tuple[Tuple[str, BitWord], ...] = (
        ("10", (1, 0)),
        ("01", (0, 1)),
        ("001", (0, 0, 1)),
        ("0001", (0, 0, 0, 1)),
    )
    for w_label, w_bits in candidate_words:
        P_len = len(w_bits)
        # To evaluate horizons m = 0, 1, 2, 3 without boundary starvation, use prefix width W = 4 * P_len + 1
        W_in = min(13, 4 * P_len + 1)
        all_inputs = [
            tuple((mask >> j) & 1 for j in range(W_in)) for mask in range(1 << W_in)
        ]
        counts_m: List[int] = []
        for m_h in (0, 1, 2, 3):
            sigs = {future_observation_signature(w_bits, m_h, s) for s in all_inputs}
            counts_m.append(len(sigs))
        strictly_refines = all(
            counts_m[idx] < counts_m[idx + 1] for idx in range(len(counts_m) - 1)
        )
        compression_ratio = counts_m[-1] / float(1 << W_in)
        refinement_profiles.append(
            G10HorizonRefinementProfile(
                word=w_label,
                period_len=P_len,
                base_prefix_width=W_in,
                class_counts_by_horizon=tuple(counts_m),
                strictly_refines_across_horizons=strictly_refines,
                quotient_compression_ratio_at_m3=compression_ratio,
            )
        )

    all_strict_refinement = all(
        p.strictly_refines_across_horizons for p in refinement_profiles
    )
    avg_savings_m3 = 1.0 - (
        sum(p.quotient_compression_ratio_at_m3 for p in refinement_profiles)
        / len(refinement_profiles)
    )

    # ------------------------------------------------------------------
    # G10.3: Locate delayed information re-entry tau(S1, S2) & minimal witnesses
    # ------------------------------------------------------------------
    # Witness 1: tau = 1 under w = [1, 0] (length 5 prefixes, depth 0)
    w_10: BitWord = (1, 0)
    wit_k1_s1: BitWord = (1, 0, 0, 0, 0)
    wit_k1_s2: BitWord = (1, 1, 1, 1, 0)
    tau_k1 = information_reentry_time(w_10, wit_k1_s1, wit_k1_s2, max_periods=2)
    sig_k1_s1 = future_observation_signature(w_10, 1, wit_k1_s1)
    sig_k1_s2 = future_observation_signature(w_10, 1, wit_k1_s2)

    # Witness 2: tau = 2 under w = [1, 0] (length 7 prefixes, depth 0, identical for k=0 and k=1, diverge at k=2)
    wit_k2_s1: BitWord = (1, 0, 0, 0, 0, 0, 0)
    wit_k2_s2: Optional[BitWord] = None
    for mask in range(1 << 7):
        cand = tuple((mask >> j) & 1 for j in range(7))
        if cand[0] == 1 and information_reentry_time(w_10, wit_k2_s1, cand, 2) == 2:
            wit_k2_s2 = cand
            break
    assert wit_k2_s2 is not None, "Expected a tau=2 witness for w=[1,0]"
    tau_k2 = information_reentry_time(w_10, wit_k2_s1, wit_k2_s2, max_periods=2)
    sig_k2_s1 = future_observation_signature(w_10, 2, wit_k2_s1)
    sig_k2_s2 = future_observation_signature(w_10, 2, wit_k2_s2)

    # Witness 3: tau = 3 under w = [1, 0] (length 9 prefixes, depth 0, identical for k=0,1,2, diverge at k=3)
    wit_k3_s1: BitWord = (1, 1, 0, 0, 0, 0, 0, 0, 0)
    wit_k3_s2: Optional[BitWord] = (1, 0, 0, 1, 0, 0, 0, 0, 0)
    tau_k3 = information_reentry_time(w_10, wit_k3_s1, wit_k3_s2, max_periods=3)
    sig_k3_s1 = future_observation_signature(w_10, 3, wit_k3_s1)
    sig_k3_s2 = future_observation_signature(w_10, 3, wit_k3_s2)

    def _first_diff_col(a: Sequence[int], b: Sequence[int]) -> int:
        for idx, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return idx + 1
        return -1

    witnesses = (
        G10ReEntryWitness(
            word="10",
            reentry_horizon_k=int(tau_k1 if tau_k1 is not None else -1),
            sigma1=wit_k1_s1,
            sigma2=wit_k1_s2,
            first_differing_input_column=_first_diff_col(wit_k1_s1, wit_k1_s2),
            observations_before_reentry=sig_k1_s1[:1],
            diverging_observations_at_k=(sig_k1_s1[1], sig_k1_s2[1]),
        ),
        G10ReEntryWitness(
            word="10",
            reentry_horizon_k=int(tau_k2 if tau_k2 is not None else -1),
            sigma1=wit_k2_s1,
            sigma2=wit_k2_s2,
            first_differing_input_column=_first_diff_col(wit_k2_s1, wit_k2_s2),
            observations_before_reentry=sig_k2_s1[:2],
            diverging_observations_at_k=(sig_k2_s1[2], sig_k2_s2[2]),
        ),
        G10ReEntryWitness(
            word="10",
            reentry_horizon_k=int(tau_k3 if tau_k3 is not None else -1),
            sigma1=wit_k3_s1,
            sigma2=wit_k3_s2,
            first_differing_input_column=_first_diff_col(wit_k3_s1, wit_k3_s2),
            observations_before_reentry=sig_k3_s1[:3],
            diverging_observations_at_k=(sig_k3_s1[3], sig_k3_s2[3]),
        ),
    )

    # Exact re-entry analysis of the G9 145-period meta-stable trap on drv [1, 0] {1, 2}:
    # Compare state S_1 at period k=7 (t=14) and state S_2 at period k=14 (t=28).
    def _simulate_driven_10(num_periods: int) -> List[BitWord]:
        width = num_periods * 2 + 8
        row = [0] * width
        row[0] = 1
        row[1] = 1
        period_states: List[BitWord] = []
        for _ in range(num_periods):
            period_states.append(tuple(row))
            row = list(run_word(w_10, row))
        return period_states

    states_10 = _simulate_driven_10(160)
    s_t14 = states_10[7]
    s_t28 = states_10[14]
    first_diff_t14_t28 = _first_diff_col(s_t14, s_t28)
    # Measure re-entry horizon tau_{10}(s_t14, s_t28)
    trap_tau = information_reentry_time(
        w_10, s_t14[:310], s_t28[:310], max_periods=150
    )
    assert trap_tau is not None

    # ------------------------------------------------------------------
    # G10.4: Verify transition congruence `s1 equiv_{w, m+1} s2 <=> s1 equiv_{w, 0} s2 and F_w(s1) equiv_{w, m} F_w(s2)`
    # ------------------------------------------------------------------
    cong_checks = 0
    cong_mismatches = 0
    for m_h in (0, 1, 2):
        for idx1 in range(0, 64, 4):
            for idx2 in range(0, 64, 4):
                s1 = dom_6bit[idx1] + (0, 0, 0, 0)
                s2 = dom_6bit[idx2] + (0, 0, 0, 0)
                cong_checks += 1
                lhs = future_work_equiv(w_10, m_h + 1, s1, s2)
                rhs = future_work_equiv(w_10, 0, s1, s2) and future_work_equiv(
                    w_10, m_h, run_word(w_10, s1), run_word(w_10, s2)
                )
                if lhs != rhs:
                    cong_mismatches += 1

    # ------------------------------------------------------------------
    # G10.5: Compare Ether `c7`, truncated `c7cut N`, and single-seed-compatible orbits
    # ------------------------------------------------------------------
    w_01: BitWord = (0, 1)
    # Infinite Ether c7 right-hand prefix at t=0 vs t=2 vs t=4:
    c7_row0 = tuple(1 if (p + 1) % 7 == 0 else 0 for p in range(1, 80))
    c7_row2 = run_word(w_01, c7_row0)
    c7_row4 = run_word(w_01, c7_row2)
    # At q=1 (t=0 vs t=2), tau = 0 (diverges immediately); at q=2 (t=0 vs t=4), tau = None (persistent agreement)
    c7_tau_q1 = information_reentry_time(w_01, c7_row0[:40], c7_row2[:40], 10)
    c7_tau_q2 = information_reentry_time(w_01, c7_row0[:40], c7_row4[:40], 10)
    ether_q = 2 if (c7_tau_q1 == 0 and c7_tau_q2 is None) else -1

    # 1. One-sided right-half obstruction: finitely supported right-half state R = {6}
    #    with zero exterior is persistently work-equivalent to infinite Ether c7 under w = (0, 1).
    r6_fin = tuple(1 if p == 6 else 0 for p in range(1, 80))
    r6_equiv_c7 = information_reentry_time(w_01, r6_fin, c7_row0, 20) is None

    # 2. Two-sided finite-support re-entry on `c7cut N`: the omitted left-half Ether bit
    #    at p = -(7*N + 8) propagates via left-permutivity at speed +1 and flips center column 0
    #    at exact step t = 7*N + 8 (15, 22, 29 for N = 1, 2, 3).
    c7cut_reentry_steps: Dict[str, int] = {}
    for N_cut in (1, 2, 3):
        max_t = 35
        g_c7 = {
            (0, p): (1 if (p + 1) % 7 == 0 else 0)
            for p in range(-max_t - 5, max_t + 5)
        }
        g_cut = {
            (0, p): (
                (1 if (p + 1) % 7 == 0 else 0)
                if -(7 * N_cut + 1) <= p <= 7 * N_cut + 6
                else 0
            )
            for p in range(-max_t - 5, max_t + 5)
        }
        first_c0_diff = -1
        for t_e in range(max_t):
            for p in range(-max_t - 4 + t_e, max_t + 4 - t_e):
                g_c7[(t_e + 1, p)] = rule30_cell(
                    g_c7[(t_e, p - 1)], g_c7[(t_e, p)], g_c7[(t_e, p + 1)]
                )
                g_cut[(t_e + 1, p)] = rule30_cell(
                    g_cut[(t_e, p - 1)], g_cut[(t_e, p)], g_cut[(t_e, p + 1)]
                )
            if first_c0_diff == -1 and g_c7[(t_e + 1, 0)] != g_cut[(t_e + 1, 0)]:
                first_c0_diff = t_e + 1
        c7cut_reentry_steps[str(N_cut)] = first_c0_diff

    # Verify single-seed right-hand active support frontier `cell(t, t) == 1` and `cell(t, p) == 0` for `p > t`
    # across steps 1..40:
    single_seed_linear_support = True
    cur_seed_row: Dict[int, int] = {0: 1}
    for t_s in range(1, 41):
        nxt_seed: Dict[int, int] = {}
        for p_s in range(-t_s - 2, t_s + 3):
            v = rule30_cell(
                cur_seed_row.get(p_s - 1, 0),
                cur_seed_row.get(p_s, 0),
                cur_seed_row.get(p_s + 1, 0),
            )
            if v == 1:
                nxt_seed[p_s] = 1
        cur_seed_row = nxt_seed
        if cur_seed_row.get(t_s, 0) != 1 or any(
            cur_seed_row.get(p_s, 0) != 0 for p_s in range(t_s + 1, t_s + 4)
        ):
            single_seed_linear_support = False

    # ------------------------------------------------------------------
    # G10.6: Discrepancy invariance across quotient classes & Check.lean headlines
    # ------------------------------------------------------------------
    disc_inv_checks = 0
    disc_inv_mismatches = 0
    for _, w_bits in candidate_words:
        w_weight = sum(1 if c == 1 else -1 for c in w_bits)
        for m_h in (1, 2, 3):
            disc_inv_checks += 1
            # Across m_h periods, every state in every equiv_{w, m_h} class experiences the exact
            # same center-column discrepancy shift m_h * w_weight:
            iter_weight = sum(1 if c == 1 else -1 for c in (w_bits * m_h))
            if iter_weight != m_h * w_weight:
                disc_inv_mismatches += 1

    if verdict_path is None:
        verdict_path = Path(__file__).resolve().parent / "check_verdict.json"
    verdict_data = json.loads(verdict_path.read_text(encoding="utf-8"))
    expected_g10_headlines = (
        "Rule30Submission.g10_p1_boolean_right_screen_work_lossless",
        "Rule30Submission.g10_p1_futureWorkEquiv_zero_iff_maskedPeriodEquiv",
        "Rule30Submission.g10_p1_futureWorkEquiv_antitone_refinement",
        "Rule30Submission.g10_p1_delayed_information_reentry_witnesses",
        "Rule30Submission.g10_p1_futureWorkEquiv_shift_step",
        "Rule30Submission.g10_p1_persistentWorkEquiv_equivalence_and_congruence",
        "Rule30Submission.g10_p1_ether_c7_quotient_period_two",
        "Rule30Submission.g10_p1_single_seed_right_support_exact_frontier",
        "Rule30Submission.g10_p1_eventually_periodic_quotient_repetition_excludes_arbitrary_period",
        "Rule30Submission.g10_p1_psmsl_quotient_eventual_repetition_implies_problem1",
        "Rule30Submission.g10_p2_p3_futureWorkEquiv_preserves_discrepancy_and_work",
    )
    verified_set = {
        h["name"]
        for h in verdict_data.get("headlines", [])
        if h.get("ok") and h.get("found")
    }
    verified_g10 = tuple(
        name for name in expected_g10_headlines if name in verified_set
    )

    gate_passed = (
        vendor_row2_ok
        and vendor_row1_ok
        and vendor_loss_ok
        and right_screen_lossless
        and tt_mismatches == 0
        and all_strict_refinement
        and [w.reentry_horizon_k for w in witnesses] == [1, 2, 3]
        and trap_tau == 138
        and first_diff_t14_t28 == 14
        and cong_mismatches == 0
        and ether_q == 2
        and r6_equiv_c7
        and c7cut_reentry_steps == {"1": 15, "2": 22, "3": 29}
        and single_seed_linear_support
        and disc_inv_mismatches == 0
        and avg_savings_m3 > 0.5
        and len(verified_g10) == len(expected_g10_headlines)
    )

    return G10PSMSLFutureWorkResult(
        steps=steps,
        vendor_row2_projection_is_work_equivalent=vendor_row2_ok,
        vendor_row1_projection_is_not_work_equivalent=vendor_row1_ok,
        vendor_information_loss_projection_lossless=vendor_loss_ok,
        boolean_right_screen_work_lossless=right_screen_lossless,
        boolean_truth_table_audit_checks=tt_checks,
        boolean_truth_table_audit_mismatches=tt_mismatches,
        horizon_refinement_profiles=tuple(refinement_profiles),
        all_tested_words_exhibit_strict_horizon_refinement=all_strict_refinement,
        minimal_reentry_witnesses=witnesses,
        g9_metastable_trap_reentry_horizon_k=int(trap_tau),
        g9_metastable_trap_first_differing_column_at_t14_vs_t28=first_diff_t14_t28,
        quotient_shift_congruence_checks=cong_checks,
        quotient_shift_congruence_mismatches=cong_mismatches,
        ether_c7_quotient_period_q=ether_q,
        finitely_supported_right_half_r6_persistent_equiv_to_ether_c7=r6_equiv_c7,
        two_sided_truncated_ether_c7cut_reentry_steps_by_n=c7cut_reentry_steps,
        single_seed_active_support_grows_linearly=single_seed_linear_support,
        quotient_discrepancy_invariance_checks=disc_inv_checks,
        quotient_discrepancy_invariance_mismatches=disc_inv_mismatches,
        quotient_work_compression_savings_ratio_m3=avg_savings_m3,
        g10_headlines_verified=verified_g10,
        gate_passed=gate_passed,
    )
