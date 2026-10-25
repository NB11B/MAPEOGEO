import unittest
from index_sieve import pell,odd_factor,run
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_pell_terms(self):
  self.assertEqual([pell(i) for i in (3,5,7,9,11,13,15)],[5,29,169,985,5741,33461,195025])
 def test_index_factors(self):self.assertEqual(odd_factor(9),3);self.assertEqual(odd_factor(15),3)
 def test_numerical_divisibility(self):self.assertTrue(self.r["all_sieve_witnesses_nontrivial"])
 def test_geometry_match(self):self.assertTrue(self.r["geometry_alignment"])
 def test_prime_index_insufficient(self):self.assertFalse(self.r["prime_index_composite_counterexample"]["prime"])
 def test_concrete_witnesses(self):self.assertEqual(pell(9)%pell(3),0);self.assertEqual(pell(15)%pell(5),0)
if __name__=="__main__":unittest.main()
