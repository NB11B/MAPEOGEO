"""Observable helpers for real-phase states."""

from __future__ import annotations

from collections.abc import Sequence
import numpy as np

from .real_phase import Array, RealPhaseError, realify_operator
from .objects import RealPhaseOperator, validate_phase_vector
from .backends.vectorized_local import apply_local_gate_vectorized

_VALID_PAULI = {"I", "X", "Y", "Z"}


def _validate_pauli_string(pauli: str, num_qubits: int | None = None) -> str:
    pauli = pauli.upper().replace(" ", "")
    if not pauli:
        raise RealPhaseError("Pauli string must not be empty.")
    invalid = sorted(set(pauli) - _VALID_PAULI)
    if invalid:
        raise RealPhaseError(f"invalid Pauli symbols {invalid}; expected only I, X, Y, Z.")
    if num_qubits is not None and len(pauli) != int(num_qubits):
        raise RealPhaseError(f"Pauli string length {len(pauli)} incompatible with num_qubits={num_qubits}.")
    return pauli


def _validate_keep(keep: Sequence[int], num_qubits: int) -> tuple[int, ...]:
    keep = tuple(int(k) for k in keep)
    if len(set(keep)) != len(keep):
        raise RealPhaseError(f"keep qubits must be unique; got {keep}.")
    if any(k < 0 or k >= num_qubits for k in keep):
        raise RealPhaseError(f"keep qubits {keep} outside num_qubits={num_qubits}.")
    return keep


def _basis_bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _basis_index(bits: Sequence[int]) -> int:
    n = len(bits)
    out = 0
    for i, bit in enumerate(bits):
        out |= int(bit) << (n - 1 - i)
    return out


def pauli_action(index: int, pauli: str) -> tuple[int, complex]:
    """Return ``(mapped_index, phase)`` for Pauli action on a basis index.

    Qubit indexing is big-endian: symbol 0 acts on the most-significant qubit.
    """
    pauli = _validate_pauli_string(pauli)
    bits = _basis_bits(index, len(pauli))
    phase = 1.0 + 0.0j
    out_bits = list(bits)
    for qubit, symbol in enumerate(pauli):
        bit = bits[qubit]
        if symbol == "I":
            continue
        if symbol == "X":
            out_bits[qubit] = 1 - bit
        elif symbol == "Y":
            out_bits[qubit] = 1 - bit
            phase *= 1j if bit == 0 else -1j
        elif symbol == "Z":
            phase *= 1.0 if bit == 0 else -1.0
    return _basis_index(out_bits), phase


def expectation_pauli_string_real_phase(state_r: Array, pauli: str) -> float:
    """Compute a Pauli-string expectation from a real-phase state vector.

    This uses only the real lanes ``q`` and ``p`` of ``state_r = [q, p]``. The
    returned value is real up to floating-point roundoff because Pauli strings
    are Hermitian.
    """
    pauli = _validate_pauli_string(pauli)
    dim = 2 ** len(pauli)
    state_r = validate_phase_vector(state_r, dim=dim)
    q = state_r[:dim]
    p = state_r[dim:]

    total = 0.0
    for idx in range(dim):
        mapped, phase = pauli_action(idx, pauli)
        pr = float(np.real(phase))
        pi = float(np.imag(phase))
        r = pr * q[mapped] - pi * p[mapped]
        s = pr * p[mapped] + pi * q[mapped]
        total += q[idx] * r + p[idx] * s
    return float(total)


def expectation_local_operator_real_phase(
    state_r: Array,
    operator_r: Array,
    targets: Sequence[int],
    num_qubits: int,
) -> float:
    """Return a local observable expectation using real-phase lanes.

    ``operator_r`` is a realified local operator acting on ``targets``. The
    implementation applies the local real operator through the vectorized local
    backend and computes ``state_r dot (operator state_r)``. For Hermitian local
    observables this equals the real complex expectation value.
    """
    dim = 2**int(num_qubits)
    state_r = validate_phase_vector(state_r, dim=dim)
    applied = apply_local_gate_vectorized(state_r, operator_r, targets, num_qubits)
    return float(np.dot(state_r, applied))


