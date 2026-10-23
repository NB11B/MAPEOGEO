# NGC / MAPEOGEO: Market observation adapter v0

Parent: `NB11B/MAPEOGEO` at `780838c`; GEO-X1 and GEO-X2 remain unchanged.

**Scope:** This is an observable-data input boundary, NOT a model of market physics and NOT a quantum-state claim.

## Deterministic layer

1. Read third-party OHLCV CSV files with explicit instrument kind (stock, ETF, mutual fund, index, future, other), symbol, source URI, SHA-256, bar width, label semantics and volume units.
2. Reject missing timezones, duplicate timestamps, overlapping bars, invalid prices or invalid volume values. Normalize timestamps to UTC.
3. Label each observation with its actual bar-close availability time. Do not leak the bar's closing price into its opening timestamp.
4. Never insert fictitious quotes or connect delay coordinates across missing bars, sessions or weekends.
5. Use observed multiscale log-close ratios as declared *candidate coordinates*; those coordinates are not a discovered law or unique latent state.
6. Calculate Earth phase only from UTC civil time (a measurement coordinate, not an explanatory driver).
7. Produce an `ngc.market_observation.v0` transport carrier with provenance, without modifying GEO-X1/X2 or renormalizing financial series into physically constrained Bloch states.
8. Expose an algebraic operator-order check for *externally supplied* matrices. A nonzero commutator is NOT causal evidence.

## Probabilistic/inferential layer

`market_inference.py` cannot alter deterministic observations. It scores only already-frozen candidate and baseline predictions on the *same holdout rows*. Choosing lag, model, state dimension or phase bins using the test set is outside the contract. Random/permutation nulls and confidence claims require separate preregistration and evidence.

## Usage

Run from the `ngc_geometry_lab/` repository directory:

```shell
python -W error -m unittest tests.test_market_observation -v
```

```python
from ngc_geometry_lab.market_observation import (
    load_ohlcv_csv, sample_multiscale_states, observation_carrier,
)
series = load_ohlcv_csv(
    "AAPL_15m.csv", symbol="AAPL", kind="stock",
    bar_seconds=900, timestamp_label="open",
    volume_kind="tick_count", source="provider:verified-file-URL",
)
states = sample_multiscale_states(series, lags=(1, 2, 4, 8))
record = observation_carrier(series, states)
```

Use exactly the documented semantics of each provider. Volume from GetData Finance's index feeds is tick volume rather than stock-share volume; it must not be treated as comparable across venues.

### Exclusions and next gate

This adapter does not fabricate a 24/7 *price*. The continuous object is a UTC sequence of market observations from separate instruments with explicit gaps. It is deliberately not wired into the physical-model-specific GEO-X1 or GEO-X2 reconstruction entrypoints. Before that integration, a neutral tensor/trajectory protocol and prospective market-specific conformance campaign are required.

Qualifying a dynamical mechanism needs distinct tests for recurrence, composition order, change of representation, randomized controls, missing data, real-versus-synthetic behavior, forward-only validation and cross-instrument clock alignment. All statistical steps must be explicitly labeled *estimates*, not deterministic findings.
