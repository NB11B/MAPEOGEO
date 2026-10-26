import unittest
from experiment import run,interaction,recursive,derived_primes
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_coefficient(self):self.assertEqual(self.r["coefficient"],2)
 def test_operator_pairs(self):self.assertEqual(self.r["operator_errors"],0)
 def test_prime_count(self):self.assertEqual(self.r["prime_count"],46)
 def test_prime_classification(self):self.assertEqual(self.r["prime_errors"],0)
 def test_mutation(self):self.assertTrue(self.r["mutated_coefficient_rejected"])
 def test_zero(self):self.assertTrue(self.r["zero_cases_pass"])
 def test_symmetry(self):self.assertEqual(interaction(7,11),interaction(11,7))
 def test_recursive(self):self.assertEqual(recursive(19,23),437)
if __name__=="__main__":unittest.main()
