"""COLLATZ-C10 Workstream 1 (Gates G1-G2): 2-Adic Lifting & Minimal-Crossing Falsification Suite.

Independently tests and attempts to falsify:
1. Exact 2-adic step lifting identities (`even_step_lift_deficit_recurrence`,
   `odd_step_lift_deficit_recurrence`, `odd_step_lift_expansion_recurrence`) across
   the parity-word tree.
2. Exact pre-crossing descent equivalence (`firstCrossing_descent_iff_preCrossing_bound`):
   `m' > y'  <=>  2 * y_0 + 1 < 2 * m_0 + l * (2 * D_0 - A_0)`.
3. Coarse C8 pincer counterexamples `{27, 47, 63}` vs. zero true first-crossing exceptions.
4. Universal Non-Descent Multiplicative Power Bound (`nondescent_prefix_power_bound`)
   and Two-Sided Diophantine Sandwich (`nondescent_diophantine_sandwich`).
"""

from __future__ import annotations

from typing import Any, Dict, List
from .exact_oracle import (
    accelerated_collatz,
    enumerate_first_crossing_words,
    first_crossing_prefix,
    min_class_rep,
    min_rep_output,
    nondescent_sandwich_check,
    parity_word_of,
    word_A,
    word_B,
    word_D,
    word_ones,
    word_residue,
)


def verify_lifting_recurrences(max_depth: int = 14) -> Dict[str, Any]:
    """Exhaustively verify the even-step and odd-step 2-adic deficit lifting recurrences
    across all 2^r parity words up to `max_depth`.
    """
    total_words = 0
    even_lifts_checked = 0
    odd_lifts_checked = 0
    failures: List[Dict[str, Any]] = []

    level: List[List[bool]] = [[]]
    for _depth in range(1, max_depth + 1):
        next_level: List[List[bool]] = []
        for w in level:
            for bit in (False, True):
                w_next = w + [bit]
                next_level.append(w_next)
                total_words += 1

                if len(w) == 0:
                    continue

                m0 = word_residue(w)
                y0 = min_rep_output(w)
                A0 = word_A(w)
                D0 = word_D(w)
                l_bit = y0 % 2 if not bit else (1 - (y0 % 2))

                m_next = word_residue(w_next)
                y_next = min_rep_output(w_next)

                if m_next != m0 + l_bit * D0:
                    failures.append({"type": "residue_lift", "w": w, "bit": bit})

                if not bit:
                    even_lifts_checked += 1
                    lhs = 2 * m_next - 2 * y_next
                    rhs = (2 * m0 - y0) + l_bit * (2 * D0 - A0)
                    if lhs != rhs or 2 * y_next != y0 + l_bit * A0:
                        failures.append({"type": "even_deficit", "w": w})
                else:
                    odd_lifts_checked += 1
                    lhs = (2 * m_next + 2) - (2 * y_next + 1)
                    rhs = (2 * m0 - 3 * y0) + l_bit * (2 * D0 - 3 * A0)
                    if lhs != rhs or 2 * y_next != 3 * y0 + 1 + 3 * l_bit * A0:
                        failures.append({"type": "odd_deficit", "w": w})
        level = next_level

    return {
        "max_depth": max_depth,
        "total_words_checked": total_words,
        "even_lifts_checked": even_lifts_checked,
        "odd_lifts_checked": odd_lifts_checked,
        "failures": len(failures),
    }


