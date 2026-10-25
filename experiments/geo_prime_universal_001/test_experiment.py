import unittest
from experiment import *
class Tests(unittest.TestCase):
 def test_orbits(self):self.assertEqual(orbit_length(9,3),3)
 def test_primes(self):self.assertTrue(all(cyclic_prime(n) for n in (2,3,5,7,11,13,17,29)))
 def test_composites(self):self.assertTrue(all(not cyclic_prime(n) for n in (1,4,6,9,15,25,49)))
 def test_witness(self):self.assertEqual(witness(9)['step'],3)
 def test_pascal(self):self.assertTrue(pascal_prime(29));self.assertFalse(pascal_prime(9))
 def test_oracle(self):
  r=run(300);self.assertEqual(r['cycle_mismatches'],[]);self.assertEqual(r['pascal_mismatches'],[])
 def test_count(self):self.assertEqual(run(300)['prime_count'],62)
 def test_invalid(self):
  with self.assertRaises(ValueError):orbit_length(1,1)
if __name__=="__main__":unittest.main()
