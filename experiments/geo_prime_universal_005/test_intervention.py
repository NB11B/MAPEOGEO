import unittest
from intervention import run,intervention_signature
from ambiguity import cyclic_four,klein_four
class Tests(unittest.TestCase):
 def test_collision(self):self.assertTrue(run()["unlabeled_collision"])
 def test_interventions(self):self.assertTrue(run()["distinguishable_with_same_operator_interventions"])
 def test_cyclic(self):self.assertEqual(intervention_signature(cyclic_four()),(1,2,4,4))
 def test_klein(self):self.assertEqual(intervention_signature(klein_four()),(1,2,2,2))
 def test_orders(self):self.assertEqual((run()["cyclic_order_two_count"],run()["klein_order_two_count"]),(1,3))
if __name__=="__main__":unittest.main()
