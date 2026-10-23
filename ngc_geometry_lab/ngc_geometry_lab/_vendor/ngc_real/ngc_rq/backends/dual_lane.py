"""Dual-lane real-phase execution backend.

This backend mirrors the hardware-oriented execution model:

    q' = A q - B p
    p' = B q + A p

It computes the q-lane and p-lane contributions as separate paths, then
synchronizes by concatenating the outputs. The reference implementation is
single-process NumPy/Python; it is intentionally structured so the two lane
functions can later map to threads, dual-core MCU tasks, or GPU-style kernels.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import numpy as np

from ..real_phase import Array, RealPhaseError
from ..objects import validate_phase_vector, block_decompose
from .local_gate import iter_local_blocks


@dataclass(frozen=True)
class DualLaneStats:
    """Basic execution counters for the dual-lane reference backend."""

    blocks: int
    local_dim: int
    q_lane_mac_blocks: int
    p_lane_mac_blocks: int


def apply_local_gate_dual_lane(
    state_r: Array,
    gate_r: Array,
    targets: Sequence[int],
    num_qubits: int,
    *,
    return_stats: bool = False,
) -> Array | tuple[Array, DualLaneStats]:
    """Apply a local gate using explicit q-lane/p-lane update paths.

    The numerical result is expected to match ``apply_local_gate`` exactly up to
    floating-point roundoff. The layout is deliberately close to the dual-core
    scheduling model: compute q_out and p_out separately from the same input
    blocks, then synchronize at the final concatenation.
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

    block_count = 0
    for idx in iter_local_blocks(num_qubits, targets):
        q_block = q[idx]
        p_block = p[idx]
        q_out[idx] = a @ q_block - b @ p_block
        p_out[idx] = b @ q_block + a @ p_block
        block_count += 1

    out = np.concatenate([q_out, p_out]).astype(float)
    if return_stats:
        return out, DualLaneStats(
            blocks=block_count,
            local_dim=local_dim,
            q_lane_mac_blocks=2 * block_count,
            p_lane_mac_blocks=2 * block_count,
        )
    return out
