# External count-data protocol

## Purpose and boundary

Use the same calibrated prediction pipeline with independently obtained observations. The analyzer tests a declared tetrahedral-state/instrument model. A fit or accurate prediction is evidence about that model's adequacy for these observations; it is not sufficient by itself to choose a unique ontology.

The instrument has four mutually exclusive outcomes. Known calibration preparations determine a fixed 4-by-4 column-stochastic response after an ideal tetrahedral measurement. State axes, preparation coordinates, and operation conventions must be established independently. The present fit does not identify unknown measurement axes or general nonlinear detector response.

## Acquisition sequence

1. Record the instrument, outcome-label order, preparation definitions, operational axes, angle convention, timestamps, acquisition window, and how losses and exclusions are handled. The four outcome directions are (+++), (+--), (-+-), (--+), divided by sqrt(3).
2. Acquire at least four affinely independent calibration preparations. The delivered synthetic campaign uses 24. Record all four integer counts for each. Additional independent settings permit residual checks; repeated copies of one setting do not add rank.
3. Fit the response once, then freeze it. Reserve preparation settings and operation sequences for prediction. Randomizing acquisition order or interleaving known monitor settings can reveal drift; drift requires a revised model rather than a hidden refit on held-out records.
4. For each held-out preparation, acquire a four-outcome count record. Give the estimator only this record and the frozen calibration.
5. Reprepare an identical ensemble, apply the declared operation sequence, and acquire verification counts. Do not interpret this as measuring the same systems after their initial destructive measurement. Record any departure from identical preparation.
6. Score all predeclared cases, including poor predictions. Preserve counts, calibration, exclusions, raw estimates, corrections, and the code/configuration versions.

The detector model assumes the four recorded outcomes exhaust the modeled ensemble. If a separate no-detection event exists, document a justified conditioning scheme or extend the outcome model. Do not silently discard losses and then interpret the result as unconditional statistics.

## JSON schema

The root object has exactly `schema`, `provenance`, `calibration`, and `cases`.

```json
{
  "schema": "ngc_geometry_lab.observations.v1",
  "provenance": {
    "kind": "experimental",
    "description": "Instrument, preparation and acquisition description",
    "metadata": {
      "instrument_id": "your instrument identifier",
      "fresh_ensemble_for_verification": true
    }
  },
  "calibration": {
    "states": [
      [0.8, 0.0, 0.0],
      [0.0, 0.8, 0.0],
      [0.0, 0.0, 0.8],
      [0.0, 0.0, 0.0]
    ],
    "counts": [
      [365, 365, 135, 135],
      [365, 135, 365, 135],
      [365, 135, 135, 365],
      [250, 250, 250, 250]
    ]
  },
  "cases": [
    {
      "id": "preparation-001",
      "counts": [365, 135, 135, 365],
      "operations": [{"axis": [1.0, 0.0, 0.0], "angle": 1.5707963267948966}],
      "verification_counts": [135, 365, 135, 365]
    }
  ]
}
```

**These numeric records are illustrative, not collected measurements.** Replace them with complete measured counts before labeling your dataset experimental. For a generated executable example that is already labeled correctly, use the `generate` command. Do not use the illustrative integer approximation as a precision calibration benchmark.

### Field meanings

| Field | Meaning |
|---|---|
| `provenance.kind` | Exactly `synthetic` or `experimental`; the analyzer preserves this label, it does not authenticate provenance |
| `provenance.description` | Nonempty account of the data source |
| `provenance.metadata` | Optional instrument/preparation/acquisition metadata |
| `calibration.states` | Known real three-vectors of norm at most one |
| `calibration.counts` | One four-integer count vector per known preparation |
| `cases[].id` | Unique nonempty identifier |
| `cases[].counts` | Initial four-outcome counts from the unknown preparation |
| `cases[].operations` | Ordered active rotations; axis normalized by the code, angle in radians |
| `cases[].verification_counts` | Counts on fresh identical preparations after the operations |

Every count vector must have a positive total at most 2**53. Boolean values, fractional counts, NaN/infinity, negative counts, duplicate JSON keys, and embedded held-out truth are rejected. A nonnegative four-outcome frequency record can still yield a nonphysical linear estimate after inversion; the raw estimate is retained and the reported physical estimate is explicitly radially projected.

## Run and interpret

```bash
python -m ngc_geometry_lab analyze --input measured_counts.json --out measured_analysis.json
```

The output contains calibration rank/condition diagnostics, residual fit error, the fitted response matrix, each raw and corrected estimate, each prediction, and its TV distance from verification frequencies. The current finite-shot campaign's mean-error threshold is an engineering gate for known synthetic truth. The external analyzer does not manufacture a truth error, statistical significance or physical discovery from verification counts alone.

For comparison with another mechanism, define its forward predictions and instrument coupling before looking at verification outcomes. Train only on its permitted calibration data, freeze its parameters, and compare predictions on the same retained records. If models make exactly the same predictions for every available observation, these data do not distinguish them.

## Joint-system and Bell scope

The delivered joint-system campaign is computational. A physical Bell study requires independently controlled settings, a specified causal/locality model, complete event accounting, and an appropriate finite-sample statistical analysis. The four-channel single-system analyzer is not a physical Bell-test analysis program. Its computed CHSH control does not assert otherwise.
