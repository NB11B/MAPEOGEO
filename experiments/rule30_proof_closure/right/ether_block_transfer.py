"""Track B — Ether block peeling vs. bilateral left-cone incompatibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..core.rule30_exact import ETHER_BLOCK_0, ether_repeat_0, iter_period_return, obs_left_word, or_col_word


@dataclass(frozen=True)
class EtherBilateralIncompatibilityResult:
    """Demonstrates that while etherRepeat0 screens the right half for 2m+2 periods,
    its periodic observation trace [0, 1], [1, 1] is bilaterally rejected by any finite left cone.
    """

    blocks_tested: int
    right_screening_horizons_verified: Dict[int, int]
    left_cone_rejection_horizons_by_transient: Dict[int, int]
    bilaterally_compatible_states_found: int


def evaluate_ether_chain_bilateral_incompatibility(max_blocks: int = 4, max_transient_t: int = 6) -> EtherBilateralIncompatibilityResult:
    """Compare right-half Ether screening horizons against left-cone bilateral rejection."""
    w = (0, 1)
    right_horizons: Dict[int, int] = {}
    for m_plus_1 in range(1, max_blocks + 1):
        m = m_plus_1 - 1
        sig_a = ether_repeat_0(m_plus_1, (0, 0, 0, 0))
        sig_b = ether_repeat_0(m_plus_1, (1, 1, 0, 1))
        for k in range(2 * m + 2):
            obs_a = or_col_word(w, iter_period_return(w, k, sig_a))
            obs_b = or_col_word(w, iter_period_return(w, k, sig_b))
            expected = (1 if (k % 2 == 1) else 0, 1)
            assert obs_a == expected and obs_b == expected
        right_horizons[m_plus_1] = 2 * m + 1

    # Target Ether observation stream over steps s = 0, 1, ...:
    # Period k even -> (0, 1); Period k odd -> (1, 1), i.e., period-4 stream (0, 1, 1, 1)^infty
    ether_obs_stream = [0 if (s % 4 == 0) else 1 for s in range(32)]
    w_stream = [s % 2 for s in range(33)]

    left_reject_by_t: Dict[int, int] = {}
    compatible_found = 0
    for t_val in range(1, max_transient_t + 1):
        max_h = 0
        for mask in range(1 << (t_val - 1)):
            lam = tuple(((mask >> i) & 1) for i in range(t_val - 1)) + (1,) + (0,) * 34
            obs_l = obs_left_word(w_stream[:32], w_stream[32], lam)
            fail_s = None
            for s in range(32):
                if obs_l[s] != ether_obs_stream[s]:
                    fail_s = s + 1
                    break
            if fail_s is None:
                compatible_found += 1
            else:
                max_h = max(max_h, fail_s)
        left_reject_by_t[t_val] = max_h

    return EtherBilateralIncompatibilityResult(
        blocks_tested=max_blocks,
        right_screening_horizons_verified=right_horizons,
        left_cone_rejection_horizons_by_transient=left_reject_by_t,
        bilaterally_compatible_states_found=compatible_found,
    )
