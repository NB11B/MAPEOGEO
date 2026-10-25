import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from bridge import selected,emit,lean_expr
from grammar import Expr
class Tests(unittest.TestCase):
 def test_selected(self):
  e=selected();self.assertTrue(all(e.eval(a,b)==a+a*b for a in range(1,11) for b in range(1,11)))
 def test_emitted_exact_ast(self):
  e=selected()
  with TemporaryDirectory() as d:
   p=Path(d)/"a.lean";emit(e,p)
   self.assertIn(lean_expr(e),p.read_text())
 def test_unsupported(self):
  with self.assertRaises(ValueError):lean_expr(Expr("divide",(Expr("x"),Expr("y"))))
 def test_wrong_arity(self):
  with self.assertRaises(ValueError):lean_expr(Expr("mul",(Expr("x"),)))
 def test_wrong_candidate_not_substituted(self):
  e=Expr("add",(Expr("x"),Expr("y")))
  with TemporaryDirectory() as d:
   p=Path(d)/"b.lean";emit(e,p)
   self.assertIn("(a + b)",p.read_text())
   self.assertNotIn("def selected (a b : Nat) : Nat := (a + (a * b))",p.read_text())
if __name__=="__main__":unittest.main()
