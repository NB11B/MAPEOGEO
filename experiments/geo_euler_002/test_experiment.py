import unittest,math
from experiment import discover
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=discover(120)
 def test_prime_count(self):self.assertEqual(len(self.r.generators),30)
 def test_first_primes(self):self.assertEqual(self.r.generators[:10],[2,3,5,7,11,13,17,19,23,29])
 def test_complete(self):self.assertTrue(self.r.complete)
 def test_unique_factorization(self):self.assertTrue(self.r.unique_factorizations)
 def test_successor(self):self.assertEqual(self.r.successors,120)
 def test_addition(self):self.assertEqual(self.r.addition_edges,7381)
 def test_product(self):self.assertGreater(self.r.prime_product,self.r.direct_sum)
 def test_ablations(self):self.assertEqual(self.r.ablations['2']['retained_count'],60)
 def test_limit(self):
  with self.assertRaises(ValueError):discover(1)
 def test_independent_reference(self):
  expected=[n for n in range(2,121) if all(n%d for d in range(2,math.isqrt(n)+1))]
  self.assertEqual(self.r.generators,expected)
if __name__=='__main__':unittest.main()
