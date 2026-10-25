import unittest
from fractions import Fraction
from infer import discover,solve
class Tests(unittest.TestCase):
 def test_coefficients(self):self.assertEqual(discover()[0],((3,2,1),(4,3,2)))
 def test_holdout(self):self.assertEqual(discover()[1],3)
 def test_rank_deficiency(self):
  with self.assertRaises(ValueError):solve([[1,0,0]]*3,[1,2,3])
 def test_fraction_exactness(self):
  self.assertEqual(solve([[2,0,0],[0,2,0],[0,0,2]],[1,3,5]),(Fraction(1,2),Fraction(3,2),Fraction(5,2)))
if __name__=="__main__":unittest.main()
