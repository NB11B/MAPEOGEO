"""Analytic and invalid-input tests independent of the complex oracle."""
import unittest

import numpy as np
from numpy.testing import assert_allclose

from ngc_geometry_lab import geometry as g


class TetraTests(unittest.TestCase):
    def test_vertices_and_fresh_storage(self):
        expected = np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]) / np.sqrt(3)
        n = g.tetra_directions()
        assert_allclose(n, expected, atol=1e-15)
        assert_allclose(n.sum(axis=0), 0, atol=1e-15)
        assert_allclose(n @ n.T, (4*np.eye(4)-1)/3, atol=1e-15)
        n[:] = 0
        assert_allclose(g.tetra_directions(), expected)

    def test_mixed_state_and_vertex_probabilities(self):
        assert_allclose(g.tetra_probabilities([0,0,0]), np.full(4, .25))
        n = g.tetra_directions()
        assert_allclose(g.tetra_probabilities(n[0]), [.5,1/6,1/6,1/6])
        assert_allclose(g.tetra_reconstruct([.5,1/6,1/6,1/6]), n[0])

    def test_transformation_matrix_and_composition(self):
        r1 = g.rotation([1, 0, 0], np.pi / 3)
        r2 = g.rotation([0, 1, 1], np.pi / 4)
        m1 = g.tetra_transformation_matrix(r1)
        m2 = g.tetra_transformation_matrix(r2)
        m12 = g.tetra_transformation_matrix(r2 @ r1)
        assert_allclose(m2 @ m1, m12, atol=1e-15)

        # Test action on probability vector matches rotated state
        state = np.array([0.3, -0.4, 0.5])
        p = g.tetra_probabilities(state)
        p_rotated = g.tetra_probabilities(r1 @ state)
        assert_allclose(m1 @ p, p_rotated, atol=1e-15)

    def test_purity_bound(self):
        # Pure state has norm 1, so sum p_i^2 = 1/4 + 1/12 = 1/3
        n = g.tetra_directions()
        p_pure = g.tetra_probabilities(n[0])
        self.assertAlmostEqual(g.tetra_purity_bound(p_pure), 1/3, places=14)

        # Mixed origin has norm 0, so sum p_i^2 = 1/4
        p_mixed = g.tetra_probabilities([0, 0, 0])
        self.assertAlmostEqual(g.tetra_purity_bound(p_mixed), 1/4, places=14)

    def test_one_hot_distribution_is_not_physical(self):
        with self.assertRaises(ValueError): g.tetra_reconstruct([1,0,0,0])
        assert_allclose(g.tetra_reconstruct([1,0,0,0], enforce_physical=False), [np.sqrt(3)]*3)

    def test_invalid_probabilities_are_not_normalized(self):
        for p in ([.2]*4, [-.1,.3,.4,.4], [1,0,0], [np.nan,0,0,1], [.25+.1j,.25,.25,.25]):
            with self.subTest(p=p), self.assertRaises(ValueError): g.tetra_reconstruct(p)

    def test_invalid_state(self):
        for state in ([1.1,0,0], [0,0], [np.inf,0,0], [1j,0,0]):
            with self.subTest(state=state), self.assertRaises(ValueError): g.tetra_probabilities(state)


