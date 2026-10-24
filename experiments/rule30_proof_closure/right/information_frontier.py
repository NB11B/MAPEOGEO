"""Track B — Explicit PSMSL information frontier state I(t) and constructive linear re-entry bounds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from experiments.rule30_falsification.psmsl_future_work import (
    ETHER_BLOCK_0,
    ETHER_BLOCK_2,
    future_work_equiv as future_work_equivalent,
    information_reentry_time as re_entry_horizon,
)
from ..core.rule30_exact import evolve_single_seed, or_col_word, row_at_right, run_right_word


@dataclass(frozen=True)
class InformationFrontierState:
    """Explicit Track B state I(t) = (active_boundary, shielding_structure, unresolved_distinctions, observable_trace)."""

    step_t: int
    active_boundary_depth_ell: int
    active_right_support_width: int
    leading_ether_blocks: int
    unresolved_tail_bits: int
    observable_period_trace: Tuple[int, ...]


@dataclass(frozen=True)
class LinearReEntryBoundSample:
    """Verification sample for universal_linear_reentry_horizon_bound on single-seed return states."""

    period_p: int
    t0: int
    m0: int
    q: int
    actual_reentry_horizon_tau: int
    theoretical_linear_upper_bound_k: int
    distinct_classes_at_linear_horizon: int
    sample_count_m: int
    bound_satisfied: bool


def _first_black_depth(sigma: Sequence[int]) -> int:
    for idx, val in enumerate(sigma):
        if val == 1:
            return idx
    return len(sigma)


def _count_leading_ether_blocks(sigma: Sequence[int]) -> int:
    count = 0
    pos = 0
    while pos + 7 <= len(sigma):
        blk = tuple(sigma[pos : pos + 7])
        if blk in (ETHER_BLOCK_0, ETHER_BLOCK_2):
            count += 1
            pos += 7
        else:
            break
    return count


def trace_information_frontier(
    word: Sequence[int],
    initial_sigma: Sequence[int],
    periods: int,
    initial_step_t: int = 1,
) -> List[InformationFrontierState]:
    """Compute the explicit Track B information frontier trajectory I(t + m*P)."""
    w = tuple(int(c) for c in word)
    p = len(w)
    cur = tuple(int(x) for x in initial_sigma)
    states: List[InformationFrontierState] = []

    for m in range(periods):
        t_cur = initial_step_t + m * p
        ell = _first_black_depth(cur)
        # Active support width up to last 1
        last_one = 0
        for idx, b in enumerate(cur):
            if b == 1:
                last_one = idx + 1
        ether_cnt = _count_leading_ether_blocks(cur)
        obs = or_col_word(w, cur)
        shielded_cols = max(ell + 1, 7 * ether_cnt)
        unresolved = max(0, last_one - shielded_cols)
        states.append(
            InformationFrontierState(
                step_t=t_cur,
                active_boundary_depth_ell=ell,
                active_right_support_width=last_one,
                leading_ether_blocks=ether_cnt,
                unresolved_tail_bits=unresolved,
                observable_period_trace=obs,
            )
        )
        cur = run_right_word(w, cur)
    return states


def verify_linear_reentry_horizon_bound(max_steps: int = 240) -> List[LinearReEntryBoundSample]:
    """Verify that every single-seed FutureWorkEquiv collision breaks strictly within the window_jen linear bound."""
    rows = evolve_single_seed(max_steps)
    samples: List[LinearReEntryBoundSample] = []

    for p in (2, 3, 4):
        # Choose first t0 >= 1 whose length-p center word has both 0 and 1
        # (guaranteed for every periodic center by periodic_center_has_black_and_white_in_every_period)
        t0 = 1
        for cand_t0 in range(1, 20):
            cand_w = tuple(rows[cand_t0 + s].get(0, 0) for s in range(p))
            if 0 in cand_w and 1 in cand_w:
                t0 = cand_t0
                break
        w = tuple(rows[t0 + s].get(0, 0) for s in range(p))
        m_count = 6
        max_k = 18
        width = (max_k + 2) * p + 2
        prefixes = [row_at_right(rows, t0 + m * p, 1, width) for m in range(24)]

        m0 = 0
        q = 1
        t1 = t0 + m0 * p
        t2 = t0 + (m0 + q) * p
        # Theoretical linear upper bound k where (k + 1) * P >= t0 + (m0 + q) * P
        k_bound = max(0, (t2 + p - 1) // p - 1)

        # By universal_linear_reentry_horizon_bound (periodic_center T P -> ¬ FutureWorkEquiv w k s1 s2),
        # within 0 <= k <= k_bound, either the single-seed center word breaks periodicity w
        # or FutureWorkEquiv w k s1 s2 fails.
        tau = k_bound + 1
        for k in range(max_k + 1):
            w1_k = tuple(rows[t1 + k * p + s].get(0, 0) for s in range(p))
            w2_k = tuple(rows[t2 + k * p + s].get(0, 0) for s in range(p))
            if w1_k != w or w2_k != w or not future_work_equivalent(w, k, prefixes[m0], prefixes[m0 + q]):
                tau = k
                break

        # Count pairwise distinct joint (center_window, FutureWorkEquiv) classes among m = 0 .. m_count - 1
        # at horizon k_distinct where (k_distinct + 1) * P >= t0 + (m_count - 1) * P
        k_distinct = max(0, (t0 + (m_count - 1) * p + p - 1) // p - 1)
        distinct_pairs_verified = True
        for i in range(m_count):
            for j in range(i + 1, m_count):
                ti = t0 + i * p
                tj = t0 + j * p
                wi = tuple(rows[ti + s].get(0, 0) for s in range((k_distinct + 1) * p))
                wj = tuple(rows[tj + s].get(0, 0) for s in range((k_distinct + 1) * p))
                if wi == wj and future_work_equivalent(w, k_distinct, prefixes[i], prefixes[j]):
                    distinct_pairs_verified = False

        samples.append(
            LinearReEntryBoundSample(
                period_p=p,
                t0=t0,
                m0=m0,
                q=q,
                actual_reentry_horizon_tau=tau,
                theoretical_linear_upper_bound_k=k_bound,
                distinct_classes_at_linear_horizon=m_count if distinct_pairs_verified else 0,
                sample_count_m=m_count,
                bound_satisfied=(tau <= k_bound and distinct_pairs_verified),
            )
        )
    return samples
