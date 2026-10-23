# Reproducible market observation panels (NGC)

Run from the `ngc_geometry_lab` package root, after obtaining input CSVs and independently checking each source's timestamp and bar semantics.

```bash
python scripts/load_market_panel.py --manifest market_panel_manifest.json --out evidence/market_panel_001.json
python -W error -m unittest tests.test_market_observation tests.test_market_real_excerpt tests.test_market_panel_loader -v
```

Example manifest with paths relative to the manifest file:

```json
{
  "schema": "ngc.market_panel_manifest.v0",
  "lags": [1, 2, 4, 8],
  "instruments": [
    {
      "path": "data/AAPL_15m.csv",
      "symbol": "AAPL",
      "kind": "stock",
      "bar_seconds": 900,
      "timestamp_label": "open",
      "volume_kind": "tick_count",
      "source": "https://github.com/getdata-finance/aapl-15m-ohlcv-stocks-historical-data/blob/main/AAPL_15m.csv"
    },
    {
      "path": "data/QQQ_15m.csv",
      "symbol": "QQQ",
      "kind": "etf",
      "bar_seconds": 900,
      "timestamp_label": "open",
      "volume_kind": "shares",
      "source": "SOURCE_URL_TO_VERIFY"
    }
  ]
}
```

**QQQ is a template, not supplied data.** Its path and volume semantics must be confirmed for the actual provider. For sources using local exchange time, audit conversion to ISO UTC separately; this strict loader refuses naive timestamps rather than guessing DST.

Emitted artifacts are deterministically constructed `ngc.market_panel_observations.v0` records. Instruments remain separate on a shared UTC axis. No continuous prices are fabricated during closure, and no interactions are estimated. GEO-X1 and GEO-X2 physical-model-specific validators are **not** invoked.

Lag fitting, candidate selection, randomized controls, uncertainty and causality belong to separately versioned inference and qualification layers. Candidate operators must be frozen before prospective evaluation.

Tests use a pinned **real AAPL excerpt** and a **deliberately duplicated ETF-labeled fixture** solely to verify the mixed-instrument loader path. That second fixture is NOT independent ETF market evidence.
