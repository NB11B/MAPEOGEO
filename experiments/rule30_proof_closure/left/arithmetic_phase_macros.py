"""Track A — Collatz-style arithmetic phase macros on the left half."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from ..core.rule30_exact import evolve_single_seed, rule30_bit


@dataclass(frozen=True)
class LeftPhaseMacroResult:
    """Verification of black-step screened forcing and 11-free autonomous zero-boundary phase macros."""

    black_step_checks: int
    black_step_mismatches: int
    effective_boundary_checks: int
    effective_boundary_mismatches: int
    autonomous_no11_max_survival_by_transient: Dict[int, int]


def evaluate_left_black_step_forcing(steps: int = 64) -> Tuple[int, int, int, int]:
    """Verify left_black_step_screened_forcing and effective_step across the single-seed trajectory."""
    rows = evolve_single_seed(steps + 1)
    black_checks = 0
    black_mismatches = 0
    eff_checks = 0
    eff_mismatches = 0

    for t in range(steps):
        c_t = rows[t].get(0, 0)
        c_next = rows[t + 1].get(0, 0)
        cell_m1 = rows[t].get(-1, 0)
        cell_m2 = rows[t].get(-2, 0)
        cell_next_m1 = rows[t + 1].get(-1, 0)

        if c_t == 1:
            black_checks += 1
            if cell_m1 != (1 ^ c_next):
                black_mismatches += 1

        eff_checks += 1
        eff_rhs = rule30_bit(cell_m2, cell_m1, c_t & c_next)
        if cell_next_m1 != eff_rhs:
            eff_mismatches += 1

    return black_checks, black_mismatches, eff_checks, eff_mismatches


def evaluate_autonomous_no11_left_evolution(
    max_transient_t: int = 7,
    max_steps: int = 48,
) -> LeftPhaseMacroResult:
    """Evaluate autonomous zero-boundary left-half survival under alternating center words."""
    b_chk, b_mis, e_chk, e_mis = evaluate_left_black_step_forcing(64)
    survival_by_t: Dict[int, int] = {}

    for t_val in range(1, max_transient_t + 1):
        max_surv = 0
        for mask in range(1 << max(0, t_val - 1)):
            cur: Dict[int, int] = {-t_val: 1}
            for i in range(1, t_val):
                cur[-i] = (mask >> (i - 1)) & 1
            col_m1: List[int] = [cur.get(-1, 0)]
            for s in range(1, max_steps):
                nxt: Dict[int, int] = {}
                for p in range(-(t_val + s), 0):
                    l = cur.get(p - 1, 0)
                    c = cur.get(p, 0)
                    r = cur.get(p + 1, 0) if p + 1 <= -1 else 0
                    nxt[p] = rule30_bit(l, c, r)
                cur = nxt
                col_m1.append(cur[-1])

            for phase in (0, 1):
                surv = 0
                for idx in range(phase, len(col_m1), 2):
                    if col_m1[idx] == 1:
                        surv += 1
                    else:
                        break
                if surv > max_surv:
                    max_surv = surv
        survival_by_t[t_val] = max_surv

    return LeftPhaseMacroResult(
        black_step_checks=b_chk,
        black_step_mismatches=b_mis,
        effective_boundary_checks=e_chk,
        effective_boundary_mismatches=e_mis,
        autonomous_no11_max_survival_by_transient=survival_by_t,
    )
