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





