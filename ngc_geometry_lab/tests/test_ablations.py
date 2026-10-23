"""Tests for the controlled ablation suite."""

import unittest
import numpy as np

from ngc_geometry_lab import ablations


class AblationTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(20261022)

    def test_temporal_ordering_ablation(self):
        # 90-degree rotations about X and Z
        rotations = [
            (np.array([1.0, 0.0, 0.0]), np.pi / 2),
            (np.array([0.0, 0.0, 1.0]), np.pi / 2),
        ]
        s0 = np.array([0.0, 1.0, 0.0])
        res = ablations.ablate_temporal_order(rotations, s0)

        self.assertTrue(res["order_matters"])
        self.assertTrue(res["recovery_requires_order"])
        self.assertGreater(res["reversed_order_discrepancy"], 0.5)
        self.assertLess(res["exact_recovery_error"], 1e-12)

    def test_plane_orientation_ablation(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        c = np.array([0.0, 0.0, 1.0])
        res = ablations.ablate_plane_orientation(a, b, c)

        self.assertTrue(res["scalar_model_blind_to_parity"])
        self.assertLess(res["scalar_parity_delta"], 1e-12)
        self.assertGreater(res["chiral_volume_delta"], 1.5)
        self.assertGreater(res["chiral_rotation_separation"], 0.5)

    def test_phase_interference_ablation(self):
        res = ablations.ablate_phase_interference(48)

        self.assertAlmostEqual(res["coherent_fringe_visibility"], 1.0, places=5)
        self.assertAlmostEqual(res["incoherent_fringe_visibility"], 0.0, places=5)
        self.assertAlmostEqual(res["fringe_destruction"], 1.0, places=5)
        self.assertTrue(res["incoherent_probabilities_flat"])

    def test_joint_correlation_ablation(self):
        res = ablations.ablate_joint_correlations()

        self.assertAlmostEqual(res["true_singlet_chsh"], 2 * np.sqrt(2), places=5)
        self.assertAlmostEqual(res["ablated_marginal_chsh"], 0.0, places=5)
        self.assertAlmostEqual(res["joint_tv_distance"], 0.25, places=5)
        self.assertTrue(res["singlet_indistinguishable_from_noise_under_marginals"])

    def test_path_geometry_ablation(self):
        res = ablations.ablate_path_geometry()

        self.assertTrue(res["loop_closed_on_bloch_sphere"])
        self.assertAlmostEqual(res["measured_holonomy_phase"], -np.pi / 4, places=5)
        self.assertGreater(res["phase_prediction_error"], 0.1)

    def test_run_all_ablations(self):
        full = ablations.run_all_ablations(seed=42)
        self.assertIn("summary", full)
        summary = full["summary"]
        self.assertGreater(summary["temporal_order_divergence"], 0.1)
        self.assertGreater(summary["parity_chiral_delta"], 0.1)
        self.assertAlmostEqual(summary["fringe_visibility_loss"], 1.0, places=5)
        self.assertAlmostEqual(summary["chsh_correlation_loss"], 2 * np.sqrt(2), places=5)
        self.assertGreater(summary["berry_phase_shift_error"], 0.1)


if __name__ == "__main__":
    unittest.main()
