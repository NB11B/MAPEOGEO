"""Real-phase circuit runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .backends.local_gate import apply_local_gate
from .backends.dual_lane import apply_local_gate_dual_lane
from .backends.vectorized_local import apply_local_gate_vectorized
from .backends.threaded_dual_lane import apply_local_gate_threaded_dual_lane
from .objects import RealPhaseOperator, RealPhaseState
from .real_phase import RealPhaseError, realify_vector
from .observables import (
    expectation_pauli_string_real_phase,
    expectation_local_operator_real_phase,
    reduced_density_real_phase,
)
from .sampling import SampleEstimate, summarize_counts
from .sparse_observable import SparsePauliObservable
from .local_observable import SparseLocalOperatorObservable
from .measurement import (
    MeasurementRegister,
    MeasurementWorkflow,
    register_counts,
    register_probabilities,
    workflow_counts,
    workflow_probabilities,
)


@dataclass(frozen=True)
class GateInstruction:
    gate: RealPhaseOperator
    targets: tuple[int, ...]
    name: str = "gate"


class RealPhaseCircuit:
    """Minimal real-phase circuit runner using local real-valued gate updates."""

    def __init__(self, num_qubits: int):
        if num_qubits <= 0:
            raise RealPhaseError("num_qubits must be positive.")
        self.num_qubits = int(num_qubits)
        self.instructions: list[GateInstruction] = []

    def add_gate(self, gate: RealPhaseOperator, targets: Sequence[int], name: str | None = None) -> "RealPhaseCircuit":
        targets = tuple(int(t) for t in targets)
        if gate.dims != tuple(2 for _ in targets):
            raise RealPhaseError(f"gate dims {gate.dims} incompatible with targets {targets}.")
        self.instructions.append(GateInstruction(gate=gate, targets=targets, name=name or "gate"))
        return self

    def initial_zero_state(self) -> RealPhaseState:
        psi = np.zeros(2**self.num_qubits, dtype=complex)
        psi[0] = 1.0
        return RealPhaseState(realify_vector(psi), tuple(2 for _ in range(self.num_qubits)))

    def run(self, initial_state: RealPhaseState | None = None, backend: str = "local") -> RealPhaseState:
        backend_map = {
            "local": apply_local_gate,
            "dual_lane": apply_local_gate_dual_lane,
            "threaded_dual_lane": apply_local_gate_threaded_dual_lane,
            "vectorized": apply_local_gate_vectorized,
        }
        if backend not in backend_map:
            raise RealPhaseError(f"unsupported backend {backend!r}; use one of {sorted(backend_map)}.")
        state = initial_state or self.initial_zero_state()
        expected_dims = tuple(2 for _ in range(self.num_qubits))
        if state.dims != expected_dims:
            raise RealPhaseError(f"state dims {state.dims} incompatible with circuit dims {expected_dims}.")
        z = state.data
        apply_gate = backend_map[backend]
        for instruction in self.instructions:
            z = apply_gate(z, instruction.gate.data, instruction.targets, self.num_qubits)
        return RealPhaseState(z, expected_dims)

    def probabilities(self, state: RealPhaseState | None = None) -> np.ndarray:
        state = state or self.run()
        dim = 2**self.num_qubits
        q = state.data[:dim]
        p = state.data[dim:]
        return q * q + p * p

    def probability_dict(self, state: RealPhaseState | None = None, *, tol: float = 0.0) -> dict[str, float]:
        probs = self.probabilities(state)
        out: dict[str, float] = {}
        for idx, prob in enumerate(probs):
            if prob > tol:
                out[format(idx, f"0{self.num_qubits}b")] = float(prob)
        return out

    def marginal_probabilities(self, keep: Sequence[int], state: RealPhaseState | None = None) -> np.ndarray:
        """Return marginal probabilities for selected qubits in big-endian order."""
        keep = tuple(int(k) for k in keep)
        if len(set(keep)) != len(keep):
            raise RealPhaseError(f"keep qubits must be unique; got {keep}.")
        if any(k < 0 or k >= self.num_qubits for k in keep):
            raise RealPhaseError(f"keep qubits {keep} outside num_qubits={self.num_qubits}.")
        probs = self.probabilities(state).reshape((2,) * self.num_qubits)
        trace_axes = tuple(i for i in range(self.num_qubits) if i not in keep)
        if trace_axes:
            probs = probs.sum(axis=trace_axes)
        return np.asarray(probs).reshape(-1)

    def register_probabilities(
        self,
        register: MeasurementRegister,
        state: RealPhaseState | None = None,
    ) -> dict[str, float]:
        """Return exact probabilities aggregated onto one named measurement register."""
        return register_probabilities(self.probabilities(state), register, self.num_qubits)

    def workflow_probabilities(
        self,
        workflow: MeasurementWorkflow,
        state: RealPhaseState | None = None,
    ) -> dict[str, dict[str, float]]:
        """Return exact probabilities for every register in a workflow."""
        return workflow_probabilities(self.probabilities(state), workflow, self.num_qubits)

    def reduced_density(self, keep: Sequence[int], state: RealPhaseState | None = None) -> RealPhaseOperator:
        """Return the reduced density operator for selected qubits as realified blocks."""
        state = state or self.run()
        return reduced_density_real_phase(state.data, keep, self.num_qubits)

    def expectation_z(self, qubit: int, state: RealPhaseState | None = None) -> float:
        """Return expectation of Pauli-Z on one qubit from probabilities."""
        qubit = int(qubit)
        if qubit < 0 or qubit >= self.num_qubits:
            raise RealPhaseError(f"qubit {qubit} outside num_qubits={self.num_qubits}.")
        probs = self.probabilities(state)
        total = 0.0
        for idx, prob in enumerate(probs):
            bit = (idx >> (self.num_qubits - 1 - qubit)) & 1
            total += (1.0 if bit == 0 else -1.0) * float(prob)
        return float(total)

    def expectation_pauli(self, pauli: str, state: RealPhaseState | None = None) -> float:
        """Return expectation of a Pauli string such as "ZI", "XX", or "YZY"."""
        state = state or self.run()
        if len(pauli.replace(" ", "")) != self.num_qubits:
            raise RealPhaseError(f"Pauli string length {len(pauli.replace(' ', ''))} incompatible with num_qubits={self.num_qubits}.")
        return expectation_pauli_string_real_phase(state.data, pauli)

    def expectation_local_operator(
        self,
        operator: RealPhaseOperator,
        targets: Sequence[int],
        state: RealPhaseState | None = None,
    ) -> float:
        """Return expectation of an arbitrary local real-phase operator."""
        targets = tuple(int(t) for t in targets)
        if operator.dims != tuple(2 for _ in targets):
            raise RealPhaseError(f"operator dims {operator.dims} incompatible with targets {targets}.")
        state = state or self.run()
        return expectation_local_operator_real_phase(state.data, operator.data, targets, self.num_qubits)

    def expectation_sparse_pauli(
        self,
        observable: SparsePauliObservable,
        state: RealPhaseState | None = None,
    ) -> float:
        """Return expectation of a sparse Pauli-sum observable."""
        if observable.num_qubits != self.num_qubits:
            raise RealPhaseError(
                f"observable num_qubits={observable.num_qubits} incompatible with circuit num_qubits={self.num_qubits}."
            )
        state = state or self.run()
        return observable.expectation_real_phase(state.data)

    def expectation_sparse_local(
        self,
        observable: SparseLocalOperatorObservable,
        state: RealPhaseState | None = None,
    ) -> float:
        """Return expectation of a sparse arbitrary-local-operator observable."""
        if observable.num_qubits != self.num_qubits:
            raise RealPhaseError(
                f"observable num_qubits={observable.num_qubits} incompatible with circuit num_qubits={self.num_qubits}."
            )
        state = state or self.run()
        return observable.expectation_real_phase(state.data)

    def sample_counts(
        self,
        shots: int,
        state: RealPhaseState | None = None,
        *,
        seed: int | None = None,
    ) -> dict[str, int]:
        """Sample computational-basis outcomes from the real-valued probabilities."""
        if shots < 0:
            raise RealPhaseError("shots must be non-negative.")
        probs = self.probabilities(state)
        probs = probs / probs.sum()
        rng = np.random.default_rng(seed)
        outcomes = rng.choice(len(probs), size=int(shots), p=probs)
        counts: dict[str, int] = {}
        for outcome in outcomes:
            key = format(int(outcome), f"0{self.num_qubits}b")
            counts[key] = counts.get(key, 0) + 1
        return counts

    def sample_register_counts(
        self,
        register: MeasurementRegister,
        shots: int,
        state: RealPhaseState | None = None,
        *,
        seed: int | None = None,
    ) -> dict[str, int]:
        """Sample full outcomes and aggregate counts onto one register."""
        return register_counts(self.sample_counts(shots, state, seed=seed), register, self.num_qubits)

    def sample_workflow_counts(
        self,
        workflow: MeasurementWorkflow,
        shots: int,
        state: RealPhaseState | None = None,
        *,
        seed: int | None = None,
    ) -> dict[str, dict[str, int]]:
        """Sample full outcomes and aggregate counts for every workflow register."""
        return workflow_counts(self.sample_counts(shots, state, seed=seed), workflow, self.num_qubits)

    def sample_summary(
        self,
        shots: int,
        state: RealPhaseState | None = None,
        *,
        seed: int | None = None,
        confidence: float = 0.95,
        include_zeros: bool = False,
    ) -> dict[str, SampleEstimate]:
        """Sample outcomes and return probability estimates with confidence intervals."""
        counts = self.sample_counts(shots, state, seed=seed)
        return summarize_counts(
            counts,
            num_qubits=self.num_qubits,
            shots=shots,
            confidence=confidence,
            include_zeros=include_zeros,
        )
