import unittest
from mixture import run
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_nominal(self):self.assertTrue(self.r["qualified"])
 def test_native_basis(self):self.assertEqual(self.r["native_basis_rank"],2)
 def test_gauge(self):self.assertLess(self.r["gauge_equivalent_operator_error"],1e-8)
 def test_training(self):self.assertLess(self.r["train_rmse"],1e-8)
 def test_holdout(self):self.assertLess(self.r["heldout_rmse"],1e-8)
 def test_assignment(self):self.assertGreater(self.r["assignment_accuracy"],.99)
 def test_identical(self):self.assertTrue(self.r["identical_refused"])
 def test_nonlinear(self):self.assertTrue(self.r["nonlinear_refused"])
 def test_rank(self):self.assertTrue(self.r["rank_deficient_refused"])
 def test_small_sample(self):self.assertTrue(self.r["small_sample_refused"])
if __name__=="__main__":unittest.main()
