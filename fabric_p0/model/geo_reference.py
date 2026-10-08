# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Python Reference Model for Fixed-Point Arithmetic and Geometric Operators

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class FixedCl20:
    s: int
    e1: int
    e2: int
    e12: int

    @classmethod
    def zero(cls) -> FixedCl20:
        return cls(0, 0, 0, 0)

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.s, self.e1, self.e2, self.e12)


class FixedPointModel:
    def __init__(self, width: int = 32, frac: int = 16):
        self.width = width
        self.frac = frac
        self.min_val = -(1 << (width - 1))
        self.max_val = (1 << (width - 1)) - 1
        self.mask = (1 << width) - 1

    def from_float(self, val: float) -> int:
        scaled = round(val * (1 << self.frac))
        if scaled < self.min_val or scaled > self.max_val:
            raise OverflowError(f"Float {val} out of range for fixed point Q{self.width-self.frac}.{self.frac}")
        return scaled

    def to_float(self, val: int) -> float:
        return val / (1 << self.frac)

    def round_product(self, product: int) -> Tuple[int, bool]:
        """Symmetric rounding of 2*width product matching RTL."""
        negative = product < 0
        magnitude = -product if negative else product
        frac_mask = (1 << self.frac) - 1
        half = 1 << (self.frac - 1)
        quotient = magnitude >> self.frac
        remainder = magnitude & frac_mask
        if remainder >= half:
            quotient += 1
        rounded = -quotient if negative else quotient
        overflow = rounded < self.min_val or rounded > self.max_val
        return (rounded if not overflow else 0), overflow

    def add(self, a: int, b: int) -> Tuple[int, bool]:
        res = a + b
        overflow = res < self.min_val or res > self.max_val
        return (res if not overflow else 0), overflow

    def sub(self, a: int, b: int) -> Tuple[int, bool]:
        res = a - b
        overflow = res < self.min_val or res > self.max_val
        return (res if not overflow else 0), overflow

    def mul(self, a: int, b: int) -> Tuple[int, bool]:
        full = a * b
        return self.round_product(full)

    def cl20_mul(self, a: FixedCl20, b: FixedCl20) -> Tuple[FixedCl20, bool]:
        """Hardened Cl(2,0) geometric product with wide accumulation and overflow detection."""
        products = [
            ("p00", a.s, b.s), ("p11", a.e1, b.e1), ("p22", a.e2, b.e2), ("p33", a.e12, b.e12),
            ("p01", a.s, b.e1), ("p10", a.e1, b.s), ("p23", a.e2, b.e12), ("p32", a.e12, b.e2),
            ("p02", a.s, b.e2), ("p20", a.e2, b.s), ("p13", a.e1, b.e12), ("p31", a.e12, b.e1),
            ("p03", a.s, b.e12), ("p30", a.e12, b.s), ("p12", a.e1, b.e2), ("p21", a.e2, b.e1)
        ]
        q = {}
        prod_ovf = False
        for name, op1, op2 in products:
            val, ovf = self.round_product(op1 * op2)
            q[name] = val
            if ovf:
                prod_ovf = True

        sum_s = q["p00"] + q["p11"] + q["p22"] - q["p33"]
        sum_e1 = q["p01"] + q["p10"] - q["p23"] + q["p32"]
        sum_e2 = q["p02"] + q["p20"] + q["p13"] - q["p31"]
        sum_e12 = q["p03"] + q["p30"] + q["p12"] - q["p21"]

        accum_ovf = any(
            x < self.min_val or x > self.max_val
            for x in (sum_s, sum_e1, sum_e2, sum_e12)
        )
        total_ovf = prod_ovf or accum_ovf
        if total_ovf:
            return FixedCl20.zero(), True
        return FixedCl20(sum_s, sum_e1, sum_e2, sum_e12), False

    def reverse(self, a: FixedCl20) -> Tuple[FixedCl20, bool]:
        if a.e12 == self.min_val:
            return FixedCl20.zero(), True
        return FixedCl20(a.s, a.e1, a.e2, -a.e12), False

    def grade_involution(self, a: FixedCl20) -> Tuple[FixedCl20, bool]:
        if a.e1 == self.min_val or a.e2 == self.min_val:
            return FixedCl20.zero(), True
        return FixedCl20(a.s, -a.e1, -a.e2, a.e12), False

    def clifford_conjugate(self, a: FixedCl20) -> Tuple[FixedCl20, bool]:
        if a.e1 == self.min_val or a.e2 == self.min_val or a.e12 == self.min_val:
            return FixedCl20.zero(), True
        return FixedCl20(a.s, -a.e1, -a.e2, -a.e12), False

    def vector_dot(self, a: FixedCl20, b: FixedCl20) -> Tuple[int, bool]:
        p1, ovf1 = self.mul(a.e1, b.e1)
        p2, ovf2 = self.mul(a.e2, b.e2)
        dot, ovf_sum = self.add(p1, p2)
        ovf = ovf1 or ovf2 or ovf_sum
        return (dot if not ovf else 0), ovf

    def vector_wedge(self, a: FixedCl20, b: FixedCl20) -> Tuple[int, bool]:
        p1, ovf1 = self.mul(a.e1, b.e2)
        p2, ovf2 = self.mul(a.e2, b.e1)
        wedge, ovf_sub = self.sub(p1, p2)
        ovf = ovf1 or ovf2 or ovf_sub
        return (wedge if not ovf else 0), ovf

    def commutator(self, a: FixedCl20, b: FixedCl20) -> Tuple[FixedCl20, bool]:
        ab, ovf_ab = self.cl20_mul(a, b)
        ba, ovf_ba = self.cl20_mul(b, a)
        ovf = ovf_ab or ovf_ba
        if ovf:
            return FixedCl20.zero(), True
        # (ab - ba) / 2
        return FixedCl20(
            (ab.s - ba.s) >> 1,
            (ab.e1 - ba.e1) >> 1,
            (ab.e2 - ba.e2) >> 1,
            (ab.e12 - ba.e12) >> 1
        ), False

    def anticommutator(self, a: FixedCl20, b: FixedCl20) -> Tuple[FixedCl20, bool]:
        ab, ovf_ab = self.cl20_mul(a, b)
        ba, ovf_ba = self.cl20_mul(b, a)
        ovf = ovf_ab or ovf_ba
        if ovf:
            return FixedCl20.zero(), True
        # (ab + ba) / 2
        return FixedCl20(
            (ab.s + ba.s) >> 1,
            (ab.e1 + ba.e1) >> 1,
            (ab.e2 + ba.e2) >> 1,
            (ab.e12 + ba.e12) >> 1
        ), False

    def matrix_to_cl20(self, a: int, b: int, c: int, d: int) -> FixedCl20:
        s = (a + d) >> 1
        x = (a - d) >> 1
        y = (b + c) >> 1
        z = (b - c) >> 1
        return FixedCl20(s, x, y, z)

    def cl20_to_matrix(self, mv: FixedCl20) -> Tuple[Tuple[int, int, int, int], bool]:
        a = mv.s + mv.e1
        b = mv.e2 + mv.e12
        c = mv.e2 - mv.e12
        d = mv.s - mv.e1
        ovf = any(val < self.min_val or val > self.max_val for val in (a, b, c, d))
        if ovf:
            return (0, 0, 0, 0), True
        return (a, b, c, d), False
