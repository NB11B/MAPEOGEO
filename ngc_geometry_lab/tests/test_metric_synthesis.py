r"""Unit tests for Autonomous Metric Object Synthesis, Blind Reconstruction, and Competing Explanations.

Verifies:
1. Gate MetricSynth-1: Symbolic derivations of G_triangle and G_disphenoid from invariants.
2. Rigorous Sylvester's criterion: Full principal-minor PSD condition (all 1x1, 2x2, and 3x3 minors).
3. Gate MetricSynth-2: Blind reconstruction of dimension m, entries, alpha, and PSD conditions
   from opaque polynomials without geometric templates or simplex dimension hints.
4. Gate MetricSynth-3: Adversarial benchmark against competing structural explanations
   (Pfaffian, discriminant, resultant, factorization, and deceptive non-metric forms),
   verifying that genuine invariants select Gram geometry while controls strictly fail closed
   with NO_METRIC_REALIZATION.
"""
import unittest
import numpy as np

from ngc_geometry_lab.metric_synthesis import (
    derive_triangle_metric_object_symbolic,
    derive_tetrahedron_metric_object_symbolic,
    audit_metric_synthesis_numerical,
    run_autonomous_metric_derivation_campaign,
    run_gate_metricsynth2_blind_campaign,
    run_gate_metricsynth3_competing_campaign,
    AutonomousMetricSynthesisCertificate
)


