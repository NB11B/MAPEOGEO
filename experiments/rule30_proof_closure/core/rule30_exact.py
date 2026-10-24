"""Exact Rule 30 reference semantics reusing frozen G11 definitions and extending to bilateral operators."""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from experiments.rule30_falsification.psmsl_future_work import (
    ETHER_BLOCK_0,
    ETHER_BLOCK_2,
    ether_repeat_0,
    ether_repeat_2,
    iter_period_return as _g11_iter_period_return,
    or_col_word as _g11_or_col_word,
    run_word as _g11_run_word,
    step_row as _g11_step_row,
)


def rule30_bit(left: int, center: int, right: int) -> int:
    """Exact local Rule 30 Boolean update: left XOR (center OR right)."""
    return (left & 1) ^ ((center & 1) | (right & 1))


def evolve_single_seed(steps: int) -> List[Dict[int, int]]:
    """Compute exact single-seed spacetime rows t = 0 .. steps."""
    rows: List[Dict[int, int]] = [{0: 1}]
    for t in range(steps):
        prev = rows[-1]
        nxt: Dict[int, int] = {}
        for p in range(-(t + 1), t + 2):
            val = rule30_bit(prev.get(p - 1, 0), prev.get(p, 0), prev.get(p + 1, 0))
            if val:
                nxt[p] = 1
        rows.append(nxt)
    return rows


def row_at_right(rows: Sequence[Dict[int, int]], t: int, p: int, n: int) -> Tuple[int, ...]:
    """Extract [cell(t, p), cell(t, p + 1), ..., cell(t, p + n - 1)]."""
    row = rows[t]
    return tuple(row.get(p + i, 0) for i in range(n))


def row_at_left(rows: Sequence[Dict[int, int]], t: int, p: int, n: int) -> Tuple[int, ...]:
    """Extract [cell(t, p), cell(t, p - 1), ..., cell(t, p - (n - 1))] from right to left."""
    row = rows[t]
    return tuple(row.get(p - i, 0) for i in range(n))


def step_right_row(left_bit: int, sigma: Sequence[int]) -> Tuple[int, ...]:
    """Reuse frozen G11 step_row for the right-half prefix."""
    return _g11_step_row(left_bit, sigma)


def run_right_word(word: Sequence[int], sigma: Sequence[int]) -> Tuple[int, ...]:
    """Reuse frozen G11 run_word for the right-half prefix."""
    return _g11_run_word(word, sigma)


def iter_period_return(word: Sequence[int], m: int, sigma: Sequence[int]) -> Tuple[int, ...]:
    """Reuse frozen G11 iter_period_return."""
    return _g11_iter_period_return(word, m, sigma)


def or_col_word(word: Sequence[int], sigma: Sequence[int]) -> Tuple[int, ...]:
    """Reuse frozen G11 or_col_word."""
    return _g11_or_col_word(word, sigma)


def step_left_row(right_bit: int, lam: Sequence[int]) -> Tuple[int, ...]:
    """One Rule 30 step on a finite left-half row [x_p, x_{p-1}, ...] with right neighbor at p + 1."""
    if len(lam) < 2:
        return ()
    out: List[int] = []
    r = right_bit & 1
    for i in range(len(lam) - 1):
        a = lam[i] & 1
        b = lam[i + 1] & 1
        out.append(rule30_bit(b, a, r))
        r = a
    return tuple(out)


def run_left_word(word: Sequence[int], lam: Sequence[int]) -> Tuple[int, ...]:
    """Advance a finite left-half prefix through center word w."""
    cur = tuple(int(x) for x in lam)
    for c in word:
        cur = step_left_row(int(c), cur)
    return cur


def obs_left_word(word: Sequence[int], c_after: int, lam: Sequence[int]) -> Tuple[int, ...]:
    """Compute the left-implied observation trace c_{s+1} XOR x_{-1}(t + s) across word w."""
    cur = tuple(int(x) for x in lam)
    w_list = [int(c) for c in word]
    out: List[int] = []
    for s, c in enumerate(w_list):
        c_next = w_list[s + 1] if s + 1 < len(w_list) else int(c_after)
        head = cur[0] if cur else 0
        out.append(c_next ^ head)
        cur = step_left_row(c, cur)
    return tuple(out)


def center_discrepancy_trace(rows: Sequence[Dict[int, int]]) -> List[int]:
    """Compute signed discrepancy sum_{t=0}^{n-1} (2*center(t) - 1) for n = 0 .. len(rows)."""
    disc = [0]
    acc = 0
    for row in rows:
        c = row.get(0, 0)
        acc += 1 if c == 1 else -1
        disc.append(acc)
    return disc


__all__ = [
    "ETHER_BLOCK_0",
    "ETHER_BLOCK_2",
    "ether_repeat_0",
    "ether_repeat_2",
    "rule30_bit",
    "evolve_single_seed",
    "row_at_right",
    "row_at_left",
    "step_right_row",
    "run_right_word",
    "iter_period_return",
    "or_col_word",
    "step_left_row",
    "run_left_word",
    "obs_left_word",
    "center_discrepancy_trace",
]
