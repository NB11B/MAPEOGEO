"""Sparse observable containers for Pauli-sum measurements."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence
import numpy as np

from .observables import expectation_pauli_string_real_phase, expectation_pauli_string_complex
from .real_phase import Array, RealPhaseError

_VALID_PAULI = {"I", "X", "Y", "Z"}
_PAULI_MATRICES = {
    "I": np.eye(2, dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


@dataclass(frozen=True)
class SparsePauliTerm:
    """One weighted Pauli-string observable term."""

    coefficient: float
    pauli: str

    def __post_init__(self) -> None:
        pauli = str(self.pauli).upper().replace(" ", "")
        if not pauli:
            raise RealPhaseError("Pauli term must not be empty.")
        invalid = sorted(set(pauli) - _VALID_PAULI)
        if invalid:
            raise RealPhaseError(f"invalid Pauli symbols {invalid}; expected only I, X, Y, Z.")
        object.__setattr__(self, "pauli", pauli)
        object.__setattr__(self, "coefficient", float(self.coefficient))


@dataclass(frozen=True)
class SparsePauliObservable:
    """Sparse real-valued observable represented as a weighted Pauli sum."""

    terms: tuple[SparsePauliTerm, ...]
    num_qubits: int

    def __post_init__(self) -> None:
        num_qubits = int(self.num_qubits)
        if num_qubits <= 0:
            raise RealPhaseError("num_qubits must be positive.")
        terms = tuple(self.terms)
        if not terms:
            raise RealPhaseError("SparsePauliObservable requires at least one term.")
        for term in terms:
            if len(term.pauli) != num_qubits:
                raise RealPhaseError(
                    f"Pauli string {term.pauli!r} has length {len(term.pauli)} incompatible with num_qubits={num_qubits}."
                )
        object.__setattr__(self, "num_qubits", num_qubits)
        object.__setattr__(self, "terms", terms)

    @classmethod
    def from_terms(cls, terms: Iterable[tuple[float, str] | SparsePauliTerm], num_qubits: int | None = None) -> "SparsePauliObservable":
        parsed: list[SparsePauliTerm] = []
        for item in terms:
            if isinstance(item, SparsePauliTerm):
                parsed.append(item)
            else:
                coefficient, pauli = item
                parsed.append(SparsePauliTerm(coefficient, pauli))
        if not parsed:
            raise RealPhaseError("SparsePauliObservable requires at least one term.")
        inferred = len(parsed[0].pauli)
        if num_qubits is None:
            num_qubits = inferred
        return cls(tuple(parsed), int(num_qubits))

    def expectation_real_phase(self, state_r: Array) -> float:
        """Evaluate the Pauli-sum expectation from a real-phase state vector."""
        total = 0.0
        for term in self.terms:
            total += term.coefficient * expectation_pauli_string_real_phase(state_r, term.pauli)
        return float(total)

    def expectation_complex(self, psi: Array) -> float:
        """Complex reference expectation for tests."""
        total = 0.0
        for term in self.terms:
            total += term.coefficient * expectation_pauli_string_complex(psi, term.pauli)
        return float(total)

    def to_complex_matrix(self) -> np.ndarray:
        """Materialize the dense complex matrix for tests and small references."""
        dim = 2**self.num_qubits
        out = np.zeros((dim, dim), dtype=complex)
        for term in self.terms:
            mat = np.array([[1]], dtype=complex)
            for symbol in term.pauli:
                mat = np.kron(mat, _PAULI_MATRICES[symbol])
            out += term.coefficient * mat
        return out

    def labels(self) -> tuple[str, ...]:
        return tuple(term.pauli for term in self.terms)

    def coefficients(self) -> tuple[float, ...]:
        return tuple(term.coefficient for term in self.terms)


def sparse_pauli_observable(terms: Sequence[tuple[float, str] | SparsePauliTerm]) -> SparsePauliObservable:
    """Convenience constructor for a sparse Pauli observable."""
    return SparsePauliObservable.from_terms(terms)
