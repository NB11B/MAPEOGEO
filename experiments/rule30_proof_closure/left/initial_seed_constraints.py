"""Track A — Left-cone initial-seed support constraints and pure left-half elimination horizons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.rule30_exact import obs_left_word


@dataclass(frozen=True)
class LeftConeEliminationSample:
    """Record of pure left-half black-step elimination for a candidate (T, w)."""

    transient_t: int
    period_p: int
    word: str
    total_cone_states: int
    left_unsat_horizon_h: Optional[int]
    surviving_left_states: int


def evaluate_left_cone_elimination(
    transient_t: int,
    word: Sequence[int],
    max_horizon: int = 48,
) -> LeftConeEliminationSample:
    """Compute the exact horizon at which all 2^{T-1} left-cone states fail c_w(s)=1 -> obs_left(s)=1."""
    w = tuple(int(b) for b in word)
    p = len(w)
    if transient_t == 0:
        candidates: List[Tuple[int, ...]] = [()]
    else:
        candidates = [
            tuple(((mask >> i) & 1) for i in range(transient_t - 1)) + (1,)
            for mask in range(1 << (transient_t - 1))
        ]

    w_ext = [w[s % p] for s in range(max_horizon + 1)]
    fail_horizons: List[Optional[int]] = []

    for lam_init in candidates:
        padded = lam_init + (0,) * (max_horizon + 2)
        obs = obs_left_word(w_ext[:max_horizon], w_ext[max_horizon], padded)
        fail_h: Optional[int] = None
        for s in range(max_horizon):
            if w_ext[s] == 1 and obs[s] != 1:
                fail_h = s + 1
                break
        fail_horizons.append(fail_h)

    surviving = sum(1 for fh in fail_horizons if fh is None)
    unsat_h = max(fh for fh in fail_horizons if fh is not None) if surviving == 0 else None
    return LeftConeEliminationSample(
        transient_t=transient_t,
        period_p=p,
        word="".join(str(b) for b in w),
        total_cone_states=len(candidates),
        left_unsat_horizon_h=unsat_h,
        surviving_left_states=surviving,
    )
