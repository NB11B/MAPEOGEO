"""Tests for native CUDA joint systems, Bell states, and CHSH verification."""

import unittest
from pathlib import Path
import numpy as np

from ngc_geometry_lab import cuda_joint

_DLL_PATH = Path(__file__).parent.parent / "build" / "ngc_rcs_geometric.dll"


class CudaJointTests(unittest.TestCase):
    def setUp(self):
        if not _DLL_PATH.is_file():
            self.skipTest(f"Compiled CUDA DLL not found at {_DLL_PATH}")

    def test_gpu_chsh_test(self):
        res = cuda_joint.run_gpu_chsh_test(_DLL_PATH, phase_bins=48)
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["chsh"]["violates_classical_bound"])
        self.assertTrue(res["chsh"]["matches_tsirelson_bound"])
        self.assertAlmostEqual(res["chsh"]["S_measured"], 2 * np.sqrt(2), places=4)
        self.assertLess(res["angular_curve"]["max_error_vs_cos"], 0.05)

    def test_gpu_ghz_test(self):
        for n in (3, 4):
            with self.subTest(num_qubits=n):
                res = cuda_joint.run_gpu_ghz_test(_DLL_PATH, num_qubits=n, phase_bins=48)
                self.assertEqual(res["status"], "PASS")
                self.assertTrue(res["ghz_verified"])
                self.assertTrue(res["incoherent_mixture_ruled_out"])
                self.assertAlmostEqual(res["p_all_zero"], 0.5, places=5)
                self.assertAlmostEqual(res["p_all_one"], 0.5, places=5)
                self.assertAlmostEqual(res["off_diagonal_coherence"], 0.5, places=4)
                self.assertAlmostEqual(res["state_fidelity"], 1.0, places=4)
                self.assertAlmostEqual(res["x_basis_parity_expectation"], 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
