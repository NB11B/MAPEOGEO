"""Measurement-register workflows for real-phase circuits."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping, Sequence
import numpy as np

from .real_phase import RealPhaseError


@dataclass(frozen=True)
class MeasurementRegister:
    """Named computational-basis measurement register."""

    name: str
    qubits: tuple[int, ...]

    def __post_init__(self) -> None:
        name = str(self.name)
        if not name:
            raise RealPhaseError("measurement register name must not be empty.")
        qubits = tuple(int(q) for q in self.qubits)
        if not qubits:
            raise RealPhaseError("measurement register must contain at least one qubit.")
        if len(set(qubits)) != len(qubits):
            raise RealPhaseError(f"measurement register qubits must be unique; got {qubits}.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "qubits", qubits)

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "qubits": list(self.qubits)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MeasurementRegister":
        return cls(str(payload["name"]), tuple(int(q) for q in payload["qubits"]))


@dataclass(frozen=True)
class MeasurementWorkflow:
    """A set of named measurement registers."""

    registers: tuple[MeasurementRegister, ...]

    def __post_init__(self) -> None:
        registers = tuple(self.registers)
        if not registers:
            raise RealPhaseError("measurement workflow requires at least one register.")
        names = [r.name for r in registers]
        if len(set(names)) != len(names):
            raise RealPhaseError(f"measurement register names must be unique; got {names}.")
        object.__setattr__(self, "registers", registers)

    @classmethod
    def from_registers(cls, registers: Iterable[MeasurementRegister | tuple[str, Sequence[int]]]) -> "MeasurementWorkflow":
        parsed: list[MeasurementRegister] = []
        for item in registers:
            if isinstance(item, MeasurementRegister):
                parsed.append(item)
            else:
                name, qubits = item
                parsed.append(MeasurementRegister(name, tuple(qubits)))
        return cls(tuple(parsed))

    def to_dict(self) -> dict[str, object]:
        return {"registers": [r.to_dict() for r in self.registers]}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MeasurementWorkflow":
        return cls(tuple(MeasurementRegister.from_dict(r) for r in payload["registers"]))


def _validate_register(register: MeasurementRegister, num_qubits: int) -> None:
    if any(q < 0 or q >= num_qubits for q in register.qubits):
        raise RealPhaseError(f"register {register.name!r} qubits {register.qubits} outside num_qubits={num_qubits}.")


def _project_index(index: int, qubits: Sequence[int], num_qubits: int) -> str:
    bits = []
    for qubit in qubits:
        bits.append(str((index >> (num_qubits - 1 - int(qubit))) & 1))
    return "".join(bits)


def register_probabilities(
    full_probabilities: Sequence[float],
    register: MeasurementRegister,
    num_qubits: int,
) -> dict[str, float]:
    """Aggregate full computational-basis probabilities onto one register."""
    num_qubits = int(num_qubits)
    _validate_register(register, num_qubits)
    probs = np.asarray(full_probabilities, dtype=float)
    expected = 2**num_qubits
    if probs.shape != (expected,):
        raise RealPhaseError(f"probability vector shape {probs.shape} incompatible with num_qubits={num_qubits}.")
    out = {format(i, f"0{len(register.qubits)}b"): 0.0 for i in range(2 ** len(register.qubits))}
    for index, prob in enumerate(probs):
        out[_project_index(index, register.qubits, num_qubits)] += float(prob)
    return out


def workflow_probabilities(
    full_probabilities: Sequence[float],
    workflow: MeasurementWorkflow,
    num_qubits: int,
) -> dict[str, dict[str, float]]:
    """Aggregate full probabilities for every workflow register."""
    return {
        register.name: register_probabilities(full_probabilities, register, num_qubits)
        for register in workflow.registers
    }


def register_counts(
    full_counts: Mapping[str, int],
    register: MeasurementRegister,
    num_qubits: int,
) -> dict[str, int]:
    """Aggregate full basis-count keys onto one register."""
    num_qubits = int(num_qubits)
    _validate_register(register, num_qubits)
    out = {format(i, f"0{len(register.qubits)}b"): 0 for i in range(2 ** len(register.qubits))}
    for basis, count in full_counts.items():
        basis = str(basis)
        if len(basis) != num_qubits:
            raise RealPhaseError(f"basis key {basis!r} incompatible with num_qubits={num_qubits}.")
        projected = "".join(basis[q] for q in register.qubits)
        out[projected] += int(count)
    return out


def workflow_counts(
    full_counts: Mapping[str, int],
    workflow: MeasurementWorkflow,
    num_qubits: int,
) -> dict[str, dict[str, int]]:
    """Aggregate full counts for every workflow register."""
    return {register.name: register_counts(full_counts, register, num_qubits) for register in workflow.registers}
