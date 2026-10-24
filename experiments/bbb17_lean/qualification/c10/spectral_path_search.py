"""COLLATZ-C10 Workstream 2 (Gate G3): Spectral Crossing & Near-Collision Analysis.

Analyzes:
1. Best rational approximations / convergents of `log_2(3)` up to `a <= 2,000`
   where `2^r > 3^a` is minimally contracting (`Delta = 2^r - 3^a` is minimal relative to `3^a`).
2. The C10 Non-Descent Power Ratio Window:
   For a non-descending prefix of length `r` with `a` odd steps and starting value `n >= N_0`,
   our Lean theorem `nondescent_lower_bound_power_ratio` proves:
       `2^r * N_0^a <= (3 * N_0 + 1)^a`.
   When `2^r > 3^a`, this forces:
       `3^a < 2^r <= (3 + 1/N_0)^a`,
   which requires the relative spectral gap `(2^r - 3^a) / 3^a` to be smaller than
   `(1 + 1/(3*N_0))^a - 1`.
3. Verification that for `N_0 = 1024`, NO pair `(r, a)` in `1 <= r <= 64` satisfies
   `3^a < 2^r` and `2^r * 1024^a <= 3073^a` (matching Lean's `checkEliahouWindow1024_64`).
"""

from __future__ import annotations

from typing import Any, Dict, List


def analyze_spectral_near_collisions(max_a: int = 2000, n0_bound: int = 1024) -> Dict[str, Any]:
    """Scan all odd-step counts `1 <= a <= max_a`, finding the minimal contracting
    depth `r = floor(a * log_2(3)) + 1` where `2^r > 3^a`, and checking:
    - whether `(r, a)` falls in the first-crossing spectral band `2^r < 3^{a+1}`,
    - whether `(r, a)` satisfies the C10 non-descent window `2^r * N_0^a <= (3*N_0 + 1)^a`,
    - record-breaking relative spectral gaps `(2^r - 3^a) / 3^a`.
    """
    r = 1
    pow2 = 2
    pow3 = 1

    band_violations = 0
    window_hits_le_64: List[Dict[str, int]] = []
    window_hits_all: List[Dict[str, Any]] = []
    record_convergents: List[Dict[str, Any]] = []
    min_rel_gap = float("inf")

    for a in range(1, max_a + 1):
        pow3 *= 3
        while pow2 <= pow3:
            r += 1
            pow2 <<= 1

        # Now pow2 = 2^r > 3^a = pow3, and 2^{r-1} < 3^a
        if not (pow3 < pow2 < 3 * pow3):
            band_violations += 1

        delta = pow2 - pow3
        rel_gap = delta / pow3
        if rel_gap < min_rel_gap:
            min_rel_gap = rel_gap
            record_convergents.append(
                {
                    "a": a,
                    "r": r,
                    "relative_gap": rel_gap,
                }
            )

        # Check C10 non-descent window for N_0 = n0_bound up to a <= 300
        if a <= 300:
            lhs = pow2 * (n0_bound ** a)
            rhs = (3 * n0_bound + 1) ** a
            if lhs <= rhs:
                entry = {"r": r, "a": a, "relative_gap": rel_gap}
                window_hits_all.append(entry)
                if r <= 64:
                    window_hits_le_64.append({"r": r, "a": a})

    return {
        "max_a": max_a,
        "n0_bound": n0_bound,
        "spectral_band_violations": band_violations,
        "window_hits_r_le_64": len(window_hits_le_64),
        "first_window_hit_for_n0_1024": window_hits_all[0] if window_hits_all else None,
        "record_convergents": record_convergents,
    }
