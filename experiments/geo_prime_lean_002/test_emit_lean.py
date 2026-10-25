import unittest
from pathlib import Path
from emit_lean import emit
class Tests(unittest.TestCase):
 def test_inferred(self):
  r=emit();self.assertEqual(r["coefficient"],2)
 def test_mutated_source(self):
  r=emit(3);self.assertIn("/ 3",Path(r["source"]).read_text())
  emit(2)
 def test_invalid(self):
  with self.assertRaises(ValueError):emit(-1)
if __name__=="__main__":unittest.main()