class OperationTests(unittest.TestCase):
    def test_active_rodrigues(self):
        r = g.rotation([0,0,4], np.pi/2)
        assert_allclose(r @ [1,0,0], [0,1,0], atol=1e-15)
        assert_allclose(r.T @ r, np.eye(3), atol=1e-15)
        self.assertAlmostEqual(np.linalg.det(r), 1)

    def test_rotation_order_matters(self):
        x = g.rotation([1,0,0], np.pi/2)
        z = g.rotation([0,0,1], np.pi/2)
        assert_allclose(x @ z @ [1,0,0], [0,0,1], atol=1e-15)
        assert_allclose(z @ x @ [1,0,0], [0,1,0], atol=1e-15)

    def test_crossed_and_inserted_polarizers(self):
        weight, final = g.projection_transmission([1,0,0], [[0,1,0]])
        self.assertEqual(weight, 0)
        assert_allclose(final, [0,0,0])
        weight, final = g.projection_transmission([1,0,0], [[1,1,0],[0,1,0]])
        self.assertAlmostEqual(weight, .25)
        assert_allclose(final, [0,.5,0], atol=1e-15)

    def test_exponents_and_no_projection(self):
        for exponent, expected in ((1,.5),(2,.25),(4,.0625)):
            self.assertAlmostEqual(g.projection_transmission([1,0,0], [[1,1,0],[0,1,0]], exponent=exponent)[0], expected)
        weight, final = g.projection_transmission([0,0,1], [])
        self.assertEqual(weight, 1)
        assert_allclose(final, [0,0,1])

    def test_invalid_operations(self):
        for axis, angle in (([0,0,0],0),([0,0],0),([1j,0,0],0),([1,0,0],np.inf),([1,0,0],1j)):
            with self.subTest(axis=axis, angle=angle), self.assertRaises(ValueError): g.rotation(axis, angle)
        for state, axes, exponent in (([2,0,0],[],2),([1j,0,0],[],2),([1,0,0],[[0,0,0]],2),([1,0,0],[[np.inf,0,0]],2),([1,0,0],[],0),([1,0,0],[],np.nan)):
            with self.subTest(state=state, axes=axes, exponent=exponent), self.assertRaises(ValueError): g.projection_transmission(state, axes, exponent=exponent)


class MetricTests(unittest.TestCase):
    def test_non_euclidean_metric_recovered_from_conjugated_cubic_family(self):
        s = np.array([[2.,.3,0],[0,1.,.2],[0,0,.5]])
        inv = np.linalg.inv(s)
        rotations = [s @ g.rotation(axis,np.pi/2) @ inv for axis in np.eye(3)]
        projectors = [s @ np.diag([1.,0,0]) @ inv]
        result = g.infer_metric(rotations, projectors)
        expected = inv.T @ inv
        expected *= 3/np.trace(expected)
        self.assertEqual(result['status'], 'unique_up_to_scale')
        self.assertEqual(result['space_dimension'], 1)
        assert_allclose(result['metric'], expected, atol=1e-10)
        self.assertLess(result['residual'], 1e-10)

    def test_insufficient_family_returns_spd_witness_with_ambiguity(self):
        result = g.infer_metric([np.eye(3)])
        self.assertEqual(result['status'], 'underdetermined')
        self.assertEqual(result['space_dimension'], 6)
        assert_allclose(result['metric'], np.eye(3))

    def test_empty_family_and_other_dimension(self):
        result = g.infer_metric([], dimension=2)
        self.assertEqual(result['space_dimension'], 3)
        self.assertEqual(result['status'], 'underdetermined')
        assert_allclose(result['metric'], np.eye(2))

    def test_inconsistent_dilation_has_no_metric(self):
        result = g.infer_metric([2*np.eye(3)])
        self.assertEqual(result['status'], 'no_positive_definite_metric')
        self.assertEqual(result['space_dimension'], 0)
        self.assertIsNone(result['metric'])

    def test_unique_indefinite_metric_is_definitively_rejected(self):
        # A planar Lorentz boost and spatial reflections fix only diag(1,-1).
        boost = np.array([[np.cosh(1),np.sinh(1)],[np.sinh(1),np.cosh(1)]])
        result = g.infer_metric([boost,np.diag([1.,-1.])], dimension=2)
        self.assertEqual(result['space_dimension'], 1)
        self.assertEqual(result['status'], 'no_positive_definite_metric')
        self.assertIsNone(result['metric'])

    def test_ill_conditioned_spd_metric_is_unresolved_at_default_tolerance(self):
        scale = 2.**20
        projectors = [np.diag([1.,0.]), np.array([[.5,scale/2],[1/(2*scale),.5]])]
        expected = 2*np.diag([scale**-2,1])/(1+scale**-2)
        self.assertGreater(np.linalg.eigvalsh(expected)[0], 0)
        self.assertLess(np.linalg.eigvalsh(expected)[0], 1e-10)
        for projector in projectors:
            assert_allclose(projector @ projector, projector, rtol=0, atol=0)
            assert_allclose(projector.T @ expected, expected @ projector, rtol=0, atol=0)
        result = g.infer_metric([],projectors,dimension=2)
        self.assertEqual(result['space_dimension'], 1)
        self.assertEqual(result['status'], 'unresolved_feasibility')
        self.assertIsNone(result['metric'])
        # An explicitly tighter requested tolerance resolves the positive eigenvalue.
        resolved = g.infer_metric([],projectors,dimension=2,tol=1e-13)
        self.assertEqual(resolved['status'], 'unique_up_to_scale')
        assert_allclose(resolved['metric'], expected, rtol=1e-12, atol=1e-15)

    def test_unique_semidefinite_boundary_is_numerically_unresolved(self):
        result = g.infer_metric([np.diag([2.,1.])], dimension=2)
        self.assertEqual(result['space_dimension'], 1)
        self.assertEqual(result['status'], 'unresolved_feasibility')
        self.assertIsNone(result['metric'])

    def test_failed_high_nullity_witness_is_unresolved(self):
        # A nontrivial shear fixes degenerate forms only; simple witness cannot certify infeasibility.
        result = g.infer_metric([np.array([[1.,1,0],[0,1,0],[0,0,1]])])
        self.assertGreater(result['space_dimension'], 1)
        self.assertEqual(result['status'], 'unresolved_feasibility')
        self.assertIsNone(result['metric'])

    def test_metric_invalid_inputs(self):
        for matrices, projectors in (([np.eye(2)],()),([np.full((3,3),np.nan)],()),([np.eye(3)*1j],()),([],[.5*np.eye(3)]),([],[np.eye(2)])):
            with self.subTest(matrices=matrices, projectors=projectors), self.assertRaises(ValueError): g.infer_metric(matrices, projectors)
        for dimension in (0,2.5,True):
            with self.assertRaises(ValueError): g.infer_metric([], dimension=dimension)
        with self.assertRaises(ValueError): g.infer_metric([], tol=-1)


