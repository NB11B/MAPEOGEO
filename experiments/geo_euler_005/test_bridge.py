import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from bridge import parse_selection,emit,render
GOOD={"status":"qualified","addition":"opaque-Y|shift=1","multiplication":"opaque-X|add-left",
      "holdout_checks":{"opaque-Y":142,"opaque-X":44},
      "holdout_errors":{"opaque-Y":0,"opaque-X":0}}
class Tests(unittest.TestCase):
 def test_good(self):
  a=parse_selection(GOOD);self.assertEqual(a["add_ast"]["step"],"successor")
 def test_actual_render(self):
  with TemporaryDirectory() as tmp:
   r=emit(GOOD,Path(tmp)/"Selected.lean")
   self.assertEqual(len(r["sha256"]),64)
   self.assertIn("selectedCertificate",Path(r["file"]).read_text())
 def test_nonqualified(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"status":"refuse"})
 def test_corrupt_first(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"addition":"opaque-Y|shift=2"})
 def test_corrupt_second(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"multiplication":"opaque-X|identity"})
 def test_role_collision(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"multiplication":"opaque-Y|add-left"})
 def test_missing_evidence(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"holdout_checks":{}})
 def test_false_evidence(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"holdout_errors":{"opaque-X":1,"opaque-Y":0}})
 def test_injection(self):
  with self.assertRaises(ValueError):parse_selection({**GOOD,"addition":"unsafe\\n#eval|shift=1"})
 def test_wrong_ast(self):
  a=parse_selection(GOOD);a["mul_ast"]["step"]="identity"
  with self.assertRaises(ValueError):render(a)
if __name__=="__main__":unittest.main()
