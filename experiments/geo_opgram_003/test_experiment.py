import unittest
from experiment import SYSTEMS,run_trial,campaign,candidates
class Qualification(unittest.TestCase):
 def test_active(self):
  for g in SYSTEMS.values():self.assertTrue(run_trial(g,'active')['correct'])
 def test_balanced(self):
  for g in SYSTEMS.values():self.assertTrue(run_trial(g,'coverage')['correct'])
 def test_random(self):
  for seed in range(20):
   for g in SYSTEMS.values():self.assertTrue(run_trial(g,'random_coverage',seed)['correct'])
 def test_active_no_better_than_balanced(self):
  for g in SYSTEMS.values():self.assertEqual(run_trial(g,'active')['queries'],run_trial(g,'coverage')['queries'])
 def test_single_corrupt_observation_can_escape(self):
  self.assertFalse(run_trial(SYSTEMS['C4'],'coverage',corruption=('r',0))['correct'])
 def test_conflict_is_recognized(self):
  self.assertEqual(candidates(4,[('r',0,1),('r',0,2)],'r'),[])
 def test_campaign(self):
  self.assertTrue(all(v['active']['all_correct'] and v['coverage']['all_correct'] and v['random_coverage']['all_correct'] for v in campaign(10).values()))
if __name__=='__main__':unittest.main()
