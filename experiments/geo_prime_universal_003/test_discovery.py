import unittest
from discovery import campaign,cyclic_family,conjugate,qualify,orbit_lengths,identity
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=campaign()
 def test_all(self):self.assertEqual(self.r["mismatches"],[])
 def test_nine(self):self.assertFalse(self.r["n9"]["prime"])
 def test_relabel(self):self.assertTrue(self.r["relabel_invariant"])
 def test_missing(self):self.assertTrue(self.r["missing_family_refused"])
 def test_duplicate(self):self.assertTrue(self.r["duplicate_refused"])
 def test_noncyclic(self):self.assertTrue(self.r["noncyclic_group_refused"])
 def test_single(self):self.assertTrue(self.r["single_full_cycle_refused"])
 def test_orbit(self):self.assertEqual(orbit_lengths((3,4,5,6,7,8,0,1,2)),(3,3,3))
 def test_two(self):self.assertTrue(qualify(cyclic_family(2)[0])["prime"])
 def test_invalid(self):self.assertEqual(qualify((identity(3),(0,0,2),(1,2,0)))["status"],"refuse")
if __name__=="__main__":unittest.main()
