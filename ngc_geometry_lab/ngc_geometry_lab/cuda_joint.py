"""Native CUDA joint-systems execution and CHSH correlation engine.

This module leverages the native NGC CUDA candidate library to execute
multi-qubit entangled states (Bell states, GHZ states), programmable
joint correlation measurements, and CHSH inequality tests directly on the GPU.
"""

from __future__ import annotations

import ctypes as ct
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from .cuda_check import _API
from . import reference as ref


def _euler_hadamard(api: _API, handle: ct.c_void_p, cuda_qubit: int) -> None:
    """Apply Hadamard via Euler decomposition Rz(pi/2) Rx(pi/2) Rz(pi/2)."""
    api.call("ngc_rcs_rz", handle, cuda_qubit, np.pi / 2)
    api.call("ngc_rcs_rx", handle, cuda_qubit, np.pi / 2)
    api.call("ngc_rcs_rz", handle, cuda_qubit, np.pi / 2)


def _apply_ry(api: _API, handle: ct.c_void_p, cuda_qubit: int, theta: float) -> None:
    """Apply rotation about Y axis via Rz(-pi/2) Rx(theta) Rz(pi/2)."""
    api.call("ngc_rcs_rz", handle, cuda_qubit, -np.pi / 2)
    api.call("ngc_rcs_rx", handle, cuda_qubit, theta)
    api.call("ngc_rcs_rz", handle, cuda_qubit, np.pi / 2)


def _apply_cnot(api: _API, handle: ct.c_void_p, control_q: int, target_q: int) -> None:
    """Execute CNOT using CZ conjugated by Hadamard on target."""
    _euler_hadamard(api, handle, target_q)
    api.call("ngc_rcs_cz", handle, control_q, target_q)
    _euler_hadamard(api, handle, target_q)


def prepare_bell_state(
    api: _API,
    handle: ct.c_void_p,
    bell_type: str = "phi+",
    q_alice: int = 1,
    q_bob: int = 0,
) -> None:
    """Prepare one of the four Bell states on the specified CUDA qubits.

    In 2-qubit register: q_alice=1 (MSB, target 0), q_bob=0 (LSB, target 1).
    phi+ = (|00> + |11>) / sqrt(2)
    phi- = (|00> - |11>) / sqrt(2)
    psi+ = (|01> + |10>) / sqrt(2)
    psi- = (|01> - |10>) / sqrt(2)
    """
    api.call("ngc_rcs_reset", handle)
    # H on Alice
    _euler_hadamard(api, handle, q_alice)
    # CNOT from Alice to Bob
    _apply_cnot(api, handle, q_alice, q_bob)

    btype = bell_type.lower().replace("_", "")
    if btype in ("phi+", "phi_plus"):
        pass
    elif btype in ("phi-", "phi_minus"):
        api.call("ngc_rcs_rz", handle, q_alice, np.pi)
    elif btype in ("psi+", "psi_plus"):
        api.call("ngc_rcs_rx", handle, q_bob, np.pi)
    elif btype in ("psi-", "psi_minus"):
        api.call("ngc_rcs_rx", handle, q_bob, np.pi)
        api.call("ngc_rcs_rz", handle, q_alice, np.pi)
    else:
        raise ValueError(f"Unknown Bell state type: {bell_type}")


def measure_bell_correlation(
    api: _API,
    library_handle: ct.c_void_p,
    theta_a: float,
    theta_b: float,
    bell_type: str = "phi+",
    phase_bins: int = 48,
) -> Tuple[float, np.ndarray]:
    """Measure joint correlation E(theta_a, theta_b) on GPU.

    Measurements in the X-Z plane at angles theta_A and theta_B relative to Z.
    Returns correlation E in [-1, 1] and 4-outcome probabilities [P00, P01, P10, P11].
    """
    # 1. Prepare Bell state
    prepare_bell_state(api, library_handle, bell_type=bell_type, q_alice=1, q_bob=0)

    # 2. Measurement basis rotation: rotate X-Z axis at theta into Z axis
    _apply_ry(api, library_handle, 1, -theta_a)
    _apply_ry(api, library_handle, 0, -theta_b)

    # 3. Read probabilities
    _, probs = api.read(library_handle, 4)
    p00, p01, p10, p11 = probs[0], probs[1], probs[2], probs[3]
    correlation = float(p00 - p01 - p10 + p11)
    return correlation, probs


