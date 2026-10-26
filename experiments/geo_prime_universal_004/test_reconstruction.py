import unittest
from reconstruction import events,discover,run
class Tests(unittest.TestCase):
 def test_all(self):self.assertEqual(run()["mismatches"],[])
 def test_nine(self):self.assertFalse(run()["nine"]["prime"])
 def test_missing(self):self.assertTrue(run()["missing_refused"])
 def test_conflict(self):self.assertTrue(run()["conflict_refused"])
 def test_order(self):
  e=events(17,seed=42);self.assertEqual(discover(e),discover(list(reversed(e))))
 def test_prime(self):self.assertTrue(discover(events(19))["prime"])
 def test_empty(self):self.assertEqual(discover([])["status"],"refuse")
if __name__=="__main__":unittest.main()
