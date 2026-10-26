import unittest
from experiment import *
class TestGrammar(unittest.TestCase):
 def test_c4_size(self):self.assertEqual(trial(c4(),('r','s'))['group_size'],4)
 def test_v4_size(self):self.assertEqual(trial(v4(),('a','b'))['group_size'],4)
 def test_d4_size(self):self.assertEqual(trial(d4(),('r','f'))['group_size'],8)
 def test_c4_commuting(self):self.assertFalse(trial(c4(),('r','s'))['noncommuting'])
 def test_v4_commuting(self):self.assertFalse(trial(v4(),('a','b'))['noncommuting'])
 def test_d4_noncommuting(self):self.assertTrue(trial(d4(),('r','f'))['noncommuting'])
 def test_holdout(self):self.assertEqual(trial(d4(),('r','f'))['errors'],[])
 def test_ambiguity(self):self.assertEqual(reconstruct(d4(),('r','f'),range(3))['status'],'abstain')
 def test_relation(self):
  g=reconstruct(d4(),('r','f'),range(4))['generators']
  self.assertEqual(word_perm(g,('f','r','f')),word_perm(g,('r','r','r')))
 def test_equivalent_words(self):
  g=reconstruct(d4(),('r','f'),range(4))['generators']
  self.assertEqual(word_perm(g,('r','r','r','r')),ident(4))
if __name__=='__main__':unittest.main()
