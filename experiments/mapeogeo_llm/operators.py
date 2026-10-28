"""Fixed-weight (zero trainable parameter) 8-bit operator circuits.

Every operator is built only from the affine/ReLU Boolean gates below and is
exact on {0,1}-valued inputs. Operators are batched: bit tensors have shape
(8, N), little-endian (row i is bit i).

`reference(op, a, b)` is an independent plain-Python implementation used as
ground truth; it never calls the circuits.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

OPS = ("ADD", "SUB", "XOR", "AND", "OR", "EQ")
COMMUTATIVE = {"ADD", "XOR", "AND", "OR", "EQ"}


def and_gate(a, b):
    return F.relu(a + b - 1)


def or_gate(a, b):
    return (a + b) - and_gate(a, b)


def xor_gate(a, b):
    return a + b - 2 * and_gate(a, b)


def not_gate(a):
    return 1 - a


def _ripple_add(a, b, carry):
    out = []
    for i in range(8):
        t = xor_gate(a[i], b[i])
        out.append(xor_gate(t, carry))
        carry = or_gate(and_gate(a[i], b[i]), and_gate(t, carry))
    return torch.stack(out)


class CompiledALU(nn.Module):
    """Six exact 8-bit operators; no nn.Parameter anywhere."""

    def forward(self, op: str, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        self._check_binary(a)
        self._check_binary(b)
        if op == "ADD":
            return _ripple_add(a, b, torch.zeros_like(a[0]))
        if op == "SUB":  # a - b mod 256 == a + ~b + 1
            return _ripple_add(a, not_gate(b), torch.ones_like(a[0]))
        if op == "XOR":
            return xor_gate(a, b)
        if op == "AND":
            return and_gate(a, b)
        if op == "OR":
            return or_gate(a, b)
        if op == "EQ":  # result is 0 or 1, re-encoded as an 8-bit value
            mism = xor_gate(a, b)
            anyb = torch.zeros_like(a[0])
            for bit in mism:
                anyb = or_gate(anyb, bit)
            out = torch.zeros_like(a)
            out[0] = 1 - anyb
            return out
        raise ValueError(f"unknown operator {op!r}")

    @staticmethod
    def _check_binary(x: torch.Tensor):
        # Gates are only exact on {0,1}; fail closed otherwise.
        if x.shape[0] != 8 or not torch.all((x == 0) | (x == 1)):
            raise ValueError("operands must be (8, N) tensors with entries in {0,1}")


def to_bits(values: torch.Tensor) -> torch.Tensor:
    values = torch.as_tensor(values, dtype=torch.int64)
    if torch.any((values < 0) | (values > 255)):
        raise ValueError("8-bit operands required")
    return torch.stack([((values >> i) & 1).to(torch.float64) for i in range(8)])


def from_bits(bits: torch.Tensor) -> torch.Tensor:
    w = (2 ** torch.arange(8, dtype=torch.int64, device=bits.device))[:, None]
    return (bits.round().to(torch.int64) * w).sum(0)


def reference(op: str, a: int, b: int) -> int:
    """Independent ground truth (plain Python integers)."""
    if op == "ADD":
        return (a + b) % 256
    if op == "SUB":
        return (a - b) % 256
    if op == "XOR":
        return a ^ b
    if op == "AND":
        return a & b
    if op == "OR":
        return a | b
    if op == "EQ":
        return int(a == b)
    raise ValueError(f"unknown operator {op!r}")


def verify_exhaustive(alu: CompiledALU | None = None) -> dict:
    """Check every operator on all 65,536 input pairs against `reference`."""
    alu = alu or CompiledALU()
    v = torch.arange(65536, dtype=torch.int64)
    a, b = v >> 8, v & 255
    ab, bb = to_bits(a), to_bits(b)
    counts = {}
    for op in OPS:
        got = from_bits(alu(op, ab, bb))
        want = torch.tensor([reference(op, int(x), int(y)) for x, y in zip(a.tolist(), b.tolist())])
        mismatches = int((got != want).sum())
        if mismatches:
            raise AssertionError(f"{op}: {mismatches} mismatches")
        counts[op] = 65536
    return counts
