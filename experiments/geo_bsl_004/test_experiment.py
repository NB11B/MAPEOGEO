import unittest
try:
 from . import experiment as e
except ImportError:
 import experiment as e
class Tests(unittest.TestCase):
 def test_digits(self):self.assertEqual(e.digits(19,7),[2,5])
 def test_degree(self):self.assertEqual(e.learn()["degree"],2)
 def test_coefficients(self):self.assertTrue(all(abs(a-b)<1e-9 for a,b in zip(e.learn()["coeff"],[0,0,1])))
 def test_training(self):self.assertLess(e.learn()["train_max_error"],1e-8)
 def test_unseen(self):self.assertLess(e.trial(e.oracle)["unseen_max_error"],1e-8)
 def test_position_rejected(self):self.assertGreater(e.learn(e.positional_oracle)["train_max_error"],1)
 def test_interaction_rejected(self):self.assertGreater(e.learn(e.interaction_oracle)["train_max_error"],1)
 def test_extrapolation(self):self.assertAlmostEqual(e.predict(15,16,e.learn()),225,places=8)
if __name__=="__main__":unittest.main()
