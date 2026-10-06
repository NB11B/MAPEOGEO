"""Derive invariant work routes from certified primitive edges (v0.5).

Unlike invariant_queries.py, this module does not encode complete source->target
routes.  It registers primitive mathematical transformations and lets the
fail-closed WorkRouter compose them.
"""
from __future__ import annotations

from .work_router import RouteEdge, WorkRouter


def primitive_router() -> WorkRouter:
    return WorkRouter((
        # Scalar/order primitives
        RouteEdge("prim.compare.zero", "math.scalar_signed", "work.sign_negative", 0.2, True, "x<0"),
        RouteEdge("prim.compare.threshold", "math.scalar", "work.scalar_above_threshold", 0.2, True, "x>threshold", requires=("work.scalar_threshold",)),
        # Norm / inner-product primitives
        RouteEdge("prim.vector.dot-self", "sensor.vector3", "math.norm_squared", 0.5, True, "dot(v,v)"),
        RouteEdge("prim.sqrt.norm", "math.norm_squared", "math.norm", 0.5, True, "sqrt"),
        RouteEdge("prim.norm.alias", "math.norm", "work.vector_norm", 0.0, True, "semantic target alias"),
        RouteEdge("prim.norm.threshold", "math.norm", "work.norm_above_threshold", 0.2, True, "compare", requires=("work.norm_threshold",)),
        # Linear stability primitives
        RouteEdge("prim.eigenvalues", "control.state_matrix", "math.eigenvalues", 10.0, True, "eig(A)", materializes=True),
        RouteEdge("prim.realparts", "math.eigenvalues", "math.eigenvalue_realparts", 0.5, True, "real(lambda)"),
        RouteEdge("prim.max", "math.eigenvalue_realparts", "math.spectral_abscissa", 0.5, True, "max"),
        RouteEdge("prim.spectral.stability", "math.spectral_abscissa", "work.asymptotically_stable", 0.2, True, "alpha<0"),
        RouteEdge("prim.generator.realpart", "psmsl.generator_g", "math.spectral_abscissa", 0.1, True, "alpha=g"),
        # Area/determinant from generator coordinates
        RouteEdge("prim.scale.sum", "psmsl.directional_scales", "math.log_area_scale", 0.5, True, "n1+n2"),
        RouteEdge("prim.logarea.sign", "math.log_area_scale", "work.area_expanding", 0.2, True, ">0"),
        # Spectral primitives
        RouteEdge("prim.vibration.fft", "vibration.window", "math.spectrum", 12.0, True, "FFT", materializes=True),
        RouteEdge("prim.spectrum.argmax", "math.spectrum", "work.dominant_frequency", 1.0, True, "argmax"),
        RouteEdge("prim.power.fft", "power.voltage_window", "math.power_spectrum", 12.0, True, "FFT", materializes=True),
        RouteEdge("prim.power.thd", "math.power_spectrum", "work.voltage_thd", 2.0, True, "harmonic/fundamental RMS"),
        # Deliberate semantic traps: attractive, invalid for execution.
        RouteEdge("trap.matrix.stable", "control.state_matrix", "work.asymptotically_stable", 0.01, False, "semantic shortcut"),
        RouteEdge("trap.rms.thd", "work.voltage_rms", "work.voltage_thd", 0.01, False, "RMS does not determine THD"),
    ))
