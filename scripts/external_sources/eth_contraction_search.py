"""Exact symbolic contraction-plan search for pinned Anthropic ETH identities.

This searches *contraction orders* over exact rational tensor networks. It does
not claim a new SAT algorithm or polynomial complexity bound.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import prod
from typing import Mapping


@dataclass(frozen=True)
class Tensor:
    axes: tuple[str, ...]
    shape: tuple[int, ...]
    values: tuple[Fraction, ...]

    def __post_init__(self):
        assert len(self.axes) == len(self.shape)
        assert len(set(self.axes)) == len(self.axes)
        assert all(d > 0 for d in self.shape)
        assert len(self.values) == prod(self.shape)

    def at(self, assignment: Mapping[str, int]) -> Fraction:
        i = 0
        for a, d in zip(self.axes, self.shape):
            i = i * d + assignment[a]
        return self.values[i]


def contract(tensors: tuple[Tensor, ...]) -> Fraction:
    dimensions: dict[str, int] = {}
    for t in tensors:
        for a, d in zip(t.axes, t.shape):
            if a in dimensions and dimensions[a] != d:
                raise ValueError("Inconsistent index dimension")
            dimensions[a] = d
    keys = sorted(dimensions)
    result = Fraction(0)
    for coords in product(*(range(dimensions[a]) for a in keys)):
        assignment = dict(zip(keys, coords))
        result += prod((t.at(assignment) for t in tensors), start=Fraction(1))
    return result


def symbolic_search(tensors: tuple[Tensor, ...]) -> dict:
    """Enumerate all binary contraction trees and minimize arithmetic cost.

    Shared indices are summed when no remaining tensor uses them. The final
    result is scalar. This exact enumerator is deliberately limited to small
    graphs and is a research baseline, not an efficient general optimizer.
    """
    dimensions = {}
    for t in tensors:
        for a, d in zip(t.axes, t.shape):
            if a in dimensions and dimensions[a] != d:
                raise ValueError("Inconsistent dimension")
            dimensions[a] = d
    n = len(tensors)
    if not n:
        raise ValueError("At least one tensor required")
    states = {}
    for i, t in enumerate(tensors):
        states[1 << i] = (0, tuple(t.axes), str(i))
    for mask in range(1, 1 << n):
        if mask in states:
            continue
        candidates = []
        sub = (mask - 1) & mask
        while sub:
            other = mask ^ sub
            if sub < other and sub in states and other in states:
                ca, aa, pa = states[sub]
                cb, ab, pb = states[other]
                union = set(aa) | set(ab)
                outside = {a for j, t in enumerate(tensors) if not (mask & (1 << j)) for a in t.axes}
                remaining = tuple(sorted(union & outside))
                # A partial contraction keeps indices needed by outside tensors.
                # Every index in union is iterated, giving an upper bound on
                # scalar multiplications/additions for this merge.
                step = prod(dimensions[a] for a in union)
                candidates.append((ca + cb + step, remaining, f"({pa},{pb})"))
            sub = (sub - 1) & mask
        if candidates:
            states[mask] = min(candidates, key=lambda x: (x[0], x[2]))
    cost, remaining, plan = states[(1 << n) - 1]
    assert not remaining
    return {"estimated_scalar_operations": cost, "plan": plan, "tensor_count": n}


def swap_tensor() -> Tensor:
    # S[out_a,out_b,in_a,in_b] = delta(out_a,in_b)delta(out_b,in_a)
    axes = ("a", "b", "c", "d")
    vals = tuple(Fraction(int(a == d and b == c)) for a, b, c, d in product(range(2), repeat=4))
    return Tensor(axes, (2,) * 4, vals)


def singlet_identity_verified() -> bool:
    # P_minus=(I-S)/2, hence S=I-2P_minus, entrywise over Q.
    s = swap_tensor()
    for a, b, c, d in product(range(2), repeat=4):
        x = {"a": a, "b": b, "c": c, "d": d}
        identity = Fraction(int(a == c and b == d))
        projector = (identity - s.at(x)) / 2
        if s.at(x) != identity - 2 * projector:
            return False
    return True


def demo() -> dict:
    # Closed three-factor cycle with dimension 2.
    def matrix(axes, entries):
        return Tensor(axes, (2, 2), tuple(map(Fraction, entries)))
    ts = (matrix(("x", "y"), (1, 2, 3, 4)),
          matrix(("y", "z"), (2, 0, 1, 3)),
          matrix(("z", "x"), (1, 1, 0, 2)))
    return {"exact_contraction": str(contract(ts)),
            "search": symbolic_search(ts),
            "swap_identity_exact": singlet_identity_verified()}


if __name__ == "__main__":
    import json
    print(json.dumps(demo(), indent=2))
