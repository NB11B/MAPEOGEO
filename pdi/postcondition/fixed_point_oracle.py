# SPDX-License-Identifier: MIT
"""Bit-Exact RTL Q16.16 Fixed-Point Arithmetic and Cl(2,0) Simulator.

Directly models the RTL hardware logic in:
- fabric_p0/rtl/operators/geo_fixed_arith.sv
- fabric_p0/rtl/operators/geo_cl20_multivector.sv

Format:
- 32-bit signed integer representing Q16.16 fixed-point value:
  value_float = value_int / 65536.0
  value_int   = round(value_float * 65536.0)
- Symmetric round-half-up (RTL round_product)
- Fail-closed overflow detection (zero on overflow)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


WIDTH = 32
FRAC = 16
INT_MIN = -(1 << (WIDTH - 1))  # -2147483648
INT_MAX = (1 << (WIDTH - 1)) - 1  # 2147483647
MASK32 = 0xFFFFFFFF


def to_q16(val: float) -> int:
    """Converts a Python float to signed 32-bit Q16.16 integer representation."""
    raw = int(round(val * 65536.0))
    if raw > INT_MAX:
        return INT_MAX
    if raw < INT_MIN:
        return INT_MIN
    return raw


def signed32(x: int) -> int:
    """Normalize integer to signed 32-bit range [-2^31, 2^31 - 1]."""
    return ((x + (1 << 31)) % (1 << 32)) - (1 << 31)


def from_q16(q: int) -> float:
    """Converts signed 32-bit Q16.16 integer to float."""
    return signed32(q) / 65536.0


def rtl_add(a: int, b: int) -> Tuple[int, bool]:
    """Models geo_fixed_arith addition."""
    ext = a + b
    overflow = (ext > INT_MAX) or (ext < INT_MIN)
    res = 0 if overflow else ext
    return res, overflow


def rtl_sub(a: int, b: int) -> Tuple[int, bool]:
    """Models geo_fixed_arith subtraction."""
    ext = a - b
    overflow = (ext > INT_MAX) or (ext < INT_MIN)
    res = 0 if overflow else ext
    return res, overflow


def rtl_round_product(p: int) -> Tuple[int, bool]:
    """Bit-exact Python replica of round_product function in geo_fixed_arith.sv."""
    negative = p < 0
    magnitude = -p if negative else p
    mask = (1 << FRAC) - 1
    half = 1 << (FRAC - 1)
    quotient = magnitude >> FRAC
    remainder = magnitude & mask
    if remainder >= half:
        quotient += 1
    rounded = -quotient if negative else quotient
    overflow = (rounded > INT_MAX) or (rounded < INT_MIN)
    return (0 if overflow else rounded), overflow


def rtl_mul(a: int, b: int) -> Tuple[int, bool]:
    """Models geo_fixed_arith multiplication."""
    full_prod = a * b
    return rtl_round_product(full_prod)


@dataclass
class Q16Multivector:
    s: int = 0
    e1: int = 0
    e2: int = 0
    e12: int = 0

    @classmethod
    def from_floats(cls, s: float = 0.0, e1: float = 0.0, e2: float = 0.0, e12: float = 0.0) -> Q16Multivector:
        return cls(to_q16(s), to_q16(e1), to_q16(e2), to_q16(e12))

    def to_floats(self) -> Tuple[float, float, float, float]:
        return (from_q16(self.s), from_q16(self.e1), from_q16(self.e2), from_q16(self.e12))

    def to_dict(self) -> dict[str, int]:
        return {"s": self.s, "e1": self.e1, "e2": self.e2, "e12": self.e12}

    def copy(self) -> Q16Multivector:
        return Q16Multivector(self.s, self.e1, self.e2, self.e12)

    def equals(self, other: Q16Multivector) -> bool:
        return (self.s == other.s and self.e1 == other.e1 and self.e2 == other.e2 and self.e12 == other.e12)

    def canonical_hex(self) -> str:
        return f"{self.s & 0xFFFFFFFF:08x}_{self.e1 & 0xFFFFFFFF:08x}_{self.e2 & 0xFFFFFFFF:08x}_{self.e12 & 0xFFFFFFFF:08x}"


class RTLCliffordSimulator:
    """Bit-exact software execution of geo_cl20_multivector.sv."""

    @classmethod
    def cl20_product(cls, a: Q16Multivector, b: Q16Multivector) -> Tuple[Q16Multivector, bool]:
        # 16 elementary product pairs
        p00 = a.s * b.s
        p11 = a.e1 * b.e1
        p22 = a.e2 * b.e2
        p33 = a.e12 * b.e12

        p01 = a.s * b.e1
        p10 = a.e1 * b.s
        p23 = a.e2 * b.e12
        p32 = a.e12 * b.e2

        p02 = a.s * b.e2
        p20 = a.e2 * b.s
        p13 = a.e1 * b.e12
        p31 = a.e12 * b.e1

        p03 = a.s * b.e12
        p30 = a.e12 * b.s
        p12 = a.e1 * b.e2
        p21 = a.e2 * b.e1

        q00, ov00 = rtl_round_product(p00)
        q11, ov11 = rtl_round_product(p11)
        q22, ov22 = rtl_round_product(p22)
        q33, ov33 = rtl_round_product(p33)

        q01, ov01 = rtl_round_product(p01)
        q10, ov10 = rtl_round_product(p10)
        q23, ov23 = rtl_round_product(p23)
        q32, ov32 = rtl_round_product(p32)

        q02, ov02 = rtl_round_product(p02)
        q20, ov20 = rtl_round_product(p20)
        q13, ov13 = rtl_round_product(p13)
        q31, ov31 = rtl_round_product(p31)

        q03, ov03 = rtl_round_product(p03)
        q30, ov30 = rtl_round_product(p30)
        q12, ov12 = rtl_round_product(p12)
        q21, ov21 = rtl_round_product(p21)

        product_overflow = (
            ov00 or ov11 or ov22 or ov33 or
            ov01 or ov10 or ov23 or ov32 or
            ov02 or ov20 or ov13 or ov31 or
            ov03 or ov30 or ov12 or ov21
        )

        sum_s = q00 + q11 + q22 - q33
        sum_e1 = q01 + q10 - q23 + q32
        sum_e2 = q02 + q20 + q13 - q31
        sum_e12 = q03 + q30 + q12 - q21

        final_overflow = (
            (sum_s > INT_MAX or sum_s < INT_MIN) or
            (sum_e1 > INT_MAX or sum_e1 < INT_MIN) or
            (sum_e2 > INT_MAX or sum_e2 < INT_MIN) or
            (sum_e12 > INT_MAX or sum_e12 < INT_MIN)
        )

        overflow = product_overflow or final_overflow
        if overflow:
            return Q16Multivector(0, 0, 0, 0), True

        return Q16Multivector(sum_s, sum_e1, sum_e2, sum_e12), False

    @classmethod
    def vector_dot(cls, a: Q16Multivector, b: Q16Multivector) -> Tuple[Q16Multivector, bool]:
        # Symmetric scalar inner product: a_e1*b_e1 + a_e2*b_e2
        p11, ov1 = rtl_mul(a.e1, b.e1)
        p22, ov2 = rtl_mul(a.e2, b.e2)
        res, ov3 = rtl_add(p11, p22)
        ov = ov1 or ov2 or ov3
        return Q16Multivector(s=0 if ov else res, e1=0, e2=0, e12=0), ov

    @classmethod
    def vector_wedge(cls, a: Q16Multivector, b: Q16Multivector) -> Tuple[Q16Multivector, bool]:
        # Exterior product: (a_e1*b_e2 - a_e2*b_e1) e12
        p12, ov1 = rtl_mul(a.e1, b.e2)
        p21, ov2 = rtl_mul(a.e2, b.e1)
        res, ov3 = rtl_sub(p12, p21)
        ov = ov1 or ov2 or ov3
        return Q16Multivector(s=0, e1=0, e2=0, e12=0 if ov else res), ov

    @classmethod
    def commutator(cls, a: Q16Multivector, b: Q16Multivector) -> Tuple[Q16Multivector, bool]:
        # 1/2 [A, B] = 1/2 (A*B - B*A)
        ab, ov1 = cls.cl20_product(a, b)
        ba, ov2 = cls.cl20_product(b, a)
        if ov1 or ov2:
            return Q16Multivector(0, 0, 0, 0), True
        diff_s, _ = rtl_sub(ab.s, ba.s)
        diff_e1, _ = rtl_sub(ab.e1, ba.e1)
        diff_e2, _ = rtl_sub(ab.e2, ba.e2)
        diff_e12, _ = rtl_sub(ab.e12, ba.e12)
        half = 1 << (FRAC - 1)  # 0.5 in Q16.16
        res_s, _ = rtl_mul(diff_s, half)
        res_e1, _ = rtl_mul(diff_e1, half)
        res_e2, _ = rtl_mul(diff_e2, half)
        res_e12, _ = rtl_mul(diff_e12, half)
        return Q16Multivector(res_s, res_e1, res_e2, res_e12), False

    @classmethod
    def compute_op(cls, op: str, srcs: list[Q16Multivector]) -> Tuple[Q16Multivector, bool]:
        if op in ("OP_VECTOR_WEDGE", "wedge"):
            return cls.vector_wedge(srcs[0], srcs[1])
        elif op in ("OP_VECTOR_DOT", "dot"):
            return cls.vector_dot(srcs[0], srcs[1])
        elif op in ("OP_CL20_PRODUCT", "mul", "geometric"):
            return cls.cl20_product(srcs[0], srcs[1])
        elif op in ("OP_COMMUTATOR", "commutator"):
            return cls.commutator(srcs[0], srcs[1])
        elif op in ("OP_SUB", "sub"):
            s, o1 = rtl_sub(srcs[0].s, srcs[1].s)
            e1, o2 = rtl_sub(srcs[0].e1, srcs[1].e1)
            e2, o3 = rtl_sub(srcs[0].e2, srcs[1].e2)
            e12, o4 = rtl_sub(srcs[0].e12, srcs[1].e12)
            return Q16Multivector(s, e1, e2, e12), (o1 or o2 or o3 or o4)
        elif op in ("OP_ADD", "add"):
            s, o1 = rtl_add(srcs[0].s, srcs[1].s)
            e1, o2 = rtl_add(srcs[0].e1, srcs[1].e1)
            e2, o3 = rtl_add(srcs[0].e2, srcs[1].e2)
            e12, o4 = rtl_add(srcs[0].e12, srcs[1].e12)
            return Q16Multivector(s, e1, e2, e12), (o1 or o2 or o3 or o4)
        elif op in ("OP_REVERSE", "reverse"):
            return Q16Multivector(srcs[0].s, srcs[0].e1, srcs[0].e2, -srcs[0].e12), False
        elif op in ("OP_GRADE_INVOLUTION", "grade_involution"):
            return Q16Multivector(srcs[0].s, -srcs[0].e1, -srcs[0].e2, srcs[0].e12), False
        elif op in ("OP_CLIFFORD_CONJUGATE", "clifford_conjugate"):
            return Q16Multivector(srcs[0].s, -srcs[0].e1, -srcs[0].e2, -srcs[0].e12), False
        raise ValueError(f"Operator {op} not supported in RTLCliffordSimulator")

