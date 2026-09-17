"""Tests for Wave F5 Independent Geometric Dual-View Witness Engine."""

import pytest
from fractions import Fraction
import numpy as np

from mapeogeo.wave_f5.dual_views import (
    geo_q01_contraction_geometry,
    geo_q02_adjoint_pairing_geometry,
    geo_q03_orthogonal_projector_geometry,
    geo_q04_resolvent_disk_geometry,
    geo_q05_spectral_subspace_geometry,
    geo_q06_picard_corridor_geometry,
    geo_q07_nonuniqueness_cusp_geometry,
    geo_q08_blowup_horizon_geometry,
    geo_q09_flow_manifold_geometry,
    geo_q10_nonautonomous_evolution_cocycle,
    geo_q11_lyapunov_ellipsoid_geometry,
    geo_q12_nonhyperbolic_phase_geometry,
    geo_q13_nonnormal_numerical_range,
    geo_q14_symplectic_phase_orbit,
    geo_q15_validated_solution_tube_geometry,
    geo_q16_invariant_polytope_geometry,
    geo_q17_transversal_hypersurface_crossing,
    geo_q18_green_operator_kernel_geometry,
)
from mapeogeo.wave_f5.enclosures import RationalInterval


def test_geo_witnesses_produce_distinct_semantic_payloads():
    # Q01
    w1 = geo_q01_contraction_geometry(lambda x: Fraction(1, 2) * x + 1, (Fraction(0), Fraction(2)), Fraction(1, 2), Fraction(2))
    assert w1["verified"] is True
    assert "geometric_staircase" in w1
    assert "lyapunov_decay_rate" in w1

    # Q02
    A = np.array([[Fraction(1), Fraction(2)], [Fraction(0), Fraction(3)]])
    G = np.array([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(1)]])
    A_star = np.array([[Fraction(1), Fraction(0)], [Fraction(4), Fraction(3)]])
    w2 = geo_q02_adjoint_pairing_geometry(A, G, A_star)
    assert w2["verified"] is True
    assert "metric_determinant" in w2

    # Q03
    P = np.array([[Fraction(1, 2), Fraction(1, 2)], [Fraction(1, 2), Fraction(1, 2)]])
    basis = [np.array([Fraction(1), Fraction(1)])]
    w3 = geo_q03_orthogonal_projector_geometry(P, basis)
    assert w3["verified"] is True
    assert "subspace_orthogonality" in w3
    assert "distance_minimization" in w3

    # Q11
    A11 = np.array([[-1.0, 0.0], [0.0, -2.0]])
    V11 = np.eye(2)
    w11 = geo_q11_lyapunov_ellipsoid_geometry(A11, V11)
    assert w11["verified"] is True
    assert "ellipsoid_semiaxes" in w11
    assert "inward_normal_flux" in w11

    # Q13
    A13 = np.array([[-1.0, 10.0], [0.0, -2.0]])
    w13 = geo_q13_nonnormal_numerical_range(A13)
    assert w13["verified"] is True
    assert w13["numerical_abscissa"] > 0.0  # Proves transient growth geometrically
    assert w13["spectral_abscissa"] < 0.0

    # Q14
    traj = [(float(np.cos(t)), float(np.sin(t))) for t in [0.0, np.pi/4, np.pi/2, np.pi]]
    w14 = geo_q14_symplectic_phase_orbit(traj)
    assert w14["verified"] is True
    assert "symplectic_area_preservation" in w14
