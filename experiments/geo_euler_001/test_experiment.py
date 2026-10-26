import math,unittest
from experiment import closure,primes_through,euler_product,run
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_closure(self):self.assertTrue(self.r["closure_complete"])
 def test_count(self):self.assertEqual(self.r["closure_count"],1000)
 def test_primes(self):self.assertEqual(self.r["prime_count"],168)
 def test_partial_less_than_basel(self):self.assertLess(self.r["finite_integer_sum"],math.pi**2/6)
 def test_removal_ratio(self):
  for v in self.r["ablations"]:self.assertLess(v["error"],1e-12)
 def test_remove_two(self):self.assertAlmostEqual(self.r["ablations"][0]["ratio"],.75)
 def test_removal_cardinality(self):
  for v in self.r["ablations"]:self.assertEqual(v["retained_states"],1000-1000//v["removed_prime"])
 def test_small_closure(self):self.assertEqual(closure([2,3],12),{1,2,3,4,6,8,9,12})
 def test_order_invariance(self):self.assertEqual(closure([2,3,5],150),closure([5,2,3],150))
 def test_small_product(self):self.assertAlmostEqual(euler_product([2,3]),1.5)
if __name__=="__main__":unittest.main()
