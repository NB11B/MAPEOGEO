r"""Unit tests for the Simplex Boundary Correspondence and Euclidean Realizability Gate.

Verifies the mathematical bridge between four-qubit polynomial invariants and classical
Euclidean metric geometry, enforcing the distinction between global algebraic identities
and local metric realizability (acute, right, obtuse, degenerate, invalid, complex).
"""
import unittest
import numpy as np

from ngc_geometry_lab.simplex_boundary_correspondence import (
    classify_euclidean_realizability,
    verify_simplex_boundary_theorems_symbolic,
    audit_simplex_boundary_correspondence_numerical,
    run_simplex_boundary_correspondence_campaign,
    SimplexBoundaryCorrespondenceCertificate,
    EuclideanRealizabilitySignature
)


class TestSimplexBoundaryCorrespondence(unittest.TestCase):
    """Test suite validating the quantum-invariant to Euclidean-metric correspondence."""

    def test_symbolic_theorems_all_proved(self):
        """Verify that all 7 symbolic boundary theorems prove with zero residual."""
        records = verify_simplex_boundary_theorems_symbolic()
        self.assertEqual(len(records), 7)
        for r in records:
            self.assertTrue(r['proved'], f"Failed theorem: {r['theorem_id']}")
            self.assertEqual(r['residual'], 0.0)

    def test_euclidean_realizability_classifications(self):
        """Verify that the realizability gate correctly partitions the parameter space."""
        # 1. Acute triangle -> Realizable disphenoid
        sig_acute = classify_euclidean_realizability(0.6, 0.5, 0.4, 0.0)
        self.assertTrue(sig_acute.triangle_realizable)
        self.assertEqual(sig_acute.triangle_classification, "ACUTE")
        self.assertTrue(sig_acute.disphenoid_realizable)

        # 2. Right triangle -> Pythagorean locus
        sig_right = classify_euclidean_realizability(0.5, 0.4, 0.3, 0.0)
        self.assertTrue(sig_right.triangle_realizable)
        self.assertEqual(sig_right.triangle_classification, "RIGHT")
        self.assertTrue(sig_right.disphenoid_realizable)

        # 3. Obtuse triangle -> Non-realizable disphenoid in R^3
        sig_obtuse = classify_euclidean_realizability(0.9, 0.5, 0.5, 0.0)
        self.assertTrue(sig_obtuse.triangle_realizable)
        self.assertEqual(sig_obtuse.triangle_classification, "OBTUSE")
        self.assertFalse(sig_obtuse.disphenoid_realizable)

        # 4. Degenerate flat triangle
        sig_flat = classify_euclidean_realizability(0.8, 0.5, 0.3, 0.0)
        self.assertEqual(sig_flat.triangle_classification, "DEGENERATE_FLAT")
        self.assertFalse(sig_flat.triangle_realizable)

        # 5. Triangle-invalid
        sig_inv = classify_euclidean_realizability(1.2, 0.5, 0.3, 0.0)
        self.assertEqual(sig_inv.triangle_classification, "NON_REALIZABLE")
        self.assertTrue(sig_inv.algebraic_continuation_active)

        # 6. Complex parameter slice
        sig_cplx = classify_euclidean_realizability(0.8 + 0.1j, 0.6 - 0.1j, 0.5, 0.2)
        self.assertEqual(sig_cplx.triangle_classification, "COMPLEX_NON_METRIC")
        self.assertTrue(sig_cplx.algebraic_continuation_active)

    def test_pythagorean_locus_vanishes_d6(self):
        """Verify that a Pythagorean right-angled triangle (3, 4, 5) forces D_6 = 0 on d=0."""
        records, max_res = audit_simplex_boundary_correspondence_numerical([
            (0.5, 0.4, 0.3, 0.0)
        ])
        rec = records[0]
        self.assertTrue(rec['algebraic_verified'])
        self.assertLess(abs(rec['D6']), 1e-14)
        self.assertEqual(rec['realizability_signature']['triangle_classification'], "RIGHT")

    def test_numerical_audit_residuals_bounded_across_all_regimes(self):
        """Verify that algebraic formulas hold across all 8 regimes (max residual < 1e-12)."""
        records, max_res = audit_simplex_boundary_correspondence_numerical()
        self.assertLess(max_res, 1e-12)
        self.assertEqual(len(records), 8)
        for r in records:
            self.assertTrue(r['algebraic_verified'])

    def test_full_campaign_execution_and_realizability_gate(self):
        """Verify that the full correspondence campaign runs and certifies all criteria."""
        cert = run_simplex_boundary_correspondence_campaign()
        self.assertIsInstance(cert, SimplexBoundaryCorrespondenceCertificate)
        self.assertTrue(cert.all_symbolic_theorems_proved)
        self.assertEqual(cert.num_theorems_verified, 7)
        self.assertTrue(cert.realizability_gate_passed)
        self.assertLess(cert.max_numerical_residual, 1e-12)
        self.assertIn("EUCLIDEAN_REALIZABILITY", cert.physical_and_geometric_interpretation)


if __name__ == '__main__':
    unittest.main()
