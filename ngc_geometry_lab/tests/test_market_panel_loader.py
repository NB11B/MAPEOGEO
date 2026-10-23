"""End-to-end pinned source-admission and fail-closed output tests."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.load_market_panel import run


class PanelLoaderTests(unittest.TestCase):
    def test_real_excerpt_pipeline_is_idempotent_and_no_overwrite(self):
        src = Path(__file__).parent / 'fixtures' / 'aapl_20260326_15m_excerpt.csv'
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            m = folder / 'panel.json'
            out = folder / 'evidence.json'
            m.write_text(json.dumps({
                'schema': 'ngc.market_panel_manifest.v0', 'lags': [1,2,4],
                'instruments': [
                    {'path': str(src.resolve()), 'symbol': 'AAPL', 'kind': 'stock',
                     'bar_seconds': 900, 'timestamp_label': 'open', 'volume_kind': 'tick_count',
                     'source': 'https://github.com/getdata-finance/aapl-15m-ohlcv-stocks-historical-data/blob/main/AAPL_15m.csv'},
                    {'path': str(src.resolve()), 'symbol': 'ETF_FIXTURE', 'kind': 'etf',
                     'bar_seconds': 900, 'timestamp_label': 'open', 'volume_kind': 'tick_count',
                     'source': 'TEST_ONLY_DUPLICATED_SOURCE'},
                ]}), encoding='utf-8')
            data=run(m,out)
            self.assertEqual(len(data['instruments']), 2)
            self.assertEqual(len(data['instruments'][0]['observations']), 9)
            self.assertEqual(data['instruments'][0]['provenance']['source_sha256'],
                             data['instruments'][1]['provenance']['source_sha256'])
            self.assertEqual(json.loads(out.read_text()), data)
            with self.assertRaisesRegex(ValueError,'already exists'):
                run(m,out)

    def test_failed_admission_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder); m=folder/'panel.json';out=folder/'evidence.json'
            m.write_text(json.dumps({'schema':'ngc.market_panel_manifest.v0',
                                     'lags':[1], 'instruments':[{'bad':'record'}]}))
            with self.assertRaises(ValueError):
                run(m,out)
            self.assertFalse(out.exists())

if __name__ == '__main__':
    unittest.main()
