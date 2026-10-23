"""
ngc_rq.real_phase

Real-valued phase-plane tools for finite-dimensional complex-to-real
equivalence tests.

Representation:
    psi = a + i b  ->  psi_R = [a, b]

    M = A + i B    ->  M_R = [[A, -B],
                              [B,  A]]

    (a,b) ⊗Ω (c,d) = (a⊗c - b⊗d, a⊗d + b⊗c)

The helpers in this module include complex baselines for validation. The
real-side operations use real arrays and preserve the block structure needed
for phase evolution, composition, measurement, partial trace, and channels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

Array = np.ndarray


class RealPhaseError(ValueError):
    """Raised when a real-phase input has an invalid shape or structure."""


def _as_real_array(x: Array, name: str) -> Array:
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 1:
        raise RealPhaseError(f"{name} must be a one-dimensional real vector; got shape {arr.shape}.")
    return arr


def _as_real_matrix(x: Array, name: str) -> Array:
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise RealPhaseError(f"{name} must be a square real matrix; got shape {arr.shape}.")
    return arr


def realify_vector(psi: Array) -> Array:
    """Convert complex vector psi into stacked real phase vector [Re psi, Im psi]."""
    psi = np.asarray(psi, dtype=complex)
    if psi.ndim != 1:
        raise RealPhaseError(f"psi must be one-dimensional; got shape {psi.shape}.")
    return np.concatenate([psi.real, psi.imag]).astype(float)


def complexify_vector(z: Array) -> Array:
    """Convert stacked real phase vector [q, p] into q + i p."""
    z = _as_real_array(z, "z")
    if z.size % 2:
        raise RealPhaseError(f"z length must be even; got length {z.size}.")
    n = z.size // 2
    return z[:n] + 1j * z[n:]


def realify_operator(m: Array) -> Array:
    """Convert complex matrix M=A+iB into real block form [[A,-B],[B,A]]."""
    m = np.asarray(m, dtype=complex)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise RealPhaseError(f"operator must be square; got shape {m.shape}.")
    a = m.real
    b = m.imag
    return np.block([[a, -b], [b, a]]).astype(float)


def complexify_operator(mr: Array) -> Array:
    """Convert valid real block operator [[A,-B],[B,A]] back into A+iB."""
    mr = _as_real_matrix(mr, "mr")
    if mr.shape[0] % 2:
        raise RealPhaseError(f"realified operator dimension must be even; got {mr.shape}.")
    n = mr.shape[0] // 2
    a = mr[:n, :n]
    minus_b = mr[:n, n:]
    b = mr[n:, :n]
    a2 = mr[n:, n:]
    if not np.allclose(a, a2, atol=1e-8):
        raise RealPhaseError("invalid realified operator: diagonal blocks A do not match.")
    if not np.allclose(minus_b, -b, atol=1e-8):
        raise RealPhaseError("invalid realified operator: off-diagonal blocks are not [-B; B].")
    return a + 1j * b


def make_J(n: int) -> Array:
    """Return canonical phase rotation J=[[0,-I],[I,0]] on R^(2n)."""
    if n <= 0:
        raise RealPhaseError("n must be positive.")
    eye = np.eye(n)
    zero = np.zeros((n, n))
    return np.block([[zero, -eye], [eye, zero]]).astype(float)


def symplectic_error(a: Array) -> float:
    """Compute ||A^T J A - J||_F for a square real operator on R^(2n)."""
    a = _as_real_matrix(a, "a")
    if a.shape[0] % 2:
        raise RealPhaseError("operator dimension must be even for symplectic_error.")
    j = make_J(a.shape[0] // 2)
    return float(np.linalg.norm(a.T @ j @ a - j, ord="fro"))


def orthogonality_error(a: Array) -> float:
    """Compute ||A^T A - I||_F for a square real operator."""
    a = _as_real_matrix(a, "a")
    return float(np.linalg.norm(a.T @ a - np.eye(a.shape[0]), ord="fro"))


def compose_phase_vectors(z1: Array, z2: Array) -> Array:
    """
    Structured real composition corresponding to complex tensor product.

    If z1=[a,b] and z2=[c,d], returns:
        [a⊗c - b⊗d, a⊗d + b⊗c]
    """
    z1 = _as_real_array(z1, "z1")
    z2 = _as_real_array(z2, "z2")
    if z1.size % 2 or z2.size % 2:
        raise RealPhaseError("both real-phase vectors must have even length.")
    n1 = z1.size // 2
    n2 = z2.size // 2
    a, b = z1[:n1], z1[n1:]
    c, d = z2[:n2], z2[n2:]
    real = np.kron(a, c) - np.kron(b, d)
    imag = np.kron(a, d) + np.kron(b, c)
    return np.concatenate([real, imag]).astype(float)


def compose_many_phase_vectors(vectors: Sequence[Array]) -> Array:
    """Associatively compose any non-empty sequence of real-phase vectors."""
    if not vectors:
        raise RealPhaseError("vectors must be non-empty.")
    out = _as_real_array(vectors[0], "vectors[0]")
    for idx, v in enumerate(vectors[1:], start=1):
        out = compose_phase_vectors(out, v)
    return out


def normalize_complex(psi: Array, eps: float = 1e-15) -> Array:
    psi = np.asarray(psi, dtype=complex)
    norm = np.linalg.norm(psi)
    if norm < eps:
        raise RealPhaseError("cannot normalize near-zero complex vector.")
    return psi / norm


def normalize_real_phase(z: Array, eps: float = 1e-15) -> Array:
    z = _as_real_array(z, "z")
    norm = np.linalg.norm(z)
    if norm < eps:
        raise RealPhaseError("cannot normalize near-zero real-phase vector.")
    return z / norm


def expectation_complex(rho: Array, obs: Array) -> complex:
    """Return Tr(rho obs) for complex density/operator matrices."""
    return np.trace(np.asarray(rho, complex) @ np.asarray(obs, complex))


def expectation_real_phase(rho_r: Array, obs_r: Array) -> float:
    """Return 1/2 Tr(rho_R obs_R) for realified density/operator matrices."""
    rho_r = _as_real_matrix(rho_r, "rho_r")
    obs_r = _as_real_matrix(obs_r, "obs_r")
    return float(0.5 * np.trace(rho_r @ obs_r))


def density_from_state_complex(psi: Array) -> Array:
    psi = normalize_complex(psi)
    return np.outer(psi, psi.conj())


def density_from_state_real_phase(z: Array) -> Array:
    """Return realified |psi><psi| for a real-phase state."""
    psi = complexify_vector(normalize_real_phase(z))
    return realify_operator(np.outer(psi, psi.conj()))


def projective_measure_complex(psi: Array, projector: Array, eps: float = 1e-15) -> Tuple[float, Array]:
    """Projectively measure a pure complex state with projector P."""
    psi = normalize_complex(psi)
    projector = np.asarray(projector, dtype=complex)
    p = float(np.real(np.vdot(psi, projector @ psi)))
    if p < eps:
        return p, np.zeros_like(psi)
    return p, projector @ psi / np.sqrt(p)


def projective_measure_real_phase(z: Array, projector_r: Array, eps: float = 1e-15) -> Tuple[float, Array]:
    """Projectively measure a pure real-phase state with realified projector P_R."""
    z = normalize_real_phase(z)
    projector_r = _as_real_matrix(projector_r, "projector_r")
    p = float(z.T @ projector_r @ z)
    if p < eps:
        return p, np.zeros_like(z)
    return p, projector_r @ z / np.sqrt(p)


def partial_trace_complex(rho: Array, dims: Sequence[int], keep: Sequence[int]) -> Array:
    """Partial trace for complex density matrices."""
    rho = np.asarray(rho, dtype=complex)
    dims = tuple(int(d) for d in dims)
    keep = tuple(int(k) for k in keep)
    n_sub = len(dims)
    total_dim = int(np.prod(dims))
    if rho.shape != (total_dim, total_dim):
        raise RealPhaseError(f"rho shape {rho.shape} incompatible with dims {dims}.")
    trace_out = tuple(i for i in range(n_sub) if i not in keep)
    tensor = rho.reshape(dims + dims)
    current_dims = list(dims)
    current_n = n_sub
    for idx in sorted(trace_out, reverse=True):
        tensor = np.trace(tensor, axis1=idx, axis2=idx + current_n)
        del current_dims[idx]
        current_n -= 1
    kept_dim = int(np.prod([dims[i] for i in keep])) if keep else 1
    return tensor.reshape((kept_dim, kept_dim))


def partial_trace_realified_blocks(rho_r: Array, dims: Sequence[int], keep: Sequence[int]) -> Array:
    """Partial trace of a realified density operator by tracing A and B blocks."""
    rho_r = _as_real_matrix(rho_r, "rho_r")
    if rho_r.shape[0] % 2:
        raise RealPhaseError("rho_r dimension must be even.")
    n = rho_r.shape[0] // 2
    a = rho_r[:n, :n]
    b = rho_r[n:, :n]
    red_a = partial_trace_complex(a.astype(complex), dims, keep).real
    red_b = partial_trace_complex(b.astype(complex), dims, keep).real
    return np.block([[red_a, -red_b], [red_b, red_a]]).astype(float)


def apply_channel_complex(rho: Array, kraus_ops: Sequence[Array]) -> Array:
    """Apply a complex Kraus channel: rho' = sum K rho K†."""
    rho = np.asarray(rho, dtype=complex)
    out = np.zeros_like(rho, dtype=complex)
    for k in kraus_ops:
        k = np.asarray(k, dtype=complex)
        out += k @ rho @ k.conj().T
    return out


