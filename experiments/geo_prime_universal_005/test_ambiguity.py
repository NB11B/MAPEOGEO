import unittest
from ambiguity import cyclic_four,klein_four,observations,signature,run,qualify
class Tests(unittest.TestCase):
 def test_collision(self):self.assertEqual(observations(cyclic_four()),observations(klein_four()))
 def test_cyclic(self):self.assertEqual(signature(cyclic_four()),(1,2,4,4))
 def test_klein(self):self.assertEqual(signature(klein_four()),(1,2,2,2))
 def test_pairs(self):self.assertTrue(run()["all_pairs_once"])
 def test_refuse(self):self.assertEqual(run()["decision"]["status"],"refuse")
 def test_different(self):self.assertNotEqual(signature(cyclic_four()),signature(klein_four()))
 def test_invalid(self):
  with self.assertRaises(ValueError):observations(((0,0),(1,0)))
 def test_relabel(self):
  p=(2,0,3,1);inv=[0]*4
  for i,x in enumerate(p):inv[x]=i
  def relabel(ops):
   return tuple(tuple(p[op[inv[i]]] for i in range(4)) for op in ops)
  self.assertEqual(observations(relabel(cyclic_four())),observations(relabel(klein_four())))
if __name__=="__main__":unittest.main()
