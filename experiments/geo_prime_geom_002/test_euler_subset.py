import unittest
from euler_subset import run,closure
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_primes(self):self.assertEqual(self.r["primes"],[5,29,5741,33461])
 def test_missing_two(self):self.assertFalse(self.r["contains_two"])
 def test_ablation(self):self.assertAlmostEqual(self.r["excluded_five_product_ratio"],24/25)
 def test_truncation(self):self.assertLess(self.r["restricted_sum"],self.r["subset_euler_product"])
 def test_multiplicative_closure(self):self.assertIn(145,closure([5,29],200))
if __name__=="__main__":unittest.main()
