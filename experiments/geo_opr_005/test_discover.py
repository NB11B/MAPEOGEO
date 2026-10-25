import unittest
from discover import discover,residual
class Tests(unittest.TestCase):
 def test_square(self):self.assertEqual(discover(2)["coefficients"],[2])
 def test_cube(self):self.assertEqual(discover(3)["coefficients"],[3,3])
 def test_holdouts(self):self.assertEqual(discover(3)["heldout"],289)
 def test_residual(self):self.assertEqual(residual(2,2,3),12)
 def test_degree_refusal(self):
  with self.assertRaises(ValueError):discover(4)
if __name__=="__main__":unittest.main()
