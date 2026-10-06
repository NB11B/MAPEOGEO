"""Electrical-power and linear-control routes for Work Router v0.3."""
from __future__ import annotations
from .work_router import RouteEdge, WorkRouter


def power_control_router() -> WorkRouter:
    return WorkRouter((
        # Phasor power: S = V * conj(I) = P + jQ.
        RouteEdge("power.complex", "power.voltage_current_phasors", "work.complex_power", 2.0, True, "V*conj(I)"),
        RouteEdge("power.real", "work.complex_power", "work.real_power", 0.2, True, "real(S)"),
        RouteEdge("power.reactive", "work.complex_power", "work.reactive_power", 0.2, True, "imag(S)"),
        RouteEdge("power.apparent", "power.voltage_current_magnitudes", "work.apparent_power", 0.5, True, "|V||I|"),
        RouteEdge("power.factor", "power.voltage_current_phasors", "work.power_factor", 1.0, True, "cos(angle(V)-angle(I))"),
        RouteEdge("power.rms.voltage", "power.voltage_window", "work.voltage_rms", 2.0, True, "sqrt(mean(v^2))"),
        RouteEdge("power.rms.current", "power.current_window", "work.current_rms", 2.0, True, "sqrt(mean(i^2))"),
        RouteEdge("power.thd.spectrum", "power.voltage_window", "work.voltage_spectrum", 12.0, True, "FFT", materializes=True),
        RouteEdge("power.thd", "work.voltage_spectrum", "work.voltage_thd", 2.0, True, "harmonic RMS / fundamental"),
        # A scalar RMS value cannot determine THD.
        RouteEdge("power.unsafe.rms-to-thd", "work.voltage_rms", "work.voltage_thd", 0.1, False, "RMS does not identify harmonic distribution"),
        # Linear control: stability is determined by spectral abscissa when available.
        RouteEdge("control.eigs", "control.state_matrix", "work.eigenvalues", 10.0, True, "eig(A)", materializes=True),
        RouteEdge("control.spectral-abscissa", "work.eigenvalues", "work.spectral_abscissa", 1.0, True, "max real(lambda)"),
        RouteEdge("control.stability", "work.spectral_abscissa", "work.asymptotically_stable", 0.2, True, "alpha(A)<0"),
        RouteEdge("control.generator-stability", "psmsl.generator_g", "work.asymptotically_stable", 0.2, True, "g<0"),
        RouteEdge("control.trajectory", "control.state_matrix", "work.time_trajectory", 20.0, True, "exp(At)x0", requires=("control.initial_state",), materializes=True),
    ))
