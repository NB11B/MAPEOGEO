"""Independent exact-integer Collatz oracle for COLLATZ-C10 (Workstream 5 / Gate G5).

Uses only Python arbitrary-precision integers (`int`) and exact modular inverses
`pow(A, -1, D)`—never floating-point approximations (`float` / `math.log2`)—and
cross-checks directional parity conventions against step-by-step execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def accelerated_step(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    return n // 2 if (n & 1) == 0 else (3 * n + 1) // 2


def accelerated_collatz(n: int) -> int:
    return accelerated_step(n)


def iterate_accelerated(n: int, steps: int) -> int:
    curr = n
    for _ in range(steps):
        curr = accelerated_step(curr)
    return curr


def parity_word_of(r: int, n: int) -> List[bool]:
    curr = n
    bits: List[bool] = []
    for _ in range(r):
        b = (curr & 1) == 1
        bits.append(b)
        curr = (3 * curr + 1) // 2 if b else curr // 2
    return bits


def apply_parity_word_exact(n: int, word: Sequence[int | bool]) -> int | None:
    curr = n
    for b in word:
        if (curr & 1) != int(bool(b)):
            return None
        curr = (3 * curr + 1) // 2 if b else curr // 2
    return curr


def affine_triple_exact(word: Sequence[int | bool]) -> tuple[int, int, int]:
    """Return (A(w), B(w), D(w)) satisfying D(w) * F_w(n) = A(w) * n + B(w)."""
    A = 1
    B = 0
    D = 1
    for b in word:
        if not b:
            D *= 2
        else:
            A *= 3
            B = 3 * B + D
            D *= 2
    return A, B, D


def word_A(word: Sequence[int | bool]) -> int:
    return affine_triple_exact(word)[0]


def word_B(word: Sequence[int | bool]) -> int:
    return affine_triple_exact(word)[1]


def word_D(word: Sequence[int | bool]) -> int:
    return affine_triple_exact(word)[2]


def word_ones(word: Sequence[int | bool]) -> int:
    return sum(1 for b in word if b)


def canonical_residue_mod_inv(word: Sequence[int | bool]) -> int:
    """Independent modular-inverse calculation of r_0(w) = (-A(w)^-1 * B(w)) mod D(w)."""
    A, B, D = affine_triple_exact(word)
    inv_A = pow(A, -1, D)
    return (-inv_A * B) % D


def word_residue(word: Sequence[int | bool]) -> int:
    return canonical_residue_mod_inv(word)


def min_rep_output(word: Sequence[int | bool]) -> int:
    A, B, D = affine_triple_exact(word)
    r0 = canonical_residue_mod_inv(word)
    return (A * r0 + B) // D


def min_word_rep_exact(word: Sequence[int | bool]) -> int:
    r0 = canonical_residue_mod_inv(word)
    D = 1 << len(word)
    return r0 + D if r0 <= 1 else r0


def min_class_rep(word: Sequence[int | bool]) -> int:
    return min_word_rep_exact(word)


def enumerate_first_crossing_words(max_depth: int) -> List[List[bool]]:
    """Enumerate all first-crossing parity words w of length 1 <= r <= max_depth."""
    results: List[List[bool]] = []
    # Queue of expanding words (w, A, D) with D <= A
    queue: List[tuple[List[bool], int, int]] = [([], 1, 1)]
    for _depth in range(1, max_depth + 1):
        next_queue: List[tuple[List[bool], int, int]] = []
        for w, A, D in queue:
            for bit in (False, True):
                w_next = w + [bit]
                A_next = A * 3 if bit else A
                D_next = D * 2
                if D_next > A_next:
                    results.append(w_next)
                else:
                    next_queue.append((w_next, A_next, D_next))
        queue = next_queue
    return results


def first_crossing_prefix(n: int, max_steps: int = 1000) -> List[bool] | None:
    curr = n
    w: List[bool] = []
    A = 1
    D = 1
    for _ in range(max_steps):
        bit = (curr & 1) == 1
        w.append(bit)
        A = A * 3 if bit else A
        D *= 2
        curr = (3 * curr + 1) // 2 if bit else curr // 2
        if D > A:
            return w
    return None


def nondescent_sandwich_check(n: int, r: int) -> Dict[str, Any]:
    """Check the C10 Non-Descent Diophantine Sandwich on the length-r prefix of n."""
    w = parity_word_of(r, n)
    A, B, D = affine_triple_exact(w)
    a = word_ones(w)
    fr = iterate_accelerated(n, r)
    fr_ge_n = fr >= n
    lower_holds = (D - A) * n <= B
    upper_holds = (n ** a) * (A * n + B) <= n * ((3 * n + 1) ** a)
    power_ratio_holds = D * (n ** a) <= ((3 * n + 1) ** a)
    return {
        "n": n,
        "r": r,
        "a": a,
        "fr": fr,
        "fr_ge_n": fr_ge_n,
        "lower_bound_holds": lower_holds,
        "upper_bound_holds": upper_holds,
        "power_ratio_holds": power_ratio_holds,
    }


def odd_to_odd_return_step(n: int) -> tuple[int, int]:
    """Return (T(n), v_2(3n + 1)) for an odd positive integer n."""
    if (n & 1) != 1:
        raise ValueError("n must be odd")
    val = 3 * n + 1
    v2 = 0
    while (val & 1) == 0:
        val >>= 1
        v2 += 1
    return val, v2


def verify_diophantine_sandwich_on_prefix(n: int, max_steps: int = 200) -> dict:
    """Verify the C10 Non-Descent Diophantine Sandwich up to the first descent step of n."""
    curr = n
    a = 0
    steps_before_descent = 0
    for r in range(1, max_steps + 1):
        b = curr & 1
        curr = (3 * curr + 1) // 2 if b else curr // 2
        a += b
        lhs = (1 << r) * (n ** a) * curr
        rhs = n * ((3 * n + 1) ** a)
        assert lhs <= rhs, (n, r, a, curr, lhs, rhs)
        if curr < n:
            return {
                "n": n,
                "descended": True,
                "descent_step": r,
                "odd_steps": a,
                "power_threshold_crossed": (1 << r) * (n ** a) > ((3 * n + 1) ** a),
            }
        assert (1 << r) * (n ** a) <= ((3 * n + 1) ** a), (n, r, a, curr)
        steps_before_descent = r
    return {"n": n, "descended": False, "steps_checked": steps_before_descent}
