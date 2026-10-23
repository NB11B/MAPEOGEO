"""Unit tests for observable Lie/Jordan algebra, Peres-Mermin contextuality, and Lindblad flows."""
import unittest
import numpy as np
import scipy.linalg

from ngc_geometry_lab.geometry import (
    bloch_observable,
    bloch_observable_decomposition,
    jordan_product,
    lie_bracket,
    geometric_jordan_product,
    geometric_lie_bracket,
    geometric_uncertainty_bound,
    real_dual_lane_operator,
    peres_mermin_square,
    peres_mermin_dual_lane_square,
    verify_peres_mermin_algebra,
    lindblad_observation_generator,
    lindblad_finite_time_transfer,
    affine_channel_transfer_matrix,
    tetra_directions,
    tetra_probabilities,
    tetra_reconstruct,
)


class TestObservableAlgebra(unittest.TestCase):
    def test_bloch_observable_roundtrip(self):
        rng = np.random.default_rng(20261022)
        for _ in range(20):
            a0 = rng.uniform(-2.0, 2.0)
            a = rng.uniform(-2.0, 2.0, size=3)
            A = bloch_observable(a0, a)
            rec_a0, rec_a = bloch_observable_decomposition(A)
            self.assertAlmostEqual(a0, rec_a0, places=12)
            np.testing.assert_allclose(a, rec_a, atol=1e-12)

    def test_jordan_product_matches_geometric_inner_product(self):
        rng = np.random.default_rng(20261023)
        for _ in range(25):
            a0 = rng.uniform(-1.5, 1.5)
            a = rng.uniform(-1.5, 1.5, size=3)
            b0 = rng.uniform(-1.5, 1.5)
            b = rng.uniform(-1.5, 1.5, size=3)

            A = bloch_observable(a0, a)
            B = bloch_observable(b0, b)
            J_mat = jordan_product(A, B)

            c0_geo, c_geo = geometric_jordan_product(a0, a, b0, b)
            J_geo = bloch_observable(c0_geo, c_geo)

            np.testing.assert_allclose(J_mat, J_geo, atol=1e-14)

    def test_lie_bracket_matches_geometric_cross_product(self):
        rng = np.random.default_rng(20261024)
        for _ in range(25):
            a = rng.uniform(-1.5, 1.5, size=3)
            b = rng.uniform(-1.5, 1.5, size=3)

            A = bloch_observable(0.0, a)
            B = bloch_observable(0.0, b)
            comm = lie_bracket(A, B)

            # [A, B] = 2i (a x b) . sigma
            gen_geo = geometric_lie_bracket(a, b)
            comm_geo = 1j * bloch_observable(0.0, gen_geo)

            np.testing.assert_allclose(comm, comm_geo, atol=1e-14)

    def test_geometric_uncertainty_volume_bound(self):
        rng = np.random.default_rng(20261025)
        for _ in range(30):
            # Unit measurement axes
            a = rng.normal(size=3)
            a /= np.linalg.norm(a)
            b = rng.normal(size=3)
            b /= np.linalg.norm(b)

            # Random physical state
            r = rng.normal(size=3)
            r = r / np.linalg.norm(r) * rng.uniform(0.1, 0.99)

            A = bloch_observable(0.0, a)
            B = bloch_observable(0.0, b)
            rho = 0.5 * bloch_observable(1.0, r)

            # Exact quantum expectations and variances
            exp_A = np.trace(rho @ A).real
            exp_B = np.trace(rho @ B).real
            var_A = np.trace(rho @ A @ A).real - exp_A**2
            var_B = np.trace(rho @ B @ B).real - exp_B**2

            unc_info = geometric_uncertainty_bound(a, b, r)
            bound = unc_info['bound']

            # Product of variances must satisfy Robertson-Schrodinger bound
            self.assertGreaterEqual(np.sqrt(var_A * var_B), bound - 1e-12)

    def test_uncertainty_saturation_on_pure_state(self):
        # When r is perpendicular to the a x b plane and pure (||r|| = 1),
        # Robertson-Schrödinger is strictly tested.
        # e.g., A = X, B = Y, state |0> (r = [0, 0, 1])
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        r = np.array([0.0, 0.0, 1.0])

        A = bloch_observable(0.0, a)
        B = bloch_observable(0.0, b)
        rho = 0.5 * bloch_observable(1.0, r)

        var_A = np.trace(rho @ A @ A).real - np.trace(rho @ A).real**2
        var_B = np.trace(rho @ B @ B).real - np.trace(rho @ B).real**2

        unc_info = geometric_uncertainty_bound(a, b, r)
        self.assertAlmostEqual(unc_info['bound'], 1.0, places=12)
        # For |0>, Delta(X) = 1, Delta(Y) = 1, product = 1.0, saturating bound = 1.0!
        self.assertAlmostEqual(np.sqrt(var_A * var_B), 1.0, places=12)


