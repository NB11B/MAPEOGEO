"""Bounded multi-domain routes for Work Router v0.2.

These routes exercise MAPEOGEO-style invariants across vector sensing and
vibration work without claiming physical qualification until source data are
run through the corresponding adapters.
"""
from __future__ import annotations
from .work_router import RouteEdge, WorkRouter


def multidomain_router() -> WorkRouter:
    return WorkRouter((
        # 3-D vector sensing: norm and alignment are invariant queries.
        RouteEdge("imu.norm", "sensor.vector3", "work.vector_norm", 1.0, True, "sqrt(dot(v,v))"),
        RouteEdge("imu.threshold", "work.vector_norm", "work.norm_above_threshold", 0.5, True, "compare norm", requires=("work.norm_threshold",)),
        RouteEdge("imu.alignment", "sensor.vector_pair3", "work.vector_alignment", 2.0, True, "normalized dot product"),
        RouteEdge("imu.full-rotation", "sensor.vector_pair3", "work.rotation_matrix", 8.0, False, "single-pair rotation is underdetermined"),
        # Vibration: energy/RMS can be answered without spectral materialization.
        RouteEdge("vib.energy", "vibration.window", "work.window_energy", 2.0, True, "sum squares"),
        RouteEdge("vib.rms", "work.window_energy", "work.window_rms", 0.5, True, "sqrt(energy/n)", requires=("vibration.window_length",)),
        RouteEdge("vib.rms-threshold", "work.window_rms", "work.vibration_above_threshold", 0.5, True, "compare rms", requires=("work.vibration_threshold",)),
        RouteEdge("vib.spectrum", "vibration.window", "work.spectrum", 12.0, True, "FFT/materialize spectrum", materializes=True),
        RouteEdge("vib.dominant-frequency", "work.spectrum", "work.dominant_frequency", 2.0, True, "argmax spectrum"),
    ))
