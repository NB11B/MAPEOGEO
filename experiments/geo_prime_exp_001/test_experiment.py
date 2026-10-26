import unittest
from experiment import F,run,prime_shift_witness,mod_three_witness
class Tests(unittest.TestCase):
 def test_first_values(self):self.assertEqual([F(n) for n in range(1,6)],[3,17,145,1649,23401])
 def test_prime_indices(self):self.assertEqual(run()["prime_indices"],[1,2])
 def test_prime_shift(self):self.assertEqual(prime_shift_witness(3),5)
 def test_all_shift(self):
  for n in run()["prime_shift_cases"]:self.assertEqual(F(n)%(n+2),0)
 def test_mod_three(self):
  for n in run()["mod_three_cases"]:self.assertEqual(F(n)%3,0)
 def test_refuse(self):self.assertIsNone(prime_shift_witness(4))
 def test_small_exception(self):self.assertIsNone(mod_three_witness(1))
 def test_invalid(self):
  with self.assertRaises(ValueError):F(0)
if __name__=="__main__":unittest.main()
