"""Real-phase gate constructors.

The public constructors return ``RealPhaseOperator`` objects. Complex matrices are
used internally as a specification bridge for this reference layer; the circuit
runtime can apply the resulting real block gates without complex arithmetic.
"""

from __future__ import annotations

import math
import numpy as np

from .objects import RealPhaseOperator
from .real_phase import RealPhaseError


def _op(matrix: np.ndarray, dims: tuple[int, ...]) -> RealPhaseOperator:
    return RealPhaseOperator.from_complex(np.asarray(matrix, dtype=complex), dims=dims)


def _qubit_dims(num_qubits: int) -> tuple[int, ...]:
    if int(num_qubits) <= 0:
        raise RealPhaseError("num_qubits must be positive.")
    return tuple(2 for _ in range(int(num_qubits)))


def I() -> RealPhaseOperator:
    return _op(np.eye(2, dtype=complex), (2,))


def X() -> RealPhaseOperator:
    return _op(np.array([[0, 1], [1, 0]], dtype=complex), (2,))


def Y() -> RealPhaseOperator:
    return _op(np.array([[0, -1j], [1j, 0]], dtype=complex), (2,))


def Z() -> RealPhaseOperator:
    return _op(np.array([[1, 0], [0, -1]], dtype=complex), (2,))


def H() -> RealPhaseOperator:
    return _op((1 / math.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex), (2,))


def PHASE(theta: float) -> RealPhaseOperator:
    """Return the single-qubit phase gate ``diag(1, exp(i theta))``."""
    return _op(np.array([[1, 0], [0, np.exp(1j * theta)]], dtype=complex), (2,))


def S() -> RealPhaseOperator:
    return PHASE(math.pi / 2)


def T() -> RealPhaseOperator:
    return PHASE(math.pi / 4)


def RX(theta: float) -> RealPhaseOperator:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return _op(np.array([[c, -1j * s], [-1j * s, c]], dtype=complex), (2,))


def RY(theta: float) -> RealPhaseOperator:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return _op(np.array([[c, -s], [s, c]], dtype=complex), (2,))


def RZ(theta: float) -> RealPhaseOperator:
    return _op(
        np.array([[np.exp(-0.5j * theta), 0], [0, np.exp(0.5j * theta)]], dtype=complex),
        (2,),
    )


def PHASE_GRADIENT(num_qubits: int, theta: float = 2 * math.pi) -> RealPhaseOperator:
    """Return a diagonal phase-gradient gate over ``num_qubits``.

    Basis state ``|k>`` receives phase ``exp(i theta k / 2**num_qubits)``. This
    is useful for Fourier-style phase ramps and for testing diagonal structured
    real evolution over multiple qubits.
    """
    n = int(num_qubits)
    dims = _qubit_dims(n)
    dim = 2**n
    phases = np.exp(1j * float(theta) * np.arange(dim) / dim)
    return _op(np.diag(phases), dims)


def QFT_PHASES(num_qubits: int) -> RealPhaseOperator:
    """Return the canonical full-turn phase gradient ``exp(2*pi*i*k/N)``."""
    return PHASE_GRADIENT(num_qubits, theta=2 * math.pi)


def CNOT() -> RealPhaseOperator:
    return CONTROLLED(X())


def CZ() -> RealPhaseOperator:
    return CONTROLLED(Z())


def SWAP() -> RealPhaseOperator:
    return _op(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ],
            dtype=complex,
        ),
        (2, 2),
    )


def CONTROLLED(gate: RealPhaseOperator) -> RealPhaseOperator:
    """Return a one-control version of a one-qubit gate.

    Target ordering is ``[control, target]``. The returned gate acts as identity
    when the control is |0> and as ``gate`` when the control is |1>.
    """
    return MCONTROLLED(gate, num_controls=1)


def MCONTROLLED(gate: RealPhaseOperator, num_controls: int) -> RealPhaseOperator:
    """Return a multi-controlled arbitrary one-qubit gate.

    Target ordering is ``[control_0, ..., control_{k-1}, target]``. The target
    receives ``gate`` only when every control qubit is 1.
    """
    if gate.dims != (2,):
        raise RealPhaseError(f"MCONTROLLED expects a one-qubit gate; got dims {gate.dims}.")
    if num_controls < 1:
        raise RealPhaseError("MCONTROLLED requires at least one control.")
    n = int(num_controls) + 1
    dim = 2**n
    matrix = np.eye(dim, dtype=complex)
    start = dim - 2
    matrix[start:dim, start:dim] = gate.to_complex()
    return _op(matrix, tuple(2 for _ in range(n)))


def CRX(theta: float) -> RealPhaseOperator:
    """Return a controlled-RX gate with targets ``[control, target]``."""
    return CONTROLLED(RX(theta))


def CRY(theta: float) -> RealPhaseOperator:
    """Return a controlled-RY gate with targets ``[control, target]``."""
    return CONTROLLED(RY(theta))


def CRZ(theta: float) -> RealPhaseOperator:
    """Return a controlled-RZ gate with targets ``[control, target]``."""
    return CONTROLLED(RZ(theta))


def MCPHASE_SINGLE(theta: float, num_controls: int) -> RealPhaseOperator:
    """Return a multi-controlled single-qubit PHASE gate."""
    return MCONTROLLED(PHASE(theta), num_controls=num_controls)


def MCX(num_controls: int) -> RealPhaseOperator:
    """Return a multi-controlled X gate.

    Target ordering is ``[control_0, ..., control_{k-1}, target]``. The target
    flips only when every control qubit is 1.
    """
    return MCONTROLLED(X(), num_controls=num_controls)


def TOFFOLI() -> RealPhaseOperator:
    """Return the CCNOT/Toffoli gate with targets ``[control0, control1, target]``."""
    return MCX(2)


def CCNOT() -> RealPhaseOperator:
    """Alias for ``TOFFOLI``."""
    return TOFFOLI()


def MCPHASE(theta: float, num_controls: int = 1) -> RealPhaseOperator:
    """Return a multi-controlled global-on-all-ones phase gate.

    The phase ``exp(i theta)`` is applied only to the all-ones basis state over
    controls plus target. For ``num_controls=1`` this is a controlled phase gate.
    """
    if num_controls < 1:
        raise RealPhaseError("MCPHASE requires at least one control.")
    n = int(num_controls) + 1
    diag = np.ones(2**n, dtype=complex)
    diag[-1] = np.exp(1j * theta)
    return _op(np.diag(diag), tuple(2 for _ in range(n)))


def CPHASE(theta: float) -> RealPhaseOperator:
    """Return a controlled phase gate with targets ``[control, target]``."""
    return MCPHASE(theta, num_controls=1)
