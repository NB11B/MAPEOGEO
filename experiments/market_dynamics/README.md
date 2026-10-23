# Market dynamics adapter v0: bounded deterministic observations

This adapter is **not a stock predictor** and does not assert quantum market physics.

## Contract
- Load timestamped OHLC observations only when each timestamp has explicit timezone information.
- Convert timestamps to UTC and store source SHA-256.
- Reject duplicated or out-of-order timestamps, invalid OHLC, nonfinite/nonpositive prices.
- Extract log-price delay coordinates only across **observed contiguous** bars. Never invent overnight, weekend, holiday, or illiquid observations.
- Extract ordered transitions, fit a regularized local/global linear measurement operator on training timestamps, and evaluate on a later holdout.
- Compute symmetric and skew parts of measured operators algebraically.
- Preserve UTC/Earth phase only as **metadata**, not as a causal or predictive hypothesis.

## Deterministic vs probabilistic
Deterministic side: bytes, provenance, schema checks, timestamp conversion,
segmentation, state reconstruction, operator algebra, generator decomposition,
commutators, and exact reproduction of a named numerical procedure.

Probabilistic side (not implemented in v0): statistical tests, uncertainty,
out-of-sample model selection, cross-market transfer, causal interpretations.
Do not export a probabilistic conclusion as a kernel-verified mathematical fact.

## Critical falsification warning
For log-price delay coordinates with lags 1,2,4, parts of consecutive
coordinates are algebraically related by construction. A linear operator
outperforming the identity **is not independent evidence** of latent market
machinery. Compare against shift-register baselines, shuffled-increment
controls, synthetic processes and several embeddings before claiming structure.

## Run
From the repository root:
```bash
python -m unittest tests/test_market_dynamics_loader.py -v
python experiments/market_dynamics/market_loader.py --manifest manifest.json --out results.json
```

Example manifest:
```json
{
  "path": "/absolute/path/to/utc_market_15m.csv",
  "cadence_seconds": 900,
  "lags": [1, 2, 4],
  "split_utc": "2026-08-01T00:00:00Z",
  "ridge": 0.00000001
}
```

## Current empirical boundary
Independent readout of the public AAPL 15m sample (2026-03-26 through
2026-09-25): 3,302 price bars, 2,794 contiguous lag states,
1,848 training transitions and 819 holdout transitions;
relative test MSE vs unchanged-state = 0.53655.
This result is expected to include deterministic delay-coordinate algebra
and **is not qualified evidence of hidden dynamics**.

The data source is:
https://github.com/getdata-finance/aapl-15m-ohlcv-stocks-historical-data

The earlier 2015 AAPL/ETF archive has undocumented timezone and is not
admitted to Earth-phase qualification without independent timezone provenance.

The next gate must independently test stocks AND funds with properly
timestamped data, including true extended-hours coverage, before any 24/7
continuity claims are made.
