"""Reference-world regression for GEO-EULER-003."""
import unittest
from experiment import world,chain
class Tests(unittest.TestCase):
 def test_successor(self):self.assertEqual(len(chain(world().successor,world().zero)),31)
 def test_encoded_zero_one(self):
  w=world();self.assertEqual(w.decode[w.zero],0);self.assertEqual(w.decode[w.one],1)
 def test_symbol_permutation(self):
  self.assertNotEqual(world(seed=47).zero,world(seed=48).zero)
 def test_table_roles(self):
  w=world()
  self.assertEqual(w.decode[w.tables["opaque-Y"][(w.one,w.one)]],2)
  self.assertEqual(w.decode[w.tables["opaque-X"][(w.one,w.one)]],1)
 def test_cycle_rejected(self):
  w=world(); w.successor[chain(w.successor,w.zero)[-1]]=w.zero
  with self.assertRaises(ValueError):chain(w.successor,w.zero)
if __name__=="__main__":unittest.main()
