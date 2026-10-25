import unittest
from gamma import gamma,cyclic,klein,symmetric3,dihedral4,spf
class GammaTests(unittest.TestCase):
 def test_prime(self): self.assertEqual(gamma(cyclic(7))['gamma'],'1')
 def test_nine(self): self.assertEqual(gamma(cyclic(9))['gamma'],'1/3')
 def test_twelve(self): self.assertEqual(gamma(cyclic(12))['gamma'],'1/6')
 def test_klein(self): self.assertEqual(gamma(klein())['gamma'],'1/2')
 def test_symmetric(self): self.assertEqual(gamma(symmetric3())['gamma'],'1/3')
 def test_dihedral(self): self.assertEqual(gamma(dihedral4())['gamma'],'1/4')
 def test_same_gamma_different_structure(self): self.assertNotEqual(gamma(cyclic(4))['order_signature'],gamma(klein())['order_signature'])
 def test_all_cyclic(self):
  for n in range(2,41):self.assertTrue(gamma(cyclic(n))['consistent'])
 def test_incomplete(self):self.assertEqual(gamma(cyclic(5)[:-1])['status'],'refuse')
 def test_duplicate(self):self.assertEqual(gamma(cyclic(4)+(cyclic(4)[0],))['status'],'refuse')
 def test_spf(self):self.assertEqual(spf(49),7)
if __name__=='__main__':unittest.main()
