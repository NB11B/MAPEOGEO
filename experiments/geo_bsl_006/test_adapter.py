import unittest
import numpy as np
from adapter import infer_linear,discover_basis,run
class NativeIntegration(unittest.TestCase):
 def test_native_basis(self):
  r=run(); self.assertEqual(r["basis_indices"],[0,1]);self.assertEqual(r["basis_rank"],2)
 def test_redundancy(self):self.assertEqual(run()["redundant_indices"],[2])
 def test_linear_holdout(self):self.assertLess(run()["max_linear_holdout_rmse"],1e-10)
 def test_nonlinearity_refused(self):self.assertTrue(run()["nonlinear_rejected"])
 def test_rank_refused(self):self.assertTrue(run()["rank_deficient_rejected"])
 def test_noncommuting(self):self.assertFalse(run()["ordering_commutes"])
 def test_no_accepted(self):
  x=np.ones((4,2));q=infer_linear(x,x,x,x)
  self.assertEqual(discover_basis([q]).rank,0)
 def test_shape_check(self):
  with self.assertRaises(ValueError):infer_linear([[1,2]],[[1]],[[1]],[[1]])
if __name__=="__main__":unittest.main()
