"""Track A — General periodic-center-to-initial-state triangular reconstruction (Theta_{w, T})."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from ..core.rule30_exact import evolve_single_seed, obs_left_word, or_col_word, row_at_left, row_at_right


@dataclass(frozen=True)
class LeftTriangularReconstructionResult:
    """Verification record for Checkpoint 01 (Reconstruction Completeness)."""

    steps_checked: int
    cells_reconstructed: int
    reconstruction_mismatches: int
    inverse_orcol_mismatches: int
    unit_triangular_sensitivity_checks: int
    unit_triangular_sensitivity_mismatches: int
    checkpoint_01_passed: bool


def reconstruct_left_column_from_orcol(
    center_trace: Sequence[int],
    or_col_trace: Sequence[int],
    max_depth_k: int,
) -> Dict[Tuple[int, int], int]:
    """Reconstruct cell(t, -k) for 1 <= k <= max_depth_k from center(t..t+k) and orCol(0, t..t+k-1).

    Uses the exact left-permutive identity:
      cell(t, i - 1) = cell(t + 1, i) XOR (cell(t, i) OR cell(t, i + 1)).
    """
    n_len = len(or_col_trace)
    assert len(center_trace) >= n_len + 1
    grid: Dict[Tuple[int, int], int] = {}
    for t in range(len(center_trace)):
        grid[(t, 0)] = int(center_trace[t]) & 1
    # k = 1: cell(t, -1) = center(t + 1) XOR orCol(0, t)
    for t in range(n_len):
        grid[(t, -1)] = grid[(t + 1, 0)] ^ (int(or_col_trace[t]) & 1)
    # k >= 2: cell(t, -k) = cell(t + 1, -(k - 1)) XOR (cell(t, -(k - 1)) OR cell(t, -(k - 2)))
    for k in range(2, max_depth_k + 1):
        for t in range(n_len - k + 1):
            c_prev1 = grid[(t, -(k - 1))]
            c_prev2 = grid[(t, -(k - 2))]
            grid[(t, -k)] = grid[(t + 1, -(k - 1))] ^ (c_prev1 | c_prev2)
    return grid


def reconstruct_orcol_from_left_cone(
    center_trace: Sequence[int],
    left_cone_row: Sequence[int],
) -> Tuple[int, ...]:
    """Invert the unit-triangular map Theta_{w, T}: given center(t..t+L) and left_cone_row
    [cell(t, -1), ..., cell(t, -L)], uniquely recover orCol(0, t..t+L-1).
    """
    l_len = len(left_cone_row)
    assert len(center_trace) >= l_len + 1
    return obs_left_word(center_trace[:l_len], center_trace[l_len], left_cone_row)


def verify_checkpoint_01_reconstruction_completeness(steps: int = 32) -> LeftTriangularReconstructionResult:
    """Verify that Theta_{w, T} and its inverse bijectively represent all compatible trajectories."""
    rows = evolve_single_seed(steps)
    center_trace = [rows[t].get(0, 0) for t in range(steps + 1)]
    or_col_trace = [rows[t].get(0, 0) | rows[t].get(1, 0) for t in range(steps)]

    recon_grid = reconstruct_left_column_from_orcol(center_trace, or_col_trace, max_depth_k=steps)
    cells_checked = 0
    mismatches = 0
    for k in range(1, steps + 1):
        for t in range(steps - k + 1):
            cells_checked += 1
            expected = rows[t].get(-k, 0)
            if recon_grid[(t, -k)] != expected:
                mismatches += 1

    # Verify inverse bijection: recovering orCol from rowAtLeft matches orColWord on rowAtRight
    inv_mismatches = 0
    for t in range(0, steps - 8):
        l_win = 8
        left_row = row_at_left(rows, t, -1, l_win + 1)
        right_row = row_at_right(rows, t, 1, l_win + 1)
        w = center_trace[t : t + l_win]
        c_after = center_trace[t + l_win]
        obs_l = obs_left_word(w, c_after, left_row)
        obs_r = or_col_word(w, right_row)
        if obs_l != obs_r or obs_l != tuple(or_col_trace[t : t + l_win]):
            inv_mismatches += 1

    # Verify unit-triangular linear sensitivity: flipping orCol(0, t + k - 1) always flips cell(t, -k)
    sens_checks = 0
    sens_mismatches = 0
    for k in range(1, 10):
        base_or = list(or_col_trace[:12])
        flipped_or = list(base_or)
        flipped_or[k - 1] ^= 1
        g0 = reconstruct_left_column_from_orcol(center_trace[:13], base_or, max_depth_k=k)
        g1 = reconstruct_left_column_from_orcol(center_trace[:13], flipped_or, max_depth_k=k)
        sens_checks += 1
        if g0[(0, -k)] == g1[(0, -k)]:
            sens_mismatches += 1

    passed = mismatches == 0 and inv_mismatches == 0 and sens_mismatches == 0
    return LeftTriangularReconstructionResult(
        steps_checked=steps,
        cells_reconstructed=cells_checked,
        reconstruction_mismatches=mismatches,
        inverse_orcol_mismatches=inv_mismatches,
        unit_triangular_sensitivity_checks=sens_checks,
        unit_triangular_sensitivity_mismatches=sens_mismatches,
        checkpoint_01_passed=passed,
    )
