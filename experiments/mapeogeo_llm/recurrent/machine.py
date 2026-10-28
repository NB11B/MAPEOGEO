"""Fixed-weight, zero-parameter execution engine combining 8-bit modular ALU
and Cl(3,0) Geometric Algebra (Clifford basis products).

Registers and types:
- 8-bit arithmetic values: represented as int in [0, 255] or 8-bit tensors.
- Multivector/blade values: (blade, sign) where blade in [0..7], sign in {+1, -1}.
- Supports precondition validation and fail-closed error handling (Gate R5 & R6).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ALU_OPS = ("ADD", "SUB", "XOR", "AND", "OR", "EQ")
GEO_OPS = ("GEO_GP3",)
ALL_OPS = ALU_OPS + GEO_OPS

def and_gate(a, b): return F.relu(a + b - 1)
def or_gate(a, b): return (a + b) - and_gate(a, b)
def xor_gate(a, b): return a + b - 2 * and_gate(a, b)
def not_gate(a): return 1 - a

def _ripple_add(a, b, carry):
    out = []
    for i in range(8):
        t = xor_gate(a[i], b[i])
        out.append(xor_gate(t, carry))
        carry = or_gate(and_gate(a[i], b[i]), and_gate(t, carry))
    return torch.stack(out)

def to_bits(val: int) -> torch.Tensor:
    if not (0 <= val <= 255):
        raise ValueError(f"Value {val} out of 8-bit bounds [0, 255]")
    return torch.tensor([(val >> i) & 1 for i in range(8)], dtype=torch.float64)

def from_bits(b: torch.Tensor) -> int:
    return sum(int(round(float(v))) << i for i, v in enumerate(b))

def gp_sign_blade(a: int, b: int, signature=(1, 1, 1)) -> tuple[int, int]:
    """Clifford basis product: e_A e_B = sign * e_(A xor B)."""
    n = len(signature)
    if not (0 <= a < 1 << n and 0 <= b < 1 << n):
        raise ValueError(f"Blade index out of bounds: a={a}, b={b}")
    sign = 1
    for i in range(n):
        if (a >> i) & 1:
            if (b & ((1 << i) - 1)).bit_count() % 2:
                sign = -sign
            if (b >> i) & 1:
                sign *= signature[i]
    return sign, a ^ b

def pauli_check_gp3(a: int, b: int) -> tuple[int, int]:
    """Independent ground truth via 2x2 complex Pauli matrices."""
    eye = np.eye(2, dtype=complex)
    pauli = [
        np.array([[0, 1], [1, 0]], complex),
        np.array([[0, -1j], [1j, 0]]),
        np.array([[1, 0], [0, -1]], complex)
    ]
    def blade_mat(mask):
        m = eye.copy()
        for i in range(3):
            if (mask >> i) & 1:
                m = m @ pauli[i]
        return m
    mats = [blade_mat(k) for k in range(8)]
    prod = mats[a] @ mats[b]
    for blade, m in enumerate(mats):
        for sign in (1, -1):
            if np.allclose(prod, sign * m):
                return sign, blade
    raise AssertionError(f"Product not found in basis blades: a={a}, b={b}")

class CompiledALU(nn.Module):
    def forward(self, op: str, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        if op == "ADD": return _ripple_add(a, b, torch.zeros_like(a[0]))
        if op == "SUB": return _ripple_add(a, not_gate(b), torch.ones_like(a[0]))
        if op == "XOR": return xor_gate(a, b)
        if op == "AND": return and_gate(a, b)
        if op == "OR": return or_gate(a, b)
        if op == "EQ":
            mism = xor_gate(a, b)
            anyb = torch.zeros_like(a[0])
            for bit in mism: anyb = or_gate(anyb, bit)
            out = torch.zeros_like(a)
            out[0] = 1 - anyb
            return out
        raise ValueError(f"Unknown ALU op: {op}")

class CompiledGeoGP3(nn.Module):
    def __init__(self, signature=(1, 1, 1)):
        super().__init__()
        weights = torch.zeros((8, 64), dtype=torch.float64)
        for a in range(8):
            for b in range(8):
                sign, blade = gp_sign_blade(a, b, signature)
                weights[blade, a * 8 + b] = sign
        self.register_buffer("weights", weights)

    def forward(self, a: int, b: int) -> tuple[int, int]:
        if not (0 <= a < 8 and 0 <= b < 8):
            raise ValueError(f"Geo blade indices must be in [0, 7], got a={a}, b={b}")
        x = F.one_hot(torch.tensor(a * 8 + b), 64).to(self.weights.dtype)
        v = self.weights @ x
        nz = torch.nonzero(v).flatten().tolist()
        assert len(nz) == 1
        blade = nz[0]
        sign = int(v[blade].item())
        return sign, blade

@dataclass
class Value:
    kind: str  # 'int' or 'geo'
    val: Union[int, Tuple[int, int]]  # int in [0..255] or (sign, blade)

class RecurrentMachineState:
    """Explicit register file state machine."""
    def __init__(self, num_scratch: int = 4):
        self.alu = CompiledALU()
        self.geo = CompiledGeoGP3()
        self.num_scratch = num_scratch
        self.registers: Dict[str, Optional[Value]] = {}
        self.faulted = False
        self.fault_reason = ""

    def reset(self, initial_env: Dict[str, Value]):
        self.registers = {k: v for k, v in initial_env.items()}
        for i in range(self.num_scratch):
            self.registers[f"R{i}"] = None
        self.faulted = False
        self.fault_reason = ""

    def get_register(self, name: str) -> Optional[Value]:
        return self.registers.get(name)

    def step(self, op: str, src1: str, src2: str, dst: str) -> bool:
        """Executes a single step. Returns True on success, False on fault."""
        if self.faulted:
            return False
        if src1 not in self.registers or self.registers[src1] is None:
            self.faulted = True
            self.fault_reason = f"Uninitialized or unknown register src1={src1}"
            return False
        if src2 not in self.registers or self.registers[src2] is None:
            self.faulted = True
            self.fault_reason = f"Uninitialized or unknown register src2={src2}"
            return False

        v1 = self.registers[src1]
        v2 = self.registers[src2]

        if op in ALU_OPS:
            if v1.kind != "int" or v2.kind != "int":
                self.faulted = True
                self.fault_reason = f"Type mismatch for {op}: operands must be int"
                return False
            bits1, bits2 = to_bits(v1.val), to_bits(v2.val)
            res_bits = self.alu(op, bits1, bits2)
            out_val = from_bits(res_bits)
            self.registers[dst] = Value(kind="int", val=out_val)
            return True

        elif op in GEO_OPS:
            if v1.kind != "geo" or v2.kind != "geo":
                self.faulted = True
                self.fault_reason = f"Type mismatch for {op}: operands must be geo blades"
                return False
            sign1, blade1 = v1.val
            sign2, blade2 = v2.val
            # Precondition: blade index in [0, 7]
            if not (0 <= blade1 < 8 and 0 <= blade2 < 8):
                self.faulted = True
                self.fault_reason = f"Geo blade out of bounds"
                return False
            prod_sign, prod_blade = self.geo(blade1, blade2)
            final_sign = sign1 * sign2 * prod_sign
            self.registers[dst] = Value(kind="geo", val=(final_sign, prod_blade))
            return True

        else:
            self.faulted = True
            self.fault_reason = f"Unknown op: {op}"
            return False