class TestMetricSynthesis(unittest.TestCase):
    """Test suite validating autonomous metric object derivation and blind reconstruction."""

    def test_triangle_metric_derivation_symbolic(self):
        """Verify M_4 = 1/4 * det(G_tri) and all principal minors checked."""
        rec = derive_triangle_metric_object_symbolic()
        self.assertTrue(rec.symbolic_identity_proved)
        self.assertEqual(rec.symbolic_residual, 0.0)
        self.assertTrue(rec.all_principal_minors_verified)
        self.assertTrue(rec.psd_recovers_realizability)
        self.assertEqual(rec.scaling_factor_alpha, 0.25)

    def test_tetrahedron_metric_derivation_symbolic(self):
        """Verify D_6 = -1/16 * det(G_disph) and all 7 principal minors checked."""
        rec = derive_tetrahedron_metric_object_symbolic()
        self.assertTrue(rec.symbolic_identity_proved)
        self.assertEqual(rec.symbolic_residual, 0.0)
        self.assertTrue(rec.all_principal_minors_verified)
        self.assertTrue(rec.psd_recovers_realizability)
        self.assertEqual(rec.scaling_factor_alpha, -0.0625)

    def test_numerical_audit_and_psd_partitions(self):
        """Verify that G >= 0 holds exactly on realizable metric regimes."""
        records, max_res = audit_metric_synthesis_numerical()
        self.assertLess(max_res, 1e-14)

        # 1. Acute: both G_tri and G_tet are strictly PSD (eigenvalues > 0)
        rec_acute = [r for r in records if r['regime_name'] == "Acute_Triangle"][0]
        self.assertTrue(rec_acute['G_triangle_is_PSD'])
        self.assertTrue(rec_acute['G_disphenoid_is_PSD'])

        # 2. Right: G_tri is PSD, G_tet has zero eigenvalue (flat)
        rec_right = [r for r in records if r['regime_name'] == "Right_Pythagorean"][0]
        self.assertTrue(rec_right['G_triangle_is_PSD'])
        self.assertTrue(rec_right['G_disphenoid_is_PSD'])
        self.assertLess(abs(rec_right['det_G_disphenoid']), 1e-14)

        # 3. Obtuse: G_tri is PSD, but G_tet is NOT PSD (negative eigenvalue)
        rec_obtuse = [r for r in records if r['regime_name'] == "Obtuse_Triangle"][0]
        self.assertTrue(rec_obtuse['G_triangle_is_PSD'])
        self.assertFalse(rec_obtuse['G_disphenoid_is_PSD'])

        # 4. Invalid: G_tri is NOT PSD
        rec_inv = [r for r in records if r['regime_name'] == "Invalid_Triangle"][0]
        self.assertFalse(rec_inv['G_triangle_is_PSD'])

    def test_gate_metricsynth2_blind_reconstruction_degree4(self):
        """Verify blind reconstruction on degree-4 invariant: deduces m=2, alpha=0.25, and 3 minors."""
        results = run_gate_metricsynth2_blind_campaign()
        res_m4 = [r for r in results if r.problem_id == "Opaque_Degree_4_Polynomial"][0]
        self.assertTrue(res_m4.reconstruction_success)
        self.assertEqual(res_m4.deduced_matrix_dimension, 2)
        self.assertEqual(res_m4.scaling_factor_alpha, 0.25)
        self.assertEqual(res_m4.symbolic_residual, 0.0)
        self.assertEqual(res_m4.num_principal_minors, 3)  # two 1x1, one 2x2
        self.assertIn("Collinear", res_m4.rank_deficient_boundary_locus)

    def test_gate_metricsynth2_blind_reconstruction_degree6(self):
        """Verify blind reconstruction on degree-6 invariant: deduces m=3, alpha=-0.0625, and 7 minors."""
        results = run_gate_metricsynth2_blind_campaign()
        res_d6 = [r for r in results if r.problem_id == "Opaque_Degree_6_Polynomial"][0]
        self.assertTrue(res_d6.reconstruction_success)
        self.assertEqual(res_d6.deduced_matrix_dimension, 3)
        self.assertEqual(res_d6.scaling_factor_alpha, -0.0625)
        self.assertEqual(res_d6.symbolic_residual, 0.0)
        self.assertEqual(res_d6.num_principal_minors, 7)  # three 1x1, three 2x2, one 3x3
        self.assertIn("Pythagorean", res_d6.rank_deficient_boundary_locus)

    def test_gate_metricsynth3_targets_select_gram_metric(self):
        """Verify Gate MetricSynth-3: M_4 and D_6 independently select Gram geometry over all competitors."""
        results = run_gate_metricsynth3_competing_campaign()
        res_m4 = [r for r in results if r.problem_id == "Target_M4_Degree4"][0]
        res_d6 = [r for r in results if r.problem_id == "Target_D6_Degree6"][0]

        # M_4 selects GRAM_DETERMINANT with 0 residual
        self.assertEqual(res_m4.selected_family, "GRAM_DETERMINANT")
        self.assertTrue(res_m4.metric_realization_admitted)
        self.assertEqual(res_m4.metric_realization_verdict, "ACCEPTED_GRAM_REALIZATION")
        self.assertIn("Euclidean triangle cone", res_m4.realizability_cone_description)

        # D_6 selects GRAM_DETERMINANT with 0 residual
        self.assertEqual(res_d6.selected_family, "GRAM_DETERMINANT")
        self.assertTrue(res_d6.metric_realization_admitted)
        self.assertEqual(res_d6.metric_realization_verdict, "ACCEPTED_GRAM_REALIZATION")
        self.assertIn("Euclidean disphenoid cone", res_d6.realizability_cone_description)

    def test_gate_metricsynth3_adversarial_controls_fail_closed(self):
        """Verify Gate MetricSynth-3: All 5 adversarial controls strictly fail closed with NO_METRIC_REALIZATION."""
        results = run_gate_metricsynth3_competing_campaign()

        # 1. Monomial L_4 selects ALGEBRAIC_FACTORIZATION, rejects Gram
        res_l4 = [r for r in results if r.problem_id == "Control_L4_Monomial"][0]
        self.assertEqual(res_l4.selected_family, "ALGEBRAIC_FACTORIZATION")
        self.assertFalse(res_l4.metric_realization_admitted)
        self.assertEqual(res_l4.metric_realization_verdict, "NO_METRIC_REALIZATION")

        # 2. Skew-symmetric Pfaffian selects PFAFFIAN, rejects Gram
        res_pfaff = [r for r in results if r.problem_id == "Control_Pfaffian_Symplectic"][0]
        self.assertEqual(res_pfaff.selected_family, "PFAFFIAN")
        self.assertFalse(res_pfaff.metric_realization_admitted)
        self.assertEqual(res_pfaff.metric_realization_verdict, "NO_METRIC_REALIZATION")

        # 3. Cubic discriminant selects POLYNOMIAL_DISCRIMINANT, rejects Gram
        res_disc = [r for r in results if r.problem_id == "Control_Cubic_Discriminant"][0]
        self.assertEqual(res_disc.selected_family, "POLYNOMIAL_DISCRIMINANT")
        self.assertFalse(res_disc.metric_realization_admitted)
        self.assertEqual(res_disc.metric_realization_verdict, "NO_METRIC_REALIZATION")

        # 4. Resultant selects RESULTANT, rejects Gram
        res_res = [r for r in results if r.problem_id == "Control_Polynomial_Resultant"][0]
        self.assertEqual(res_res.selected_family, "RESULTANT")
        self.assertFalse(res_res.metric_realization_admitted)
        self.assertEqual(res_res.metric_realization_verdict, "NO_METRIC_REALIZATION")

        # 5. Deceptive non-metric selects NO_COMPACT_STRUCTURE due to signature obstruction
        res_decep = [r for r in results if r.problem_id == "Control_Deceptive_Nonmetric"][0]
        self.assertEqual(res_decep.selected_family, "NO_COMPACT_STRUCTURE")
        self.assertFalse(res_decep.metric_realization_admitted)
        self.assertEqual(res_decep.metric_realization_verdict, "NO_METRIC_REALIZATION")

    def test_full_campaign_execution(self):
        """Verify that the full metric synthesis campaign executes and certifies all three gates."""
        cert = run_autonomous_metric_derivation_campaign()
        self.assertIsInstance(cert, AutonomousMetricSynthesisCertificate)
        self.assertTrue(cert.all_derivations_proved)
        self.assertEqual(cert.num_metric_objects_derived, 2)
        self.assertEqual(len(cert.metricsynth2_blind_results), 2)
        self.assertEqual(len(cert.metricsynth3_competing_results), 7)
        self.assertTrue(cert.all_metricsynth3_classified_correctly)
        self.assertLess(cert.max_numerical_residual, 1e-14)


if __name__ == '__main__':
    unittest.main()
