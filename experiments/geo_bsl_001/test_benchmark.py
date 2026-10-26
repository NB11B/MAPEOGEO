"""Run: python -m unittest discover -s experiments/geo_bsl_001 -v"""
import unittest
import numpy as np
try:
    from .benchmark import cycle_adjacency,path_adjacency,laplacian,topology,inverse_trace,fit_cycle_invariant,accepts,run
except ImportError:
    from benchmark import cycle_adjacency,path_adjacency,laplacian,topology,inverse_trace,fit_cycle_invariant,accepts,run

class TestGeoBSL(unittest.TestCase):
    def test_cycle_recognition(self):
        self.assertEqual(topology(cycle_adjacency(13)),"cycle")
    def test_path_recognition(self):
        self.assertEqual(topology(path_adjacency(13)),"path")
    def test_finite_spectral_oracle(self):
        for n in (3,4,5,8,16,32,64):
            self.assertAlmostEqual(inverse_trace(cycle_adjacency(n)),(n*n-1)/12,places=8)
    def test_fitted_coefficients(self):
        a,b=fit_cycle_invariant()
        self.assertAlmostEqual(a,1/12,places=11)
        self.assertAlmostEqual(b,-1/12,places=11)
    def test_permutation_invariance(self):
        n=17; p=np.random.default_rng(3).permutation(n);a=cycle_adjacency(n)
        self.assertAlmostEqual(inverse_trace(a),inverse_trace(a[np.ix_(p,p)]),places=9)
    def test_laplacian_null_mode(self):
        self.assertTrue(np.allclose(laplacian(cycle_adjacency(15))@np.ones(15),0))
    def test_falsification(self):
        r=run()
        self.assertTrue(all([r["broken_cycle_rejected"],r["path_rejected"],r["weighted_cycle_rejected"],r["disconnected_cycles_rejected"]]))
    def test_holdout(self):
        r=run()
        self.assertLess(r["max_holdout_absolute_error"],1e-8)
        self.assertTrue(r["permuted_holdout_pass"])
    def test_disconnected_rejected(self):
        a=np.zeros((10,10));a[:5,:5]=cycle_adjacency(5);a[5:,5:]=cycle_adjacency(5)
        self.assertEqual(topology(a),"disconnected")
    def test_invalid_adjacency(self):
        with self.assertRaises(ValueError):
            laplacian(np.array([[0.,-1.],[-1.,0.]]))

if __name__=="__main__": unittest.main()