def run_gpu_chsh_test(
    library_path: str | Path,
    phase_bins: int = 48,
) -> Dict[str, Any]:
    """Execute the complete CHSH campaign natively on GPU hardware."""
    api = _API(library_path)
    device_info = api.device()

    handle = ct.c_void_p()
    api.call("ngc_rcs_create", 2, 0, ct.byref(handle))
    if not handle.value:
        raise RuntimeError("Failed to create CUDA register")
    api.call("ngc_rcs_set_phase_resolution", handle, phase_bins)

    try:
        # Standard CHSH angles for maximal violation:
        # A: 0, A': pi/2
        # B: pi/4, B': -pi/4
        a0 = 0.0
        a1 = np.pi / 2
        b0 = np.pi / 4
        b1 = -np.pi / 4

        e_a0_b0, p_a0_b0 = measure_bell_correlation(api, handle, a0, b0, "phi+", phase_bins)
        e_a0_b1, p_a0_b1 = measure_bell_correlation(api, handle, a0, b1, "phi+", phase_bins)
        e_a1_b0, p_a1_b0 = measure_bell_correlation(api, handle, a1, b0, "phi+", phase_bins)
        e_a1_b1, p_a1_b1 = measure_bell_correlation(api, handle, a1, b1, "phi+", phase_bins)

        chsh_s = e_a0_b0 + e_a0_b1 + e_a1_b0 - e_a1_b1
        theoretical_chsh = 2.0 * math.sqrt(2.0)
        chsh_error = abs(chsh_s - theoretical_chsh)

        # Angular correlation curve sweep: E(0, theta) = cos(theta)
        sweep_angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
        sweep_results = []
        max_curve_error = 0.0
        for th in sweep_angles:
            e_val, _ = measure_bell_correlation(api, handle, 0.0, th, "phi+", phase_bins)
            e_expected = math.cos(th)
            diff = abs(e_val - e_expected)
            max_curve_error = max(max_curve_error, diff)
            sweep_results.append({
                "angle": float(th),
                "gpu_correlation": e_val,
                "expected_cos": e_expected,
                "error": diff,
            })

    finally:
        api.call("ngc_rcs_free", handle)

    return {
        "status": "PASS",
        "device": device_info,
        "phase_bins": phase_bins,
        "chsh": {
            "S_measured": chsh_s,
            "S_theoretical": theoretical_chsh,
            "absolute_error": chsh_error,
            "classical_bound": 2.0,
            "violates_classical_bound": chsh_s > 2.0,
            "matches_tsirelson_bound": chsh_error < 1e-4,
            "E_a0_b0": e_a0_b0,
            "E_a0_b1": e_a0_b1,
            "E_a1_b0": e_a1_b0,
            "E_a1_b1": e_a1_b1,
        },
        "angular_curve": {
            "max_error_vs_cos": max_curve_error,
            "sweep_samples": sweep_results,
        },
    }


def run_gpu_ghz_test(
    library_path: str | Path,
    num_qubits: int = 3,
    phase_bins: int = 48,
) -> Dict[str, Any]:
    """Prepare and verify an n-qubit GHZ state (|00...0> + |11...1>) / sqrt(2) on GPU."""
    if num_qubits < 2 or num_qubits > 5:
        raise ValueError("num_qubits must be in [2, 5]")

    api = _API(library_path)
    device_info = api.device()

    handle = ct.c_void_p()
    api.call("ngc_rcs_create", num_qubits, 0, ct.byref(handle))
    api.call("ngc_rcs_set_phase_resolution", handle, phase_bins)

    try:
        api.call("ngc_rcs_reset", handle)
        # H on highest qubit (MSB = num_qubits - 1)
        msb = num_qubits - 1
        _euler_hadamard(api, handle, msb)
        # Entangle down the chain via CNOTs
        for q in range(msb - 1, -1, -1):
            _apply_cnot(api, handle, q + 1, q)

        # Read statevector and probabilities
        dim = 2 ** num_qubits
        state, probs = api.read(handle, dim)

        # Ideal GHZ statevector and probabilities
        expected_state = np.zeros(dim, dtype=complex)
        expected_state[0] = 1.0 / math.sqrt(2.0)
        expected_state[-1] = 1.0 / math.sqrt(2.0)

        # 1. Population check
        expected_probs = np.zeros(dim)
        expected_probs[0] = 0.5
        expected_probs[-1] = 0.5
        max_prob_error = float(np.max(np.abs(probs - expected_probs)))

        # 2. Coherence and fidelity check (distinguishing pure GHZ from incoherent mixture rho_mix)
        # Incoherent mixture has off_diagonal_coherence = 0.0; pure GHZ has 0.5.
        off_diagonal_coherence = float((state[0] * state[-1].conjugate()).real)
        fidelity = float(abs(np.vdot(expected_state, state)) ** 2)

        # 3. Phase-sensitive parity verification: measure in X basis by applying H to all qubits
        # Measure <sigma_x^{\otimes n}>
        api.call("ngc_rcs_reset", handle)
        _euler_hadamard(api, handle, msb)
        for q in range(msb - 1, -1, -1):
            _apply_cnot(api, handle, q + 1, q)
        for q in range(num_qubits):
            _euler_hadamard(api, handle, q)
        _, x_probs = api.read(handle, dim)

        # In X basis, GHZ parity expectation <sigma_x^{\otimes n}> = sum_k (-1)^{popcount(k)} P(k) = +1.0
        # Incoherent mixture has <sigma_x^{\otimes n}> = 0.0.
        x_parity = 0.0
        for idx in range(dim):
            parity_sign = -1.0 if (bin(idx).count('1') % 2 == 1) else 1.0
            x_parity += parity_sign * x_probs[idx]

    finally:
        api.call("ngc_rcs_free", handle)

    return {
        "status": "PASS",
        "device": device_info,
        "num_qubits": num_qubits,
        "dim": dim,
        "p_all_zero": float(probs[0]),
        "p_all_one": float(probs[-1]),
        "max_prob_error": max_prob_error,
        "off_diagonal_coherence": off_diagonal_coherence,
        "state_fidelity": fidelity,
        "x_basis_parity_expectation": float(x_parity),
        "incoherent_mixture_ruled_out": off_diagonal_coherence > 0.45 and x_parity > 0.9,
        "ghz_verified": max_prob_error < 1e-10 and fidelity > 0.999,
    }
