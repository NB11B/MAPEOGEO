"""Experimental matrix-product-state helpers.

This module is intentionally conservative: it provides exact state-vector to MPS
factorization, optional SVD truncation metadata, and reconstruction back to a
complex state vector. It does not replace the validated state-vector backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
import numpy as np

from ..objects import RealPhaseState
from ..real_phase import Array, RealPhaseError, realify_vector


@dataclass(frozen=True)
class MPSTruncationReport:
    """Summary of SVD truncation during MPS construction."""

    discarded_weight: float
    max_bond_dimension: int
    bond_dimensions: tuple[int, ...]


@dataclass(frozen=True)
class MatrixProductState:
    """Open-boundary MPS with tensors shaped ``(left_bond, physical_dim, right_bond)``."""

    tensors: tuple[Array, ...]
    dims: tuple[int, ...]
    truncation: MPSTruncationReport

    def __post_init__(self) -> None:
        dims = tuple(int(d) for d in self.dims)
        tensors = tuple(np.asarray(t, dtype=complex) for t in self.tensors)
        if len(tensors) != len(dims):
            raise RealPhaseError("number of tensors must match number of subsystem dims.")
        left = 1
        for tensor, dim in zip(tensors, dims):
            if tensor.ndim != 3:
                raise RealPhaseError(f"MPS tensor must be rank-3; got shape {tensor.shape}.")
            if tensor.shape[0] != left:
                raise RealPhaseError("MPS adjacent bond dimensions are inconsistent.")
            if tensor.shape[1] != dim:
                raise RealPhaseError(f"MPS tensor physical dim {tensor.shape[1]} incompatible with dim {dim}.")
            left = int(tensor.shape[2])
        if left != 1:
            raise RealPhaseError("final MPS right bond dimension must be 1 for open-boundary state.")
        object.__setattr__(self, "tensors", tensors)
        object.__setattr__(self, "dims", dims)

    @classmethod
    def from_complex_state(
        cls,
        psi: Array,
        dims: Sequence[int],
        *,
        max_bond_dim: int | None = None,
        svd_cutoff: float = 0.0,
    ) -> "MatrixProductState":
        """Factor a dense complex state vector into an open-boundary MPS."""
        dims = tuple(int(d) for d in dims)
        if any(d <= 0 for d in dims):
            raise RealPhaseError(f"all dims must be positive; got {dims}.")
        dim_total = int(np.prod(dims)) if dims else 1
        psi = np.asarray(psi, dtype=complex).reshape(-1)
        if psi.shape != (dim_total,):
            raise RealPhaseError(f"state shape {psi.shape} incompatible with dims {dims}.")
        if max_bond_dim is not None and int(max_bond_dim) <= 0:
            raise RealPhaseError("max_bond_dim must be positive when supplied.")
        if svd_cutoff < 0:
            raise RealPhaseError("svd_cutoff must be non-negative.")

        tensors: list[Array] = []
        bond_left = 1
        remainder = psi.reshape(1, dim_total)
        discarded_weight = 0.0
        bond_dimensions: list[int] = []
        zero_tol = max(float(svd_cutoff), 1e-14)

        for site, phys_dim in enumerate(dims[:-1]):
            remainder = remainder.reshape(bond_left * phys_dim, -1)
            u, s, vh = np.linalg.svd(remainder, full_matrices=False)
            keep = int(np.sum(s > zero_tol))
            if max_bond_dim is not None:
                keep = min(keep, int(max_bond_dim))
            keep = max(1, keep)

            discarded = s[keep:]
            if discarded.size:
                discarded_weight += float(np.sum(discarded * discarded))
            u = u[:, :keep]
            s_keep = s[:keep]
            vh = vh[:keep, :]
            tensors.append(u.reshape(bond_left, phys_dim, keep))
            bond_dimensions.append(keep)
            remainder = np.diag(s_keep) @ vh
            bond_left = keep

        if dims:
            tensors.append(remainder.reshape(bond_left, dims[-1], 1))
        else:
            tensors.append(remainder.reshape(1, 1, 1))
            dims = (1,)

        report = MPSTruncationReport(
            discarded_weight=float(discarded_weight),
            max_bond_dimension=max(bond_dimensions) if bond_dimensions else 1,
            bond_dimensions=tuple(bond_dimensions),
        )
        return cls(tuple(tensors), dims, report)

    @classmethod
    def from_real_phase_state(
        cls,
        state: RealPhaseState,
        *,
        max_bond_dim: int | None = None,
        svd_cutoff: float = 0.0,
    ) -> "MatrixProductState":
        """Factor a real-phase state into an MPS through its complex view."""
        return cls.from_complex_state(
            state.to_complex(),
            state.dims,
            max_bond_dim=max_bond_dim,
            svd_cutoff=svd_cutoff,
        )

    def to_complex_state(self) -> Array:
        """Reconstruct the dense complex state vector from the MPS."""
        tensor = self.tensors[0]
        for next_tensor in self.tensors[1:]:
            tensor = np.tensordot(tensor, next_tensor, axes=([-1], [0]))
        physical = tensor.reshape(tuple(self.dims))
        return np.asarray(physical, dtype=complex).reshape(-1)

    def to_real_phase_state(self) -> RealPhaseState:
        """Reconstruct a dense real-phase state from the MPS."""
        return RealPhaseState(realify_vector(self.to_complex_state()), self.dims)

    def norm(self) -> float:
        """Return the dense reconstructed state norm."""
        psi = self.to_complex_state()
        return float(np.linalg.norm(psi))

    def reconstruction_error(self, reference: RealPhaseState | Array) -> float:
        """Return L2 reconstruction error against a dense reference state."""
        if isinstance(reference, RealPhaseState):
            ref = reference.to_complex()
        else:
            ref = np.asarray(reference, dtype=complex).reshape(-1)
        return float(np.linalg.norm(self.to_complex_state() - ref))


def real_phase_state_to_mps(
    state: RealPhaseState,
    *,
    max_bond_dim: int | None = None,
    svd_cutoff: float = 0.0,
) -> MatrixProductState:
    """Convenience wrapper for ``MatrixProductState.from_real_phase_state``."""
    return MatrixProductState.from_real_phase_state(state, max_bond_dim=max_bond_dim, svd_cutoff=svd_cutoff)
