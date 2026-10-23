"""Object wrappers for real-phase states and operators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

from .real_phase import (
    Array,
    RealPhaseError,
    compose_phase_vectors,
    complexify_operator,
    complexify_vector,
    density_from_state_real_phase,
    orthogonality_error,
    projective_measure_real_phase,
    realify_operator,
    realify_vector,
    symplectic_error,
)


def dims_product(dims: Sequence[int]) -> int:
    dims = tuple(int(d) for d in dims)
    if any(d <= 0 for d in dims):
        raise RealPhaseError(f"all dims must be positive; got {dims}.")
    return int(np.prod(dims)) if dims else 1


def validate_phase_vector(z: Array, *, dim: int | None = None) -> Array:
    z = np.asarray(z, dtype=float)
    if z.ndim != 1:
        raise RealPhaseError(f"phase vector must be one-dimensional; got shape {z.shape}.")
    if z.size % 2:
        raise RealPhaseError(f"phase vector length must be even; got {z.size}.")
    if dim is not None and z.size != 2 * int(dim):
        raise RealPhaseError(f"phase vector length {z.size} incompatible with dim {dim}.")
    return z


def block_decompose(mr: Array, *, atol: float = 1e-8, validate: bool = True) -> Tuple[Array, Array]:
    mr = np.asarray(mr, dtype=float)
    if mr.ndim != 2 or mr.shape[0] != mr.shape[1]:
        raise RealPhaseError(f"realified operator must be square; got shape {mr.shape}.")
    if mr.shape[0] % 2:
        raise RealPhaseError(f"realified operator dimension must be even; got {mr.shape}.")
    n = mr.shape[0] // 2
    a = mr[:n, :n]
    minus_b = mr[:n, n:]
    b = mr[n:, :n]
    a2 = mr[n:, n:]
    if validate:
        if not np.allclose(a, a2, atol=atol):
            raise RealPhaseError("invalid realified operator: diagonal blocks A do not match.")
        if not np.allclose(minus_b, -b, atol=atol):
            raise RealPhaseError("invalid realified operator: off-diagonal blocks are not [-B; B].")
    return a, b


def is_realified_operator(mr: Array, *, atol: float = 1e-8) -> bool:
    try:
        block_decompose(mr, atol=atol, validate=True)
        return True
    except RealPhaseError:
        return False


def validate_realified_operator(mr: Array, *, dim: int | None = None, atol: float = 1e-8) -> Array:
    mr = np.asarray(mr, dtype=float)
    if dim is not None and mr.shape != (2 * int(dim), 2 * int(dim)):
        raise RealPhaseError(f"operator shape {mr.shape} incompatible with dim {dim}.")
    block_decompose(mr, atol=atol, validate=True)
    return mr


@dataclass(frozen=True)
class RealPhaseOperator:
    """A realified block operator with optional subsystem dimensions."""

    data: Array
    dims: Tuple[int, ...]

    def __post_init__(self) -> None:
        dims = tuple(int(d) for d in self.dims)
        dim = dims_product(dims)
        data = validate_realified_operator(self.data, dim=dim)
        object.__setattr__(self, "data", data)
        object.__setattr__(self, "dims", dims)

    @classmethod
    def from_complex(cls, op: Array, dims: Sequence[int]) -> "RealPhaseOperator":
        dims = tuple(int(d) for d in dims)
        dim = dims_product(dims)
        op = np.asarray(op, dtype=complex)
        if op.shape != (dim, dim):
            raise RealPhaseError(f"operator shape {op.shape} incompatible with dims {dims}.")
        return cls(realify_operator(op), dims)

    def to_complex(self) -> Array:
        return complexify_operator(self.data)

    def apply(self, state: "RealPhaseState") -> "RealPhaseState":
        if state.dims != self.dims:
            raise RealPhaseError(f"operator dims {self.dims} do not match state dims {state.dims}.")
        return RealPhaseState(self.data @ state.data, state.dims)

    def compose(self, other: "RealPhaseOperator") -> "RealPhaseOperator":
        composed = np.kron(self.to_complex(), other.to_complex())
        return RealPhaseOperator.from_complex(composed, self.dims + other.dims)

    def symplectic_error(self) -> float:
        return symplectic_error(self.data)

    def orthogonality_error(self) -> float:
        return orthogonality_error(self.data)


@dataclass(frozen=True)
class RealPhaseState:
    """A real phase vector [q,p] with subsystem dimensions."""

    data: Array
    dims: Tuple[int, ...]

    def __post_init__(self) -> None:
        dims = tuple(int(d) for d in self.dims)
        dim = dims_product(dims)
        data = validate_phase_vector(self.data, dim=dim)
        object.__setattr__(self, "data", data)
        object.__setattr__(self, "dims", dims)

    @classmethod
    def from_complex(cls, psi: Array, dims: Sequence[int]) -> "RealPhaseState":
        dims = tuple(int(d) for d in dims)
        dim = dims_product(dims)
        psi = np.asarray(psi, dtype=complex)
        if psi.shape != (dim,):
            raise RealPhaseError(f"state shape {psi.shape} incompatible with dims {dims}.")
        return cls(realify_vector(psi), dims)

    def to_complex(self) -> Array:
        return complexify_vector(self.data)

    def compose(self, other: "RealPhaseState") -> "RealPhaseState":
        return RealPhaseState(compose_phase_vectors(self.data, other.data), self.dims + other.dims)

    def density(self) -> Array:
        return density_from_state_real_phase(self.data)

    def measure(self, projector: RealPhaseOperator) -> Tuple[float, "RealPhaseState"]:
        if projector.dims != self.dims:
            raise RealPhaseError(f"projector dims {projector.dims} do not match state dims {self.dims}.")
        p, post = projective_measure_real_phase(self.data, projector.data)
        return p, RealPhaseState(post, self.dims)
