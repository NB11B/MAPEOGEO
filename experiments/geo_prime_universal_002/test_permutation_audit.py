import unittest
from permutation_audit import run,orbit_partition,permute_matrix
from native import shift
class Tests(unittest.TestCase):
 def test_relabeling(self):self.assertEqual(len(run()),5)
 def test_nine(self):self.assertEqual(orbit_partition(shift(9,3)),(3,3,3))
 def test_seventeen(self):self.assertEqual(orbit_partition(shift(17,4)),(17,))
 def test_invalid(self):
  with self.assertRaises(ValueError):orbit_partition(((1.,0.),(1.,0.)))
 def test_permute_inverse(self):
  a=shift(9,3);p=list(reversed(range(9)))
  self.assertEqual(permute_matrix(permute_matrix(a,p),p),a)
if __name__=="__main__":unittest.main()
