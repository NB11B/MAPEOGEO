import numpy as np

from ngc_rq import gates
from ngc_rq.backends.dual_lane import apply_local_gate_dual_lane
from ngc_rq.backends.local_gate import apply_local_gate, iter_local_blocks
from ngc_rq.circuit import RealPhaseCircuit
from ngc_rq.real_phase import random_complex_state, realify_vector


def test_dual_lane_backend_matches_local_backend_for_random_states():
    rng = np.random.default_rng(20260627)
    gate_cases = [
        (gates.H(), (0,)),
        (gates.RZ(0.37), (2,)),
        (gates.CNOT(), (0, 2)),
        (gates.CZ(), (2, 1)),
        (gates.SWAP(), (0, 2)),
    ]
    for gate, targets in gate_cases:
        for _ in range(20):
            psi = random_complex_state(8, rng)
            z = realify_vector(psi)
            local = apply_local_gate(z, gate.data, targets, num_qubits=3)
            dual, stats = apply_local_gate_dual_lane(z, gate.data, targets, num_qubits=3, return_stats=True)
            assert np.linalg.norm(local - dual) < 1e-12
            assert stats.blocks == 2 ** (3 - len(targets))
            assert stats.local_dim == 2 ** len(targets)


def test_circuit_dual_lane_backend_matches_local_backend():
    circuit = RealPhaseCircuit(4)
    circuit.add_gate(gates.H(), [0])
    circuit.add_gate(gates.RZ(0.2), [1])
    circuit.add_gate(gates.CNOT(), [0, 2])
    circuit.add_gate(gates.CZ(), [2, 3])
    circuit.add_gate(gates.SWAP(), [1, 3])
    local = circuit.run(backend="local")
    dual = circuit.run(backend="dual_lane")
    assert np.linalg.norm(local.data - dual.data) < 1e-12
    assert np.allclose(circuit.probabilities(local), circuit.probabilities(dual))


def test_iter_local_blocks_big_endian_indexing():
    blocks = iter_local_blocks(num_qubits=3, targets=(0, 2))
    assert blocks == [[0, 1, 4, 5], [2, 3, 6, 7]]
