"""Track B — PSMSL future-work quotient and bilateral conservation law across column 0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from experiments.rule30_falsification.psmsl_future_work import (
    future_work_equiv as future_work_equivalent,
    information_reentry_time as re_entry_horizon,
)
from ..core.rule30_exact import evolve_single_seed, obs_left_word, or_col_word, row_at_left, row_at_right


@dataclass(frozen=True)
class BilateralConservationResult:
    """Verification of bilateral_center_conservation and FutureWorkEquiv <-> left column -1 agreement."""

    steps_checked: int
    conservation_mismatches: int
    window_equivalence_checks: int
    window_equivalence_mismatches: int
    passed: bool


def verify_bilateral_conservation_and_work_equivalence(steps: int = 80) -> BilateralConservationResult:
    """Verify cell(t, -1) = center(t + 1) XOR orCol(0, t) and equivalence of left/right traces."""
    rows = evolve_single_seed(steps + 16)
    cons_mismatches = 0
    for t in range(steps):
        c_next = rows[t + 1].get(0, 0)
        or_0 = rows[t].get(0, 0) | rows[t].get(1, 0)
        cell_m1 = rows[t].get(-1, 0)
        if cell_m1 != (c_next ^ or_0) or or_0 != (c_next ^ cell_m1):
            cons_mismatches += 1

    win_checks = 0
    win_mismatches = 0
    for t in range(1, steps - 12):
        for p_len in (2, 3, 4):
            w = tuple(rows[t + s].get(0, 0) for s in range(p_len))
            c_after = rows[t + p_len].get(0, 0)
            left_row = row_at_left(rows, t, -1, p_len + 2)
            right_row = row_at_right(rows, t, 1, p_len + 2)
            win_checks += 1
            if obs_left_word(w, c_after, left_row) != or_col_word(w, right_row):
                win_mismatches += 1

    return BilateralConservationResult(
        steps_checked=steps,
        conservation_mismatches=cons_mismatches,
        window_equivalence_checks=win_checks,
        window_equivalence_mismatches=win_mismatches,
        passed=(cons_mismatches == 0 and win_mismatches == 0),
    )


__all__ = [
    "BilateralConservationResult",
    "future_work_equivalent",
    "re_entry_horizon",
    "verify_bilateral_conservation_and_work_equivalence",
]
