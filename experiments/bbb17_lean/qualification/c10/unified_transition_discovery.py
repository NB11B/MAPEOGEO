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
