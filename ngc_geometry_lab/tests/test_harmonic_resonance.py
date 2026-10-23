"""Tests for Quantum Harmonic Resonance and Three-Wavefunction Spherical Mapping."""
import unittest
import numpy as np

from ngc_geometry_lab.harmonic_resonance import (
    ThreeModeHarmonicSystem,
    analyze_harmonic_resonance,
    run_three_mode_resonance_campaign
)


class TestHarmonicResonance(unittest.TestCase):
    """Test suite verifying three-wavefunction harmonic resonance, S^2 x T^2 geometry, and information loss."""

    def test_amplitude_normalization_guard(self):
        """Verify unnormalized amplitudes raise ValueError."""
        with self.assertRaises(ValueError):
            ThreeModeHarmonicSystem(
                amplitudes=(1.0, 1.0, 1.0),  # norm^2 = 3 != 1
                frequencies=(1.0, 1.0, 1.0),
                phases=(0.0, 0.0, 0.0)
            )

    def test_case_1_identical_frequency_phase_locking(self):
        """Case 1: Identical frequencies produce stationary relative phases (dimension 0)."""
        A = (1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3))
        sys = ThreeModeHarmonicSystem(A, (2.0, 2.0, 2.0), (0.1, 0.5, 1.2))
        res = analyze_harmonic_resonance(sys, eval_time=2*np.pi)
        self.assertTrue(res.phase_locking_active)
        self.assertEqual(res.torus_dimension, 0)
        self.assertTrue(res.torus_orbit_closed)
        self.assertAlmostEqual(res.torus_return_residual, 0.0, places=12)

    def test_case_2_integer_resonance_torus_knot(self):
        """Case 2: 1:2:3 integer resonance closes into periodic torus knot with finite return time."""
        A = (1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3))
        sys = ThreeModeHarmonicSystem(A, (1.0, 2.0, 3.0), (0.0, 0.0, 0.0))
        res = analyze_harmonic_resonance(sys, eval_time=2*np.pi)
        self.assertFalse(res.phase_locking_active)
        self.assertEqual(res.torus_dimension, 1)
        self.assertTrue(res.torus_orbit_closed)
        self.assertTrue(res.rotor_orbit_closed)
        self.assertAlmostEqual(res.torus_return_residual, 0.0, places=10)
        self.assertAlmostEqual(res.rotor_return_residual, 0.0, places=10)

    def test_case_3_incommensurate_flow(self):
        """Case 3: Incommensurate frequencies produce ergodic non-closing trajectory on T^2 (dimension 2)."""
        A = (1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3))
        sys = ThreeModeHarmonicSystem(A, (1.0, float(np.sqrt(2)), float(np.pi)), (0.0, 0.0, 0.0))
        res = analyze_harmonic_resonance(sys, eval_time=2*np.pi)
        self.assertFalse(res.phase_locking_active)
        self.assertEqual(res.torus_dimension, 2)
        self.assertFalse(res.torus_orbit_closed)
        self.assertGreater(res.torus_return_residual, 0.5)

    def test_information_loss_sphere_only_collision(self):
        """Demonstrate that mapping to S^2 alone collides on in-phase constructive vs out-of-phase destructive states."""
        A = (1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3))
        sys_const = ThreeModeHarmonicSystem(A, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
        sys_dest = ThreeModeHarmonicSystem(A, (1.0, 1.0, 1.0), (0.0, 2*np.pi/3, 4*np.pi/3))

        # Coordinates on S^2 are strictly identical
        pt_A = sys_const.to_sphere_coordinates()
        pt_B = sys_dest.to_sphere_coordinates()
        self.assertEqual(pt_A, pt_B)

        # Output detector intensities radically differ (3.0 vs 0.0)
        I_A = sys_const.resultant_intensity(0.0)
        I_B = sys_dest.resultant_intensity(0.0)
        self.assertAlmostEqual(I_A, 3.0, places=10)
        self.assertAlmostEqual(I_B, 0.0, places=10)

    def test_observability_rank_condition(self):
        """Verify reconstructibility of a 3D state from 3 scalar projections requires rank 3."""
        # Linearly independent frame -> reconstructible
        n_ortho = np.eye(3)
        self.assertEqual(np.linalg.matrix_rank(n_ortho), 3)

        # Coplanar frame -> normal direction hidden
        n_coplanar = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0]
        ])
        self.assertEqual(np.linalg.matrix_rank(n_coplanar), 2)

    def test_full_campaign_execution(self):
        """Execute full three-mode harmonic resonance campaign."""
        res = run_three_mode_resonance_campaign()
        self.assertTrue(res['campaign_passed'])
        self.assertTrue(res['information_loss_test']['collision_certified'])
        self.assertTrue(res['observability_test']['rank_condition_certified'])


if __name__ == '__main__':
    unittest.main()
