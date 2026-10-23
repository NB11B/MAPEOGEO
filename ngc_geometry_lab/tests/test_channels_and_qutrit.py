"""Tests for irreversible CPTP channels and qutrit (d=3) 8D geometry."""

import unittest
import numpy as np
from numpy.testing import assert_allclose
from scipy.linalg import expm

from ngc_geometry_lab import geometry as g
from ngc_geometry_lab import reference as ref


class CPTPChannelTests(unittest.TestCase):
    def setUp(self):
        self.paulis = ref.paulis()

        # 1. Amplitude damping (gamma = 0.37)
        gamma = 0.37
        k0_ad = np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=complex)
        k1_ad = np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=complex)
        self.A_ad, self.c_ad = g.bloch_channel_from_kraus([k0_ad, k1_ad])

        # 2. Dephasing (lambda = 0.42)
        lam = 0.42
        k0_dp = np.sqrt(1.0 - lam / 2.0) * self.paulis[0]
        k1_dp = np.sqrt(lam / 2.0) * self.paulis[3]
        self.A_dp, self.c_dp = g.bloch_channel_from_kraus([k0_dp, k1_dp])

        # 3. Depolarizing (eta = 0.31)
        eta = 0.31
        k_depol = [
            np.sqrt(1.0 - 3.0 * eta / 4.0) * self.paulis[0],
            np.sqrt(eta / 4.0) * self.paulis[1],
            np.sqrt(eta / 4.0) * self.paulis[2],
            np.sqrt(eta / 4.0) * self.paulis[3],
        ]
        self.A_depol, self.c_depol = g.bloch_channel_from_kraus(k_depol)

    def test_cptp_transfer_matrix_composition(self):
        # Transfer matrices
        M_ad = g.affine_channel_transfer_matrix(self.A_ad, self.c_ad)
        M_dp = g.affine_channel_transfer_matrix(self.A_dp, self.c_dp)
        M_depol = g.affine_channel_transfer_matrix(self.A_depol, self.c_depol)

        # Test negative entry in amplitude damping transfer matrix
        self.assertLess(np.min(M_ad), 0.0)
        self.assertAlmostEqual(np.min(M_ad), -0.0427675965597, places=5)

        # Pairwise compositions: E2 o E1: A_comp = A2 @ A1, c_comp = A2 @ c1 + c2
        pairs = [
            ("ad -> dp", self.A_ad, self.c_ad, self.A_dp, self.c_dp, M_ad, M_dp),
            ("depol -> ad", self.A_depol, self.c_depol, self.A_ad, self.c_ad, M_depol, M_ad),
            ("dp -> depol", self.A_dp, self.c_dp, self.A_depol, self.c_depol, M_dp, M_depol),
        ]
        for name, A1, c1, A2, c2, M1, M2 in pairs:
            with self.subTest(channel_composition=name):
                A_comp = A2 @ A1
                c_comp = A2 @ c1 + c2
                M_comp = g.affine_channel_transfer_matrix(A_comp, c_comp)
                assert_allclose(M2 @ M1, M_comp, atol=1e-15)

    def test_cptp_preserves_physical_state_ball(self):
        rng = np.random.default_rng(20261022)
        M_ad = g.affine_channel_transfer_matrix(self.A_ad, self.c_ad)
        u4 = np.full(4, 0.25)

        for _ in range(100):
            r = rng.normal(size=3)
            norm = np.linalg.norm(r)
            if norm > 1.0:
                r /= norm
            p = g.tetra_probabilities(r)
            p_prime = M_ad @ p

            # Must sum to 1
            self.assertAlmostEqual(p_prime.sum(), 1.0, places=14)
            # Must remain inside the physical probability ball: ||p' - u|| <= 1 / (2*sqrt(3))
            self.assertLessEqual(np.linalg.norm(p_prime - u4), 1.0 / (2.0 * np.sqrt(3.0)) + 1e-14)


