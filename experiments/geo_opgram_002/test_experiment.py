import unittest
from experiment import train,version_space,probe,heldout,campaign
D={'r':(1,2,3,0),'f':(0,3,2,1)}
class Tests(unittest.TestCase):
 def test_active_identifies(self):self.assertEqual(train(4,D,'active',8)['status'],'identified')
 def test_passive_ambiguous(self):self.assertEqual(train(4,D,'passive',8)['status'],'ambiguous')
 def test_holdout(self):self.assertEqual(heldout(4,D,train(4,D,'active',8))[0],0)
 def test_full_space(self):self.assertEqual(len(version_space(4,('r',),[])['r']),24)
 def test_one_edge(self):self.assertEqual(len(version_space(4,('r',),[('r',0,1)])['r']),6)
 def test_conflict(self):self.assertIsNone(version_space(4,('r',),[('r',0,1),('r',0,2)]))
 def test_invalid(self):self.assertIsNone(version_space(4,('r',),[('r',9,2)]))
 def test_probe(self):self.assertIsNotNone(probe(version_space(4,('r',),[]),4,('r',)))
 def test_no_probe_complete(self):self.assertIsNone(probe(version_space(2,('r',),[('r',0,1)]),2,('r',)))
 def test_all(self):
  for v in campaign().values():
   self.assertEqual(v['active'],'identified')
   self.assertEqual(v['passive'],'ambiguous')
   self.assertEqual(v['heldout'][0],0)
if __name__=='__main__':unittest.main()