class CenterAndGeometryTests(unittest.TestCase):
    def test_unique_common_center(self):
        center = np.array([2.,-3,4])
        operators = [(np.diag([-1.,-1,1]), np.array([4.,-6,0])), (np.diag([1.,-1,-1]), np.array([0.,-6,8]))]
        result = g.infer_center(operators)
        self.assertEqual(result['status'], 'unique')
        self.assertEqual(result['rank'], 3)
        assert_allclose(result['center'], center)
        self.assertLess(result['residual'], 1e-10)

    def test_nonunique_center_is_least_norm_representative(self):
        result = g.infer_center([(np.diag([-1.,1,1]), [4,0,0])])
        self.assertEqual(result['status'], 'underdetermined')
        self.assertEqual(result['rank'], 1)
        assert_allclose(result['center'], [2,0,0])

    def test_inconsistent_centers(self):
        result = g.infer_center([(np.eye(3), [1,0,0])])
        self.assertEqual(result['status'], 'inconsistent')
        self.assertIsNone(result['center'])
        self.assertGreater(result['residual'], .9)

    def test_invalid_centers(self):
        for operators in ([], [(np.eye(2),[0,0,0])], [(np.eye(3)*1j,[0,0,0])], [(np.eye(3),[np.inf,0,0])]):
            with self.subTest(operators=operators), self.assertRaises(ValueError): g.infer_center(operators)

    def test_gram_edges_and_volume(self):
        result = g.tetra_geometry([5,6,7], np.eye(3))
        assert_allclose(result['edges'], [1,1,1,np.sqrt(2),np.sqrt(2),np.sqrt(2)])
        assert_allclose(result['gram'], np.eye(3))
        self.assertAlmostEqual(result['volume'], 1/6)
        result = g.tetra_geometry([0,0,0], np.eye(3), np.diag([4.,9,16]))
        assert_allclose(result['edges'], [2,3,4,np.sqrt(13),np.sqrt(20),5])
        self.assertAlmostEqual(result['volume'], 4)

    def test_invalid_tetrahedron(self):
        for origin, displacement, metric in (([0,0],np.eye(3),None),([0,0,0],np.zeros((3,3)),None),([0,0,0],np.eye(3),np.diag([1,1,-1])),([0,0,0],np.eye(3),np.array([[1,1,0],[0,1,0],[0,0,1]])),([0,0,0],np.eye(3)*1j,None)):
            with self.subTest(origin=origin, displacement=displacement, metric=metric), self.assertRaises(ValueError): g.tetra_geometry(origin,displacement,metric)


