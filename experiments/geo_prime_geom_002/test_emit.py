import unittest,tempfile
from pathlib import Path
from emit_lean import emit
class Tests(unittest.TestCase):
 def test_actual_coefficients(self):
  with tempfile.TemporaryDirectory() as d:
   t=emit(Path(d)/"a.lean").read_text()
   self.assertIn("(3*x+4*c)^2",t);self.assertIn("(2*x+3*c)^2",t)
 def test_mutation_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   t=emit(Path(d)/"bad.lean",mutation=True).read_text()
   self.assertIn("(3*x+6*c)^2",t)
if __name__=="__main__":unittest.main()
