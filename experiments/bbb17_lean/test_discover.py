import unittest
from discover import discover
class Checks(unittest.TestCase):
    def test_early(self):
        x=discover(100000)
        self.assertEqual(x['beeps'],351)
        self.assertEqual(x['last_beep'],62273)
        self.assertEqual(x['boundaries'][-1]['rank'],26)
        self.assertTrue(x['hypotheses']['triangular_checkpoints_head_minus_one'])
        self.assertTrue(x['hypotheses']['triangular_checkpoints_left_boundary'])
        self.assertFalse(x['hypotheses']['triangular_checkpoints_ones_triangular'])
        self.assertFalse(x['universal_proof'])
    def test_prefix(self):
        for n in (0,1,5,25,100):
            x=discover(n)
            self.assertEqual(x['steps'],n)
            self.assertTrue(x['beeps']<=n)
if __name__=='__main__': unittest.main()
