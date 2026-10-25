import unittest
from fractions import Fraction
from experiment import run,closest
class Tests(unittest.TestCase):
 def test_proposed(self):self.assertEqual(run()["proposed"],"22/7")
 def test_missing_factor(self):self.assertEqual(run()["unscaled"],"11/7")
 def test_nested(self):self.assertEqual(run()["nested"],"11/7")
 def test_denominator_seven(self):self.assertEqual(closest(7),Fraction(22,7))
 def test_denominator_113(self):self.assertEqual(closest(113),Fraction(355,113))
 def test_not_exact(self):self.assertNotEqual(run()["error"],0)
if __name__=="__main__":unittest.main()
