"""Vectorized local real-phase gate backend.

This backend preserves the same mathematical update as ``local_gate.py``:

    q' = A q - B p
    p' = B q + A p

but batches all affected local blocks into 2-D arrays so the core q/p lane
updates happen through matrix products rather than one Python loop per block.
It still avoids materializing a dense global operator.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import numpy as np

from ..real_phase import Array, RealPhaseError
from ..objects import validate_phase_vector, block_decompose
from .local_gate import iter_local_blocks


@dataclass(frozen=True)
class VectorizedLocalStats:
    blocks: int
    local_dim: int
    gathered_shape: tuple[int, int]


def apply_local_gate_vectorized(
    state_r: Array,
    gate_r: Array,
    targets: Sequence[int],
    num_qubits: int,
    *,
    return_stats: bool = False,
) -> Array | tuple[Array, VectorizedLocalStats]:
    """Apply a local gate by batching all local index blocks.

    Qubit indexing is big-endian and matches ``apply_local_gate``. The returned
    state should match both the scalar local backend and the dual-lane backend
    up to floating-point roundoff.
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

    blocks = np.asarray(iter_local_blocks(num_qubits, targets), dtype=int)
    if blocks.ndim != 2 or blocks.shape[1] != local_dim:
        raise RealPhaseError("internal local-block layout error.")

    q = state_r[:dim]
    p = state_r[dim:]
    q_blocks = q[blocks].T
    p_blocks = p[blocks].T

    q_new = (a @ q_blocks - b @ p_blocks).T
    p_new = (b @ q_blocks + a @ p_blocks).T

    q_out = q.copy()
    p_out = p.copy()
    q_out[blocks] = q_new
    p_out[blocks] = p_new

    out = np.concatenate([q_out, p_out]).astype(float)
    if return_stats:
        return out, VectorizedLocalStats(
            blocks=int(blocks.shape[0]),
            local_dim=local_dim,
            gathered_shape=tuple(int(v) for v in q_blocks.shape),
        )
    return out
