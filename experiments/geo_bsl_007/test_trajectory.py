import unittest
from trajectory import experiment
class UnknownGeneratorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.result=experiment()
 def test_qualified(self):self.assertEqual(self.result["qualified"],[True,True,True])
 def test_basis(self):self.assertEqual(self.result["basis_indices"],[0,1])
 def test_redundancy(self):self.assertEqual(self.result["redundant"],[2])
 def test_holdout(self):self.assertLess(self.result["maximum_holdout_error"],1e-10)
 def test_deficient(self):self.assertTrue(self.result["rank_deficient_refused"])
 def test_nonlinear(self):self.assertTrue(self.result["nonlinear_refused"])
if __name__=="__main__":unittest.main()
