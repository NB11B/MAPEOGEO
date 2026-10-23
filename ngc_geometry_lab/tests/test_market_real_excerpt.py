"""Real-market admission only, not dynamics qualification."""
from pathlib import Path
import unittest
from ngc_geometry_lab.market_observation import load_ohlcv_csv, sample_multiscale_states, observation_carrier

SOURCE = 'https://github.com/getdata-finance/aapl-15m-ohlcv-stocks-historical-data/blob/main/AAPL_15m.csv'

class RealDataExcerptTests(unittest.TestCase):
    def test_aapl_source_excerpt(self):
        path = Path(__file__).resolve().parent / 'fixtures' / 'aapl_20260326_15m_excerpt.csv'
        s = load_ohlcv_csv(path, symbol='AAPL', kind='stock', bar_seconds=900,
                           timestamp_label='open', volume_kind='tick_count', source=SOURCE)
        states = sample_multiscale_states(s, lags=(1, 2, 4))
        self.assertEqual(len(s.bars), 13)
        self.assertEqual(len(states), 9)
        self.assertEqual(states[0].at_utc.isoformat(), '2026-03-26T14:45:00+00:00')
        self.assertEqual(states[-1].at_utc.isoformat(), '2026-03-26T16:45:00+00:00')
        self.assertEqual(observation_carrier(s, states)['coordinate_dimension'], 3)

if __name__ == '__main__':
    unittest.main()
