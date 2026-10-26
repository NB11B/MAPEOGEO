import unittest
from experiment import is_prime,consecutive_triangles,run
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=run();cls.cases=cls.r["cases"]
 def test_first_four(self):self.assertEqual([(x["base"],x["height"],x["hypotenuse"]) for x in self.cases[:4]],[(3,4,5),(20,21,29),(119,120,169),(696,697,985)])
 def test_primitive(self):self.assertTrue(self.r["all_primitive"])
 def test_pell(self):self.assertTrue(self.r["all_negative_pell"])
 def test_primitive_not_prime(self):self.assertFalse(is_prime(169))
 def test_nonsquare_composite(self):self.assertFalse(self.cases[3]["prime"]);self.assertFalse(self.cases[3]["hypotenuse_square"])
 def test_examples_prime(self):self.assertTrue(is_prime(5));self.assertTrue(is_prime(29))
 def test_counts(self):self.assertEqual((self.r["integer_triangles"],self.r["prime_hypotenuses"]),(7,4))
 def test_nine(self):self.assertFalse(is_prime(9));self.assertEqual(9,3**2)
if __name__=="__main__":unittest.main()
