import unittest
try:
 from . import discovery as d
except ImportError:
 import discovery as d
class DiscoveryTests(unittest.TestCase):
 def test_oracle_example(self): self.assertEqual([d.oracle(19,b) for b in (2,7,10,16)],[3,29,82,10])
 def test_operator_selection(self): self.assertEqual(d.fit()[0],2)
 def test_training_fit(self): self.assertEqual(d.fit()[1][2][0],0)
 def test_holdout_integers(self): self.assertEqual(d.run()["seen_bases_held_integers"]["max_error"],0)
 def test_unseen_bases(self): self.assertEqual(d.run()["unseen_bases_held_integers"]["max_error"],0)
 def test_baseline_positive(self): self.assertGreater(d.run()["baseline_unseen_rmse"],10)
 def test_shuffled_negative(self): self.assertGreater(d.run()["shuffled_train_best_rmse"],10)
 def test_digit_roundtrip_internal(self):
  for b in range(2,17):
   for n in range(100):
    val=0
    for x in d.digits(n,b): val=val*b+x
    self.assertEqual(n,val)
if __name__=="__main__": unittest.main()
