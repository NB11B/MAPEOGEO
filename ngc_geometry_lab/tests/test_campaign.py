import unittest

from ngc_geometry_lab.campaign import run_campaign


class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_campaign()

    def test_all_frozen_gates_pass_and_controls_present(self):
        self.assertTrue(self.result['qualified'], self.result.get('gates'))
        required = {'source_integrity', 'connected_operators', 'exact_closure', 'metric_and_center', 'tetra_reconstruction', 'heldout_rotations', 'dual_lane_equivalence', 'finite_shot_prediction', 'readout_selection', 'joint_reconstruction', 'correlation_controls', 'identifiability'}
        self.assertEqual(required, {g['id'] for g in self.result['gates']})
        self.assertTrue(all(g['passed'] for g in self.result['gates']))

    def test_evidence_scope_is_explicit(self):
        self.assertEqual(self.result['scope']['observations'], 'synthetic')
        self.assertEqual(self.result['scope']['cuda_execution'], 'not_run_cpu_only_campaign')
        self.assertFalse(self.result['scope']['physical_theory_validated'])
        self.assertGreaterEqual(self.result['experiments']['dual_lane']['gate_applications'], 1000)
        self.assertEqual(self.result['experiments']['single_qubit']['states'], 256)
        self.assertEqual(self.result['experiments']['single_qubit']['rotation_predictions'], 3072)

    def test_no_unexpected_upstream_failures_are_hidden(self):
        baseline = self.result['experiments']['connected_operators']['upstream_baseline']
        self.assertEqual(baseline['known_bad_test_expectations'], 1)
        self.assertEqual(baseline['unexpected_failures'], 0)


if __name__ == '__main__':
    unittest.main()
