import unittest
from native import geometry,native_audit,run,cycles
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_full(self):self.assertEqual(self.r["mismatches"],[])
 def test_count(self):self.assertEqual(self.r["prime_count"],25)
 def test_nine(self):self.assertEqual(native_audit(9,3)["lengths"],[3,3,3])
 def test_prime(self):self.assertTrue(geometry(17)["prime"])
 def test_witness(self):self.assertEqual(geometry(9)["witness"]["step"],3)
 def test_inverse(self):self.assertTrue(native_audit(9,3)["inverse"])
 def test_invertible(self):self.assertTrue(native_audit(9,3)["invertible"])
 def test_invalid(self):
  with self.assertRaises(ValueError):cycles(1,1)
if __name__=="__main__":unittest.main()
