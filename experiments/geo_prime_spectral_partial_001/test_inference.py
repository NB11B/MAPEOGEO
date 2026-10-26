import unittest
from inference import infer,cycle_type,spectral_profile
class TestPartialSpectral(unittest.TestCase):
 def test_prime_complete(self):
  n=7;p=[(i+3)%n for i in range(n)]
  self.assertEqual(infer(n,list(enumerate(p)))['cycle_types'],[(7,)])
 def test_composite_complete(self):
  n=8;p=[(i+2)%n for i in range(n)]
  self.assertEqual(infer(n,list(enumerate(p)))['cycle_types'],[(4,4)])
 def test_ambiguous(self):
  r=infer(4,[(0,1)])
  self.assertEqual(r['status'],'ambiguous')
  self.assertTrue(r['full_orbit_possible'])
  self.assertFalse(r['full_orbit_certain'])
 def test_one_missing_inferred(self):
  self.assertEqual(infer(4,[(0,1),(1,2),(2,3)])['cycle_types'],[(4,)])
 def test_two_missing_ambiguous(self):
  self.assertEqual(infer(4,[(0,1),(1,2)])['status'],'ambiguous')
 def test_noninjective(self):self.assertEqual(infer(4,[(0,1),(2,1)])['reason'],'not_injective')
 def test_contradictory(self):self.assertEqual(infer(4,[(0,1),(0,2)])['reason'],'contradictory_edge')
 def test_bound(self):self.assertEqual(infer(9,[])['reason'],'outside_enumeration_bound')
 def test_eigen_order(self):self.assertEqual(spectral_profile((1,0,3,2)),((2,2),2))
 def test_identity(self):self.assertEqual(cycle_type((0,1,2)),(1,1,1))
if __name__=='__main__':unittest.main()