def reduced_density_real_phase(state_r: Array, keep: Sequence[int], num_qubits: int) -> RealPhaseOperator:
    """Return a reduced density operator as a realified block operator.

    The computation is performed directly from real lanes ``q`` and ``p``. For
    kept subsystem index ``i`` and ``j`` and environment index ``e``:

    ``Re rho_ij = sum_e q_ie q_je + p_ie p_je``
    ``Im rho_ij = sum_e p_ie q_je - q_ie p_je``
    """
    num_qubits = int(num_qubits)
    keep = _validate_keep(keep, num_qubits)
    trace = tuple(i for i in range(num_qubits) if i not in keep)
    dim = 2**num_qubits
    state_r = validate_phase_vector(state_r, dim=dim)
    q = state_r[:dim].reshape((2,) * num_qubits)
    p = state_r[dim:].reshape((2,) * num_qubits)

    axes = list(keep) + list(trace)
    q_ke = np.transpose(q, axes).reshape(2 ** len(keep), -1)
    p_ke = np.transpose(p, axes).reshape(2 ** len(keep), -1)
    real = q_ke @ q_ke.T + p_ke @ p_ke.T
    imag = p_ke @ q_ke.T - q_ke @ p_ke.T
    rho = real + 1j * imag
    return RealPhaseOperator(realify_operator(rho), tuple(2 for _ in keep))


def reduced_density_complex(psi: Array, keep: Sequence[int], num_qubits: int) -> np.ndarray:
    """Complex reference reduced density matrix for tests."""
    num_qubits = int(num_qubits)
    keep = _validate_keep(keep, num_qubits)
    trace = tuple(i for i in range(num_qubits) if i not in keep)
    psi = np.asarray(psi, dtype=complex)
    if psi.shape != (2**num_qubits,):
        raise RealPhaseError(f"state shape {psi.shape} incompatible with num_qubits={num_qubits}.")
    tensor = psi.reshape((2,) * num_qubits)
    axes = list(keep) + list(trace)
    moved = np.transpose(tensor, axes).reshape(2 ** len(keep), -1)
    return moved @ moved.conj().T


def _apply_complex_local_operator(
    psi: np.ndarray,
    operator: np.ndarray,
    targets: Sequence[int],
    num_qubits: int,
) -> np.ndarray:
    targets = tuple(int(t) for t in targets)
    if len(set(targets)) != len(targets):
        raise RealPhaseError(f"targets must be unique; got {targets}.")
    if any(t < 0 or t >= num_qubits for t in targets):
        raise RealPhaseError(f"targets {targets} outside num_qubits={num_qubits}.")
    local_dim = 2 ** len(targets)
    operator = np.asarray(operator, dtype=complex)
    if operator.shape != (local_dim, local_dim):
        raise RealPhaseError(f"operator shape {operator.shape} incompatible with {len(targets)} targets.")
    psi = np.asarray(psi, dtype=complex)
    if psi.shape != (2**num_qubits,):
        raise RealPhaseError(f"state shape {psi.shape} incompatible with num_qubits={num_qubits}.")
    tensor = psi.reshape((2,) * num_qubits)
    axes = list(targets) + [i for i in range(num_qubits) if i not in targets]
    inv_axes = np.argsort(axes)
    moved = np.transpose(tensor, axes).reshape(local_dim, -1)
    moved = operator @ moved
    return np.transpose(moved.reshape((2,) * num_qubits), inv_axes).reshape(-1)


def expectation_local_operator_complex(
    psi: Array,
    operator: Array,
    targets: Sequence[int],
    num_qubits: int,
) -> float:
    """Complex reference expectation for local observables."""
    psi = np.asarray(psi, dtype=complex)
    applied = _apply_complex_local_operator(psi, np.asarray(operator, dtype=complex), targets, num_qubits)
    return float(np.real_if_close(np.vdot(psi, applied)).real)


def expectation_pauli_string_complex(psi: Array, pauli: str) -> float:
    """Complex reference implementation for tests and benchmarks."""
    pauli = _validate_pauli_string(pauli)
    psi = np.asarray(psi, dtype=complex)
    dim = 2 ** len(pauli)
    if psi.shape != (dim,):
        raise RealPhaseError(f"state shape {psi.shape} incompatible with Pauli string length {len(pauli)}.")
    total = 0.0 + 0.0j
    for idx in range(dim):
        mapped, phase = pauli_action(idx, pauli)
        total += np.conj(psi[idx]) * phase * psi[mapped]
    return float(np.real_if_close(total).real)
