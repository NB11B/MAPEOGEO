"""Sparse sums of arbitrary local real-phase observables."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence
import numpy as np

from .objects import RealPhaseOperator
from .observables import expectation_local_operator_real_phase
from .real_phase import Array, RealPhaseError


@dataclass(frozen=True)
class SparseLocalOperatorTerm:
    """One weighted local operator term."""

    coefficient: float
    operator: RealPhaseOperator
    targets: tuple[int, ...]

    def __post_init__(self) -> None:
        coefficient = float(self.coefficient)
        targets = tuple(int(t) for t in self.targets)
        if not targets:
            raise RealPhaseError("local operator term must target at least one qubit.")
        if len(set(targets)) != len(targets):
            raise RealPhaseError(f"local operator targets must be unique; got {targets}.")
        if self.operator.dims != tuple(2 for _ in targets):
            raise RealPhaseError(f"operator dims {self.operator.dims} incompatible with targets {targets}.")
        object.__setattr__(self, "coefficient", coefficient)
        object.__setattr__(self, "targets", targets)


@dataclass(frozen=True)
class SparseLocalOperatorObservable:
    """Sparse observable formed from arbitrary local real-phase operators."""

    terms: tuple[SparseLocalOperatorTerm, ...]
    num_qubits: int

    def __post_init__(self) -> None:
        num_qubits = int(self.num_qubits)
        if num_qubits <= 0:
            raise RealPhaseError("num_qubits must be positive.")
        terms = tuple(self.terms)
        if not terms:
            raise RealPhaseError("sparse local observable requires at least one term.")
        for term in terms:
            if any(t < 0 or t >= num_qubits for t in term.targets):
                raise RealPhaseError(f"term targets {term.targets} outside num_qubits={num_qubits}.")
        object.__setattr__(self, "num_qubits", num_qubits)
        object.__setattr__(self, "terms", terms)

    @classmethod
    def from_terms(
        cls,
        terms: Iterable[tuple[float, RealPhaseOperator, Sequence[int]]],
        *,
        num_qubits: int,
    ) -> "SparseLocalOperatorObservable":
        """Build from ``(coefficient, operator, targets)`` tuples."""
        parsed = tuple(SparseLocalOperatorTerm(c, op, tuple(targets)) for c, op, targets in terms)
        return cls(parsed, int(num_qubits))

    def expectation_real_phase(self, state_r: Array) -> float:
        """Evaluate the sparse local observable on a real-phase state vector."""
        total = 0.0
        for term in self.terms:
            value = expectation_local_operator_real_phase(state_r, term.operator.data, term.targets, self.num_qubits)
            total += term.coefficient * float(value)
        return float(total)

    def to_complex_matrix(self) -> Array:
        """Build a dense complex matrix reference for small systems/tests."""
        dim = 2**self.num_qubits
        dense = np.zeros((dim, dim), dtype=complex)
        for term in self.terms:
            dense += term.coefficient * _embed_operator(term.operator.to_complex(), term.targets, self.num_qubits)
        return dense

    def expectation_complex(self, psi: Array) -> float:
        """Dense complex reference expectation for tests/small systems."""
        psi = np.asarray(psi, dtype=complex).reshape(-1)
        if psi.shape != (2**self.num_qubits,):
            raise RealPhaseError(f"state shape {psi.shape} incompatible with num_qubits={self.num_qubits}.")
        return float(np.real(np.vdot(psi, self.to_complex_matrix() @ psi)))


def _embed_operator(operator: Array, targets: Sequence[int], num_qubits: int) -> Array:
    """Embed a local complex operator into the full computational-basis space."""
    targets = tuple(int(t) for t in targets)
    k = len(targets)
    dim = 2**int(num_qubits)
    local_dim = 2**k
    op = np.asarray(operator, dtype=complex)
    if op.shape != (local_dim, local_dim):
        raise RealPhaseError(f"operator shape {op.shape} incompatible with {k} target qubits.")
    target_positions = {target: i for i, target in enumerate(targets)}
    dense = np.zeros((dim, dim), dtype=complex)

    for col in range(dim):
        local_col = 0
        untouched = 0
        untouched_bits: list[tuple[int, int]] = []
        for qubit in range(num_qubits):
            bit = (col >> (num_qubits - 1 - qubit)) & 1
            if qubit in target_positions:
                local_col = (local_col << 1) | bit
            else:
                untouched_bits.append((qubit, bit))
                untouched = (untouched << 1) | bit

        for local_row in range(local_dim):
            amp = op[local_row, local_col]
            if amp == 0:
                continue
            row = 0
            target_bit_idx = 0
            untouched_idx = 0
            for qubit in range(num_qubits):
                row <<= 1
                if qubit in target_positions:
                    bit = (local_row >> (k - 1 - target_bit_idx)) & 1
                    target_bit_idx += 1
                else:
                    bit = untouched_bits[untouched_idx][1]
                    untouched_idx += 1
                row |= bit
            dense[row, col] += amp
    return dense


def sparse_local_observable(
    terms: Iterable[tuple[float, RealPhaseOperator, Sequence[int]]],
    *,
    num_qubits: int,
) -> SparseLocalOperatorObservable:
    """Convenience constructor for sparse local operator observables."""
    return SparseLocalOperatorObservable.from_terms(terms, num_qubits=num_qubits)
