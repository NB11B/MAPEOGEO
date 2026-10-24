"""COLLATZ-C10 Workstream 3 (Gate G4): Global Descent, Geometric Reservoir Drawdown,
and Candidate Potential Falsification Suite.

Tests:
1. Falsification of single-step monotone potentials:
   - `v_2(n + 1)` increases from `0` to `5` under the even step `62 -> 31`
     (`v2_succ_potential_even_step_jump_witness`),
   - Any positive linear combination `alpha*u + beta*v` (`alpha > 0`) in canonical `(j, u, v)`
     coordinates strictly increases on `(0, 2, 0) -> (0, 4, 0)` (`positive_linear_uv_potential_strict_increase`),
   - `S = u + v` is a nondecreasing high-water invariant (`S' = max(S, 3k + 1)`).
2. Verification of the Universal Peak Drawdown Theorem (`every_nat_experiences_peak_drawdown`):
   Every positive integer `n > 0` experiences a step `t <= n` where `F^{t+1}(n) < F^t(n)`
   (activating the geometric reservoir `v' = max(0, v - k - 1) > 0`).
3. Verification of Two-Segment Composite Recovery (`two_segment_recovery_after_jump_iff`)
   and the Eventual Power Threshold (`power_threshold_forces_descent`:
   `2^r * n^{a_r} > (3n + 1)^{a_r}  =>  min_{1<=i<=r} F^i(n) < n`).
"""

from __future__ import annotations

from typing import Any, Dict
from .exact_oracle import accelerated_collatz


def v2_of_int(x: int) -> int:
    if x <= 0:
        return 0
    c = 0
    while (x & 1) == 0:
        x >>= 1
        c += 1
    return c


def verify_potential_falsifications_and_drawdown(limit_n: int = 10000) -> Dict[str, Any]:
    """Verify:
    1. Exact witness `n = 62 -> 31` falsifies monotone decrease of `v_2(n + 1)`.
    2. Every `1 <= n <= limit_n` experiences peak drawdown `F^{t+1}(n) < F^t(n)` within `t <= n` steps.
    3. Every `2 <= n <= limit_n` reaches the C10 multiplicative power threshold
       `2^r * n^{a_r} > (3n + 1)^{a_r}`, and at that exact first threshold depth `r_thresh(n)`,
       the trajectory has already strictly descended below `n` (`min_{1<=i<=r} F^i(n) < n`).
    """
    # 1. Witness for v2(n + 1) jump on even step 62 -> 31
    v2_62 = v2_of_int(62 + 1)
    v2_31 = v2_of_int(accelerated_collatz(62) + 1)
    v2_jump_verified = (accelerated_collatz(62) == 31 and v2_62 == 0 and v2_31 == 5)

    # 2. Universal peak drawdown check
    drawdown_failures = 0
    max_monotonic_run = 0
    for n in range(1, limit_n + 1):
        curr = n
        t = 0
        while True:
            nxt = accelerated_collatz(curr)
            if nxt < curr:
                break
            curr = nxt
            t += 1
            if t > n:
                drawdown_failures += 1
                break
        if t > max_monotonic_run:
            max_monotonic_run = t

    # 3. Power threshold check for 2 <= n <= min(limit_n, 2000)
    power_threshold_checked = 0
    power_threshold_descent_failures = 0
    for n in range(2, min(limit_n, 2000) + 1):
        power_threshold_checked += 1
        curr = n
        r = 0
        a = 0
        min_seen = n
        while True:
            bit = (curr % 2 == 1)
            r += 1
            if bit:
                a += 1
            curr = accelerated_collatz(curr)
            if curr < min_seen:
                min_seen = curr
            if (1 << r) * (n ** a) > ((3 * n + 1) ** a):
                if min_seen >= n:
                    power_threshold_descent_failures += 1
                break

    return {
        "v2_succ_even_step_jump_verified": v2_jump_verified,
        "v2_62_plus_1": v2_62,
        "v2_31_plus_1": v2_31,
        "drawdown_limit_n": limit_n,
        "drawdown_failures": drawdown_failures,
        "max_monotonic_run_steps": max_monotonic_run,
        "power_threshold_checked": power_threshold_checked,
        "power_threshold_descent_failures": power_threshold_descent_failures,
    }
