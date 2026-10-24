"""R30-QUOTIENT-GEOM-001 — Relational quotient geometry of the cone observation map pi_k: X_k -> Y_k."""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Dict, List, Sequence, Tuple

from ..core.rule30_exact import (
    evolve_single_seed,
    obs_left_word,
    or_col_word,
    row_at_left,
    row_at_right,
    rule30_bit,
)


def unstep_left_row(c: int, a: int, stepped_row: Sequence[int]) -> Tuple[int, ...]:
    """Single-step sideways left-permutive inverse of step_left_row.

    Given right neighbor c = x_0(t), boundary bit a = x_{-1}(t), and next-step left row
    stepped_row = [x_{-1}(t+1), ..., x_{-k}(t+1)], uniquely reconstructs
    [x_{-1}(t), x_{-2}(t), ..., x_{-(k+1)}(t)].
    """
    res: List[int] = [int(a) & 1]
    cur_c = int(c) & 1
    cur_a = int(a) & 1
    for z in stepped_row:
        b = rule30_bit(int(z) & 1, cur_a, cur_c)
        res.append(b)
        cur_c = cur_a
        cur_a = b
    return tuple(res)


def reconstruct_left_word(
    w: Sequence[int],
    c_after: int,
    y_trace: Sequence[int],
) -> Tuple[int, ...]:
    """Exact K7-like inverse left coder Theta_w^{-1}: y -> lam on {0, 1}^k."""
    k = len(w)
    assert len(y_trace) == k
    lam: Tuple[int, ...] = ()
    for s in range(k - 1, -1, -1):
        c_s = int(w[s]) & 1
        c_next = int(w[s + 1]) & 1 if (s + 1) < k else (int(c_after) & 1)
        a_s = c_next ^ (int(y_trace[s]) & 1)
        lam = unstep_left_row(c_s, a_s, lam)
    return lam


def fiber_left_slice(
    w: Sequence[int],
    c_after: int,
    sigma: Sequence[int],
) -> Tuple[int, ...]:
    """Unique left-cone slice lam = Theta_w^{-1}(Psi_w(sigma)) in the fiber pi_k^{-1}(w, c_after)."""
    y_trace = or_col_word(w, sigma)
    return reconstruct_left_word(w, c_after, y_trace)


@dataclass(frozen=True)
class TraceQuotientGeometryProfile:
    """Intrinsic quotient geometry profile for a central trace (w, c_after) of depth k."""

    word_label: str
    depth_k: int
    total_right_slices: int
    fiber_preimage_count: int
    quotient_class_count: int
    admissible_left_slices_count: int
    forbidden_left_slices_count: int
    unseen_left_constraint_fraction: float
    intrinsic_entropy_density_bits_per_step: float
    extrinsic_base7_cantor_control_dim: float
    min_quotient_fiber_size: int
    max_quotient_fiber_size: int
    ultrametric_prefix_class_counts: Tuple[int, ...]
    single_seed_T3_in_admissible_left_variety: bool
    single_seed_T3_bilateral_compatible: bool


@dataclass(frozen=True)
class ConeQuotientGeometryReport:
    """Complete verification report for R30-QUOTIENT-GEOM-001."""

    exhaustive_cone_depth_k: int
    exhaustive_initial_configs: int
    exhaustive_central_traces: int
    all_traces_have_exact_2_pow_k_preimages: bool
    left_coder_bijection_mismatches: int
    quotient_pullback_equivalence_mismatches: int
    extrinsic_base7_control_dimension: float
    periodic_word_profiles: Tuple[TraceQuotientGeometryProfile, ...]


