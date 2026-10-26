import unittest
from experiment import wheel,extend,count_removed,campaign
class Tests(unittest.TestCase):
 def test_30_to_210(self):self.assertEqual(extend(wheel(30),7),wheel(210))
 def test_210_to_2310(self):self.assertEqual(extend(wheel(210),11),wheel(2310))
 def test_new_exclusions(self):self.assertEqual((count_removed(wheel(30),7),count_removed(wheel(210),11)),(8,48))
 def test_survivors(self):self.assertEqual((sum(wheel(30)),sum(wheel(210)),sum(wheel(2310))),(8,48,480))
 def test_rotation(self):
  for residual in campaign()['rotation_magnitude_residual'].values():self.assertLess(residual,1e-9)
 def test_requires_next_factor(self):self.assertNotEqual(extend(wheel(30),7),extend(wheel(30),11))
if __name__=='__main__':unittest.main()
