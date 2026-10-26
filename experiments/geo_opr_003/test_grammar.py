import unittest
from grammar import Expr,discover,benchmark
class Tests(unittest.TestCase):
 def test_successor(self):self.assertEqual(Expr("succ",(Expr("x"),)).eval(2,3),3)
 def test_positions(self):
  self.assertEqual(Expr("x").eval(2,3),2)
  self.assertEqual(Expr("y").eval(2,3),3)
 def test_composite(self):self.assertTrue(benchmark()["all_holdout_pass"])
 def test_ood(self):self.assertEqual(benchmark()["holdout_count"],49)
 def test_rejection(self):self.assertIsNone(discover([(1,1,999999)]))
 def test_square(self):self.assertEqual(Expr("mul",(Expr("x"),Expr("x"))).eval(3,2),9)
 def test_operand_order(self):
  a=Expr("add",(Expr("mul",(Expr("x"),Expr("y"))),Expr("x")))
  self.assertNotEqual(a.eval(2,3),a.eval(3,2))
if __name__=="__main__":unittest.main()
