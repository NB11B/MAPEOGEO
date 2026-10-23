"""Local real-phase gate application backend.

This backend applies one- and multi-qubit gates directly to the real phase state
vector. It does not materialize the dense global operator and does not use
complex arithmetic in the update loop.
"""

from __future__ import annotations

from collections.abc import Sequence
import numpy as np

from ..real_phase import Array, RealPhaseError
from ..objects import validate_phase_vector, block_decompose


def _basis_index(bits: Sequence[int]) -> int:
    n = len(bits)
    out = 0
    for i, bit in enumerate(bits):
        out |= int(bit) << (n - 1 - i)
    return out


def _int_bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _target_indices(num_qubits: int, targets: tuple[int, ...], base_bits: list[int]) -> list[int]:
    indices: list[int] = []
    for target_value in range(2 ** len(targets)):
        bits = list(base_bits)
        target_bits = _int_bits(target_value, len(targets))
        for qubit, bit in zip(targets, target_bits):
            bits[qubit] = bit
        indices.append(_basis_index(bits))
    return indices


def iter_local_blocks(num_qubits: int, targets: Sequence[int]) -> list[list[int]]:
    """Return index blocks affected by a local gate.

    Each returned list contains the basis-state indices for one fixed
    assignment of all non-target qubits. The target qubits vary in the order
    supplied by ``targets``.
    """
    targets = tuple(int(t) for t in targets)
    rest = [i for i in range(num_qubits) if i not in targets]
    blocks: list[list[int]] = []
    for rest_value in range(2 ** len(rest)):
        base_bits = [0] * num_qubits
        for qubit, bit in zip(rest, _int_bits(rest_value, len(rest))):
            base_bits[qubit] = bit
        blocks.append(_target_indices(num_qubits, targets, base_bits))
    return blocks


def apply_local_gate(state_r: Array, gate_r: Array, targets: Sequence[int], num_qubits: int) -> Array:
    """Apply a realified local gate to selected qubits of a real-phase state.

    Qubit indexing is big-endian: qubit 0 is the leftmost/most-significant
    tensor factor, matching NumPy ``kron`` ordering in the test baselines.
    """
    if num_qubits <= 0:
        raise RealPhaseError("num_qubits must be positive.")
    targets = tuple(int(t) for t in targets)
    if len(set(targets)) != len(targets):
        raise RealPhaseError(f"targets must be unique; got {targets}.")
    if any(t < 0 or t >= num_qubits for t in targets):
        raise RealPhaseError(f"targets {targets} outside num_qubits={num_qubits}.")

    dim = 2**num_qubits
    state_r = validate_phase_vector(state_r, dim=dim)
    a, b = block_decompose(gate_r, validate=True)
    local_dim = 2 ** len(targets)
    if a.shape != (local_dim, local_dim):
        raise RealPhaseError(f"gate dimension {a.shape} incompatible with {len(targets)} targets.")

    q = state_r[:dim]
    p = state_r[dim:]
    q_out = q.copy()
    p_out = p.copy()

    for idx in iter_local_blocks(num_qubits, targets):
        q_block = q[idx]
        p_block = p[idx]
        q_out[idx] = a @ q_block - b @ p_block
        p_out[idx] = b @ q_block + a @ p_block

    return np.concatenate([q_out, p_out]).astype(float)