class ObservabilityTests(unittest.TestCase):
    def test_duplicate_directions_and_sequence_rank(self):
        c = np.array([[1.,0,0],[1,0,0]])
        transition = np.array([[0.,1,0],[0,0,1],[1,0,0]])
        self.assertEqual(np.linalg.matrix_rank(c), 1)
        result = g.observability_matrix(c,transition,3)
        assert_allclose(result, np.repeat(np.eye(3),2,axis=0))
        self.assertEqual(np.linalg.matrix_rank(result), 3)

    def test_single_observation_vector(self):
        result = g.observability_matrix([1,0], [[0,1],[1,0]], 2)
        assert_allclose(result, np.eye(2))

    def test_invalid_observability(self):
        for c,a,steps in (([[1,0]],np.eye(3),2),([1,0],np.eye(2),0),([1,0],np.eye(2),2.5),([1j,0],np.eye(2),2),([1,0],np.eye(2),True),([1,0],[[1,np.inf],[0,1]],2)):
            with self.subTest(c=c,a=a,steps=steps), self.assertRaises(ValueError): g.observability_matrix(c,a,steps)


class JointTests(unittest.TestCase):
    def test_singlet_joint_probabilities_and_inverse(self):
        expected = np.full((4,4), 1/12)
        np.fill_diagonal(expected, 0)
        probabilities = g.joint_probabilities(np.zeros(3),np.zeros(3),-np.eye(3))
        assert_allclose(probabilities, expected, atol=1e-15)
        a,b,c = g.joint_reconstruct(expected)
        assert_allclose(a, 0, atol=1e-15)
        assert_allclose(b, 0, atol=1e-15)
        assert_allclose(c, -np.eye(3), atol=1e-15)

    def test_product_coordinates(self):
        a = np.array([0.,0,1])
        b = np.array([1.,0,0])
        result = g.joint_probabilities(a,b,np.outer(a,b))
        assert_allclose(result, np.outer(g.tetra_probabilities(a),g.tetra_probabilities(b)))
        actual = g.joint_reconstruct(result)
        for lhs,rhs in zip(actual,(a,b,np.outer(a,b))): assert_allclose(lhs,rhs,atol=1e-15)

    def test_generic_probability_coordinates_do_not_claim_quantum_physicality(self):
        p = np.zeros((4,4)); p[0,0] = 1
        a,b,c = g.joint_reconstruct(p)
        self.assertGreater(np.linalg.norm(a), 1)
        assert_allclose(g.joint_probabilities(a,b,c), p, atol=1e-15)

    def test_chsh_singlet(self):
        value = g.chsh_value(-np.eye(3), [1,0,0],[0,0,1],[-1,0,-1],[-1,0,1])
        self.assertAlmostEqual(value,2*np.sqrt(2))

    def test_joint_invalid_inputs(self):
        for a,b,c in (([0,0],[0,0,0],np.eye(3)),([0,0,0],[0,0,0],np.eye(2)),([1j,0,0],[0,0,0],np.eye(3)),([0,0,0],[0,0,0],np.full((3,3),np.inf)),([0,0,0],[0,0,0],10*np.eye(3))):
            with self.subTest(a=a,b=b,c=c), self.assertRaises(ValueError): g.joint_probabilities(a,b,c)
        for p in (np.ones((4,4)), np.full((4,4),-1/16), np.ones((3,3))/9, np.ones((4,4))*1j/16, np.full((4,4),np.nan)):
            with self.subTest(p=p), self.assertRaises(ValueError): g.joint_reconstruct(p)
        with self.assertRaises(ValueError): g.chsh_value(np.eye(3), [0,0,0],[1,0,0],[1,0,0],[1,0,0])


if __name__ == '__main__': unittest.main()