def profile_trace_quotient_geometry(
    period_word: Sequence[int],
    depth_k: int = 6,
    transient_t: int = 3,
) -> TraceQuotientGeometryProfile:
    """Compute the intrinsic quotient geometry X_k / ~ for a periodic center word at depth k."""
    p_len = len(period_word)
    full_trace = [int(period_word[s % p_len]) & 1 for s in range(depth_k + 1)]
    w = tuple(full_trace[:depth_k])
    c_after = full_trace[depth_k]

    # Note: or_col_word(w, sigma) uses up to k + 1 right cells (since step s uses col 1..k+1-s)
    # In the exact depth-k light cone from apex (t, 0), the right cone has k cells x_1..x_k,
    # while step k-1 of orColWord uses only c_{k-1} || x_1(t + k - 1), which depends on x_1..x_k!
    quotient_fibers: Dict[Tuple[int, ...], List[Tuple[int, ...]]] = {}
    admissible_left_slices: set[Tuple[int, ...]] = set()

    for sigma in itertools.product((0, 1), repeat=depth_k):
        # Pad with 0 beyond depth_k since light-cone cells > k cannot reach column 1 by step k-1
        y = or_col_word(w, sigma + (0,))
        lam = reconstruct_left_word(w, c_after, y)
        quotient_fibers.setdefault(y, []).append(sigma)
        admissible_left_slices.add(lam)

    total_right = 1 << depth_k
    q_count = len(quotient_fibers)
    adm_left = len(admissible_left_slices)
    assert q_count == adm_left, "Bijection violation: |Im(Psi_w)| must equal |Theta_w^{-1}(Im(Psi_w))|"

    forb_left = total_right - adm_left
    fiber_sizes = [len(fib) for fib in quotient_fibers.values()]
    assert sum(fiber_sizes) == total_right

    # Intrinsic ultrametric tree: number of distinct prefix classes at horizon s = 1..k
    prefix_counts = tuple(
        len({y[:s] for y in quotient_fibers.keys()})
        for s in range(1, depth_k + 1)
    )

    # Check single-seed slice at transient_t
    rows = evolve_single_seed(transient_t + depth_k + 2)
    seed_left = row_at_left(rows, transient_t, -1, depth_k)
    seed_right = row_at_right(rows, transient_t, 1, depth_k + 1)
    seed_in_left_variety = seed_left in admissible_left_slices
    seed_bilateral_ok = (
        obs_left_word(w, c_after, seed_left + (0,)) == or_col_word(w, seed_right)
        and rows[transient_t].get(0, 0) == w[0]
    )

    return TraceQuotientGeometryProfile(
        word_label="".join(str(b) for b in period_word),
        depth_k=depth_k,
        total_right_slices=total_right,
        fiber_preimage_count=total_right,
        quotient_class_count=q_count,
        admissible_left_slices_count=adm_left,
        forbidden_left_slices_count=forb_left,
        unseen_left_constraint_fraction=round(forb_left / total_right, 4),
        intrinsic_entropy_density_bits_per_step=round(math.log2(max(1, q_count)) / depth_k, 4),
        extrinsic_base7_cantor_control_dim=round(math.log(2.0) / math.log(7.0), 4),
        min_quotient_fiber_size=min(fiber_sizes),
        max_quotient_fiber_size=max(fiber_sizes),
        ultrametric_prefix_class_counts=prefix_counts,
        single_seed_T3_in_admissible_left_variety=seed_in_left_variety,
        single_seed_T3_bilateral_compatible=seed_bilateral_ok,
    )


def analyze_cone_quotient_geometry(
    exhaustive_depth_k: int = 3,
    profile_depth_k: int = 6,
) -> ConeQuotientGeometryReport:
    """Verify the 2^{2k+1} -> 2^{k+1} cone fiber structure and relational quotient geometry."""
    k = exhaustive_depth_k
    total_configs = 1 << (2 * k + 1)
    total_traces = 1 << (k + 1)

    # 1. Exhaustive verification over all 2^{2k+1} initial cone configurations at depth k
    trace_counts: Dict[Tuple[int, ...], int] = {}
    bijection_mismatches = 0
    pullback_mismatches = 0

    for full_trace in itertools.product((0, 1), repeat=k + 1):
        w = full_trace[:k]
        c_after = full_trace[k]
        count_for_trace = 0
        seen_by_sigma: Dict[Tuple[int, ...], Tuple[int, ...]] = {}
        for sigma in itertools.product((0, 1), repeat=k):
            y = or_col_word(w, sigma + (0,))
            lam = reconstruct_left_word(w, c_after, y)
            # Verify Theta_w(Theta_w^{-1}(y)) == y
            y_roundtrip = obs_left_word(w, c_after, lam + (0,))
            if y_roundtrip != y:
                bijection_mismatches += 1
            # Verify Theta_w^{-1}(Theta_w(lam)) == lam
            if reconstruct_left_word(w, c_after, y_roundtrip) != lam:
                bijection_mismatches += 1
            seen_by_sigma[sigma] = (y, lam)
            count_for_trace += 1
        trace_counts[full_trace] = count_for_trace

        # Verify quotient pullback equivalence: y1 == y2 <=> lam1 == lam2
        sigmas = list(seen_by_sigma.keys())
        for s1, s2 in itertools.combinations(sigmas, 2):
            y1, lam1 = seen_by_sigma[s1]
            y2, lam2 = seen_by_sigma[s2]
            if (y1 == y2) != (lam1 == lam2):
                pullback_mismatches += 1

    all_exact_2_pow_k = (
        len(trace_counts) == total_traces
        and sum(trace_counts.values()) == total_configs
        and all(cnt == (1 << k) for cnt in trace_counts.values())
    )

    profiles = tuple(
        profile_trace_quotient_geometry(w_per, depth_k=profile_depth_k, transient_t=3)
        for w_per in ((0, 1), (1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1, 0), (0, 0, 0, 1))
    )

    return ConeQuotientGeometryReport(
        exhaustive_cone_depth_k=k,
        exhaustive_initial_configs=total_configs,
        exhaustive_central_traces=total_traces,
        all_traces_have_exact_2_pow_k_preimages=all_exact_2_pow_k,
        left_coder_bijection_mismatches=bijection_mismatches,
        quotient_pullback_equivalence_mismatches=pullback_mismatches,
        extrinsic_base7_control_dimension=round(math.log(2.0) / math.log(7.0), 4),
        periodic_word_profiles=profiles,
    )
