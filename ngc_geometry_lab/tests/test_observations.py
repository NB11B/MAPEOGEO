import copy
import unittest

import numpy as np

from ngc_geometry_lab.observations import (
    analyze_dataset, calibrate_detector, estimate_state,
    predict_after_operations, validate_counts,
)


N = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3)


def calibration_fixture():
    # The six axes span the affine observation space. Rational tetrahedron
    # coordinates make integer counts exact, avoiding a test rounding oracle.
    states = np.vstack([N, -N]) * 0.6
    response = 0.8 * np.eye(4) + 0.2 * np.ones((4, 4)) / 4
    ideal = (1 + states @ N.T) / 4
    counts = np.rint((ideal @ response.T) * 100000).astype(int)
    return states, counts, response


class ObservationTests(unittest.TestCase):
    def test_calibration_recovers_known_detector_from_counts(self):
        states, counts, expected = calibration_fixture()
        fit = calibrate_detector(states, counts)
        np.testing.assert_allclose(fit['matrix'], expected, atol=1e-12, rtol=0)
        self.assertEqual(fit['design_rank'], 4)
        self.assertLess(fit['training_rmse'], 1e-12)

    def test_inversion_uses_counts_and_frozen_detector(self):
        states, counts, _ = calibration_fixture()
        fit = calibrate_detector(states, counts)
        estimate = estimate_state(counts[0], fit)
        np.testing.assert_allclose(estimate['state'], states[0], atol=1e-12, rtol=0)
        self.assertFalse(estimate['projected'])

    def test_unphysical_sampling_estimate_preserves_raw_record(self):
        fit = {'matrix': np.eye(4)}
        estimate = estimate_state([100, 0, 0, 0], fit)
        self.assertAlmostEqual(estimate['raw_norm'], 3)
        self.assertTrue(estimate['projected'])
        np.testing.assert_allclose(estimate['raw_state'], 3 * N[0], atol=1e-12, rtol=0)
        np.testing.assert_allclose(estimate['state'], N[0], atol=1e-12, rtol=0)
        unprojected = estimate_state([100, 0, 0, 0], fit, project_physical=False)
        np.testing.assert_allclose(unprojected['state'], 3 * N[0], atol=1e-12, rtol=0)

    def test_rotation_prediction_has_correct_sign_and_order(self):
        out = predict_after_operations([0, 0, 1], [{'axis': [1, 0, 0], 'angle': np.pi / 2}], {'matrix': np.eye(4)})
        np.testing.assert_allclose(out['state'], [0, -1, 0], atol=1e-12, rtol=0)
        np.testing.assert_allclose(out['observed_probabilities'], (1-N[:, 1])/4, atol=1e-12, rtol=0)

    def test_rank_deficient_calibration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'rank'):
            calibrate_detector(np.zeros((8, 3)), np.full((8, 4), 25))

    def test_uninformative_detector_rejected(self):
        states, _, _ = calibration_fixture()
        with self.assertRaisesRegex(ValueError, 'singular|condition'):
            calibrate_detector(states, np.full((8, 4), 25))

    def test_counts_validation(self):
        for invalid in ([0, 0, 0, 0], [1, -1, 2, 2], [1.5, 2, 3, 4], [1, 2, 3], [1, 2, 3, np.nan], [True, False, False, False], [1+1j, 2, 3, 4]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_counts(invalid)

    def test_large_counts_are_rejected_before_float_rounding(self):
        for invalid in ([2**53+1, 0, 0, 0], [2**53, 1, 0, 0], [10**100, 0, 0, 0]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_counts(invalid)
        np.testing.assert_array_equal(validate_counts([2**53, 0, 0, 0]), [2**53, 0, 0, 0])

    def test_mixed_boolean_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_counts([1, True, 2, 3])

    def test_detector_validation_rejects_invalid_matrices(self):
        for matrix in (np.zeros((4, 4)), np.ones((4, 4)), np.eye(3), np.eye(4)*np.nan, np.eye(4).astype(complex)+1j):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                estimate_state([25]*4, {'matrix': matrix})

    def payload(self):
        states, counts, _ = calibration_fixture()
        return {
            'schema': 'ngc_geometry_lab.observations.v1',
            'provenance': {'kind': 'synthetic', 'description': 'Analytic unit test'},
            'calibration': {'states': states.tolist(), 'counts': counts.tolist()},
            'cases': [{'id': 'heldout', 'counts': counts[0].tolist(), 'operations': [], 'verification_counts': counts[0].tolist()}],
        }

    def test_blind_dataset_workflow(self):
        data = self.payload()
        original = copy.deepcopy(data)
        result = analyze_dataset(data)
        self.assertEqual(result['data_kind'], 'synthetic')
        self.assertEqual(len(result['cases']), 1)
        self.assertLess(result['cases'][0]['verification_total_variation'], 1e-12)
        self.assertEqual(data, original)

    def test_schema_rejects_embedded_truth_and_duplicate_ids(self):
        data = self.payload()
        data['cases'][0]['true_state'] = [0, 0, 1]
        with self.assertRaisesRegex(ValueError, 'unexpected|unknown'):
            analyze_dataset(data)
        data = self.payload()
        data['cases'].append(copy.deepcopy(data['cases'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            analyze_dataset(data)

    def test_schema_requires_explicit_provenance(self):
        data = self.payload()
        del data['provenance']
        with self.assertRaises(ValueError):
            analyze_dataset(data)


if __name__ == '__main__':
    unittest.main()
