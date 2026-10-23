"""Tests for extrapolation qualification engine, structured Reason Certificates,
Generic Compatibility Hypergraph subsystem with F_2 left-nullspace solver,
and Autonomous Category-Ambiguous Admissibility Grammar Engine.
"""
import unittest
import numpy as np

from ngc_geometry_lab.extrapolation import (
    ReasonCertificate,
    evaluate_horodecki_ppt_entanglement,
    evaluate_decoherence_free_subspace,
    evaluate_stabilizer_error_correction,
    evaluate_kcbs_contextuality,
    evaluate_peres_mermin_contextuality_hypergraph,
    evaluate_qutrit_mubs,
    evaluate_transposition_adversary,
    evaluate_qutrit_cubic_adversary,
    evaluate_lindblad_triangle_adversary,
    run_extrapolation_campaign,
    GenericCompatibilityHypergraph,
    ObstructionCertificate,
    AdmissibilityGrammarEngine,
    CarrierInterface,
    solve_f2_system,
    infer_object_category,
    run_category_ambiguous_campaign,
)


class TestExtrapolationQualification(unittest.TestCase):
    """Test suite verifying unfamiliar quantum structure extrapolations and Reason Certificates."""

    def test_horodecki_ppt_bound_entanglement(self):
        """Verify Horodecki 3x3 bound entangled state satisfies PPT but is entangled by Range Criterion."""
        cert = evaluate_horodecki_ppt_entanglement(a=0.5)
        self.assertIsInstance(cert, ReasonCertificate)
        self.assertTrue(cert.admissible)
        self.assertIn("BOUND ENTANGLEMENT", cert.verdict)
        self.assertIn("Range Criterion", cert.verdict)
        self.assertGreaterEqual(cert.witness_metric, -1e-12)

        # Verify explicit nullspace certificate
        self.assertIsNotNone(cert.nullspace_certificate)
        null_info = cert.nullspace_certificate
        self.assertEqual(null_info['nullspace_dimension'], 2)
        self.assertEqual(null_info['rank_dimension'], 7)
        self.assertEqual(len(null_info['nullspace_basis']), 9)

        # Test parameter variation
        for a_val in [0.2, 0.5, 0.8]:
            c = evaluate_horodecki_ppt_entanglement(a=a_val)
            self.assertTrue(c.admissible)
            self.assertGreaterEqual(c.witness_metric, -1e-12)

    def test_decoherence_free_subspace(self):
        """Verify 2-qubit singlet subspace has zero commutator with collective noise."""
        cert = evaluate_decoherence_free_subspace()
        self.assertIsInstance(cert, ReasonCertificate)
        self.assertTrue(cert.admissible)
        self.assertIn("DECOHERENCE-FREE", cert.verdict)
        self.assertLess(cert.witness_metric, 1e-12)

    def test_stabilizer_error_correction_all_syndromes(self):
        """Verify [[3, 1, 1]] stabilizer code distinguishes all single bit-flips and achieves F=1."""
        errors = {
            'X1': (-1.0, 1.0),
            'X2': (-1.0, -1.0),
            'X3': (1.0, -1.0),
            'none': (1.0, 1.0),
        }
        for err, expected_syn in errors.items():
            cert = evaluate_stabilizer_error_correction(error_op=err)
            self.assertTrue(cert.admissible)
            self.assertAlmostEqual(cert.witness_metric, 1.0, places=9)
            self.assertIn("RECOVERED", cert.verdict)
            self.assertIn(f"({expected_syn[0]:.0f}, {expected_syn[1]:.0f})", cert.verdict)
            self.assertIn("bit-flip", cert.observable_consequence)

    def test_kcbs_contextuality_pentagram(self):
        """Verify KCBS pentagram has adjacent orthogonality and reaches sqrt(5) > 2."""
        cert = evaluate_kcbs_contextuality()
        self.assertIsInstance(cert, ReasonCertificate)
        self.assertTrue(cert.admissible)
        self.assertIn("CONTEXTUAL", cert.verdict)
        self.assertAlmostEqual(cert.witness_metric, np.sqrt(5.0), places=6)
        self.assertGreater(cert.witness_metric, 2.0)

    def test_peres_mermin_hypergraph_certificate(self):
        """Verify Peres-Mermin contextuality hypergraph evaluation produces obstruction certificate."""
        cert = evaluate_peres_mermin_contextuality_hypergraph()
        self.assertIsInstance(cert, ReasonCertificate)
        self.assertTrue(cert.admissible)
        self.assertIn("CONTEXTUAL OBSTRUCTION", cert.verdict)
        self.assertEqual(cert.witness_metric, 1.0)
        self.assertIsNotNone(cert.nullspace_certificate)
        self.assertEqual(cert.nullspace_certificate['left_nullspace_certificate'], [1, 1, 1, 1, 1, 1])

    def test_qutrit_mubs_orthonormality_and_overlap(self):
        """Verify 4 MUBs in d=3 have exact mutual overlap 1/3."""
        cert = evaluate_qutrit_mubs()
        self.assertIsInstance(cert, ReasonCertificate)
        self.assertTrue(cert.admissible)
        self.assertIn("MUTUALLY UNBIASED", cert.verdict)
        self.assertLess(cert.witness_metric, 1e-12)

    def test_transposition_adversary_certificate(self):
        """Verify single-qubit transposition fails relational extension."""
        cert = evaluate_transposition_adversary()
        self.assertFalse(cert.admissible)
        self.assertIn("INADMISSIBLE", cert.verdict)
        self.assertAlmostEqual(cert.witness_metric, -0.5, places=6)

    def test_qutrit_cubic_adversary_certificate(self):
        """Verify qutrit spectrum (0.6, 0.6, -0.2) fails cubic determinant positivity."""
        cert = evaluate_qutrit_cubic_adversary()
        self.assertFalse(cert.admissible)
        self.assertIn("INADMISSIBLE", cert.verdict)
        self.assertLess(cert.witness_metric, 0.0)
        self.assertAlmostEqual(cert.witness_metric, -0.072, places=6)

    def test_lindblad_triangle_adversary_certificate(self):
        """Verify Lindblad generator violating triangle inequality produces Choi negativity."""
        cert = evaluate_lindblad_triangle_adversary()
        self.assertFalse(cert.admissible)
        self.assertIn("INADMISSIBLE", cert.verdict)
        self.assertLess(cert.witness_metric, 0.0)

    def test_extrapolation_campaign_execution(self):
        """Verify full extrapolation campaign executes and all verdicts are sound."""
        results = run_extrapolation_campaign()
        self.assertEqual(results['total_evaluations'], 10)
        self.assertTrue(results['all_verdicts_sound'])
        certs = results['certificates']
        self.assertEqual(len(certs), 10)

        required_fields = {
            'object_type', 'target_object', 'preserved_invariant',
            'relational_test', 'witness_name', 'witness_metric',
            'admissible', 'verdict', 'observable_consequence', 'nullspace_certificate'
        }
        for c in certs:
            self.assertEqual(set(c.keys()), required_fields)
            self.assertIsNotNone(c['target_object'])
            self.assertIsInstance(c['admissible'], bool)

    def test_solve_f2_system_exact_nullspace_certificate(self):
        """Verify solve_f2_system solves consistent systems and produces left nullspace witnesses."""
        # 1. Consistent system
        H_cons = np.array([[1, 0, 1], [0, 1, 1], [1, 1, 0]], dtype=int)
        b_cons = np.array([1, 1, 0], dtype=int)
        is_cons, x, y = solve_f2_system(H_cons, b_cons)
        self.assertTrue(is_cons)
        self.assertIsNotNone(x)
        self.assertTrue(np.all((H_cons @ x) % 2 == b_cons))
        self.assertIsNone(y)

        # 2. Inconsistent system
        b_incons = np.array([1, 1, 1], dtype=int)  # rows sum to 0 mod 2, but b sums to 1
        is_cons2, x2, y2 = solve_f2_system(H_cons, b_incons)
        self.assertFalse(is_cons2)
        self.assertIsNone(x2)
        self.assertIsNotNone(y2)
        self.assertTrue(np.all((y2 @ H_cons) % 2 == 0))
        self.assertEqual(int((y2 @ b_incons) % 2), 1)

    def test_isolated_frustrated_cycle_with_even_total_parity(self):
        """Verify left nullspace solver isolates frustrated cycle even when total parity sum is even."""
        # Two disconnected triangles: both frustrated, each product is -1
        # Total sum of parity bits = 1 + 1 = 2 = 0 mod 2!
        # Naive parity sum fails, but left nullspace solver finds y = (1, 1, 1, 0, 0, 0)
        hg = GenericCompatibilityHypergraph(
            name="Two Frustrated Triangles (Even Total Parity)",
            num_nodes=6,
            contexts=[(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)],
            parities=[1, 1, -1, 1, 1, -1],
        )
        cert = hg.audit()
        self.assertTrue(cert.has_f2_obstruction)
        self.assertFalse(cert.is_consistent)
        self.assertIsNotNone(cert.left_nullspace_certificate)
        # Left nullspace vector must be an exact witness
        y = np.array(cert.left_nullspace_certificate)
        self.assertTrue(np.all((y @ hg.H) % 2 == 0))
        syndrome_f2 = np.array([0 if p == 1 else 1 for p in hg.parities], dtype=int)
        self.assertEqual(int((y @ syndrome_f2) % 2), 1)
        self.assertIn("unsatisfiable subcycle", cert.verdict)

    def test_admissibility_grammar_engine_inference(self):
        """Verify automated AdmissibilityGrammarEngine infers invariants and witnesses across 5 categories."""
        engine = AdmissibilityGrammarEngine

        # 1. Affine map: Transposition adversary
        res_trans = engine.infer_and_evaluate(
            "affine_bloch_map",
            {"A": np.diag([1.0, -1.0, 1.0]), "c": np.zeros(3)},
            name="Transposition Test",
        )
        self.assertFalse(res_trans['admissible'])
        self.assertAlmostEqual(res_trans['witness_metric'], -0.5, places=5)
        self.assertIn("Choi-Jamiolkowski", res_trans['relational_test'])

        # 2. Qutrit vector: Quadratic pass / cubic fail
        from ngc_geometry_lab.geometry import gell_mann_matrices
        gm = gell_mann_matrices()
        rho_bad = np.diag([0.6, 0.6, -0.2]).astype(complex)
        r_bad = np.array([float(np.trace(rho_bad @ gm[a]).real) for a in range(8)])
        res_qutrit = engine.infer_and_evaluate(
            "qutrit_bloch_vector",
            {"r": r_bad},
            name="Cubic Adversary Test",
        )
        self.assertFalse(res_qutrit['admissible'])
        self.assertAlmostEqual(res_qutrit['witness_metric'], -0.072, places=5)

        # 3. Lindblad generator: Triangle-violating generator
        res_lind = engine.infer_and_evaluate(
            "lindblad_generator",
            {"M": np.diag([-0.1, -0.1, -0.5]), "v": np.zeros(3)},
            name="Lindblad Triangle Test",
        )
        self.assertFalse(res_lind['admissible'])
        self.assertLess(res_lind['witness_metric'], 0.0)

        # 4. Bipartite state: Horodecki 3x3 bound entangled state
        a = 0.5
        b = (1.0 + a) / 2.0
        c_val = np.sqrt(1.0 - a**2) / 2.0
        rho_h = np.zeros((9, 9), dtype=complex)
        rho_h[0, 0] = a; rho_h[1, 1] = a; rho_h[2, 2] = a
        rho_h[3, 3] = a; rho_h[4, 4] = a; rho_h[5, 5] = a
        rho_h[6, 6] = b; rho_h[7, 7] = a; rho_h[8, 8] = b
        rho_h[0, 4] = a; rho_h[4, 0] = a
        rho_h[0, 8] = a; rho_h[8, 0] = a
        rho_h[4, 8] = a; rho_h[8, 4] = a
        rho_h[6, 8] = c_val; rho_h[8, 6] = c_val
        rho_h /= (8.0 * a + 1.0)
        res_bip = engine.infer_and_evaluate(
            "bipartite_density",
            {"rho": rho_h, "dim_A": 3, "dim_B": 3, "is_horodecki": True},
            name="Horodecki Range Test",
        )
        self.assertTrue(res_bip['admissible'])
        self.assertIn("BOUND ENTANGLEMENT", res_bip['verdict'])
        self.assertGreaterEqual(res_bip['witness_metric'], -1e-12)
        self.assertIsNotNone(res_bip.get('nullspace_certificate'))

        # 5. Compatibility hypergraph: Peres-Mermin grid
        contexts = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8)
        ]
        parities = [1, 1, 1, 1, 1, -1]
        res_hg = engine.infer_and_evaluate(
            "compatibility_hypergraph",
            {"num_nodes": 9, "contexts": contexts, "parities": parities},
            name="Peres-Mermin Hypergraph Test",
        )
        self.assertTrue(res_hg['admissible'])
        self.assertIn("CONTEXTUAL OBSTRUCTION", res_hg['verdict'])
        self.assertEqual(res_hg['witness_metric'], 1.0)
        self.assertEqual(res_hg['left_nullspace_certificate'], [1, 1, 1, 1, 1, 1])

    def test_category_ambiguous_campaign_execution(self):
        """Verify category-ambiguous campaign infers all categories and evaluates all 5 hybrid cases."""
        campaign_results = run_category_ambiguous_campaign()
        self.assertEqual(campaign_results['total_cases'], 5)
        self.assertTrue(campaign_results['all_categories_inferred_correctly'])
        self.assertTrue(campaign_results['all_witnesses_sound'])

        evals = campaign_results['evaluations']
        # Check inferred categories match expectation
        expected_cats = [
            'affine_bloch_map',
            'qutrit_bloch_vector',
            'compatibility_hypergraph',
            'lindblad_generator',
            'bipartite_density',
        ]
        for e, exp_cat in zip(evals, expected_cats):
            self.assertEqual(e['inferred_category'], exp_cat)
            self.assertIn('witness_metric', e)
            self.assertIn('verdict', e)


if __name__ == '__main__':
    unittest.main()
