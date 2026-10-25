import unittest
from experiment import next_triangle,generate,run,is_prime
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run()
 def test_seed(self):self.assertEqual(generate()[0]["hypotenuse"],5)
 def test_recurrence(self):self.assertEqual(next_triangle(3,5),(20,29))
 def test_brute(self):self.assertTrue(self.r["exact_brute_agreement"])
 def test_pell(self):self.assertTrue(self.r["all_pell"])
 def test_primitive(self):self.assertTrue(self.r["all_primitive"])
 def test_counts(self):self.assertEqual((self.r["number_of_candidates"],self.r["prime_count"]),(7,4))
 def test_square_counterexample(self):self.assertFalse(is_prime(169))
 def test_nonsquare_counterexample(self):
  self.assertFalse(is_prime(985))
  self.assertEqual(self.r["square_filter_false_accepts"],2)
 def test_monotonic(self):self.assertTrue(all(x["base"]<y["base"] for x,y in zip(generate(),generate()[1:])))
 def test_small_bound(self):self.assertEqual([(v["base"],v["hypotenuse"]) for v in generate(21)],[(3,5),(20,29)])
if __name__=="__main__":unittest.main()
