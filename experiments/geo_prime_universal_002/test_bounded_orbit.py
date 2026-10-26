import unittest
from bounded_orbit import bounded_reach,run
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_all(self):self.assertEqual(self.r["mismatches"],[])
 def test_count(self):self.assertEqual(self.r["checked_steps"],3160)
 def test_nine(self):self.assertEqual(bounded_reach(9,3),(False,3,0))
 def test_prime(self):self.assertEqual(bounded_reach(17,4),(True,17,0))
 def test_zero_invalid(self):
  with self.assertRaises(ValueError):bounded_reach(9,0)
if __name__=="__main__":unittest.main()
