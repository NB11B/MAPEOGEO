"""Standalone admission tests; no dependency on a financial vendor or clock locale."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import numpy as np

from ngc_geometry_lab.market_observation import (
    load_ohlcv_csv, sample_multiscale_states, adjacent_pairs,
    observation_carrier, ordered_operator_diagnostics, earth_phase_utc,
)
from ngc_geometry_lab.market_inference import evaluate_frozen_predictions
from datetime import datetime, timezone

HEADER = "datetime,open,high,low,close,volume\n"


def row(t, p, volume=100):
    return f"{t},{p},{p},{p},{p},{volume}\n"


class MarketBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'source.csv'

    def write(self, body):
        self.path.write_text(HEADER + body, encoding='utf-8')

    def load(self, **kwargs):
        args = dict(symbol='TEST', kind='etf', bar_seconds=900,
                    timestamp_label='open', volume_kind='tick_count', source='fixture:v1')
        args.update(kwargs)
        return load_ohlcv_csv(self.path, **args)

    def test_provenance_and_availability_prevent_bar_start_leakage(self):
        self.write(row('2026-03-26T13:30:00+00:00', 100) +
                   row('2026-03-26T13:45:00+00:00', 101) +
                   row('2026-03-26T14:00:00+00:00', 102))
        s = self.load()
        self.assertEqual(len(s.bars), 3)
        self.assertEqual(s.bars[0].available_at_utc.isoformat(), '2026-03-26T13:45:00+00:00')
        self.assertEqual(s.source_sha256, hashlib.sha256(self.path.read_bytes()).hexdigest())
        points = sample_multiscale_states(s, lags=(1, 2))
        self.assertEqual(len(points), 1)
        self.assertAlmostEqual(points[0].coordinates[0], np.log(102/101))
        self.assertAlmostEqual(points[0].coordinates[1], np.log(102/100))
        self.assertEqual(observation_carrier(s, points)['epistemic_status'], 'DETERMINISTIC_OBSERVATION_ONLY')

    def test_fail_closed_naive_duplicate_overlap_invalid_ohlc(self):
        base = row('2026-03-26T13:30:00+00:00', 100)
        bad = [base.replace('+00:00',''), base+base,
               base+row('2026-03-26T13:40:00+00:00',101),
               '2026-03-26T13:30:00+00:00,101,100,100,101,20\n',
               row('2026-03-26T13:30:00+00:00', -2),
               row('2026-03-26T13:30:00+00:00', 100, -1)]
        for body in bad:
            with self.subTest(body=body):
                self.write(body)
                with self.assertRaises(ValueError):
                    self.load()

    def test_no_gap_interpolation_or_weekend_transition(self):
        self.write(''.join(row(f'2026-03-26T{hh}:00:00+00:00', 100+i)
                           for i,hh in enumerate(['13','14','15']))+
                   row('2026-03-27T13:00:00+00:00', 110) +
                   row('2026-03-27T14:00:00+00:00', 111))
        s = self.load(bar_seconds=3600)
        points = sample_multiscale_states(s, lags=(1,))
        self.assertEqual(len(points), 3)
        self.assertEqual(len(adjacent_pairs(points, interval_seconds=3600)), 1)

    def test_phase_utc_not_machine_locale(self):
        t = datetime(2026, 3, 26, 12, tzinfo=timezone.utc)
        self.assertAlmostEqual(earth_phase_utc(t), np.pi)
        with self.assertRaises(ValueError):
            earth_phase_utc(datetime(2026,3,26,12))

    def test_operator_order_algebra_and_no_causal_claim(self):
        A = np.array([[1., 1.], [0., 1.]])
        B = np.array([[1., 0.], [1., 1.]])
        x = np.array([2.,3.])
        d = ordered_operator_diagnostics(A,B,x,B@A@x)
        self.assertGreater(d['commutator_frobenius'], 0)
        self.assertAlmostEqual(d['observed_order_error'], 0)
        self.assertGreater(d['reversed_order_error'], 0)
        self.assertIn('NOT_CAUSAL', d['evidence_status'])

    def test_probabilistic_scores_isolated_from_deterministic_ingestion(self):
        a=np.array([[1.,2.],[2.,3.]])
        result=evaluate_frozen_predictions(a,a,np.zeros_like(a))
        self.assertEqual(result['candidate_mse'],0)
        self.assertEqual(result['error_ratio'],0)
        self.assertIn('NOT_MECHANISM',result['epistemic_status'])
        with self.assertRaises(ValueError):
            evaluate_frozen_predictions(a, a[:1], a)

if __name__ == '__main__':
    unittest.main()
