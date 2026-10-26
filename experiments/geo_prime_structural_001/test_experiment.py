import unittest
from experiment import classify
class Test(unittest.TestCase):
 def test_known_one_edge(self): self.assertEqual(classify(5,[(0,1)],'known_coordinates')['models'],1)
 def test_arbitrary_count(self): self.assertEqual(classify(5,[(0,1)],'arbitrary')['models'],24)
 def test_latent_count(self): self.assertEqual(classify(5,[(0,1)],'latent_coordinates')['models'],6)
 def test_latent_spectrum_unique(self):self.assertTrue(classify(5,[(0,1)],'latent_coordinates')['spectral_identified'])
 def test_latent_operator_ambiguous(self):self.assertEqual(classify(5,[(0,1)],'latent_coordinates')['status'],'ambiguous')
 def test_arbitrary_spectrum_ambiguous(self):self.assertGreater(classify(5,[(0,1)],'arbitrary')['spectra'],1)
 def test_empty_latent(self):self.assertEqual(classify(5,[],'latent_coordinates')['models'],24)
 def test_conflicting(self):self.assertEqual(classify(5,[(0,1),(2,1)],'latent_coordinates')['status'],'refuse')
 def test_six_latent(self):self.assertEqual(classify(6,[(0,1)],'latent_coordinates')['models'],24)
 def test_six_spectrum(self):self.assertEqual(classify(6,[(0,1)],'latent_coordinates')['cycle_types'],[(6,)])
if __name__=='__main__':unittest.main()
