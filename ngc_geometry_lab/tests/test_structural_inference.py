"""Tests for Gate L2-E: Type-Erased Structural Inference Qualification."""
import unittest
import numpy as np

from ngc_geometry_lab.structural_inference import (
    OpaqueCarrier,
    solve_f2_system_minimal_support,
    compute_horodecki_range_product_span_rank,
    probe_and_infer_structure,
    evaluate_opaque_carrier,
    run_l2e_qualification_campaign,
    audit_representation_adequacy_framework,
)
from ngc_geometry_lab.geometry import gell_mann_matrices


class TestStructuralInferenceL2E(unittest.TestCase):
    """Test suite verifying Gate L2-E type-erased structural inference."""

    def test_minimal_support_left_nullspace_solver(self):
        """Verify solver strictly minimizes ||y||_0 on inconsistent hypergraphs."""
        # 1. Peres-Mermin 9-node grid: all 6 contexts required for obstruction
        contexts = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8)
        ]
        H_pm = np.zeros((6, 9), dtype=int)
        for e, c in enumerate(contexts):
            for v in c:
                H_pm[e, v] = 1
        b_pm = np.array([0, 0, 0, 0, 0, 1], dtype=int)
        is_cons, _, min_y, min_wt = solve_f2_system_minimal_support(H_pm, b_pm)
        self.assertFalse(is_cons)
        self.assertEqual(min_wt, 6)
        self.assertTrue(np.all(min_y == 1))

        # 2. Two frustrated triangles: each has weight 3, sum is weight 6 (even parity sum)
        # Solver must find the strictly minimal weight 3, NOT 6!
        H_two = np.array([
            [1, 1, 0, 0, 0, 0],
            [0, 1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 1, 0, 1],
        ], dtype=int)
        b_two = np.array([0, 0, 1, 0, 0, 1], dtype=int)
        is_cons2, _, min_y2, min_wt2 = solve_f2_system_minimal_support(H_two, b_two)
        self.assertFalse(is_cons2)
        self.assertEqual(min_wt2, 3)  # Strictly minimal!
        self.assertTrue(np.all((min_y2 @ H_two) % 2 == 0))
        self.assertEqual(int((min_y2 @ b_two) % 2), 1)

    def test_independent_horodecki_product_span_solver(self):
        """Verify algorithmic product-vector solver independently certifies range deficiency."""
        a = 0.5
        b_val = (1.0 + a) / 2.0
        c_val = np.sqrt(1.0 - a**2) / 2.0
        rho_h = np.zeros((9, 9), dtype=complex)
        rho_h[0, 0] = a; rho_h[1, 1] = a; rho_h[2, 2] = a
        rho_h[3, 3] = a; rho_h[4, 4] = a; rho_h[5, 5] = a
        rho_h[6, 6] = b_val; rho_h[7, 7] = a; rho_h[8, 8] = b_val
        rho_h[0, 4] = a; rho_h[4, 0] = a
        rho_h[0, 8] = a; rho_h[8, 0] = a
        rho_h[4, 8] = a; rho_h[8, 4] = a
        rho_h[6, 8] = c_val; rho_h[8, 6] = c_val
        rho_h /= (8.0 * a + 1.0)

        res = compute_horodecki_range_product_span_rank(rho_h, num_samples=300)
        self.assertEqual(res['nullspace_rho_dim'], 2)
        self.assertEqual(res['nullspace_pt_dim'], 3)
        self.assertEqual(res['rank_rho'], 7)
        self.assertTrue(res['is_range_deficient'])
        self.assertLess(res['product_span_rank'], res['rank_rho'])

    def test_category_confusion_identical_3x3_shapes(self):
        """Verify 4 opaque carriers with identical (3, 3) shape are differentiated by operational probing."""
        # 1. Transformation
        c1 = OpaqueCarrier("trans", (3, 3), {'matrix': np.diag([1.0, -1.0, 1.0])})
        self.assertEqual(probe_and_infer_structure(c1), 'affine_bloch_map')
        eval1 = evaluate_opaque_carrier(c1)
        self.assertFalse(eval1['admissible'])
        self.assertIn("INADMISSIBLE", eval1['verdict'])

        # 2. Generator
        c2 = OpaqueCarrier("gen", (3, 3), {'matrix': np.diag([-0.1, -0.1, -0.5])})
        self.assertEqual(probe_and_infer_structure(c2), 'lindblad_generator')
        eval2 = evaluate_opaque_carrier(c2)
        self.assertFalse(eval2['admissible'])

        # 3. Density state
        c3 = OpaqueCarrier("state", (3, 3), {'matrix': np.diag([0.6, 0.3, 0.1]).astype(complex)})
        self.assertEqual(probe_and_infer_structure(c3), 'qutrit_density_state')
        eval3 = evaluate_opaque_carrier(c3)
        self.assertTrue(eval3['admissible'])

        # 4. Hypergraph
        c4 = OpaqueCarrier("hyper", (3, 3), {
            'H': np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]]),
            'b': np.array([0, 0, 1]),
            'parities': [1, 1, -1]
        })
        self.assertEqual(probe_and_infer_structure(c4), 'compatibility_hypergraph')
        eval4 = evaluate_opaque_carrier(c4)
        self.assertIn("CONTEXTUAL OBSTRUCTION", eval4['verdict'])

    def test_representation_scrambling_invariance(self):
        """Verify that verdicts and minimal witnesses remain invariant under basis and context permutations."""
        # Scramble context and vertex order of a frustrated triangle
        H_orig = np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]], dtype=int)
        b_orig = np.array([0, 0, 1], dtype=int)

        # Permute vertices (columns) and contexts (rows)
        col_perm = [2, 0, 1]
        row_perm = [1, 2, 0]
        H_scrambled = H_orig[row_perm][:, col_perm]
        b_scrambled = b_orig[row_perm]

        _, _, y1, wt1 = solve_f2_system_minimal_support(H_orig, b_orig)
        _, _, y2, wt2 = solve_f2_system_minimal_support(H_scrambled, b_scrambled)

        self.assertEqual(wt1, wt2)
        self.assertEqual(wt1, 3)

    def test_equivalent_forms_challenge(self):
        """Verify equivalent representations of qutrit pure state yield identical admissibility."""
        gm = gell_mann_matrices()
        rho = np.zeros((3, 3), dtype=complex)
        rho[0, 0] = 1.0  # |0><0|
        r = np.array([float(np.trace(rho @ gm[a]).real) for a in range(8)])

        c_rho = OpaqueCarrier("eq_rho", (3, 3), {'matrix': rho})
        c_r = OpaqueCarrier("eq_r", (8,), {'vec': r})

        res_rho = evaluate_opaque_carrier(c_rho)
        res_r = evaluate_opaque_carrier(c_r)

        self.assertTrue(res_rho['admissible'])
        self.assertTrue(res_r['admissible'])

    def test_full_l2e_qualification_campaign(self):
        """Execute full L2-E campaign and assert all qualification criteria pass."""
        res = run_l2e_qualification_campaign()
        self.assertTrue(res['all_l2e_passed'])
        self.assertTrue(res['confusion_passed'])
        self.assertTrue(res['minimal_support_passed'])
        self.assertTrue(res['horodecki_independent_passed'])
        self.assertTrue(res['equivalent_forms_passed'])

    def test_representation_adequacy_schema_universal_audit(self):
        """Verify the formal Collision -> Missing Relation -> Grammar Expansion schema across all 6 domains."""
        records = audit_representation_adequacy_framework()
        self.assertEqual(len(records), 6)
        expected_domains = [
            "Qubit_Admissibility_Gate_L1",
            "Channel_Complete_Positivity_World_C",
            "Qutrit_Admissibility_World_B",
            "Hypergraph_Contextuality_World_D",
            "Three_Qubit_SLOCC_Gate_L3_C",
            "Four_Qubit_Invariant_Ring_Gate_L4_R",
        ]
        for r, exp_id in zip(records, expected_domains):
            self.assertEqual(r.domain_id, exp_id)
            self.assertTrue(r.adequacy_certified)
            self.assertTrue(len(r.expanded_grammar) > len(r.initial_grammar) or r.syzygy_or_dependency_eliminated is not None)
            self.assertIn("quotient", r.quotient_space_interpretation.lower())


if __name__ == '__main__':
    unittest.main()
