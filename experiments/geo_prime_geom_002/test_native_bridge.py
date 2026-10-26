import unittest
from native_bridge import run
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_native_import(self):self.assertTrue(self.r["native_import"])
 def test_inverse(self):self.assertTrue(self.r["inverse_exact"])
 def test_quadratic_invariant(self):self.assertTrue(self.r["norm_preserved"])
 def test_invertibility(self):self.assertTrue(self.r["operator_invertible"])
 def test_basis_rank(self):self.assertEqual(self.r["basis_rank"],2)
 def test_redundancy(self):self.assertEqual(tuple(self.r["redundant_indices"]),(2,))
 def test_commutation(self):self.assertTrue(self.r["commutes_with_square"])
if __name__=="__main__":unittest.main()
