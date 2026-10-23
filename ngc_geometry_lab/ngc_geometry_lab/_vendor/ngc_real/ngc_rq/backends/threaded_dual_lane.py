"""Experimental threaded dual-lane real-phase execution backend.

This backend keeps the same numerical contract as ``dual_lane`` but executes the
q-lane and p-lane block formulas through a small thread pool. It is a scheduling
experiment for hardware-oriented lane separation, not a proven Python speedup.
"""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import numpy as np

from ..real_phase import Array, RealPhaseError
from ..objects import validate_phase_vector, block_decompose
from .local_gate import iter_local_blocks


@dataclass(frozen=True)
class ThreadedDualLaneStats:
    """Execution counters for the threaded dual-lane backend."""

    blocks: int
    local_dim: int
    max_workers: int
    lane_tasks: int


def _q_lane(a: Array, b: Array, q_block: Array, p_block: Array) -> Array:
    return a @ q_block - b @ p_block


def _p_lane(a: Array, b: Array, q_block: Array, p_block: Array) -> Array:
    return b @ q_block + a @ p_block


def apply_local_gate_threaded_dual_lane(
    state_r: Array,
    gate_r: Array,
    targets: Sequence[int],
    num_qubits: int,
    *,
    max_workers: int = 2,
    return_stats: bool = False,
) -> Array | tuple[Array, ThreadedDualLaneStats]:
    """Apply a local gate with threaded q-lane/p-lane block scheduling."""
    if num_qubits <= 0:
        raise RealPhaseError("num_qubits must be positive.")
    if max_workers <= 0:
        raise RealPhaseError("max_workers must be positive.")
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
    blocks = list(iter_local_blocks(num_qubits, targets))

    with ThreadPoolExecutor(max_workers=int(max_workers)) as pool:
        for idx in blocks:
            q_block = q[idx]
            p_block = p[idx]
            q_future = pool.submit(_q_lane, a, b, q_block, p_block)
            p_future = pool.submit(_p_lane, a, b, q_block, p_block)
            q_out[idx] = q_future.result()
            p_out[idx] = p_future.result()

    out = np.concatenate([q_out, p_out]).astype(float)
    if return_stats:
        return out, ThreadedDualLaneStats(
            blocks=len(blocks),
            local_dim=local_dim,
            max_workers=int(max_workers),
            lane_tasks=2 * len(blocks),
        )
    return out
