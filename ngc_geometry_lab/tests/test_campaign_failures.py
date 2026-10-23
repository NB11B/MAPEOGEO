"""Fault-injection regressions for evidence handling, separate from algorithm tests."""

from contextlib import ExitStack
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from ngc_geometry_lab import campaign, experiments as exp, repository as repo


@lru_cache(maxsize=1)
def nominal_campaign():
    """Use actual finite measurements to isolate unrelated campaign stages."""
    return campaign.run_campaign()


def stage_stubs():
    measured = deepcopy(nominal_campaign()['experiments'])
    baseline = measured['connected_operators'].pop('upstream_baseline')
    rows = [{'fixture': 'unrelated stage already measured'}]
    return {
        'verify_sources': (repo, measured['source_integrity']),
        'connected_operator_demo': (repo, measured['connected_operators']),
        'exact_closure': (repo, measured['exact_closure']),
        'upstream_baselines': (exp, baseline),
        'metric_and_center': (exp, measured['metric_and_center']),
        'single_qubit': (exp, (measured['single_qubit'], deepcopy(rows))),
        'dual_lane': (exp, (measured['dual_lane'], deepcopy(rows))),
        'finite_shot': (exp, (measured['finite_shot'], deepcopy(rows), {}, {}, {})),
        'readout_selection': (exp, (measured['readout'], deepcopy(rows))),
        'joint_systems': (exp, (measured['joint'], deepcopy(rows))),
        'identifiability': (exp, measured['identifiability']),
    }


def isolated_campaign(*, overrides=None, real_stages=(), output_dir=None):
    """Keep the target failure real while reusing unrelated finite measurements."""
    stubs = stage_stubs()
    with ExitStack() as stack:
        for name, (module, value) in stubs.items():
            if name not in real_stages:
                replacement = (overrides or {}).get(name, value)
                stack.enter_context(patch.object(module, name, return_value=replacement))
        return campaign.run_campaign(output_dir=output_dir)


def final_gate_corruption(value):
    original = repo.dual_lane_apply
    calls = []

    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(1)
        if len(calls) % 20 == 0:
            result[:] = value
        return result

    return corrupt, calls


class NonfiniteComparisonTests(unittest.TestCase):
    def test_dual_lane_rejects_nonfinite_final_gate_before_reduction(self):
        for value in (np.nan, np.inf):
            with self.subTest(value=value):
                corrupt, calls = final_gate_corruption(value)
                with patch.object(repo, 'dual_lane_apply', side_effect=corrupt):
                    with self.assertRaisesRegex(ValueError, r'dual_lane.*circuit=0.*step=20.*nonfinite'):
                        exp.dual_lane(20261022)
                self.assertEqual(len(calls), 20)

    def test_single_final_rotation_nonfinite_probability_is_rejected(self):
        original = exp.geo.tetra_probabilities
        for value in (np.nan, np.inf):
            calls = []

            def corrupt(*args, **kwargs):
                result = original(*args, **kwargs)
                calls.append(1)
                # One direct comparison, then two calls per rotation. The
                # candidate call at the last rotation is call 24.
                if len(calls) == 24:
                    result[:] = value
                return result

            with self.subTest(value=value), patch.object(exp.geo, 'tetra_probabilities', side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, r'single_qubit.*case=0.*step=12.*nonfinite'):
                    exp.single_qubit(20261022)

    def test_joint_final_rotation_nonfinite_probability_is_rejected(self):
        original = exp.geo.joint_probabilities
        for value in (np.nan, np.inf):
            calls = []

            def corrupt(*args, **kwargs):
                result = original(*args, **kwargs)
                calls.append(1)
                if len(calls) == 9:  # Direct comparison plus eight rotations.
                    result[:] = value
                return result

            with self.subTest(value=value), patch.object(exp.geo, 'joint_probabilities', side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, r'joint.*case=0.*step=8.*nonfinite'):
                    exp.joint_systems(20261022)

    def test_finite_shot_rejects_nonfinite_record_metrics(self):
        original = exp.analyze_dataset
        for value in (np.nan, np.inf):
            def corrupt(observations):
                result = original(observations)
                result['cases'][0]['verification_total_variation'] = value
                return result

            with self.subTest(value=value), patch.object(exp, 'analyze_dataset', side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, r'finite_shot.*verification.*nonfinite'):
                    exp.finite_shot(20261022)

    def test_readout_rejects_nonfinite_score_before_selecting_winner(self):
        original = exp.np.log
        for value in (np.nan, np.inf):
            calls = []

            def corrupt(values, *args, **kwargs):
                result = original(values, *args, **kwargs)
                calls.append(1)
                if len(calls) == 1:
                    return np.full_like(result, value)
                return result

            with self.subTest(value=value), patch.object(exp.np, 'log', side_effect=corrupt):
                with self.assertRaisesRegex(ValueError, r'readout.*calibration.*nonfinite'):
                    exp.readout_selection(20261022)


class CampaignFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nominal = nominal_campaign()

    def assert_failed_stage(self, result, name, gate):
        self.assertFalse(result['qualified'])
        self.assertIn(name, result['stage_errors'])
        self.assertEqual(result['experiments'][name], result['stage_errors'][name])
        self.assertFalse(next(g['passed'] for g in result['gates'] if g['id'] == gate))
        self.assertIn('nonfinite', result['stage_errors'][name]['error'])
        json.dumps(result, allow_nan=False)

    def test_nominal_results_remain_qualified(self):
        self.assertTrue(self.nominal['qualified'])
        self.assertEqual(self.nominal['stage_errors'], {})
        self.assertEqual(len(self.nominal['gates']), 12)

    def test_final_gate_failure_is_retained_without_output_directory(self):
        for value in (np.nan, np.inf):
            corrupt, _ = final_gate_corruption(value)
            with self.subTest(value=value), patch.object(repo, 'dual_lane_apply', side_effect=corrupt):
                result = isolated_campaign(real_stages=('dual_lane',))
            self.assert_failed_stage(result, 'dual_lane', 'dual_lane_equivalence')

    def test_final_gate_failure_publishes_checkpoint_exception_and_report(self):
        for value in (np.nan, np.inf):
            corrupt, _ = final_gate_corruption(value)
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                with patch.object(repo, 'dual_lane_apply', side_effect=corrupt):
                    result = isolated_campaign(real_stages=('dual_lane',), output_dir=directory)
                self.assert_failed_stage(result, 'dual_lane', 'dual_lane_equivalence')
                path = Path(directory)
                checkpoint = json.loads((path/'checkpoints/dual_lane.json').read_text())
                self.assertEqual(checkpoint, result['stage_errors']['dual_lane'])
                self.assertIn('step=20', checkpoint['error'])
                self.assertIn('nonfinite', (path/'dual_lane_exception.txt').read_text())
                self.assertIn('Result: FAIL', (path/'REPORT.md').read_text())
                self.assertEqual(json.loads((path/'results.json').read_text()), result)
                self.assertTrue((path/'manifest.json').is_file())

    def test_nonfinite_summaries_are_caught_inside_stage_boundary(self):
        cases = (
            ('metric_and_center', 'metric_and_center', 'metric_and_center', 'max_metric_error'),
            ('dual_lane', 'dual_lane', 'dual_lane_equivalence', 'max_norm_error'),
            ('finite_shot', 'finite_shot', 'finite_shot_prediction', 'mean_state_error'),
            ('readout_selection', 'readout', 'readout_selection', 'direct_crossed_weight'),
            ('joint_systems', 'joint', 'joint_reconstruction', 'max_prediction_error'),
        )
        for function, name, gate, field in cases:
            for value in (np.nan, np.inf):
                replacement = deepcopy(stage_stubs()[function][1])
                summary = replacement[0] if isinstance(replacement, tuple) else replacement
                summary[field] = value
                with self.subTest(stage=name, value=value):
                    result = isolated_campaign(overrides={function:replacement})
                    self.assert_failed_stage(result, name, gate)

    def test_nonfinite_table_and_auxiliary_payloads_are_preserved_as_failure_evidence(self):
        for target in ('table', 'auxiliary'):
            for value in (np.nan, np.inf):
                replacement = deepcopy(stage_stubs()['finite_shot'][1])
                if target == 'table':
                    replacement[1][0]['verification_total_variation'] = value
                else:
                    replacement[4]['damaged_metric'] = value
                for saved in (False, True):
                    with self.subTest(target=target, value=value, saved=saved), tempfile.TemporaryDirectory() as directory:
                        result = isolated_campaign(overrides={'finite_shot':replacement},
                                                   output_dir=directory if saved else None)
                        self.assert_failed_stage(result, 'finite_shot', 'finite_shot_prediction')
                        failures = result['stage_errors']['finite_shot']['invalid_evidence']
                        self.assertTrue(any(item['value'] == repr(float(value)) for item in failures))
                        if saved:
                            path = Path(directory)
                            self.assertIn(repr(float(value)), (path/'finite_shot_invalid_evidence.txt').read_text())
                            self.assertIn('Result: FAIL', (path/'REPORT.md').read_text())
                            self.assertFalse((path/'finite_shot.csv').exists())
                            self.assertFalse((path/'blind_analysis.json').exists())


class KnownUpstreamFailureTests(unittest.TestCase):
    known_name = 'test_noncommuting_operators_can_be_equivalent_after_work_projection'

    def test_original_pinned_failure_is_still_visible_and_narrowly_recognized(self):
        result = exp.upstream_baselines()
        self.assertEqual((result['tests_executed'], result['passed'], result['failed']), (24, 23, 1))
        self.assertEqual(result['known_bad_test_expectations'], 1)
        self.assertEqual(result['unexpected_failures'], 0)
        failure = next(r for r in result['tests'] if r['status'] == 'FAIL')
        self.assertEqual(failure['failure_line'], 13)
        self.assertEqual(failure['exception'], 'AssertionError')
        self.assertEqual(failure['message'], '')

    def test_unrelated_assertion_with_same_test_name_is_unexpected(self):
        original = exp.runpy.run_path

        def unrelated_assertion():
            raise AssertionError()

        def wrapped(path):
            namespace = original(path)
            if self.known_name in namespace:
                namespace[self.known_name] = unrelated_assertion
            return namespace

        with patch.object(exp.runpy, 'run_path', side_effect=wrapped):
            result = exp.upstream_baselines()
        self.assertEqual(result['known_bad_test_expectations'], 0)
        self.assertEqual(result['unexpected_failures'], 1)

    def test_legitimate_earlier_assertion_in_exact_pinned_file_is_unexpected(self):
        original = exp.runpy.run_path

        def wrapped(path):
            namespace = original(path)
            if self.known_name in namespace:
                function = namespace[self.known_name]
                function.__globals__['work_relative_commutation'] = lambda *args: SimpleNamespace(exact_equal=True)
            return namespace

        with patch.object(exp.runpy, 'run_path', side_effect=wrapped):
            result = exp.upstream_baselines()
        self.assertEqual(result['known_bad_test_expectations'], 0)
        self.assertEqual(result['unexpected_failures'], 1)
        failure = next(r for r in result['tests'] if r['status'] == 'FAIL')
        self.assertEqual(failure['failure_line'], 8)


if __name__ == '__main__':
    unittest.main()