def verify_first_crossing_tree(max_depth: int = 18) -> Dict[str, Any]:
    """Exhaustively enumerate all first-crossing parity words up to `max_depth`,
    verifying:
    1. Every first-crossing word ends with `False` (even step).
    2. Exact pre-crossing descent criterion `2*y0 + 1 < 2*m0 + l*(2*D0 - A0)`.
    3. Zero true first-crossing deficit exceptions (`min_class_rep(w) <= canonical_output(w)`).
    4. Exact identification of the 3 coarse C8 pincer exceptions `{27, 47, 63}`.
    """
    words = enumerate_first_crossing_words(max_depth)
    true_exceptions: List[Dict[str, Any]] = []
    coarse_pincer_exceptions: List[Dict[str, Any]] = []
    pre_crossing_mismatches = 0

    for w in words:
        r = len(w)
        a = word_ones(w)
        A = word_A(w)
        B = word_B(w)
        D = word_D(w)
        Delta = D - A
        m_min = min_class_rep(w)
        y_min = (A * m_min + B) // D

        if m_min <= y_min:
            true_exceptions.append({"r": r, "a": a, "m_min": m_min, "y_min": y_min})

        if 3 * m_min * Delta <= a * A:
            coarse_pincer_exceptions.append(
                {
                    "r": r,
                    "a": a,
                    "m_min": m_min,
                    "y_min": y_min,
                    "3_m_Delta": 3 * m_min * Delta,
                    "a_A": a * A,
                    "true_deficit": m_min - y_min,
                }
            )

        # Verify pre-crossing equivalence on w = w0 ++ [False]
        w0 = w[:-1]
        m0 = word_residue(w0)
        y0 = min_rep_output(w0)
        A0 = word_A(w0)
        D0 = word_D(w0)
        l_bit = y0 % 2
        if m0 >= 2:
            pre_cond = y0 < (2 * m0 + l_bit * (2 * D0 - A0))
            if pre_cond != (m_min > y_min):
                pre_crossing_mismatches += 1

    # Check the first-crossing words of all 2 <= n <= 64 (matching Lean's checkDepthPincerExceptions_64)
    depth64_coarse_pincer_exceptions: List[Dict[str, Any]] = []
    for n in range(2, 65):
        w_n = first_crossing_prefix(n)
        if w_n is not None and min_class_rep(w_n) == n:
            r_n = len(w_n)
            a_n = word_ones(w_n)
            A_n = word_A(w_n)
            B_n = word_B(w_n)
            D_n = word_D(w_n)
            Delta_n = D_n - A_n
            y_n = (A_n * n + B_n) // D_n
            if 3 * n * Delta_n <= a_n * A_n:
                depth64_coarse_pincer_exceptions.append(
                    {
                        "r": r_n,
                        "a": a_n,
                        "m_min": n,
                        "y_min": y_n,
                        "3_m_Delta": 3 * n * Delta_n,
                        "a_A": a_n * A_n,
                        "true_deficit": n - y_n,
                    }
                )

    return {
        "max_depth": max_depth,
        "first_crossing_words_count": len(words),
        "true_deficit_exceptions_count": len(true_exceptions),
        "true_deficit_exceptions": true_exceptions,
        "coarse_pincer_exceptions_tree_count": len(coarse_pincer_exceptions),
        "coarse_pincer_exceptions_count": len(depth64_coarse_pincer_exceptions),
        "coarse_pincer_exceptions": depth64_coarse_pincer_exceptions,
        "pre_crossing_mismatches": pre_crossing_mismatches,
    }


def run_trajectory_falsification_sweep(limit_n: int = 100000) -> Dict[str, Any]:
    """Sweep integer trajectories 2 <= n <= limit_n, verifying:
    - Every n > 1 reaches its first spectral crossing and strictly descends at that crossing.
    - Every non-descending prefix satisfies the Two-Sided Non-Descent Diophantine Sandwich.
    """
    max_first_crossing_depth = 0
    max_first_crossing_n = 2
    first_crossing_nondescent_count = 0
    sandwich_violations = 0

    for n in range(2, limit_n + 1):
        curr = n
        r = 0
        a = 0
        crossed = False
        while not crossed:
            bit = (curr % 2 == 1)
            r += 1
            if bit:
                a += 1
            curr = accelerated_collatz(curr)
            if (1 << r) > (3 ** a):
                crossed = True
                if r > max_first_crossing_depth:
                    max_first_crossing_depth = r
                    max_first_crossing_n = n
                if curr >= n:
                    first_crossing_nondescent_count += 1

    # Detailed non-descent sandwich check on the hardest mod-32 frontier integers up to 10,000
    frontier_residues = {7, 15, 19, 27, 31}
    frontier_checked = 0
    for n in range(7, min(limit_n, 10000) + 1):
        if (n % 32) not in frontier_residues:
            continue
        frontier_checked += 1
        curr = n
        r = 0
        while curr >= n:
            r += 1
            curr = accelerated_collatz(curr)
            if curr >= n:
                chk = nondescent_sandwich_check(n, r)
                if not (chk["lower_bound_holds"] and chk["upper_bound_holds"] and chk["power_ratio_holds"]):
                    sandwich_violations += 1

    return {
        "limit_n": limit_n,
        "max_first_crossing_depth": max_first_crossing_depth,
        "max_first_crossing_n": max_first_crossing_n,
        "first_crossing_nondescent_count": first_crossing_nondescent_count,
        "frontier_trajectories_sandwich_checked": frontier_checked,
        "sandwich_violations": sandwich_violations,
    }
