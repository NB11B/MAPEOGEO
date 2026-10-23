"""Independent analytic checks for the complex quantum reference.

All expected states and probabilities below come from elementary complex
linear algebra or explicit computational-basis mappings, never the model.
"""
import importlib
import unittest

import numpy as np


ATOL = 2e-12


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        try:
            self.ref = importlib.import_module("ngc_geometry_lab.reference")
        except ModuleNotFoundError as exc:
            self.fail(f"Independent reference module is required: {exc}")

    def close(self, actual, expected, atol=ATOL):
        np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)

    def test_paulis_order_and_complex_dtype(self):
        expected = np.array([[[1, 0], [0, 1]], [[0, 1], [1, 0]],
                             [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]])
        matrices = self.ref.paulis()
        self.assertEqual(matrices.shape, (4, 2, 2))
        self.assertTrue(np.iscomplexobj(matrices))
        self.close(matrices, expected)

    def test_density_validation_general_dimension_and_copy(self):
        rho = np.eye(3) / 3
        result = self.ref.validate_density(rho)
        self.assertTrue(np.iscomplexobj(result))
        self.close(result, rho)
        result[0, 0] = 0
        self.close(rho, np.eye(3) / 3)

    def test_density_validation_rejects_invalid(self):
        bad = [[], [1, 0], np.ones((2, 3)), np.zeros((0, 0)),
               np.eye(2), [[1, 1], [0, 0]], np.diag([1.1, -.1]),
               [[np.nan, 0], [0, 1]], [[np.inf, 0], [0, 0]]]
        for rho in bad:
            with self.subTest(rho=rho), self.assertRaises(ValueError):
                self.ref.validate_density(rho)
        for tol in [-1, np.inf, np.nan, 1j]:
            with self.subTest(atol=tol), self.assertRaises(ValueError):
                self.ref.validate_density(np.eye(2)/2, atol=tol)

    def test_density_validation_absolute_tolerance(self):
        self.ref.validate_density(np.diag([1 + 5e-12, -5e-12]), atol=1e-11)
        with self.assertRaises(ValueError):
            self.ref.validate_density(np.diag([1 + 5e-12, -5e-12]), atol=1e-13)
        with self.assertRaises(ValueError):
            self.ref.validate_density(np.eye(2)/2 + np.eye(2)*1e-7, atol=1e-10)

    def test_standard_single_qubit_states(self):
        cases = [([0, 0, 1], [1, 0]), ([0, 0, -1], [0, 1]),
                 ([1, 0, 0], np.array([1, 1])/np.sqrt(2)),
                 ([0, 1, 0], np.array([1, 1j])/np.sqrt(2))]
        for bloch, ket in cases:
            with self.subTest(bloch=bloch):
                expected = np.outer(ket, np.conjugate(ket))
                self.close(self.ref.density_from_bloch(bloch), expected)
                self.close(self.ref.bloch_from_density(expected), bloch)
                self.close(np.trace(self.ref.density_from_bloch(bloch)), 1)
        self.close(self.ref.density_from_bloch([0, 0, 0]), np.eye(2)/2)
        self.close(self.ref.bloch_from_density(np.eye(2)/2), [0, 0, 0])

    def test_bloch_rejects_invalid_and_non_qubit(self):
        for state in [[1, 1, 0], [0, 0], [[0, 0, 0]], [0, 0, 1j],
                      [np.nan, 0, 0], [np.inf, 0, 0]]:
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.ref.density_from_bloch(state)
        with self.assertRaises(ValueError):
            self.ref.bloch_from_density(np.eye(3)/3)

    def test_tetra_effects_order_positivity_and_completeness(self):
        effects = self.ref.tetra_effects()
        directions = np.array([[1,1,1], [1,-1,-1], [-1,1,-1], [-1,-1,1]])/np.sqrt(3)
        self.close(effects.sum(axis=0), np.eye(2))
        for effect, (x, y, z) in zip(effects, directions):
            expected = np.array([[1+z, x-1j*y], [x+1j*y, 1-z]])/4
            self.close(effect, expected)
            self.close(np.linalg.eigvalsh(effect), [0, .5])

    def test_tetra_probabilities_analytic(self):
        s = 1/np.sqrt(3)
        cases = [(np.diag([1, 0]), np.array([1+s, 1-s, 1-s, 1+s])/4),
                 (np.diag([0, 1]), np.array([1-s, 1+s, 1+s, 1-s])/4),
                 (np.ones((2,2))/2, np.array([1+s, 1+s, 1-s, 1-s])/4),
                 (np.array([[1,-1j],[1j,1]])/2, np.array([1+s,1-s,1+s,1-s])/4),
                 (np.eye(2)/2, np.ones(4)/4)]
        for rho, expected in cases:
            self.close(self.ref.tetra_probabilities(rho), expected)

    def test_tetra_probabilities_rejects_wrong_dimension(self):
        with self.assertRaises(ValueError):
            self.ref.tetra_probabilities(np.eye(4)/4)

    def test_rx_pi_and_rz_phase(self):
        rx = self.ref.rotation_unitary([2, 0, 0], np.pi)
        self.close(rx, [[0, -1j], [-1j, 0]])
        down = self.ref.evolve_density(np.diag([1,0]), rx)
        self.close(down, np.diag([0,1]))
        s = 1/np.sqrt(3)
        self.close(self.ref.tetra_probabilities(down), np.array([1-s,1+s,1+s,1-s])/4)
        rz = self.ref.rotation_unitary([0,0,1], np.pi/2)
        self.close(rz, np.diag([np.exp(-1j*np.pi/4), np.exp(1j*np.pi/4)]))
        self.close(self.ref.evolve_density(np.ones((2,2))/2, rz), [[.5,-.5j],[.5j,.5]])

    def test_rotations_reject_invalid_axis_and_angle(self):
        for axis in [[0,0,0], [1,0], [[1,0,0]], [1j,0,0], [np.nan,0,1], [np.inf,0,0]]:
            with self.subTest(axis=axis), self.assertRaises(ValueError):
                self.ref.rotation_unitary(axis, 0.2)
        for angle in [np.inf, np.nan, 1j, [0.2]]:
            with self.subTest(angle=angle), self.assertRaises(ValueError):
                self.ref.rotation_unitary([1,0,0], angle)

    def test_evolution_rejects_nonunitary_and_mismatch(self):
        for u in [np.eye(2)*2, np.ones((2,3)), np.eye(3), np.array([[1,np.nan],[0,1]])]:
            with self.subTest(unitary=u), self.assertRaises(ValueError):
                self.ref.evolve_density(np.eye(2)/2, u)

    def test_random_density_wishart_pure_and_full(self):
        for dimension in [1, 2, 3, 4, 8]:
            for pure in [False, True]:
                with self.subTest(dimension=dimension, pure=pure):
                    rho = self.ref.random_density(dimension, np.random.default_rng(73), pure=pure)
                    self.assertEqual(rho.shape, (dimension, dimension))
                    self.ref.validate_density(rho)
                    self.close(np.trace(rho), 1)
                    if pure:
                        self.close(rho@rho, rho)
                    else:
                        self.assertTrue(np.all(np.linalg.eigvalsh(rho)>0))
        self.close(self.ref.random_density(4, np.random.default_rng(3)),
                   self.ref.random_density(4, np.random.default_rng(3)))

    def test_random_density_invalid_arguments(self):
        for dim in [0, -1, 2.5, True]:
            with self.subTest(dimension=dim), self.assertRaises(ValueError):
                self.ref.random_density(dim, np.random.default_rng(3))
        with self.assertRaises(ValueError):
            self.ref.random_density(2, None)

    def test_local_gate_big_endian_nonadjacent_and_reversed(self):
        x = np.array([[0,1],[1,0]])
        cnot = np.array([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]])
        basis = np.eye(8, dtype=complex)
        self.close(self.ref.local_gate(basis[:,0], x, [0], 3), basis[:,4])
        self.close(self.ref.local_gate(basis[:,4], cnot, [0,2], 3), basis[:,5])
        self.close(self.ref.local_gate(basis[:,1], cnot, [2,0], 3), basis[:,5])
        self.close(self.ref.local_gate(basis[:,4], cnot, [2,0], 3), basis[:,4])
        self.close(self.ref.local_gate(basis[:,7], cnot, [2,0], 3), basis[:,3])

    def test_local_gate_arbitrary_unitary_vs_dense_kron(self):
        rng = np.random.default_rng(481)
        raw = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
        unitary, _ = np.linalg.qr(raw)
        ket = rng.normal(size=8)+1j*rng.normal(size=8)
        ket /= np.linalg.norm(ket)
        self.close(self.ref.local_gate(ket, unitary, [0,1], 3), np.kron(unitary,np.eye(2))@ket)
        self.close(self.ref.local_gate(ket, unitary, [1,2], 3), np.kron(np.eye(2),unitary)@ket)
        self.close(np.linalg.norm(self.ref.local_gate(ket, unitary, [2,0], 3)), 1)

    def test_local_gate_invalid_state_targets_and_gate(self):
        ket = [1,0,0,0]
        identity = np.eye(2)
        cases = [([1,0],identity,[0],2), ([2,0,0,0],identity,[0],2),
                 ([np.nan,0,0,0],identity,[0],2), (np.array(ket).reshape(2,2),identity,[0],2),
                 (ket,identity,[0,0],2), (ket,identity,[2],2), (ket,identity,[-1],2),
                 (ket,identity,[.5],2), (ket,identity,[True],2), (ket,identity,[],2),
                 (ket,identity,[0],2.0), (ket,identity,[0],True),
                 (ket,np.eye(4),[0],2), (ket,identity*2,[0],2),
                 (ket,[[1,np.inf],[0,1]],[0],2)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.ref.local_gate(*args)

    def test_joint_product_01(self):
        rho = np.diag([0,1,0,0])
        a,b,c = self.ref.joint_parameters(rho)
        self.close(a, [0,0,1])
        self.close(b, [0,0,-1])
        self.close(c, np.diag([0,0,-1]))
        self.close(self.ref.density_from_joint(a,b,c), rho)
        s = 1/np.sqrt(3)
        p0 = np.array([1+s,1-s,1-s,1+s])/4
        p1 = np.array([1-s,1+s,1+s,1-s])/4
        self.close(self.ref.joint_tetra_probabilities(rho), np.outer(p0,p1))

    def test_joint_singlet_and_chsh(self):
        ket = np.array([0,1,-1,0])/np.sqrt(2)
        rho = np.outer(ket,ket)
        a,b,c = self.ref.joint_parameters(rho)
        self.close(a, [0,0,0])
        self.close(b, [0,0,0])
        self.close(c, -np.eye(3))
        self.close(self.ref.density_from_joint(a,b,c),rho)
        self.close(self.ref.joint_tetra_probabilities(rho), (np.ones((4,4))-np.eye(4))/12)
        # z and x at Alice, (z+x)/sqrt2 and (z-x)/sqrt2 at Bob.
        z,x = np.array([0,0,1]), np.array([1,0,0])
        bp,bm = (z+x)/np.sqrt(2), (z-x)/np.sqrt(2)
        self.close(z@c@bp + z@c@bm + x@c@bp - x@c@bm, -2*np.sqrt(2))

    def test_joint_maximally_mixed_and_random_roundtrip(self):
        self.close(self.ref.joint_tetra_probabilities(np.eye(4)/4), np.ones((4,4))/16)
        rho = self.ref.random_density(4, np.random.default_rng(81))
        params = self.ref.joint_parameters(rho)
        self.close(self.ref.density_from_joint(*params), rho)
        self.close(self.ref.joint_tetra_probabilities(rho).sum(), 1)

    def test_joint_non_psd_even_when_tetra_probabilities_positive(self):
        # C=I, a=b=0 gives three eigenvalues +1/2 and one -1/2.
        # Its formal tetra probabilities are (1+n_i.n_j)/16: all >0.
        with self.assertRaises(ValueError):
            self.ref.density_from_joint([0,0,0],[0,0,0],np.eye(3))

    def test_joint_rejects_invalid_dimensions_nonfinite_and_complex(self):
        for function in [self.ref.joint_parameters, self.ref.joint_tetra_probabilities]:
            with self.assertRaises(ValueError):
                function(np.eye(2)/2)
        for a,b,c in [([0,0],[0,0,0],np.zeros((3,3))),
                      ([0,0,0],[0,0,0],np.zeros((2,3))),
                      ([1j,0,0],[0,0,0],np.zeros((3,3))),
                      ([np.nan,0,0],[0,0,0],np.zeros((3,3))),
                      ([0,0,0],[0,0,0],np.full((3,3),np.inf)),
                      ([2,0,0],[0,0,0],np.zeros((3,3)))]:
            with self.subTest(a=a,b=b,c=c), self.assertRaises(ValueError):
                self.ref.density_from_joint(a,b,c)


if __name__ == "__main__":
    unittest.main()
