import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ngc_geometry_lab.observations import analyze_dataset
from ngc_geometry_lab.synthetic import generate_dataset


class SyntheticWorkflowTests(unittest.TestCase):
    def test_seed_reproducibility_and_truth_separation(self):
        observations, truth = generate_dataset(417, case_count=8, shots=10000)
        again, same_truth = generate_dataset(417, case_count=8, shots=10000)
        self.assertEqual(observations, again)
        self.assertEqual(truth, same_truth)
        self.assertNotIn('truth', observations)
        self.assertNotIn('true_state', observations['cases'][0])
        self.assertEqual(observations['provenance']['kind'], 'synthetic')
        self.assertEqual(len(truth['cases']), 8)
        other, _ = generate_dataset(418, case_count=8, shots=10000)
        self.assertNotEqual(observations, other)

    def test_counts_and_independent_prediction_workflow(self):
        observations, truth = generate_dataset(729, case_count=12)
        result = analyze_dataset(observations)
        errors = []
        for actual, expected in zip(result['cases'], truth['cases']):
            self.assertEqual(actual['id'], expected['id'])
            self.assertEqual(actual['estimate']['shots'], 65536)
            errors.append(np.linalg.norm(actual['estimate']['state'] - expected['initial_state']))
        self.assertLess(np.mean(errors), .035)
        self.assertLess(result['mean_verification_total_variation'], .02)

    def test_configuration_validation(self):
        for kwargs in ({'calibration_count': 3}, {'case_count': 0}, {'shots': 0}, {'shots': 2.5}, {'case_count': True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generate_dataset(**kwargs)


if __name__ == '__main__':
    unittest.main()
