import unittest
from certificate import certificate,exhaustive
class Tests(unittest.TestCase):
 def test_exhaustive(self):
  checked,errors=exhaustive(6)
  self.assertEqual(checked,15123)
  self.assertEqual(errors,[])
 def test_two_missing_ambiguous(self):self.assertEqual(certificate(7,[(i,(i+3)%7) for i in range(5)])['status'],'ambiguous')
 def test_one_missing_identified(self):self.assertEqual(certificate(7,[(i,(i+3)%7) for i in range(6)])['status'],'identified')
 def test_noninjective_rejected(self):self.assertEqual(certificate(3,[(0,1),(2,1)])['status'],'refuse')
 def test_conflicting_rejected(self):self.assertEqual(certificate(3,[(0,1),(0,2)])['status'],'refuse')
if __name__=='__main__':unittest.main()
