"""Circuit serialization and metric helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .circuit import RealPhaseCircuit
from .measurement import MeasurementWorkflow
from .objects import RealPhaseOperator
from .real_phase import RealPhaseError


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CircuitMetrics:
    """Structural metrics for a real-phase circuit."""

    num_qubits: int
    gate_count: int
    depth: int
    max_gate_width: int
    gate_counts: dict[str, int]
    two_qubit_or_wider_count: int


def circuit_to_dict(circuit: RealPhaseCircuit) -> dict[str, Any]:
    """Serialize a circuit to a JSON-compatible dictionary.

    Gate operators are stored as realified matrices, so this format preserves all
    current gate constructors without depending on a symbolic gate registry.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "format": "ngc-rq-real-phase-circuit",
        "num_qubits": circuit.num_qubits,
        "instructions": [
            {
                "name": instruction.name,
                "targets": list(instruction.targets),
                "dims": list(instruction.gate.dims),
                "operator_real": instruction.gate.data.tolist(),
            }
            for instruction in circuit.instructions
        ],
    }


def circuit_from_dict(payload: dict[str, Any]) -> RealPhaseCircuit:
    """Load a circuit from a dictionary produced by ``circuit_to_dict``."""
    if int(payload.get("schema_version", -1)) != SCHEMA_VERSION:
        raise RealPhaseError(f"unsupported circuit schema_version={payload.get('schema_version')!r}.")
    if payload.get("format") != "ngc-rq-real-phase-circuit":
        raise RealPhaseError(f"unsupported circuit format={payload.get('format')!r}.")
    circuit = RealPhaseCircuit(int(payload["num_qubits"]))
    for item in payload.get("instructions", []):
        gate = RealPhaseOperator(item["operator_real"], tuple(item["dims"]))
        circuit.add_gate(gate, tuple(item["targets"]), name=str(item.get("name") or "gate"))
    return circuit


def circuit_to_json(circuit: RealPhaseCircuit, *, indent: int = 2) -> str:
    """Serialize a circuit to JSON text."""
    return json.dumps(circuit_to_dict(circuit), indent=indent, sort_keys=True) + "\n"


def circuit_from_json(text: str) -> RealPhaseCircuit:
    """Load a circuit from JSON text."""
    return circuit_from_dict(json.loads(text))


def save_circuit(circuit: RealPhaseCircuit, path: str | Path) -> None:
    """Save a circuit JSON file."""
    Path(path).write_text(circuit_to_json(circuit))


def load_circuit(path: str | Path) -> RealPhaseCircuit:
    """Load a circuit JSON file."""
    return circuit_from_json(Path(path).read_text())


def circuit_bundle_to_dict(circuit: RealPhaseCircuit, workflow: MeasurementWorkflow | None = None) -> dict[str, Any]:
    """Serialize a circuit plus optional measurement workflow."""
    payload = circuit_to_dict(circuit)
    if workflow is not None:
        payload["measurement_workflow"] = workflow.to_dict()
    return payload


def circuit_bundle_from_dict(payload: dict[str, Any]) -> tuple[RealPhaseCircuit, MeasurementWorkflow | None]:
    """Load a circuit and optional measurement workflow from one dictionary."""
    circuit = circuit_from_dict(payload)
    workflow_payload = payload.get("measurement_workflow")
    workflow = MeasurementWorkflow.from_dict(workflow_payload) if workflow_payload is not None else None
    return circuit, workflow


def circuit_bundle_to_json(
    circuit: RealPhaseCircuit,
    workflow: MeasurementWorkflow | None = None,
    *,
    indent: int = 2,
) -> str:
    """Serialize a circuit bundle to JSON text."""
    return json.dumps(circuit_bundle_to_dict(circuit, workflow), indent=indent, sort_keys=True) + "\n"


def circuit_bundle_from_json(text: str) -> tuple[RealPhaseCircuit, MeasurementWorkflow | None]:
    """Load a circuit bundle from JSON text."""
    return circuit_bundle_from_dict(json.loads(text))


def circuit_metrics(circuit: RealPhaseCircuit) -> CircuitMetrics:
    """Compute width/depth/gate-mix metrics for a circuit.

    Depth is computed by greedy qubit layering: each instruction is assigned to
    one plus the maximum current layer of its target qubits.
    """
    layers = [0 for _ in range(circuit.num_qubits)]
    gate_counts: Counter[str] = Counter()
    max_gate_width = 0
    two_plus = 0

    for instruction in circuit.instructions:
        targets = tuple(int(t) for t in instruction.targets)
        if not targets:
            raise RealPhaseError("circuit instruction must target at least one qubit.")
        width = len(targets)
        max_gate_width = max(max_gate_width, width)
        if width >= 2:
            two_plus += 1
        name = instruction.name or "gate"
        gate_counts[name] += 1
        layer = 1 + max(layers[t] for t in targets)
        for target in targets:
            layers[target] = layer

    return CircuitMetrics(
        num_qubits=circuit.num_qubits,
        gate_count=len(circuit.instructions),
        depth=max(layers) if layers else 0,
        max_gate_width=max_gate_width,
        gate_counts=dict(sorted(gate_counts.items())),
        two_qubit_or_wider_count=two_plus,
    )


def metrics_to_dict(metrics: CircuitMetrics) -> dict[str, Any]:
    """Convert metrics to a JSON-compatible dictionary."""
    return {
        "num_qubits": metrics.num_qubits,
        "gate_count": metrics.gate_count,
        "depth": metrics.depth,
        "max_gate_width": metrics.max_gate_width,
        "gate_counts": dict(metrics.gate_counts),
        "two_qubit_or_wider_count": metrics.two_qubit_or_wider_count,
    }
