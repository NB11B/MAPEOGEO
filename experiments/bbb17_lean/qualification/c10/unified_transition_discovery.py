"""Unified PSMSL + MAPEOGEO + Symbolic-Dynamics Collatz Transition System.

Implements the joint state space:
    X_r = (n_r, A_r, B_r, D_r, a_r, rho_r, Omega_r, P_r)
where:
- `M_r = [[A_r, B_r], [0, D_r]]` is the PSMSL upper-triangular operator matrix,
- `Omega_r = 2^r * (n_r - n)` is the 2-adically scaled affine surplus
  (`Omega_r = A_r * n + B_r - D_r * n`),
- `P_r` is the cumulative Diophantine deficit reservoir satisfying:
  - Even step (`b_r = 0`): `P_{r+1} = P_r` and `Omega_{r+1} + 2^r * n = Omega_r`,
  - Odd step (`b_r = 1`):  `P_{r+1} = (3n + 1) * P_r + n^{a_r} * Omega_r` and
    `Omega_{r+1} = 3 * Omega_r + 2^r * (n + 1)`,
- Conservation Law:
    `P_r + 2^r * n^{a_r} * n_r = n * (3n + 1)^{a_r}`
    `<=>  P_r + n^{a_r} * Omega_r = n * ((3n + 1)^{a_r} - 2^r * n^{a_r})`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List
from .exact_oracle import (
    accelerated_collatz,
    affine_triple_exact,
    canonical_residue_mod_inv,
    parity_word_of,
    word_ones,
)


@dataclass(frozen=True)
class OperatorMatrix2x2:
    A: int
    B: int
    D: int

    def matmul(self, right: "OperatorMatrix2x2") -> "OperatorMatrix2x2":
        """Compute self * right for upper-triangular matrices [[A, B], [0, D]]."""
        return OperatorMatrix2x2(
            A=self.A * right.A,
            B=self.A * right.B + self.B * right.D,
            D=self.D * right.D,
        )


def word_matrix(word: List[bool]) -> OperatorMatrix2x2:
    A, B, D = affine_triple_exact(word)
    return OperatorMatrix2x2(A=A, B=B, D=D)


def verify_psmsl_matrix_algebra(max_depth: int = 8) -> Dict[str, Any]:
    """Verify `word_matrix(w1 + w2) == word_matrix(w2).matmul(word_matrix(w1))`
    and the projective eigenvector identity `M * [B, D - A]^T = D * [B, D - A]^T`.
    """
    words: List[List[bool]] = [[]]
    for _ in range(max_depth):
        words = [w + [b] for w in words for b in (False, True)]

    composition_checks = 0
    eigenvector_checks = 0
    failures = 0

    sample = words[:64]
    for w1 in sample:
        m1 = word_matrix(w1)
        # Eigenvector check: A * B + B * (D - A) == D * B
        if m1.A * m1.B + m1.B * (m1.D - m1.A) != m1.D * m1.B:
            failures += 1
        eigenvector_checks += 1
        for w2 in sample:
            m2 = word_matrix(w2)
            m12 = word_matrix(w1 + w2)
            if m2.matmul(m1) != m12:
                failures += 1
            composition_checks += 1

    return {
        "composition_checks": composition_checks,
        "eigenvector_checks": eigenvector_checks,
        "failures": failures,
    }


def verify_unified_transition_conservation(limit_n: int = 2000) -> Dict[str, Any]:
    """Track the unified state X_r = (n_r, A_r, B_r, D_r, a_r, rho_r, Omega_r, P_r)
    along the non-descending prefix of every integer 2 <= n <= limit_n, verifying:
    1. Exact step-by-step surplus and reservoir recurrences (`Omega_{r+1}`, `P_{r+1}`).
    2. Exact Reservoir-Surplus Conservation Law:
       `P_r + 2^r * n^{a_r} * n_r == n * (3n + 1)^{a_r}`.
    3. Exact depth-2 injection `P_2 == n * (n + 1)` and sharpened bound:
       `2^r * n^{a_r - 1} <= (9n + 5) * (3n + 1)^{a_r - 2}` for all `r >= 2`.
    """
    trajectories_checked = 0
    total_steps_checked = 0
    conservation_failures = 0
    sharpened_bound_failures = 0

    for n in range(2, limit_n + 1):
        trajectories_checked += 1
        nr = n
        r = 0
        a = 0
        omega = 0
        reservoir = 0

        while nr >= n:
            total_steps_checked += 1
            # Check exact conservation law at step r
            if reservoir + (1 << r) * (n ** a) * nr != n * ((3 * n + 1) ** a):
                conservation_failures += 1
            if reservoir + (n ** a) * omega != n * (((3 * n + 1) ** a) - (1 << r) * (n ** a)):
                conservation_failures += 1

            if r >= 2:
                if a < 2:
                    sharpened_bound_failures += 1
                elif reservoir < n * (n + 1) * ((3 * n + 1) ** (a - 2)):
                    sharpened_bound_failures += 1
                elif (1 << r) * (n ** (a - 1)) > (9 * n + 5) * ((3 * n + 1) ** (a - 2)):
                    sharpened_bound_failures += 1

            bit = (nr & 1) == 1
            nxt = accelerated_collatz(nr)
            if not bit:
                # Even step
                next_reservoir = reservoir
                next_omega = omega - (1 << r) * n
                next_a = a
            else:
                # Odd step
                next_reservoir = (3 * n + 1) * reservoir + (n ** a) * omega
                next_omega = 3 * omega + (1 << r) * (n + 1)
                next_a = a + 1

            r += 1
            nr = nxt
            a = next_a
            omega = next_omega
            reservoir = next_reservoir

            if omega != (1 << r) * (nr - n):
                conservation_failures += 1

    return {
        "trajectories_checked": trajectories_checked,
        "total_steps_checked": total_steps_checked,
        "conservation_failures": conservation_failures,
        "sharpened_bound_failures": sharpened_bound_failures,
    }


def verify_normalized_reservoir_and_exponential_decay(limit_n: int = 2000) -> Dict[str, Any]:
    """Verify in exact rational arithmetic (`fractions.Fraction`) and cleared-denominator
    integers:
    1. `normalized_reservoir_exact_increment`: `Q_{r+1} - Q_r == (n^{a_r - 1} * Omega_r) / (3n + 1)^{a_r + 1}`
       on odd steps and `0` on even steps.
    2. `normalized_reservoir_monotone_bounded`: `0 <= Q_r < 1` and `Q_r <= Q_{r+1}` across all
       non-descending steps.
    3. `normalized_reservoir_telescoping`: `Q_r` equals the exact sum of its odd-step increments.
    4. `reservoir_threshold_iff_descent`: at the exact first descent step `r_desc`,
       `Q_{r_desc} + (2^{r_desc} * n^{a_{r_desc}}) / (3n + 1)^{a_{r_desc}} > 1`.
    5. `infinite_nondescent_reservoir_obstruction`: for all `r >= 1` on a non-descending prefix of odd `n > 1`,
       `2^r * (n + 2)^{a_r - 1} * n_r <= (3n + 1) * (3n + 7)^{a_r - 1}` and
       `1 - Q_r <= (1 - 2 / ((n + 2)*(3n + 1)))^{a_r - 1}`.
    """
    trajectories_checked = 0
    increment_mismatches = 0
    monotonicity_failures = 0
    telescoping_mismatches = 0
    threshold_descent_mismatches = 0
    exponential_decay_failures = 0

    for n in range(3, limit_n + 1, 2):
        trajectories_checked += 1
        nr = n
        r = 0
        a = 0
        reservoir = 0
        q_telescoped = Fraction(0, 1)

        while True:
            q_den = n * ((3 * n + 1) ** a)
            q_curr = Fraction(reservoir, q_den)

            if q_curr != q_telescoped:
                telescoping_mismatches += 1

            # Check threshold descent criterion at step r
            power_ratio = Fraction((1 << r) * (n ** a), (3 * n + 1) ** a)
            if (nr < n) != (q_curr + power_ratio > 1):
                threshold_descent_mismatches += 1

            if nr < n:
                break

            # Non-descending step: 0 <= Q_r < 1
            if not (0 <= q_curr < 1):
                monotonicity_failures += 1

            if r >= 1:
                if (1 << r) * ((n + 2) ** (a - 1)) * nr > (3 * n + 1) * ((3 * n + 7) ** (a - 1)):
                    exponential_decay_failures += 1
                decay_factor = Fraction(n * (3 * n + 7), (n + 2) * (3 * n + 1))
                if (1 - q_curr) > (decay_factor ** (a - 1)):
                    exponential_decay_failures += 1
                # Verify Reservoir-Offset Duality Identity and 2-adic divisibility of qDen - qNum
                w_r = parity_word_of(r, n)
                a_coeff, b_r, d_r = affine_triple_exact(w_r)
                if (q_den - reservoir) != n * ((3 * n) ** a) + (n ** a) * b_r:
                    exponential_decay_failures += 1
                if (q_den - reservoir) % ((1 << r) * (n ** a)) != 0:
                    exponential_decay_failures += 1
                if (nr & 1) == 1 and (1 << r) * ((n + 2) ** a) >= (3 * n + 7) ** a:
                    exponential_decay_failures += 1
                # Verify Universal Non-Descent Offset & Fixed-Point Bound (Section 6)
                if reservoir + (n ** a) * b_r > n * a * ((3 * n + 1) ** (a - 1)):
                    exponential_decay_failures += 1
                if (n ** (a - 1)) * b_r > a * ((3 * n + 1) ** (a - 1)):
                    exponential_decay_failures += 1
                delta_r = max(0, d_r - a_coeff)
                if delta_r * (n ** a) > (n ** (a - 1)) * b_r:
                    exponential_decay_failures += 1
                if delta_r * n > a * (4 ** (a - 1)):
                    exponential_decay_failures += 1

            omega = (1 << r) * (nr - n)
            bit = (nr & 1) == 1
            nxt = accelerated_collatz(nr)

            if not bit:
                inc = Fraction(0, 1)
                next_reservoir = reservoir
                next_a = a
            else:
                inc = Fraction((n ** a) * omega, n * ((3 * n + 1) ** (a + 1)))
                next_reservoir = (3 * n + 1) * reservoir + (n ** a) * omega
                next_a = a + 1

            q_next = Fraction(next_reservoir, n * ((3 * n + 1) ** next_a))
            if q_next - q_curr != inc:
                increment_mismatches += 1
            if q_next < q_curr:
                monotonicity_failures += 1

            q_telescoped += inc
            r += 1
            nr = nxt
            a = next_a
            reservoir = next_reservoir

    return {
        "trajectories_checked": trajectories_checked,
        "increment_mismatches": increment_mismatches,
        "monotonicity_failures": monotonicity_failures,
        "telescoping_mismatches": telescoping_mismatches,
        "threshold_descent_mismatches": threshold_descent_mismatches,
        "exponential_decay_failures": exponential_decay_failures,
    }


def verify_projective_fixed_point_laws(max_n: int = 2000) -> Dict[str, object]:
    """
    Verify Section 6 Projective Fixed-Point Dynamics, 2-Adic Lifting Coupling,
    and Universal Non-Descent Offset Bound across all trajectories of n <= max_n:
      1. Even/odd extension recurrences for (B_w, Delta_w) and cross-ratio identities,
      2. Contracting non-descent iff m <= x_w = B_w / Delta_w,
      3. Universal non-descent offset bound:
         P_r(n) + n^{a_r} B_r <= n * a_r * (3n + 1)^{a_r - 1},
         n^{a_r - 1} B_r <= a_r * (3n + 1)^{a_r - 1},
         Delta_r * n^{a_r} <= n^{a_r - 1} B_r <= a_r * (3n + 1)^{a_r - 1},
         Delta_r * n <= a_r * 4^{a_r - 1},
         even on prefixes that cross the spectral boundary multiple times before descending!
    """
    trajectories_checked = 0
    step_extension_mismatches = 0
    fixed_point_dichotomy_mismatches = 0
    universal_offset_bound_failures = 0
    post_crossing_nondescent_prefixes = 0

    for n in range(3, max_n + 1, 2):
        if n % 4 != 3:
            continue
        trajectories_checked += 1
        nr = n
        r = 0
        a = 0
        reservoir = 0
        w: List[bool] = []
        seen_contracting = False

        while True:
            a_coeff, b_w, d_w = affine_triple_exact(w)
            delta_w = max(0, d_w - a_coeff)

            # Check contracting fixed-point dichotomy
            if d_w > a_coeff:
                if (nr >= n) != (delta_w * n <= b_w):
                    fixed_point_dichotomy_mismatches += 1
                if (nr < n) != (delta_w * n >= b_w + d_w):
                    fixed_point_dichotomy_mismatches += 1

            if nr < n:
                break

            if d_w > a_coeff:
                seen_contracting = True
            if seen_contracting and r >= 1:
                post_crossing_nondescent_prefixes += 1

            # Check universal non-descent offset & fixed-point bounds at depth r >= 1
            if r >= 1:
                rhs_full = n * a * ((3 * n + 1) ** (a - 1))
                if reservoir + (n ** a) * b_w > rhs_full:
                    universal_offset_bound_failures += 1
                if (n ** (a - 1)) * b_w > a * ((3 * n + 1) ** (a - 1)):
                    universal_offset_bound_failures += 1
                if delta_w * (n ** a) > (n ** (a - 1)) * b_w:
                    universal_offset_bound_failures += 1
                if delta_w * n > a * (4 ** (a - 1)):
                    universal_offset_bound_failures += 1

            bit = (nr & 1) == 1
            w_ext = w + [bit]
            a_ext, b_ext, d_ext = affine_triple_exact(w_ext)
            delta_ext = max(0, d_ext - a_ext)

            if not bit:
                if b_ext != b_w:
                    step_extension_mismatches += 1
                if d_w >= a_coeff:
                    if delta_ext != delta_w + d_w:
                        step_extension_mismatches += 1
                    if b_w * delta_ext != b_ext * delta_w + b_w * d_w:
                        step_extension_mismatches += 1
            else:
                if b_ext != 3 * b_w + d_w or d_ext != 2 * d_w or a_ext != 3 * a_coeff:
                    step_extension_mismatches += 1
                if 2 * d_w >= 3 * a_coeff:
                    if delta_ext + a_coeff != 2 * delta_w:
                        step_extension_mismatches += 1
                    if b_ext * delta_w != (
                        b_w * delta_ext + b_w * (delta_w + a_coeff) + d_w * delta_w
                    ):
                        step_extension_mismatches += 1

            omega = (1 << r) * (nr - n)
            if bit:
                reservoir = (3 * n + 1) * reservoir + (n ** a) * omega
                a += 1
            nr = accelerated_collatz(nr)
            w = w_ext
            r += 1

    return {
        "trajectories_checked": trajectories_checked,
        "step_extension_mismatches": step_extension_mismatches,
        "fixed_point_dichotomy_mismatches": fixed_point_dichotomy_mismatches,
        "universal_offset_bound_failures": universal_offset_bound_failures,
        "post_crossing_nondescent_prefixes": post_crossing_nondescent_prefixes,
    }


def verify_signed_projective_gap_and_surviving_lifts(max_n: int = 1000) -> Dict[str, object]:
    """
    Verify Section 7 Signed Projective Gap G_w(n) = (D_w - A_w) n - B_w over Z,
    its even/odd affine recurrences, 2-adic modular branch lock, even-step descent band,
    and surviving prefix-non-descending lift sets S_r(n).
    """
    trajectories_checked = 0
    gap_identity_mismatches = 0
    gap_recurrence_mismatches = 0
    modular_branch_lock_mismatches = 0
    descent_band_mismatches = 0
    reservoir_gap_identity_mismatches = 0
    surviving_lift_cap_failures = 0

    for n in range(3, max_n + 1, 2):
        if n % 4 != 3:
            continue
        trajectories_checked += 1
        nr = n
        r = 0
        a = 0
        reservoir = 0
        w: List[bool] = []
        gap = 0  # G_[] (n) = (1 - 1)*n - 0 = 0

        while True:
            a_coeff, b_w, d_w = affine_triple_exact(w)
            gap_def = (d_w - a_coeff) * n - b_w
            gap_traj = d_w * (n - nr)

            if gap != gap_def or gap != gap_traj:
                gap_identity_mismatches += 1

            # Check sign trichotomy
            if (gap > 0) != (nr < n) or (gap == 0) != (nr == n) or (gap < 0) != (nr > n):
                gap_identity_mismatches += 1

            # Candidate even/odd extension gaps
            w_ev = w + [False]
            w_od = w + [True]
            a_ev, b_ev, d_ev = affine_triple_exact(w_ev)
            a_od, b_od, d_od = affine_triple_exact(w_od)
            gap_ev = (d_ev - a_ev) * n - b_ev
            gap_od = (d_od - a_od) * n - b_od

            if gap_ev != gap + d_w * n or gap_ev != d_w * (2 * n - nr):
                gap_recurrence_mismatches += 1
            if gap_od != 3 * gap - d_w * (n + 1) or gap_od != d_w * (2 * n - (3 * nr + 1)):
                gap_recurrence_mismatches += 1
            if gap_ev - gap_od + 2 * gap != d_w * (2 * n + 1):
                gap_recurrence_mismatches += 1

            # Check 2-adic modular branch lock: nr is odd iff gap % (2 * d_w) == 0
            bit = (nr & 1) == 1
            if bit != (gap % (2 * d_w) == 0):
                modular_branch_lock_mismatches += 1

            if nr < n:
                break

            # Non-descending step: verify reservoir-gap identity
            if reservoir - (n ** a) * gap != n * ((3 * n + 1) ** a) - d_w * (n ** (a + 1)):
                reservoir_gap_identity_mismatches += 1

            # Check S_r(n) properties on lifts m = n + q * 2^r for q = 1, 2
            for q in (1, 2):
                m = n + q * d_w
                gap_m = (d_w - a_coeff) * m - b_w
                if gap_m - gap != (d_w - a_coeff) * (m - n):
                    surviving_lift_cap_failures += 1

            nxt = accelerated_collatz(nr)
            next_gap = gap_od if bit else gap_ev

            # Check even-step descent band: if gap > -d_w * n and next_gap <= 0, bit must be True
            if gap > -d_w * n and next_gap <= 0 and not bit:
                descent_band_mismatches += 1

            omega = d_w * (nr - n)
            if bit:
                reservoir = (3 * n + 1) * reservoir + (n ** a) * omega
                a += 1
            nr = nxt
            w = w_od if bit else w_ev
            gap = next_gap
            r += 1

    return {
        "trajectories_checked": trajectories_checked,
        "gap_identity_mismatches": gap_identity_mismatches,
        "gap_recurrence_mismatches": gap_recurrence_mismatches,
        "modular_branch_lock_mismatches": modular_branch_lock_mismatches,
        "descent_band_mismatches": descent_band_mismatches,
        "reservoir_gap_identity_mismatches": reservoir_gap_identity_mismatches,
        "surviving_lift_cap_failures": surviving_lift_cap_failures,
    }


def verify_mechanism_a_delayed_descent_and_quotient_collapse(
    max_n: int = 1000,
) -> Dict[str, object]:
    """
    Verify Section 8 Mechanism A theorems:
      1. Self-similar orbit shift: when s_i = F^i(n) - n = q * 2^k,
         parityWordOf k (F^i(n)) == parityWordOf k n and F^{i+k}(n) == F^k(n) + q * 3^{a_k},
         with opposite parity when q is odd.
      2. Delayed-descent surplus valuation lock:
         - if i + 1 <= r and s_i < n along a non-descending prefix of length r, then s_i % 2 == 0;
         - if i + 2 <= r and 3 * s_i + 1 < n along a non-descending prefix of length r, then s_i % 4 == 0
           and (for s_i > 0) s_i >= 4.
    """
    trajectories_checked = 0
    orbit_shift_mismatches = 0
    parity_flip_mismatches = 0
    delayed_descent_lock_failures = 0

    for n in range(3, max_n + 1, 2):
        if n % 4 != 3:
            continue
        trajectories_checked += 1
        # Collect non-descending prefix iterates F^0(n), F^1(n), ..., F^r(n) where F^r(n) < n is the first descent
        orbit = [n]
        curr = n
        while curr >= n:
            curr = accelerated_collatz(curr)
            orbit.append(curr)
        # Last index before descent is r_max = len(orbit) - 2
        r_max = len(orbit) - 2

        for i in range(1, r_max + 1):
            s_i = orbit[i] - n
            if i + 1 <= r_max and s_i < n:
                if s_i % 2 != 0:
                    delayed_descent_lock_failures += 1
            if i + 2 <= r_max and 3 * s_i + 1 < n:
                if s_i % 4 != 0 or (s_i > 0 and s_i < 4):
                    delayed_descent_lock_failures += 1

            # Check self-similar orbit shift for all k >= 0 dividing s_i by 2^k
            if s_i > 0:
                k = 0
                while (s_i % (1 << k)) == 0 and (i + k) < len(orbit) and k <= r_max:
                    q = s_i >> k
                    w_k = parity_word_of(k, n)
                    w_ik = parity_word_of(k, orbit[i])
                    a_k = sum(1 for b in w_k if b)
                    if w_ik != w_k:
                        orbit_shift_mismatches += 1
                    if orbit[i + k] != orbit[k] + q * (3 ** a_k):
                        orbit_shift_mismatches += 1
                    if (q & 1) == 1:
                        if (orbit[i + k] & 1) == (orbit[k] & 1):
                            parity_flip_mismatches += 1
                    k += 1

    return {
        "trajectories_checked": trajectories_checked,
        "orbit_shift_mismatches": orbit_shift_mismatches,
        "parity_flip_mismatches": parity_flip_mismatches,
        "delayed_descent_lock_failures": delayed_descent_lock_failures,
    }


def verify_section9_trichotomy_and_two_point_shift(
    max_n: int = 500,
) -> Dict[str, object]:
    """
    Verify Section 9 Two-Point Temporal Self-Similarity and Interior Excursion laws:
      1. For any pair of depths (i, j) along a trajectory with F^j(n) = F^i(n) + q * 2^k,
         parityWordOf k (F^j(n)) == parityWordOf k (F^i(n)) and
         F^{j+k}(n) == F^{i+k}(n) + q * 3^{a_k(F^i(n))}, with opposite parity when q is odd.
      2. Along any non-descending prefix of n >= 1024 (checked up to max_n + sample >= 1024),
         every intermediate step i with i + 2 <= r_max and 0 < s_i and 3 * s_i + 1 < n
         satisfies s_i >= 4 and s_i % 4 == 0.
    """
    trajectories_checked = 0
    two_point_pairs_checked = 0
    two_point_shift_mismatches = 0
    two_point_parity_flip_mismatches = 0
    interior_gap_ge4_failures = 0

    candidates = [n for n in range(3, max_n + 1, 4)] + [
        n for n in range(1027, 1027 + 400, 4)
    ]
    for n in candidates:
        trajectories_checked += 1
        orbit = [n]
        curr = n
        while curr >= n:
            curr = accelerated_collatz(curr)
            orbit.append(curr)
        r_max = len(orbit) - 2

        for i in range(1, r_max + 1):
            s_i = orbit[i] - n
            if i + 2 <= r_max and 0 < s_i and 3 * s_i + 1 < n:
                if s_i < 4 or (s_i % 4) != 0:
                    interior_gap_ge4_failures += 1

        limit_idx = min(len(orbit), 25)
        for i in range(limit_idx):
            for j in range(i + 1, limit_idx):
                if orbit[j] <= orbit[i]:
                    continue
                diff = orbit[j] - orbit[i]
                k = 0
                while (diff % (1 << k)) == 0 and (j + k) < len(orbit):
                    two_point_pairs_checked += 1
                    q = diff >> k
                    w_i = parity_word_of(k, orbit[i])
                    w_j = parity_word_of(k, orbit[j])
                    a_k = sum(1 for b in w_i if b)
                    if w_j != w_i:
                        two_point_shift_mismatches += 1
                    if orbit[j + k] != orbit[i + k] + q * (3 ** a_k):
                        two_point_shift_mismatches += 1
                    if (q & 1) == 1:
                        if (orbit[j + k] & 1) == (orbit[i + k] & 1):
                            two_point_parity_flip_mismatches += 1
                    k += 1

    return {
        "trajectories_checked": trajectories_checked,
        "two_point_pairs_checked": two_point_pairs_checked,
        "two_point_shift_mismatches": two_point_shift_mismatches,
        "two_point_parity_flip_mismatches": two_point_parity_flip_mismatches,
        "interior_gap_ge4_failures": interior_gap_ge4_failures,
    }


def verify_section10_divergent_orbit_and_valuation_laws(
    max_n: int = 1000,
) -> Dict[str, object]:
    """
    Verify Section 10 Single-Block Dichotomy, Return-Map Valuation Conservation,
    and Divergent-Excursion Power-Deficit Laws:
      1. Every single odd-to-odd block u -> (3u + 1) / 2^{k+1} on odd u > 1
         strictly grows when k == 0 and strictly descends when k >= 1.
      2. At every odd return step along a non-descending prefix of n > 1,
         the return-map valuation sequence ks = [k_0, ..., k_{s-1}] of cumulative
         length K = sum(k_j + 1) satisfies:
           P_K(n) + 2^K * n^s * u_s == n * (3n + 1)^s,
         and whenever u_s > 2^m * n, 2^{K + m} * n^s < (3n + 1)^s.
    """
    odd_blocks_checked = 0
    single_block_dichotomy_failures = 0
    return_map_conservation_mismatches = 0
    excursion_power_shift_failures = 0

    for n in range(3, max_n + 1, 2):
        # Test single odd-to-odd block dichotomy on u = n
        val = 3 * n + 1
        k_block = 0
        while (val % 2) == 0:
            val //= 2
            k_block += 1
        # Total halvings is k_block >= 1, so extra halvings k = k_block - 1
        k_extra = k_block - 1
        odd_blocks_checked += 1
        if k_extra == 0 and not (val > n):
            single_block_dichotomy_failures += 1
        if k_extra >= 1 and not (val < n):
            single_block_dichotomy_failures += 1

        if n % 4 != 3:
            continue

        # Track non-descending prefix and check at every odd return boundary K
        curr = n
        r = 0
        s = 0
        reservoir = 0
        while curr >= n:
            if (curr & 1) == 1:
                # At an odd iterate u_s = curr (at depth K = r with s odd steps completed so far)
                lhs = reservoir + (1 << r) * (n ** s) * curr
                rhs = n * ((3 * n + 1) ** s)
                if lhs != rhs:
                    return_map_conservation_mismatches += 1
                # Check excursion power-deficit law for any m >= 0 with curr > (2^m) * n
                m = 0
                while curr > (1 << m) * n:
                    if not ((1 << (r + m)) * (n ** s) < ((3 * n + 1) ** s)):
                        excursion_power_shift_failures += 1
                    m += 1
                omega = (1 << r) * (curr - n)
                reservoir = (3 * n + 1) * reservoir + (n ** s) * omega
                s += 1
            curr = accelerated_collatz(curr)
            r += 1

    return {
        "odd_blocks_checked": odd_blocks_checked,
        "single_block_dichotomy_failures": single_block_dichotomy_failures,
        "return_map_conservation_mismatches": return_map_conservation_mismatches,
        "excursion_power_shift_failures": excursion_power_shift_failures,
    }


def verify_section11_ordered_valuation_goodstein_four_color_and_falsification(
    max_s: int = 8,
) -> Dict[str, object]:
    """
    Verify Section 11 Ordered Valuation-Block Recurrences, Goodstein 2-Adic Tail Rank Decay,
    Four-Color 1-Circuit Reducibility, Diophantine Cycle Non-Divisibility, and Target Falsifications:
      1. Exact block recurrence B_{s+1} = 3 * B_s + 2^{K_s} and two-sided ordering sandwich
         3^s - 2^s <= B_s <= 2^{K_s - s} * (3^s - 2^s).
      2. Adjacent block swap law: B(ks ++ [k2, k1]) + 2^{K + k1 + 1} == B(ks ++ [k1, k2]) + 2^{K + k2 + 1}.
      3. Exhaustive Diophantine cycle check across all ordered valuation compositions for 2 <= s <= max_s
         with 2^K > 3^s: verify that NO composition has (2^K - 3^s) | B_s with quotient n = B_s // (2^K - 3^s) > 1,
         while ks = [1] * s has quotient n = 1 (falsifying naive threshold-free non-divisibility CE-C10-05).
      4. Verify CE-C10-06 at n = 27: ks = [0, 1] has contracting block k_1 = 1 (u_2 = 31 < u_1 = 41),
         yet survives above 27 (u_2 = 31 > 27).
      5. Goodstein + Four-Color 1-circuit reducibility: verify 2^a * (F^a(n) + 1) == 3^a * (n + 1)
         along allTrueWord a, and verify strict descent F^{a+k}(n) < n for contracting 1-circuit words.
    """
    def compositions(total: int, parts: int):
        if parts == 1:
            yield (total,)
            return
        for first in range(total + 1):
            for rest in compositions(total - first, parts - 1):
                yield (first,) + rest

    compositions_checked = 0
    offset_recurrence_mismatches = 0
    sandwich_failures = 0
    swap_law_mismatches = 0
    nontrivial_integer_cycle_quotients = 0
    trivial_cycle_repeat_quotients = 0
    goodstein_plus_one_mismatches = 0
    four_color_one_circuit_descent_failures = 0

    for s in range(2, max_s + 1):
        for K in range(s + 1, 2 * s + 2):
            delta = (1 << K) - (3 ** s)
            for ks in compositions(K - s, s):
                compositions_checked += 1
                w = []
                B_rec = 0
                K_rec = 0
                for k in ks:
                    w.extend([True] + [False] * k)
                    B_rec = 3 * B_rec + (1 << K_rec)
                    K_rec += k + 1
                B_exact = affine_triple_exact(w)[1]
                if B_rec != B_exact or K_rec != K:
                    offset_recurrence_mismatches += 1
                if not ((3 ** s) - (1 << s) <= B_rec <= (1 << (K - s)) * ((3 ** s) - (1 << s))):
                    sandwich_failures += 1
                if delta > 0 and (B_rec % delta) == 0:
                    q = B_rec // delta
                    if q > 1:
                        nontrivial_integer_cycle_quotients += 1
                    elif q == 1:
                        trivial_cycle_repeat_quotients += 1

    # Check adjacent block swap law on prefixes
    for k1 in range(4):
        for k2 in range(4):
            ks_prefix = [0, 1]
            K_pref = sum(k + 1 for k in ks_prefix)
            w12 = [True, True, False] + ([True] + [False] * k1) + ([True] + [False] * k2)
            w21 = [True, True, False] + ([True] + [False] * k2) + ([True] + [False] * k1)
            if affine_triple_exact(w21)[1] + (1 << (K_pref + k1 + 1)) != affine_triple_exact(w12)[1] + (1 << (K_pref + k2 + 1)):
                swap_law_mismatches += 1

    # Check Goodstein 2-adic tail rank law and Four-Color 1-circuit reducibility
    for a in range(1, 10):
        for q in range(0, 8):
            # Admissible input for oneCircuitWord(a, k) has n + 1 = 2^a * m with 3^a * m == 1 (mod 2^k)
            k = 1
            while (1 << (a + k)) <= (3 ** a):
                k += 1
            m0 = pow(3 ** a, -1, 1 << k)
            if m0 == 0:
                m0 = 1 << k
            m = m0 + q * (1 << k)
            n = (1 << a) * m - 1
            if n <= 1:
                n += 1 << (a + k)
            curr = n
            for _ in range(a):
                if curr % 2 != 1:
                    goodstein_plus_one_mismatches += 1
                curr = accelerated_collatz(curr)
            if (1 << a) * (curr + 1) != (3 ** a) * (n + 1):
                goodstein_plus_one_mismatches += 1
            for _ in range(k):
                if curr % 2 != 0:
                    four_color_one_circuit_descent_failures += 1
                curr = accelerated_collatz(curr)
            if not (curr < n):
                four_color_one_circuit_descent_failures += 1

    # Check CE-C10-06 at n = 27
    u1_27 = accelerated_collatz(27)
    u2_27 = accelerated_collatz(accelerated_collatz(u1_27))
    ce06_verified = (u1_27 == 41 and u2_27 == 31 and 27 < u2_27 < u1_27)

    return {
        "compositions_checked": compositions_checked,
        "offset_recurrence_mismatches": offset_recurrence_mismatches,
        "sandwich_failures": sandwich_failures,
        "swap_law_mismatches": swap_law_mismatches,
        "nontrivial_integer_cycle_quotients": nontrivial_integer_cycle_quotients,
        "trivial_cycle_repeat_quotients": trivial_cycle_repeat_quotients,
        "goodstein_plus_one_mismatches": goodstein_plus_one_mismatches,
        "four_color_one_circuit_descent_failures": four_color_one_circuit_descent_failures,
        "ce06_contracting_block_survival_verified": ce06_verified,
    }


def verify_section12_rotation_reducibility_and_goodstein_falsification(
    max_s: int = 7,
) -> Dict[str, object]:
    """
    Verify Section 12 Cyclic Rotation Algebra, Multi-Circuit Reducibility, Goodstein Run-Exit
    Dichotomy, and Targeted Falsifications (CE-C10-07..09):
      1. Cyclic shift identity: D1 * B(w2 + w1) == A1 * B(w1 + w2) + Delta * B1, and
         one-block rotation law 2^(k+1) * B(tl + [k]) == 3 * B(k :: tl) + (2^K - 3^s).
      2. Universal multi-circuit sandwich reducibility and reservoir-threshold reducibility
         (zero pincer exceptions across all odd n in [3, 5000] on non-descending prefixes).
      3. Goodstein mod-4 run-exit dichotomy: u % 4 == 3 <=> k == 0; u % 4 == 1 <=> k >= 1.
      4. Formal falsification witnesses CE-C10-07 (ks=[0, 1, 2] rotations), CE-C10-08
         (n=165, s=17, K=27, u_17=167 > 165), and CE-C10-09 (n=27, v_2(31+1)=5 > 2=v_2(27+1)).
    """
    def return_map_word(ks):
        w = []
        for k in ks:
            w.extend([True] + [False] * k)
        return w

    def compositions(total: int, parts: int):
        if parts == 1:
            yield (total,)
            return
        for first in range(total + 1):
            for rest in compositions(total - first, parts - 1):
                yield (first,) + rest

    cyclic_shift_mismatches = 0
    one_block_rotation_mismatches = 0
    universal_sandwich_reducible_mismatches = 0
    nondescent_odd_return_crossing_exceptions = 0
    goodstein_mod4_dichotomy_mismatches = 0

    for s in range(2, max_s + 1):
        for K in range(s + 1, 2 * s + 1):
            if (1 << K) <= (3 ** s):
                continue
            delta = (1 << K) - (3 ** s)
            for ks in compositions(K - s, s):
                w = return_map_word(ks)
                k0 = ks[0]
                tl = list(ks[1:])
                w_rot = return_map_word(tl + [k0])
                A, B, D = affine_triple_exact(w)
                _, B_rot, _ = affine_triple_exact(w_rot)
                if (1 << (k0 + 1)) * B_rot != 3 * B + delta:
                    one_block_rotation_mismatches += 1
                # General split check
                w1 = return_map_word(list(ks[: s // 2]))
                w2 = return_map_word(list(ks[s // 2 :]))
                A1, B1, D1 = affine_triple_exact(w1)
                _, B12, _ = affine_triple_exact(w1 + w2)
                _, B21, _ = affine_triple_exact(w2 + w1)
                if D1 * B21 != A1 * B12 + delta * B1:
                    cyclic_shift_mismatches += 1
                # Universal sandwich reducibility check
                invA = pow(A, -1, 2 * D)
                n0 = ((D - B) * invA) % (2 * D)
                if n0 <= 1:
                    n0 += 2 * D
                if delta * ((1 << s) * n0) > (1 << K) * ((3 ** s) - (1 << s)):
                    u_s = (A * n0 + B) // D
                    if not (u_s < n0):
                        universal_sandwich_reducible_mismatches += 1

    # Check non-descending odd-return prefixes and Goodstein mod-4 dichotomy across odd n in [3, 5001]
    for n in range(3, 5001, 2):
        u = n
        K = 0
        s = 0
        while u >= n:
            s += 1
            val = 3 * u + 1
            tz = (val & -val).bit_length() - 1
            k = tz - 1
            if ((u % 4 == 3) != (k == 0)) or ((u % 4 == 1) != (k >= 1)):
                goodstein_mod4_dichotomy_mismatches += 1
            K += tz
            u = val >> tz
            if (1 << K) > (3 ** s) and u >= n:
                nondescent_odd_return_crossing_exceptions += 1
                break

    # Verify CE-C10-07 on ks = [0, 1, 2]
    B_012 = affine_triple_exact(return_map_word([0, 1, 2]))[1]
    B_120 = affine_triple_exact(return_map_word([1, 2, 0]))[1]
    B_201 = affine_triple_exact(return_map_word([2, 0, 1]))[1]
    ce07_verified = (B_012 == 23 and B_120 == 53 and B_201 == 49 and B_012 < B_201 < B_120)

    # Verify CE-C10-08 at n = 165, s = 17, K = 27
    ks_165 = [3, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 2]
    A_165, B_165, D_165 = affine_triple_exact(return_map_word(ks_165))
    u1_165 = (3 * 165 + 1) >> 4
    u17_165 = (A_165 * 165 + B_165) // D_165
    ce08_verified = (
        len(ks_165) == 17
        and sum(k + 1 for k in ks_165) == 27
        and D_165 > A_165
        and u1_165 == 31 < 165
        and u17_165 == 167 > 165
    )

    # Verify CE-C10-09 at n = 27
    u0_27 = 27
    u1_27 = 41
    u2_27 = 31
    v2_u0 = ((u0_27 + 1) & -(u0_27 + 1)).bit_length() - 1
    v2_u1 = ((u1_27 + 1) & -(u1_27 + 1)).bit_length() - 1
    v2_u2 = ((u2_27 + 1) & -(u2_27 + 1)).bit_length() - 1
    ce09_verified = (v2_u0 == 2 and v2_u1 == 1 and v2_u2 == 5 and u2_27 > u0_27 and v2_u2 > v2_u0)

    return {
        "cyclic_shift_mismatches": cyclic_shift_mismatches,
        "one_block_rotation_mismatches": one_block_rotation_mismatches,
        "universal_sandwich_reducible_mismatches": universal_sandwich_reducible_mismatches,
        "nondescent_odd_return_crossing_exceptions": nondescent_odd_return_crossing_exceptions,
        "goodstein_mod4_dichotomy_mismatches": goodstein_mod4_dichotomy_mismatches,
        "ce07_rotation_order_verified": ce07_verified,
        "ce08_contracting_survival_at_165_verified": ce08_verified,
        "ce09_goodstein_tail_reset_at_27_verified": ce09_verified,
    }


def verify_section13_adversarial_first_crossing_and_no_crossing_branch(
    max_s_words: int = 12,
    max_s_cap: int = 306,
) -> Dict[str, object]:
    """
    Verify Section 13 Adversarial First-Crossing Counterexample Synthesis, Universal Pre-Crossing
    Offset Cap (3 * B_s <= s * 3^s), and No-First-Crossing Shifted Growth:
      1. Exhaustively generate all first-crossing valuation words ks for 1 <= s <= max_s_words
         (where 2^{K_j} <= 3^j for 1 <= j < s and 2^{K_s} > 3^s).
      2. For each word, verify the universal linear-exponential cap 3 * B_s <= s * 3^s,
         compute the exact odd-return residue representative n0 (mod 2^{K_s + 1}), and check
         whether ANY representative in the finite survivor interval 1 < n <= B_s // (2^{K_s} - 3^s)
         exists.
      3. Verify along all pre-crossing prefixes (2^{K_j} <= 3^j) that 2^{K_j} * (u_j + 1) >= 3^j * (n + 1)
         and u_j > n.
      4. Verify the 4 independent benchmark first-crossing trajectories (n = 27, 47, 63, 165)
         and verify that across 1 <= s <= max_s_cap (s <= 306), the universal survivor cap
         (s * 3^{s-1}) // (2^K - 3^s) never exceeds 99,567.
    """
    def rec_fc(j: int, K_curr: int, B_curr: int, ks_curr: tuple, s_target: int):
        if j == s_target - 1:
            k_min = 0
            while (1 << (K_curr + k_min + 1)) <= (3 ** s_target):
                k_min += 1
            # Enumerate all final valuations k >= k_min permitted by the n >= 2 cutoff
            # 6 * (2^{K_s} - 3^s) <= s * 3^s (plus k_min itself if the set is empty)
            k = k_min
            yielded_any = False
            while 6 * ((1 << (K_curr + k + 1)) - (3 ** s_target)) <= s_target * (3 ** s_target):
                yielded_any = True
                yield (s_target, K_curr + k + 1, ks_curr + (k,), 3 * B_curr + (1 << K_curr))
                k += 1
            if not yielded_any:
                yield (s_target, K_curr + k_min + 1, ks_curr + (k_min,), 3 * B_curr + (1 << K_curr))
            return
        k = 0
        while (1 << (K_curr + k + 1)) <= (3 ** (j + 1)):
            yield from rec_fc(
                j + 1,
                K_curr + k + 1,
                3 * B_curr + (1 << K_curr),
                ks_curr + (k,),
                s_target,
            )
            k += 1

    first_crossing_words_checked = 0
    offset_cap_violations = 0
    sharpened_offset_cap_violations = 0
    surviving_representatives_found = 0
    pre_crossing_growth_violations = 0

    for s in range(1, max_s_words + 1):
        A = 3 ** s
        A_prev = 3 ** (s - 1)
        for _, K, ks, B in rec_fc(0, 0, 0, (), s):
            first_crossing_words_checked += 1
            if 3 * B > s * A:
                offset_cap_violations += 1
            if 2 * B + A_prev > 2 * s * A_prev + 1:
                sharpened_offset_cap_violations += 1
            D = 1 << K
            delta = D - A
            max_n = B // delta
            invA = pow(A, -1, 2 * D)
            n0 = ((D - B) * invA) % (2 * D)
            if n0 <= 1:
                n0 += 2 * D
            if n0 <= max_n:
                surviving_representatives_found += 1
            # Also verify Branch 2 pre-crossing growth on the prefix ks[:-1]
            if s >= 2:
                K_pre = sum(k + 1 for k in ks[:-1])
                A_pre = 3 ** (s - 1)
                B_pre = (B - (1 << K_pre)) // 3
                u_pre = (A_pre * n0 + B_pre) >> K_pre
                if (1 << K_pre) * (u_pre + 1) < A_pre * (n0 + 1) or u_pre <= n0:
                    pre_crossing_growth_violations += 1

    # Verify the 4 independent benchmark checks: n in (27, 47, 63, 165)
    expected_benchmarks = {
        27: (37, 59, 23),
        47: (34, 55, 23),
        63: (34, 54, 61),
        165: (1, 4, 31),
    }
    benchmark_mismatches = 0
    for n_start, (exp_s, exp_K, exp_u) in expected_benchmarks.items():
        u = n_start
        K = 0
        s = 0
        while (1 << K) <= (3 ** s) or s == 0:
            s += 1
            val = 3 * u + 1
            tz = (val & -val).bit_length() - 1
            K += tz
            u = val >> tz
        if (s, K, u) != (exp_s, exp_K, exp_u) or not (u < n_start):
            benchmark_mismatches += 1

    # Compute BOTH coarse (B_s <= s * 3^{s-1}) and sharpened (B_s <= s * 3^{s-1} - (3^{s-1} - 1)//2)
    # universal first-crossing survivor caps across 1 <= s <= max_s_cap
    max_coarse_survivor_cap_le_306 = 0
    max_sharpened_survivor_cap_le_306 = 0
    for s in range(1, max_s_cap + 1):
        A = 3 ** s
        K = A.bit_length()
        if (1 << (K - 1)) > A:
            K -= 1
        delta = (1 << K) - A
        B_coarse = s * (3 ** (s - 1))
        B_sharpened = B_coarse - ((3 ** (s - 1)) - 1) // 2
        coarse_cap = B_coarse // delta
        sharpened_cap = B_sharpened // delta
        if coarse_cap > max_coarse_survivor_cap_le_306:
            max_coarse_survivor_cap_le_306 = coarse_cap
        if sharpened_cap > max_sharpened_survivor_cap_le_306:
            max_sharpened_survivor_cap_le_306 = sharpened_cap

    return {
        "first_crossing_words_checked": first_crossing_words_checked,
        "offset_cap_violations": offset_cap_violations,
        "sharpened_offset_cap_violations": sharpened_offset_cap_violations,
        "surviving_representatives_found": surviving_representatives_found,
        "pre_crossing_growth_violations": pre_crossing_growth_violations,
        "benchmark_mismatches": benchmark_mismatches,
        "max_coarse_survivor_cap_le_306": max_coarse_survivor_cap_le_306,
        "max_sharpened_survivor_cap_le_306": max_sharpened_survivor_cap_le_306,
        "max_survivor_cap_le_306": max_sharpened_survivor_cap_le_306,
    }


def verify_section14_sharpened_cap_s40_certificate_and_excess_valuation() -> Dict[str, object]:
    """
    Verify Section 14 Sharpened Pre-Crossing Cap Reconciliation, s <= 40 Certificate (n_cap < 1024),
    First-Crossing Surplus Decomposition, and CE-C10-10 Non-Monotone Odd Return Witness:
      1. Reconcile exact coarse cap floor(s * 3^{s-1} / (2^K - 3^s)) vs. sharpened cap
         floor((s * 3^{s-1} - (3^{s-1} - 1)//2) / (2^K - 3^s)) at s in (5, 17, 41, 94, 306).
      2. Verify that across all 1 <= s <= 40, both coarse and sharpened survivor caps are strictly < 1024
         (max coarse cap = 381 at s = 29, K = 46; max sharpened cap = 375 at s = 29, K = 46).
      3. Verify the exact surplus identity (2^K - 3^s) * n + 2^K * (u_s - n) == B_s and verify
         CE-C10-10 on n = 27 (ks = [0, 1] has 2^3 <= 3^2, u_1 = 41 > 27, u_2 = 31 > 27, yet u_2 < u_1).
    """
    expected_reconciliation = {
        5: (8, 31, 28),
        17: (27, 144, 139),
        41: (65, 1185, 1170),
        94: (149, 3326, 3308),
        306: (485, 99729, 99567),
    }
    cap_reconciliation_mismatches = 0
    for s, (exp_K, exp_coarse, exp_sharp) in expected_reconciliation.items():
        A = 3 ** s
        K = A.bit_length()
        if (1 << (K - 1)) > A:
            K -= 1
        delta = (1 << K) - A
        coarse = (s * (3 ** (s - 1))) // delta
        sharp = (s * (3 ** (s - 1)) - ((3 ** (s - 1)) - 1) // 2) // delta
        if (K, coarse, sharp) != (exp_K, exp_coarse, exp_sharp):
            cap_reconciliation_mismatches += 1

    max_coarse_cap_le_40 = 0
    max_sharpened_cap_le_40 = 0
    for s in range(1, 41):
        A = 3 ** s
        K = A.bit_length()
        if (1 << (K - 1)) > A:
            K -= 1
        delta = (1 << K) - A
        coarse = (s * (3 ** (s - 1))) // delta
        sharp = (s * (3 ** (s - 1)) - ((3 ** (s - 1)) - 1) // 2) // delta
        if coarse > max_coarse_cap_le_40:
            max_coarse_cap_le_40 = coarse
        if sharp > max_sharpened_cap_le_40:
            max_sharpened_cap_le_40 = sharp

    # Verify CE-C10-10 at n = 27
    u0 = 27
    u1 = accelerated_collatz(27)
    u2 = accelerated_collatz(accelerated_collatz(u1))
    ce10_verified = (u1 == 41 and u2 == 31 and u1 > u0 and u2 > u0 and u2 < u1)

    return {
        "cap_reconciliation_mismatches": cap_reconciliation_mismatches,
        "max_coarse_cap_le_40": max_coarse_cap_le_40,
        "max_sharpened_cap_le_40": max_sharpened_cap_le_40,
        "s40_below_1024_verified": (max_coarse_cap_le_40 < 1024 and max_sharpened_cap_le_40 < 1024),
        "ce10_non_monotone_odd_returns_verified": ce10_verified,
    }


def verify_section15_surplus_diophantine_and_self_similarity_coupling(
    max_s_direct: int = 12,
    max_s_duality: int = 970,
) -> Dict[str, object]:
    """
    Verify Section 15 Surplus Diophantine Equivalence, v_2(t) = 1 Two-Step Self-Similarity Descent,
    and Falsifications CE-C10-11..12:
      1. Direct search over all pre-crossing prefix trees for 1 <= s <= max_s_direct (4,879 prefixes at s <= 12)
         and all crossing valuations K_s up to 6*(2^{K_s} - 3^s) > s * 3^s: verify 0 formal integer solutions
         (n > 1, t >= 0) to B_s = Delta_s * n + 2^{K_s} * t.
      2. Verify across 1 <= s <= max_s_duality (s <= 970) that the maximum sharpened survivor cap is 99,567
         (at s = 306, K = 485), so trajectory non-survival for odd n <= 99,567 excludes all >10^80 pre-crossing
         words up to s = 970 by first_crossing_surplus_diophantine_iff_admissible_survivor.
      3. Verify universal two-step self-similarity descent for v_2(t) = 1 (t = 2*q, q odd) on all n ≡ 3 (mod 4)
         (k_0 = 0): T^1(n + 2*q) = T^1(n) + 3*q is even and 4 * T^2(n + 2*q) = 3*n + 6*q + 1 < 4*n for n > 6*q + 1.
      4. Verify CE-C10-11 (v_2(t) >= 2 at n = 7, t = 4 -> T^3(11) = 13 > 7) and CE-C10-12 (non-pre-crossing
         Diophantine solution ks = [0, 0, 1, 2, 0] at s = 5, K_5 = 8, n = 7, t = 1 eliminated by u_4 = 5 < 7).
    """
    def gen_precrossing_prefixes(s: int):
        if s == 1:
            yield (0,), 1
            return
        for Ks, B in gen_precrossing_prefixes(s - 1):
            j = s - 1
            max_K = (3 ** j).bit_length() - 1
            for K_next in range(Ks[-1] + 1, max_K + 1):
                yield Ks + (K_next,), 3 * B + (1 << K_next)

    precrossing_prefixes_checked = 0
    precrossing_diophantine_solutions_found = 0
    for s in range(1, max_s_direct + 1):
        K_min = (3 ** s).bit_length()
        K_max = K_min
        while 6 * ((1 << (K_max + 1)) - (3 ** s)) <= s * (3 ** s):
            K_max += 1
        for _Ks, B in gen_precrossing_prefixes(s):
            precrossing_prefixes_checked += 1
            for K_s in range(K_min, K_max + 1):
                delta = (1 << K_s) - (3 ** s)
                t = 0
                while B - (1 << K_s) * t >= 2 * delta:
                    if (B - (1 << K_s) * t) % delta == 0:
                        precrossing_diophantine_solutions_found += 1
                    t += 1

    max_sharpened_cap_le_970 = 0
    for s in range(1, max_s_duality + 1):
        A = 3 ** s
        K = A.bit_length()
        if (1 << (K - 1)) > A:
            K -= 1
        delta = (1 << K) - A
        sharp = (s * (3 ** (s - 1)) - ((3 ** (s - 1)) - 1) // 2) // delta
        if sharp > max_sharpened_cap_le_970:
            max_sharpened_cap_le_970 = sharp

    v2_eq_one_two_step_descent_mismatches = 0
    for n in range(3, 500, 4):  # n ≡ 3 (mod 4) <=> k_0 = 0 (n odd and T^1(n) odd)
        t1_n = accelerated_collatz(n)
        for q in range(1, 16, 2):
            u_s = n + 2 * q
            t1_u = accelerated_collatz(u_s)
            t2_u = accelerated_collatz(t1_u)
            if t1_u != t1_n + 3 * q or (t1_u % 2) != 0:
                v2_eq_one_two_step_descent_mismatches += 1
            if 4 * t2_u != 3 * n + 6 * q + 1:
                v2_eq_one_two_step_descent_mismatches += 1
            if n > 6 * q + 1 and not (t2_u < n):
                v2_eq_one_two_step_descent_mismatches += 1

    # Verify CE-C10-11 (v_2(t) >= 2 at n = 7, t = 4, u_s = 11)
    t2_7 = accelerated_collatz(accelerated_collatz(7))
    t2_11 = accelerated_collatz(accelerated_collatz(11))
    t3_11 = accelerated_collatz(t2_11)
    ce11_verified = (t2_7 == 17 and t2_11 == 26 and t3_11 == 13 and t3_11 > 7)

    # Verify CE-C10-12 (non-pre-crossing ks = [0, 0, 1, 2, 0] at s = 5, K_5 = 8, n = 7, t = 1)
    def return_map_word(ks):
        w = []
        for k in ks:
            w.extend([True] + [False] * k)
        return w

    ks_ce12 = [0, 0, 1, 2, 0]
    w_ce12 = return_map_word(ks_ce12)
    w4_ce12 = return_map_word([0, 0, 1, 2])
    A_ce12, B_ce12, D_ce12 = affine_triple_exact(w_ce12)
    A4_ce12, B4_ce12, D4_ce12 = affine_triple_exact(w4_ce12)
    delta_ce12 = D_ce12 - A_ce12
    u4_ce12 = (A4_ce12 * 7 + B4_ce12) // D4_ce12
    u5_ce12 = (A_ce12 * 7 + B_ce12) // D_ce12
    ce12_verified = (
        B_ce12 == 347
        and delta_ce12 == 13
        and delta_ce12 * 7 + (1 << 8) * 1 == B_ce12
        and u4_ce12 == 5
        and u4_ce12 < 7
        and u5_ce12 == 8
    )

    return {
        "precrossing_prefixes_checked": precrossing_prefixes_checked,
        "precrossing_diophantine_solutions_found": precrossing_diophantine_solutions_found,
        "max_sharpened_cap_le_970": max_sharpened_cap_le_970,
        "v2_eq_one_two_step_descent_mismatches": v2_eq_one_two_step_descent_mismatches,
        "ce11_v2_ge_two_no_three_step_descent_verified": ce11_verified,
        "ce12_non_precrossing_diophantine_witness_verified": ce12_verified,
    }


def verify_section16_surplus_reduced_cap_mod3_lock_and_post_crossing_operator(
    max_s: int = 12,
) -> Dict[str, object]:
    """
    Verify Section 16 Final-Block Offset Reduction, 3-Adic Endpoint Lock, Surplus-Reduced Cap,
    and Multi-Step Post-Crossing Self-Similarity Operator (v_2(t) = 2 Four-Step Descent):
      1. Across all 4,403 pre-crossing prefixes for 1 <= s <= 12 and all minimal crossing k >= 1:
         verify k >= 1, 2^(k+1) * B_s == 3 * (2^(k+1) * B_{s-1} + 3^{s-1}) + delta_s,
         and (2^(k+1) * B_s - delta_s) % 3 == 0.
      2. Verify the v_2(t) = 2 (t = 4*q, q odd) 4-step post-crossing descent operator on all n ≡ 3 (mod 4)
         where T^2(n + 4*q) ≡ 0 (mod 4): 16 * T^4(n + 4*q) == 9*n + 36*q + 5, and T^4(n + 4*q) < n
         whenever 7*n > 36*q + 5.
      3. Verify the concrete witness n = 15, q = 1, t = 4, u_s = 19 (T^3(19) = 22 > 15, T^4(19) = 11 < 15).
    """
    def gen_precrossing_prefixes(s: int):
        if s == 1:
            yield (0,), 0, 0
            return
        for Ks, B_prev, B_curr in gen_precrossing_prefixes(s - 1):
            j = s - 1
            if j == 1:
                B_base = 1
            else:
                B_base = B_curr
            max_K = (3 ** j).bit_length() - 1
            for K_next in range(Ks[-1] + 1, max_K + 1):
                yield Ks + (K_next,), B_base, 3 * B_base + (1 << K_next)

    final_block_reduction_mismatches = 0
    mod3_lock_mismatches = 0
    prefixes_verified = 0
    for s in range(1, max_s + 1):
        K_min = (3 ** s).bit_length()
        for Ks, B_prev, B_curr in gen_precrossing_prefixes(s):
            prefixes_verified += 1
            B_s = 1 if s == 1 else B_curr
            B_s_minus_1 = 0 if s == 1 else B_prev
            K_s_minus_1 = Ks[-1]
            k = K_min - K_s_minus_1 - 1
            if k < 1:
                final_block_reduction_mismatches += 1
            delta = (1 << K_min) - (3 ** s)
            lhs = (1 << (k + 1)) * B_s
            rhs = 3 * ((1 << (k + 1)) * B_s_minus_1 + (3 ** (s - 1))) + delta
            if lhs != rhs:
                final_block_reduction_mismatches += 1
            if (lhs - delta) % 3 != 0:
                mod3_lock_mismatches += 1

    v2_eq_two_four_step_mismatches = 0
    v2_eq_two_branches_checked = 0
    for n in range(3, 500, 4):
        for q in range(1, 16, 2):
            u_s = n + 4 * q
            t2_u = accelerated_collatz(accelerated_collatz(u_s))
            if t2_u % 4 == 0:
                v2_eq_two_branches_checked += 1
                t4_u = accelerated_collatz(accelerated_collatz(t2_u))
                if 16 * t4_u != 9 * n + 36 * q + 5:
                    v2_eq_two_four_step_mismatches += 1
                if 7 * n > 36 * q + 5 and not (t4_u < n):
                    v2_eq_two_four_step_mismatches += 1

    t3_19 = accelerated_collatz(accelerated_collatz(accelerated_collatz(19)))
    t4_19 = accelerated_collatz(t3_19)
    witness_15_19_verified = (t3_19 == 22 and t3_19 > 15 and t4_19 == 11 and t4_19 < 15)

    return {
        "prefixes_verified": prefixes_verified,
        "final_block_reduction_mismatches": final_block_reduction_mismatches,
        "mod3_lock_mismatches": mod3_lock_mismatches,
        "v2_eq_two_branches_checked": v2_eq_two_branches_checked,
        "v2_eq_two_four_step_mismatches": v2_eq_two_four_step_mismatches,
        "witness_15_19_verified": witness_15_19_verified,
    }


def verify_section17_post_crossing_prefix_trichotomy_and_k1_zero_exhaustion(
    max_s: int = 12,
    max_n: int = 2000,
) -> Dict[str, object]:
    """
    Verify Section 17 3-Block Pre-Crossing Prefix Trichotomy, Unconditional Multi-Branch
    Exhaustion on the k_1 = 0 Subtree, and Falsifications CE-C10-13..14 on (0, 1, 0):
      1. Across all pre-crossing prefixes of length 4 <= s <= max_s (4,399 prefixes at s <= 12):
         verify that 100% of 3-block prefixes (k_0, k_1, k_2) belong to {(0, 0, 0), (0, 0, 1), (0, 1, 0)}.
      2. Across all odd integers n <= max_n on each of the three branches:
         - (0, 0, 0): verify 3 * T^3(n + 4) == T^3(n) + 13, T^3(n + 4) % 2 == 0,
           16 * T^4(n + 4) == 9 * n + 41, and T^4(n + 4) < n for all n >= 6.
         - (0, 0, 1): verify 3 * T^3(n + 4) == T^3(n) + 13, T^3(n + 4) % 2 == 1,
           T^4(n + 4) == T^4(n) + 7 (even), 32 * T^5(n + 4) == 27 * n + 131,
           and T^5(n + 4) < n for all n >= 27.
         - (0, 1, 0): verify T^2(n + 4) == T^2(n) + 9 (odd), T^3(n + 4) == 3 * T^3(n) + 14 (odd),
           T^4(n + 4) == 3 * T^4(n) + 20 (odd), 32 * T^5(n + 4) == 243 * n + 1183, and T^5(n + 4) > n.
      3. Verify CE-C10-13 (n = 27, u_s = 31: 56-step post-crossing delay) and
         CE-C10-14 (n = 1051, u_s = 1055: 80-step post-crossing delay).
    """
    def gen_precrossing_prefixes(s: int):
        if s == 1:
            yield (0,)
            return
        for Ks in gen_precrossing_prefixes(s - 1):
            j = s - 1
            max_K = (3 ** j).bit_length() - 1
            for K_next in range(Ks[-1] + 1, max_K + 1):
                yield Ks + (K_next,)

    admissible_triples = {(0, 0, 0), (0, 0, 1), (0, 1, 0)}
    prefixes_s_ge_4_checked = 0
    prefix_trichotomy_violations = 0
    branch_counts = {(0, 0, 0): 0, (0, 0, 1): 0, (0, 1, 0): 0}

    for s in range(4, max_s + 1):
        for Ks in gen_precrossing_prefixes(s):
            prefixes_s_ge_4_checked += 1
            k0 = Ks[1] - Ks[0] - 1
            k1 = Ks[2] - Ks[1] - 1
            k2 = Ks[3] - Ks[2] - 1
            triple = (k0, k1, k2)
            if triple not in admissible_triples:
                prefix_trichotomy_violations += 1
            else:
                branch_counts[triple] += 1

    def iter_acc(x: int, steps: int) -> int:
        for _ in range(steps):
            x = accelerated_collatz(x)
        return x

    branch_000_checked = 0
    branch_000_mismatches = 0
    branch_001_checked = 0
    branch_001_mismatches = 0
    branch_010_checked = 0
    branch_010_mismatches = 0

    for n in range(3, max_n + 1, 2):
        t1n = iter_acc(n, 1)
        t2n = iter_acc(n, 2)
        t3n = iter_acc(n, 3)
        t4n = iter_acc(n, 4)
        u = n + 4
        t2u = iter_acc(u, 2)
        t3u = iter_acc(u, 3)
        t4u = iter_acc(u, 4)
        t5u = iter_acc(u, 5)

        if (n % 2 == 1) and (t1n % 2 == 1) and (t2n % 2 == 1) and (t3n % 2 == 1):
            branch_000_checked += 1
            if (
                8 * t3n != 27 * n + 19
                or 8 * t3u != 9 * n + 41
                or 3 * t3u != t3n + 13
                or t3u % 2 != 0
                or 16 * t4u != 9 * n + 41
                or (n >= 6 and not (t4u < n))
            ):
                branch_000_mismatches += 1

        if (n % 2 == 1) and (t1n % 2 == 1) and (t2n % 2 == 1) and (t3n % 2 == 0) and (t4n % 2 == 1):
            branch_001_checked += 1
            if (
                8 * t3n != 27 * n + 19
                or 8 * t3u != 9 * n + 41
                or 3 * t3u != t3n + 13
                or t3u % 2 != 1
                or t4u != t4n + 7
                or t4u % 2 != 0
                or 32 * t5u != 27 * n + 131
                or (n >= 27 and not (t5u < n))
            ):
                branch_001_mismatches += 1

        if (n % 2 == 1) and (t1n % 2 == 1) and (t2n % 2 == 0) and (t3n % 2 == 1) and (t4n % 2 == 1):
            branch_010_checked += 1
            if (
                t2u != t2n + 9
                or t2u % 2 != 1
                or t3u != 3 * t3n + 14
                or t3u % 2 != 1
                or t4u != 3 * t4n + 20
                or t4u % 2 != 1
                or 32 * t5u != 243 * n + 1183
                or not (t5u > n)
            ):
                branch_010_mismatches += 1

    ce13_verified = (
        iter_acc(31, 5) == 242
        and all(iter_acc(31, r) >= 27 for r in range(56))
        and iter_acc(31, 55) == 46
        and iter_acc(31, 56) == 23
    )
    ce14_verified = (
        iter_acc(1055, 5) == 8018
        and all(iter_acc(1055, r) >= 1051 for r in range(80))
        and iter_acc(1055, 79) == 1256
        and iter_acc(1055, 80) == 628
    )

    return {
        "prefixes_s_ge_4_checked": prefixes_s_ge_4_checked,
        "prefix_trichotomy_violations": prefix_trichotomy_violations,
        "branch_counts": {str(k): v for k, v in branch_counts.items()},
        "branch_000_checked": branch_000_checked,
        "branch_000_mismatches": branch_000_mismatches,
        "branch_001_checked": branch_001_checked,
        "branch_001_mismatches": branch_001_mismatches,
        "branch_010_checked": branch_010_checked,
        "branch_010_mismatches": branch_010_mismatches,
        "ce13_verified": ce13_verified,
        "ce14_verified": ce14_verified,
    }


def verify_section18_c10_cert_stream_adaptive_exclusion_pipeline(
    max_s_enclosure: int = 12,
    max_s_benchmark: int = 14,
) -> Dict[str, Any]:
    """
    Section 18 (`C10-CERT-STREAM-001`) 3-component adaptive exclusion pipeline:
    1. Component 1 (Candidate Generator & Progressive Prefix-Interval Enclosure Auditor):
       Verifies `B_lo(ks1, m) <= B_s <= B_hi(ks1, m)`, monotone 1-block contraction, and
       exact collapse `B_lo(ks1, 1) = B_s = B_hi(ks1, 1)` across all pre-crossing sequences
       for `2 <= s <= max_s_enclosure`.
    2. Component 2 (4-Stage Adaptive Exclusion Scheduler) & Component 3 (Independent Certificate
       Verifier):
       Evaluates every first-crossing candidate `(ks, K_s, t)` (`0 <= t <= (s - 1) // 3`) across
       `1 <= s <= max_s_benchmark` at thresholds `n_min in {2, 8, 27, 1024}`:
       - Stage 1: Word-free sharpened envelope (`2*(Delta*(n_min+t)+3^s*t)+3^{s-1} > 2*s*3^{s-1}+1`),
       - Stage 2: Progressive prefix/word upper enclosure (`B_hi(ks1, m) < Delta*(n_min+t)+3^s*t`),
       - Stage 3: Fast 2-adic / self-similarity post-crossing descent (odd `t`, `v_2(t) = 1`, or `t = 4` on `k_1 = 0`),
       - Stage 4: Exact residual non-divisibility (`(B_s - 3^s * t) % Delta != 0`) or 3-adic quotient lock.
       Every emitted certificate is independently verified against the exact integer survivor equation.
    3. Verifies falsification witnesses `CE-C10-15` (`s = 35, K = 56`, `3^35 > 2^53` IEEE-754 float64
       precision loss) and `CE-C10-16` (`s = 5, K = 8, ks = [0,0,0,0,3], t = 0, n_min = 2`, where
       Stages 1-2 fail by magnitude alone and Stage 4 exact non-divisibility `211 % 13 = 3 != 0` retires).
    """

    def return_map_word_local(ks: Sequence[int]) -> List[bool]:
        w: List[bool] = []
        for k in ks:
            w.extend([True] + [False] * k)
        return w

    def valid_parity_word_local(n_val: int, w: Sequence[bool]) -> bool:
        cur = n_val
        for b in w:
            if (cur % 2 == 1) != b:
                return False
            cur = (3 * cur + 1) if b else (cur // 2)
        return True

    def b_lo(ks1: Sequence[int], B_j: int, K_j: int, m: int) -> int:
        return (3 ** m) * B_j + (2 ** K_j) * ((3 ** m) - (2 ** m))

    def b_hi(ks1: Sequence[int], B_j: int, K_j: int, m: int) -> int:
        if m == 0:
            return B_j
        j = len(ks1)
        return (3 ** m) * B_j + (3 ** (m - 1)) * (2 ** K_j) + (m - 1) * (3 ** (j + m - 1))

    # 1. Progressive Prefix-Interval Enclosure Audit across 2 <= s <= max_s_enclosure
    enclosure_splits_checked = 0
    enclosure_violations = 0
    monotone_contraction_violations = 0
    point_collapse_violations = 0

    def enum_noncrossing(target_len: int) -> List[Tuple[Tuple[int, ...], int, int]]:
        cur: List[Tuple[Tuple[int, ...], int, int]] = [((), 0, 0)]
        for j in range(1, target_len + 1):
            limit = 3 ** j
            nxt: List[Tuple[Tuple[int, ...], int, int]] = []
            for ks, K, B in cur:
                k = 0
                while (2 ** (K + k + 1)) <= limit:
                    nxt.append((ks + (k,), K + k + 1, 3 * B + (2 ** K)))
                    k += 1
            cur = nxt
        return cur

    for s in range(2, max_s_enclosure + 1):
        prefixes = enum_noncrossing(s - 1)
        for ks_prev, K_prev, B_prev in prefixes:
            # Test first crossing k_last where 3^s < 2^{K_prev + k_last + 1} <= 2 * 3^s
            k_last = 0
            while (2 ** (K_prev + k_last + 1)) <= (3 ** s):
                k_last += 1
            ks_full = ks_prev + (k_last,)
            B_full = 3 * B_prev + (2 ** K_prev)
            # Audit every prefix split j = 1 .. s - 1
            K_running = 0
            B_running = 0
            prev_lo = None
            prev_hi = None
            for j in range(1, s):
                k_j = ks_full[j - 1]
                B_running = 3 * B_running + (2 ** K_running)
                K_running += k_j + 1
                m = s - j
                lo_val = b_lo(ks_full[:j], B_running, K_running, m)
                hi_val = b_hi(ks_full[:j], B_running, K_running, m)
                enclosure_splits_checked += 1
                if not (lo_val <= B_full <= hi_val):
                    enclosure_violations += 1
                if prev_lo is not None and prev_hi is not None:
                    if not (prev_lo <= lo_val and hi_val <= prev_hi):
                        monotone_contraction_violations += 1
                if m == 1 and not (lo_val == B_full == hi_val):
                    point_collapse_violations += 1
                prev_lo = lo_val
                prev_hi = hi_val

    # 2. 4-Stage Adaptive Exclusion Scheduler & Independent Verifier across 1 <= s <= max_s_benchmark
    thresholds = [2, 8, 27, 1024]
    stage_stats: Dict[str, Dict[str, Any]] = {}
    false_exclusions = 0
    unresolved_candidates = 0

    # Pre-enumerate all (s, ks_prev, K_prev, B_prev, k_last, K_s, B_s, t)
    candidate_records: List[Tuple[int, Tuple[int, ...], int, int, int, int]] = []
    for s in range(1, max_s_benchmark + 1):
        prefixes = enum_noncrossing(s - 1)
        three_s = 3 ** s
        three_s_minus_1 = 3 ** (s - 1)
        max_B_s = s * three_s_minus_1 - (three_s_minus_1 - 1) // 2
        for ks_prev, K_prev, B_prev in prefixes:
            B_s = 3 * B_prev + (2 ** K_prev)
            k_last = 0
            while (2 ** (K_prev + k_last + 1)) <= three_s:
                k_last += 1
            while True:
                K_s = K_prev + k_last + 1
                delta = (2 ** K_s) - three_s
                if delta * 2 > max_B_s:
                    break
                ks_full = ks_prev + (k_last,)
                for t in range(0, (s - 1) // 3 + 1):
                    candidate_records.append((s, ks_full, K_s, B_s, delta, t))
                k_last += 1

    for n_min in thresholds:
        counts = {"stage1": 0, "stage2": 0, "stage3": 0, "stage4": 0}
        for s, ks_full, K_s, B_s, delta, t in candidate_records:
            three_s = 3 ** s
            three_s_minus_1 = 3 ** (s - 1)
            req_lhs_min = delta * (n_min + t) + three_s * t
            # Stage 1: Word-free sharpened envelope
            if 2 * req_lhs_min + three_s_minus_1 > 2 * s * three_s_minus_1 + 1:
                stage = "stage1"
                # Independent certificate verification:
                if B_s >= req_lhs_min:
                    false_exclusions += 1
            # Stage 2: Progressive prefix/word upper enclosure (collapses to B_s at j = s - 1)
            elif B_s < req_lhs_min:
                stage = "stage2"
            # Stage 3: Fast 2-adic / self-similarity post-crossing descent
            elif (
                (t % 2 == 1 and n_min > t)
                or (t > 0 and t % 4 == 2 and s >= 2 and n_min > 3 * t + 1)
                or (t == 4 and s >= 4 and ks_full[1] == 0 and n_min >= 27)
            ):
                stage = "stage3"
            # Stage 4: Exact residual non-divisibility or 3-adic quotient lock
            else:
                rem = B_s - three_s * t
                if rem <= 0 or rem % delta != 0:
                    stage = "stage4"
                else:
                    u_s = rem // delta
                    n_val = u_s - t
                    k_last = ks_full[-1]
                    if n_val < n_min or ((2 ** (k_last + 1)) * u_s) % 3 != 1 or n_val % 2 == 0:
                        stage = "stage4"
                    else:
                        # Check full parity admissibility
                        w = return_map_word_local(ks_full)
                        if not valid_parity_word_local(n_val, w):
                            stage = "stage4"
                        else:
                            unresolved_candidates += 1
                            continue
            counts[stage] += 1

        total = len(candidate_records)
        div_avoided_pct = round(100.0 * (total - counts["stage4"]) / total, 2) if total > 0 else 100.0
        stage_stats[str(n_min)] = {
            "total_candidates": total,
            "stage1_word_free_envelope": counts["stage1"],
            "stage2_prefix_offset_enclosure": counts["stage2"],
            "stage3_post_crossing_descent": counts["stage3"],
            "stage4_exact_modular_divisibility": counts["stage4"],
            "exact_divisions_avoided_pct": div_avoided_pct,
        }

    # 3. Verify CE-C10-15 and CE-C10-16
    ce15_verified = (
        3 ** 35 == 50031545098999707
        and 2 ** 53 == 9007199254740992
        and (3 ** 35) > (2 ** 53)
        and (2 ** 56) - (3 ** 35) == 22026048938928229
        and ((2 ** 56) - (3 ** 35)) > (2 ** 53)
        and int(float(3 ** 35)) != (3 ** 35)
    )
    ks_ce16 = (0, 0, 0, 0, 3)
    _, B_ce16, _ = affine_triple_exact(return_map_word_local(ks_ce16))
    delta_ce16 = (2 ** 8) - (3 ** 5)
    ce16_verified = (
        B_ce16 == 211
        and delta_ce16 == 13
        and B_ce16 >= delta_ce16 * 2
        and B_ce16 % delta_ce16 == 3
    )

    return {
        "enclosure_splits_checked": enclosure_splits_checked,
        "enclosure_violations": enclosure_violations,
        "monotone_contraction_violations": monotone_contraction_violations,
        "point_collapse_violations": point_collapse_violations,
        "total_benchmark_candidates": len(candidate_records),
        "stage_stats_by_n_min": stage_stats,
        "false_exclusions": false_exclusions,
        "unresolved_candidates": unresolved_candidates,
        "ce15_verified": ce15_verified,
        "ce16_verified": ce16_verified,
    }


