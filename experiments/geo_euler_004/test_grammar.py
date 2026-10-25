import unittest
from grammar import world,split_tables,discover,run
class Tests(unittest.TestCase):
 def test_nominal(self):self.assertEqual(run()["status"],"qualified")
 def test_roles(self):
  r=run();self.assertEqual(r["addition"],"opaque-Y|shift=1")
  self.assertEqual(r["multiplication"],"opaque-X|add-left")
 def test_holdout(self):self.assertEqual(sum(run()["holdout_errors"].values()),0)
 def test_prime(self):self.assertEqual(run()["primes_reference"],[2,3,5,7,11,13,17,19,23,29])
 def test_permutations(self):
  for seed in (3,7,14,27,88):self.assertEqual(run(seed)["status"],"qualified")
 def test_missing(self):
  w=world();t,h=split_tables(w);t["opaque-X"]={}
  self.assertEqual(discover(w,t,h)["status"],"refuse")
 def test_impostor(self):
  w=world(impostor=True);t,h=split_tables(w)
  self.assertEqual(discover(w,t,h)["status"],"refuse")
 def test_ambiguity(self):
  w=world();t,h=split_tables(w);t["fake"]=dict(t["opaque-Y"])
  self.assertEqual(discover(w,t,h)["status"],"refuse")
 def test_no_decode(self):
  w=world();t,h=split_tables(w);w.decode.clear()
  self.assertEqual(discover(w,t,h)["status"],"qualified")
 def test_holdout_count(self):self.assertGreater(sum(run()["withheld_entries"].values()),100)
if __name__=="__main__":unittest.main()
