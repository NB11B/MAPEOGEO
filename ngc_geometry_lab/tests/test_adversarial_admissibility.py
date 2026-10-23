"""Adversarial admissibility gates and prospective blind campaign tests."""
import unittest
import numpy as np

from ngc_geometry_lab.geometry import (
    is_completely_positive_affine,
    is_locally_positive_affine,
    partial_transpose_extension_eigenvalues,
    choi_matrix_from_affine,
    qutrit_is_physical,
    qutrit_cubic_invariant,
    gell_mann_matrices,
    peres_mermin_hypergraph_audit,
    classify_lindblad_generator,
    geometric_uncertainty_bound,
    pauli_projective_frame,
    trine_povm_frame,
    cubic_povm_frame,
    analyze_measurement_frame,
    bipartite_channel_transfer,
    partial_trace_A,
    partial_trace_B,
    bipartite_state_positivity,
    is_entanglement_breaking,
    qubit_hamiltonian_generator,
    su3_structure_constants,
    qutrit_hamiltonian_generator,
    ContextGraph,
)
from ngc_geometry_lab.blind_benchmark import (
    generate_blind_test_cases,
    run_blind_qualification_campaign,
    generate_large_scale_blind_suite,
    run_large_scale_blind_campaign,
)


class TestAdversarialAdmissibility(unittest.TestCase):
    def test_transposition_adversary_rejected_by_choi_gate(self):
        """Transposition r -> (x, -y, z) is an isometry on the local Bloch ball,

        but MUST be rejected as an unphysical local operation because its extension
        to a Bell pair produces negative joint density eigenvalue -0.5.
        """
        A_T = np.diag([1.0, -1.0, 1.0])
        c_0 = np.zeros(3)

        # 1. Local geometry accepts it (maps B_1 isometrically into B_1)
        self.assertTrue(is_locally_positive_affine(A_T, c_0))

        # 2. Joint Bell extension produces eigenvalues [-0.5, 0.5, 0.5, 0.5]
        eigvals = partial_transpose_extension_eigenvalues(A_T, c_0)
        np.testing.assert_allclose(np.sort(eigvals), [-0.5, 0.5, 0.5, 0.5], atol=1e-12)

        # 3. Complete positivity gate strictly rejects it
        self.assertFalse(is_completely_positive_affine(A_T, c_0))

    def test_contracting_reflection_adversary(self):
        """A strictly contracting reflection (e.g. radius 0.8) maps all states strictly

        inside the interior of B_1, yet violates complete positivity (Choi min eig = -0.35).
        """
        A_refl = np.diag([0.8, -0.8, 0.8])
        c_0 = np.zeros(3)

        # 1. Strictly inside local ball
        self.assertTrue(is_locally_positive_affine(A_refl, c_0))

        # 2. Choi eigenvalues [-0.35, 0.45, 0.45, 0.45]
        eigvals = partial_transpose_extension_eigenvalues(A_refl, c_0)
        self.assertAlmostEqual(float(np.min(eigvals)), -0.35, places=12)

        # 3. Rejected by CP gate
        self.assertFalse(is_completely_positive_affine(A_refl, c_0))

    def test_qutrit_quadratic_pass_cubic_fail_adversary(self):
        """Adversarial qutrit spectrum (0.6, 0.6, -0.2) satisfies the quadratic Casimir

        purity bound, but fails the cubic determinant and positivity checks.
        """
        gm = gell_mann_matrices()
        rho_adv = np.diag([0.6, 0.6, -0.2]).astype(complex)
        r_adv = np.array([float(np.trace(rho_adv @ gm[a]).real) for a in range(8)])

        report = qutrit_is_physical(r_adv)

        # 1. Quadratic purity passes: ||r||^2 = 0.8533 <= 4/3
        self.assertTrue(report['quadratic_pass'])
        self.assertAlmostEqual(report['norm_sq'], 0.8533333333333334, places=10)

        # 2. Cubic determinant fails: det(rho) = -0.072 < 0
        self.assertFalse(report['cubic_pass'])
        self.assertAlmostEqual(report['determinant'], -0.072, places=10)

        # 3. Min eigenvalue is negative (-0.2)
        self.assertFalse(report['positivity_pass'])
        self.assertAlmostEqual(report['min_eigenvalue'], -0.2, places=10)

        # 4. Overall physical verdict is REJECTED
        self.assertFalse(report['physical'])
        self.assertIn("Cubic determinant violation", report['rejection_reason'])

    def test_lindblad_three_tier_generator_classification(self):
        """Classify generators into:

        1. Valid Lindblad (passes trace, local ball, and CP)
        2. Trace-preserving but expanding (fails local ball)
        3. Local contraction violating triangle inequality (passes local ball, fails CP)
        """
        # Tier 1: Valid Lindblad
        M1 = np.diag([-0.2, -0.2, -0.3])
        v1 = np.array([0.0, 0.0, 0.3])
        res1 = classify_lindblad_generator(M1, v1)
        self.assertEqual(res1['classification'], 'VALID_LINDBLAD')
        self.assertTrue(res1['trace_preserving'])
        self.assertTrue(res1['local_positivity'])
        self.assertTrue(res1['complete_positivity'])

        # Tier 2: Expanding generator
        M2 = np.diag([0.5, -0.2, -0.2])
        v2 = np.zeros(3)
        res2 = classify_lindblad_generator(M2, v2)
        self.assertEqual(res2['classification'], 'LOCAL_POSITIVITY_VIOLATION')
        self.assertTrue(res2['trace_preserving'])
        self.assertFalse(res2['local_positivity'])

        # Tier 3: Contracting generator violating triangle inequality:
        # Gx = 0.1, Gy = 0.1, Gz = 0.5 -> Gz > Gx + Gy
        M3 = np.diag([-0.1, -0.1, -0.5])
        v3 = np.zeros(3)
        res3 = classify_lindblad_generator(M3, v3)
        self.assertEqual(res3['classification'], 'COMPLETE_POSITIVITY_VIOLATION')
        self.assertTrue(res3['trace_preserving'])
        self.assertTrue(res3['local_positivity'])
        self.assertFalse(res3['complete_positivity'])
        self.assertLess(res3['min_choi_eigenvalue'], -1e-4)

    def test_peres_mermin_hypergraph_f2_obstruction(self):
        """Peres-Mermin contextuality hypergraph has an exact F_2 parity contradiction

        between incidence matrix row sum (0 mod 2) and context parities (1 mod 2).
        """
        audit = peres_mermin_hypergraph_audit()
        self.assertTrue(audit['algebraic_obstruction'])
        self.assertEqual(audit['f2_incidence_sum'], 0)
        self.assertEqual(audit['f2_syndrome_sum'], 1)
        # Maximum satisfaction bound over all 512 valuations is strictly 5/6
        self.assertEqual(audit['max_satisfied_contexts'], 5)
        self.assertEqual(audit['total_contexts'], 6)

    def test_uncertainty_distinguishes_lower_bound_from_actual_product(self):
        """Verify that the framework distinguishes the geometric lower bound

        from the actual variance product on non-saturating states.
        """
        a = np.array([1.0, 0.0, 0.0]) # X
        b = np.array([0.0, 1.0, 0.0]) # Y

        # State 1: Pure |0> (r along z-axis, perpendicular to x-y plane) -> SATURATING
        r_sat = np.array([0.0, 0.0, 1.0])
        unc_sat = geometric_uncertainty_bound(a, b, r_sat)
        self.assertAlmostEqual(unc_sat['bound'], 1.0, places=12)
        self.assertAlmostEqual(unc_sat['actual_product'], 1.0, places=12)
        self.assertAlmostEqual(unc_sat['gap'], 0.0, places=12)
        self.assertTrue(unc_sat['is_saturated'])

        # State 2: State in x-y plane (r = [0.5, 0.5, 0.0]) -> NON-SATURATING
        # Volume bound is 0.0, but actual product > 0.0
        r_nonsat = np.array([0.5, 0.5, 0.0])
        unc_nonsat = geometric_uncertainty_bound(a, b, r_nonsat)
        self.assertAlmostEqual(unc_nonsat['bound'], 0.0, places=12)
        self.assertGreater(unc_nonsat['actual_product'], 0.5)
        self.assertGreater(unc_nonsat['gap'], 0.5)
        self.assertFalse(unc_nonsat['is_saturated'])

    def test_prospective_blind_campaign(self):
        """Execute the full pre-registered prospective blind benchmark."""
        report = run_blind_qualification_campaign()
        self.assertTrue(report['all_passed'])
        self.assertEqual(report['accuracy'], 1.0)
        self.assertEqual(report['false_positives'], 0)
        self.assertEqual(report['false_negatives'], 0)
        self.assertGreaterEqual(report['total_cases'], 50)

    def test_measurement_frames_beyond_sic(self):
        """Verify rank, null space, and information completeness across measurement frames."""
        # Pauli projective frame: 6 outcomes, rank 3, no null space
        dirs_pauli, w_pauli = pauli_projective_frame()
        res_pauli = analyze_measurement_frame(dirs_pauli, w_pauli)
        self.assertEqual(res_pauli['rank'], 3)
        self.assertTrue(res_pauli['informationally_complete'])
        self.assertEqual(len(res_pauli['null_space']), 0)
        self.assertTrue(res_pauli['centroid_zero_sum'])

        # Trine POVM: 3 planar outcomes, rank 2, kernel = span(e_z)
        dirs_trine, w_trine = trine_povm_frame()
        res_trine = analyze_measurement_frame(dirs_trine, w_trine)
        self.assertEqual(res_trine['rank'], 2)
        self.assertFalse(res_trine['informationally_complete'])
        self.assertEqual(len(res_trine['null_space']), 1)
        # Check null space is along z-axis
        z_null = res_trine['null_space'][0]
        self.assertAlmostEqual(abs(z_null[2]), 1.0, places=10)

        # Cubic frame: 8 outcomes, rank 3, overcomplete
        dirs_cube, w_cube = cubic_povm_frame()
        res_cube = analyze_measurement_frame(dirs_cube, w_cube)
        self.assertEqual(res_cube['rank'], 3)
        self.assertTrue(res_cube['informationally_complete'])
        self.assertEqual(res_cube['num_outcomes'], 8)

    def test_composite_system_channels_and_partial_trace(self):
        """Verify local channels on entangled states, partial trace, and entanglement breaking."""
        # Bell state (rA=0, rB=0, T=diag(1, -1, 1))
        rA = np.zeros(3)
        rB = np.zeros(3)
        T = np.diag([1.0, -1.0, 1.0])

        # Partial trace recovery
        self.assertTrue(np.allclose(partial_trace_A(rA, rB, T), rB))
        self.assertTrue(np.allclose(partial_trace_B(rA, rB, T), rA))

        # Local amplitude damping on A (gamma=0.4), local dephasing on B (lambda=0.5)
        g = 0.4
        chA = (np.diag([np.sqrt(1 - g), np.sqrt(1 - g), 1 - g]), np.array([0.0, 0.0, g]))
        lam = 0.5
        chB = (np.diag([1 - lam, 1 - lam, 1.0]), np.zeros(3))

        rAp, rBp, Tp = bipartite_channel_transfer(rA, rB, T, chA, chB)
        pos = bipartite_state_positivity(rAp, rBp, Tp)
        self.assertTrue(pos['positive'])
        self.assertGreaterEqual(pos['min_eigenvalue'], -1e-12)

        # Entanglement-breaking channel: complete depolarizing channel (eta = 0.75)
        # Depolarizing channel with eta >= 2/3 is entanglement breaking!
        A_eb = 0.25 * np.eye(3) # eta = 0.75 > 2/3
        c_eb = np.zeros(3)
        self.assertTrue(is_entanglement_breaking(A_eb, c_eb))

        # Unitary rotation is NOT entanglement breaking
        A_rot = np.diag([1.0, 1.0, 1.0])
        c_rot = np.zeros(3)
        self.assertFalse(is_entanglement_breaking(A_rot, c_rot))

    def test_hamiltonian_flows_from_generators(self):
        """Verify qubit and qutrit dynamics generated directly from geometric generators."""
        import scipy.linalg
        # Qubit: dr/dt = 2 (h x r) = Omega @ r
        h = np.array([0.3, -0.4, 0.5])
        Omega_qubit = qubit_hamiltonian_generator(h)
        # Omega must be skew-symmetric in so(3)
        np.testing.assert_allclose(Omega_qubit, -Omega_qubit.T, atol=1e-14)

        r0 = np.array([0.2, 0.1, 0.7])
        t = 1.4
        R_qubit = scipy.linalg.expm(t * Omega_qubit)
        r_t = R_qubit @ r0
        # Preserves state norm identically
        self.assertAlmostEqual(np.linalg.norm(r_t), np.linalg.norm(r0), places=12)

        # Qutrit: dr_a/dt = sum Omega_ac r_c
        f_su3 = su3_structure_constants()
        self.assertEqual(f_su3.shape, (8, 8, 8))
        # Anti-symmetry in all pairs
        np.testing.assert_allclose(f_su3, -np.swapaxes(f_su3, 0, 1), atol=1e-14)
        np.testing.assert_allclose(f_su3, -np.swapaxes(f_su3, 1, 2), atol=1e-14)

        h_8d = np.ones(8) * 0.2
        Omega_qutrit = qutrit_hamiltonian_generator(h_8d)
        np.testing.assert_allclose(Omega_qutrit, -Omega_qutrit.T, atol=1e-14)
        R_qutrit = scipy.linalg.expm(t * Omega_qutrit)
        # Preserves 8D norm identically
        r0_8d = np.ones(8) / np.sqrt(8.0) * 0.8
        r_t_8d = R_qutrit @ r0_8d
        self.assertAlmostEqual(np.linalg.norm(r_t_8d), np.linalg.norm(r0_8d), places=12)

    def test_general_context_graph(self):
        """Verify formal ContextGraph object detects contextuality and F_2 parity obstructions."""
        # Peres-Mermin Magic Square as ContextGraph
        pm_contexts = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
        ]
        pm_parities = [1, 1, 1, 1, 1, -1]
        cg_pm = ContextGraph(9, pm_contexts, pm_parities)
        audit_pm = cg_pm.audit_valuation()
        self.assertTrue(audit_pm['is_contextual'])
        self.assertTrue(audit_pm['has_f2_obstruction'])
        self.assertEqual(audit_pm['max_satisfied_contexts'], 5)

        # Consistent non-contextual graph
        cg_non = ContextGraph(4, [(0, 1), (1, 2), (2, 3)], [1, 1, 1])
        audit_non = cg_non.audit_valuation()
        self.assertFalse(audit_non['is_contextual'])
        self.assertFalse(audit_non['has_f2_obstruction'])
        self.assertEqual(audit_non['max_satisfied_contexts'], 3)

    def test_large_scale_blind_campaign(self):
        """Execute the 1,000+ case prospective blind qualification campaign."""
        report = run_large_scale_blind_campaign()
        self.assertGreaterEqual(report['total_cases'], 1000)
        self.assertTrue(report['zero_false_positives'])
        self.assertTrue(report['zero_false_negatives'])
        self.assertEqual(report['overall_accuracy'], 1.0)



if __name__ == '__main__':
    unittest.main()
