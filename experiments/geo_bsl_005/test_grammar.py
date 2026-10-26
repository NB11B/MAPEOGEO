import unittest
from grammar import discover, digits, features
class Tests(unittest.TestCase):
 def test_digits(self):self.assertEqual(digits(19,7),[2,5])
 def test_additive(self):self.assertEqual(discover('additive')['selected'],'additive')
 def test_positional(self):self.assertEqual(discover('positional')['selected'],'positional')
 def test_pair(self):self.assertEqual(discover('pair')['selected'],'pair')
 def test_combined(self):self.assertEqual(discover('combined')['selected'],'combined')
 def test_ood_refusal(self):self.assertIsNone(discover('parity')['selected'])
 def test_holdout(self):
  for f in ('additive','positional','pair','combined'):
   r=discover(f);self.assertLess(r['models'][r['selected']]['test_rmse'],1e-7)
 def test_wrong_additive_rejected(self):
  for f in ('positional','pair','combined'):
   self.assertGreater(discover(f)['models']['additive']['train_rmse'],1e-4)
 def test_basis_dimensionality(self):
  self.assertEqual([len(features(243,7,f)) for f in ('additive','positional','pair','combined')],[3,6,6,9])
if __name__=='__main__':unittest.main()
