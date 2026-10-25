import unittest
from inference import reconstruct,observations
def cyclic_four():
 return tuple(tuple((x+k)%4 for x in range(4)) for k in range(4))
def klein_four():
 return tuple(tuple(x^k for x in range(4)) for k in range(4))
class Tests(unittest.TestCase):
 def test_four_ambiguity(self):
  r=reconstruct(list(observations(cyclic_four()).elements()))
  self.assertEqual(r['status'],'ambiguous')
  self.assertIn((1,2,4,4),r['signatures'])
  self.assertIn((1,2,2,2),r['signatures'])
 def test_same_data(self):
  self.assertEqual(reconstruct(list(observations(cyclic_four()).elements())),reconstruct(list(observations(klein_four()).elements())))
 def test_incomplete(self):
  self.assertEqual(reconstruct(list(observations(cyclic_four()).elements())[:-1])['status'],'refuse')
 def test_three(self):
  rows=[(a,b) for a in range(3) for b in range(3)]
  self.assertEqual(reconstruct(rows)['status'],'structurally_identified')
 def test_bound(self):
  self.assertEqual(reconstruct([(a,b) for a in range(5) for b in range(5)])['reason'],'outside_bound')
if __name__=='__main__':unittest.main()