def apply_channel_real_phase(rho_r: Array, kraus_ops_r: Sequence[Array]) -> Array:
    """Apply a realified Kraus channel: rho_R' = sum K_R rho_R K_R^T."""
    rho_r = _as_real_matrix(rho_r, "rho_r")
    out = np.zeros_like(rho_r, dtype=float)
    for k in kraus_ops_r:
        k = _as_real_matrix(k, "kraus_r")
        out += k @ rho_r @ k.T
    return out


def random_complex_state(dim: int, rng: np.random.Generator) -> Array:
    psi = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    return normalize_complex(psi)


def random_unitary(dim: int, rng: np.random.Generator) -> Array:
    """Generate a Haar-ish random unitary using QR decomposition."""
    z = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    q, r = np.linalg.qr(z)
    phases = np.diag(r)
    phases = phases / np.where(np.abs(phases) == 0, 1.0, np.abs(phases))
    return q * phases


def random_hermitian(dim: int, rng: np.random.Generator) -> Array:
    a = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    return 0.5 * (a + a.conj().T)


def random_density(dim: int, rng: np.random.Generator, rank: int | None = None) -> Array:
    rank = dim if rank is None else int(rank)
    x = rng.normal(size=(dim, rank)) + 1j * rng.normal(size=(dim, rank))
    rho = x @ x.conj().T
    return rho / np.trace(rho)


def random_projector(dim: int, rank: int, rng: np.random.Generator) -> Array:
    u = random_unitary(dim, rng)
    basis = u[:, :rank]
    return basis @ basis.conj().T


def random_kraus_channel(dim: int, num_ops: int, rng: np.random.Generator) -> List[Array]:
    """Generate a random CPTP channel using random matrices normalized by S^{-1/2}."""
    raw = [rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim)) for _ in range(num_ops)]
    s = sum(k.conj().T @ k for k in raw)
    evals, evecs = np.linalg.eigh(s)
    evals = np.maximum(evals, 1e-14)
    inv_sqrt = evecs @ np.diag(1.0 / np.sqrt(evals)) @ evecs.conj().T
    return [k @ inv_sqrt for k in raw]


@dataclass(frozen=True)
class EquivalenceResult:
    name: str
    max_error: float
    mean_error: float
    trials: int

    def passed(self, tolerance: float = 1e-10) -> bool:
        return self.max_error <= tolerance