class QutritTests(unittest.TestCase):
    def test_gell_mann_matrices(self):
        gm = g.gell_mann_matrices()
        self.assertEqual(len(gm), 8)
        for a in range(8):
            self.assertAlmostEqual(np.trace(gm[a]).real, 0.0, places=15)
            for b in range(8):
                expected = 2.0 if a == b else 0.0
                assert_allclose(np.trace(gm[a] @ gm[b]).real, expected, atol=1e-15)

    def test_sic_povm_properties(self):
        vecs = g.qutrit_sic_vectors()
        self.assertEqual(len(vecs), 9)
        # Completeness: sum 1/3 |psi_k><psi_k| = I_3
        identity = sum((1.0 / 3.0) * np.outer(v, v.conj()) for v in vecs)
        assert_allclose(identity, np.eye(3), atol=1e-15)

        # Overlaps |<psi_j|psi_k>|^2 = 1/4 for all j != k
        for j in range(9):
            for k in range(9):
                fid = abs(np.vdot(vecs[j], vecs[k])) ** 2
                expected = 1.0 if j == k else 0.25
                self.assertAlmostEqual(fid, expected, places=14)

    def test_qutrit_8d_frame_identities(self):
        n_8d = g.qutrit_sic_directions()
        self.assertEqual(n_8d.shape, (9, 8))
        # Centroid zero-sum
        assert_allclose(n_8d.sum(axis=0), 0.0, atol=1e-15)
        # Resolution of identity in 8D: sum n_k n_k^T = 3/2 I_8
        assert_allclose(n_8d.T @ n_8d, 1.5 * np.eye(8), atol=1e-15)
        # Norm squared = 4/3
        for k in range(9):
            self.assertAlmostEqual(np.linalg.norm(n_8d[k]) ** 2, 4.0 / 3.0, places=14)

    def test_qutrit_exact_reconstruction(self):
        rng = np.random.default_rng(20261022)
        gm = g.gell_mann_matrices()
        vecs = g.qutrit_sic_vectors()

        for _ in range(20):
            psi = rng.normal(size=3) + 1j * rng.normal(size=3)
            psi /= np.linalg.norm(psi)
            rho = np.outer(psi, psi.conj())

            # Ground truth 8D vector
            r_true = np.array([np.trace(rho @ m).real for m in gm])

            # 9-outcome SIC probabilities
            p = np.array([float(np.trace(rho @ np.outer(v, v.conj())).real / 3.0) for v in vecs])
            self.assertAlmostEqual(p.sum(), 1.0, places=14)

            # Invert: r = 4 * sum p_k n_k
            r_rec = g.qutrit_reconstruct(p)
            assert_allclose(r_rec, r_true, atol=1e-14)

    def test_qutrit_transfer_matrix_composition(self):
        rng = np.random.default_rng(42)
        # Generate two random SU(3) unitaries via Lie algebra exponentiation
        H1 = rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))
        H1 = H1 + H1.conj().T
        U1 = expm(1j * H1)

        H2 = rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))
        H2 = H2 + H2.conj().T
        U2 = expm(1j * H2)

        M_U1 = g.qutrit_transformation_matrix(U1)
        M_U2 = g.qutrit_transformation_matrix(U2)
        M_U12 = g.qutrit_transformation_matrix(U2 @ U1)

        # Composition preservation
        assert_allclose(M_U2 @ M_U1, M_U12, atol=1e-14)

    def test_qutrit_purity_bound(self):
        # Pure state purity in 9-outcome space is 1/6
        vecs = g.qutrit_sic_vectors()
        rho_pure = np.outer(vecs[0], vecs[0].conj())
        p_pure = np.array([float(np.trace(rho_pure @ np.outer(v, v.conj())).real / 3.0) for v in vecs])
        self.assertAlmostEqual(g.qutrit_purity_bound(p_pure), 1.0 / 6.0, places=14)

        # Mixed state at origin has p_k = 1/9, so sum p_k^2 = 9 * (1/81) = 1/9
        p_mixed = np.full(9, 1.0 / 9.0)
        self.assertAlmostEqual(g.qutrit_purity_bound(p_mixed), 1.0 / 9.0, places=14)


if __name__ == "__main__":
    unittest.main()