class TestContextualityPeresMermin(unittest.TestCase):
    def test_real_dual_lane_homomorphism(self):
        rng = np.random.default_rng(20261026)
        for _ in range(15):
            M1 = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
            M2 = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))

            phi_M1 = real_dual_lane_operator(M1)
            phi_M2 = real_dual_lane_operator(M2)
            phi_prod = real_dual_lane_operator(M1 @ M2)

            np.testing.assert_allclose(phi_M1 @ phi_M2, phi_prod, atol=1e-13)

    def test_peres_mermin_real_dual_lane_algebra(self):
        pm_square = peres_mermin_dual_lane_square()
        report = verify_peres_mermin_algebra(pm_square)

        self.assertLess(report['max_involutory_error'], 1e-15)
        self.assertLess(report['max_commutation_error'], 1e-15)

        for err in report['row_product_errors']:
            self.assertLess(err, 1e-15)

        for err in report['col_product_errors']:
            self.assertLess(err, 1e-15)

        # Classical non-contextual impossibility
        self.assertTrue(report['classical_contradiction'])
        self.assertEqual(report['max_classical_satisfied_contexts'], 5)
        self.assertEqual(report['total_contexts'], 6)


class TestLindbladDissipativeFlows(unittest.TestCase):
    def test_generator_column_zero_sum(self):
        # Amplitude damping
        gamma = 0.4
        M = np.diag([-gamma / 2.0, -gamma / 2.0, -gamma])
        v = np.array([0.0, 0.0, gamma])
        L_obs = lindblad_observation_generator(M, v)
        np.testing.assert_allclose(np.sum(L_obs, axis=0), 0.0, atol=1e-14)

    def test_continuous_flow_matches_integrated_cptp_affine_transfer(self):
        # Dissipation and precession simultaneously:
        # dr/dt = M r + v
        gamma = 0.5
        omega = 1.2
        M = np.array([
            [-gamma / 2.0, -omega, 0.0],
            [omega, -gamma / 2.0, 0.0],
            [0.0, 0.0, -gamma],
        ])
        v = np.array([0.0, 0.0, gamma])

        # Test at multiple durations
        for t in [0.1, 0.5, 1.0, 2.0]:
            M_trans_exp = lindblad_finite_time_transfer(M, v, t)

            # Compute exact integrated affine map parameters:
            # r(t) = exp(t M) r(0) + int_0^t exp((t-s)M) v ds
            # int_0^t exp((t-s)M) ds = M^{-1} (exp(t M) - I)
            A_t = scipy.linalg.expm(t * M)
            c_t = np.linalg.solve(M, (A_t - np.eye(3)) @ v)

            M_trans_affine = affine_channel_transfer_matrix(A_t, c_t)

            np.testing.assert_allclose(M_trans_exp, M_trans_affine, atol=1e-14)

    def test_dissipative_trajectory_stays_in_physical_ball(self):
        # Pure state initial condition evolved under dephasing and decay
        gamma = 0.3
        M = np.diag([-gamma, -gamma, -gamma])
        v = np.zeros(3)

        initial_r = np.array([1.0, 0.0, 0.0]) # Pure state on x-axis
        initial_p = tetra_probabilities(initial_r)

        u = np.full(4, 0.25)
        ball_radius = 1.0 / (2.0 * np.sqrt(3.0))

        # Check at 10 successive time steps
        for step in range(1, 11):
            t = step * 0.2
            M_t = lindblad_finite_time_transfer(M, v, t)
            p_t = M_t @ initial_p

            self.assertAlmostEqual(np.sum(p_t), 1.0, places=12)
            dist_to_u = np.linalg.norm(p_t - u)
            self.assertLessEqual(dist_to_u, ball_radius + 1e-12)

            # Decaying toward maximally mixed state
            r_t = tetra_reconstruct(p_t)
            self.assertLess(np.linalg.norm(r_t), 1.0)


if __name__ == '__main__':
    unittest.main()
