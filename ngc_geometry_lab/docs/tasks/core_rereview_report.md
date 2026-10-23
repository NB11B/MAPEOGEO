# Scoped core correction re-review

## Verdict

**Approved: both findings from `core_review_report.md` are resolved. No new important or critical issue found in the corrections.** This verdict covers only the metric-classification and exact-count-validation changes, their regression tests, and directly affected controls. It is not approval of the still-developing campaign or other files.

## P2: metric boundary classification — resolved

`infer_metric` now reports `unresolved_feasibility` when a unique trace-normalized candidate has an eigenvalue within `tol` of zero, including the previously misclassified strictly positive example. It retains definitive no-SPD rejection for a negative eigenvalue separated from zero. The near-zero-trace branch likewise checks a separated mixed-sign spectrum before rejecting the unique scalar family; a small trace by itself no longer becomes an infeasibility certificate.

The added exact-dyadic projector regression independently verifies idempotency, the known SPD witness, the one-dimensional solution space, default-tolerance unresolved classification, and tighter-tolerance successful recovery. The separate semidefinite-boundary regression verifies conservative handling at zero. Existing Lorentz-indefinite and dilation controls still reject, and the ordinary conjugated cubic family still recovers its metric.

This is an intentional numerical clarification of the original task brief's statement that nullity-one classification is definitive: at an unresolved floating-point eigenvalue boundary the implementation now avoids claiming a proof of nonexistence. The function docstring states this behavior.

## P3: exact count validation — resolved

`validate_counts` preserves supplied values in an object array, rejects boolean values before numeric conversion, converts validated integral values to Python integers, and checks the exact Python-integer total before constructing `np.int64` output. All accepted values and totals fit the specified `2**53` range, hence also fit `int64`.

The new tests reject the original `2**53+1` value, the `2**53+1` total split across channels, a very large Python integer, and mixed boolean/integer input. They also verify that the valid exact boundary `2**53` is preserved. Ordinary count-validation and exact detector-calibration controls still pass.

## Verification

Inspected the scoped source/test diff and the preserved metric red/green and count-precision red evidence. Independently ran this focused command from the repository root:

```sh
PYTHONPATH=tests python -W error -m unittest -v test_geometry.MetricTests.test_ill_conditioned_spd_metric_is_unresolved_at_default_tolerance test_geometry.MetricTests.test_unique_semidefinite_boundary_is_numerically_unresolved test_geometry.MetricTests.test_unique_indefinite_metric_is_definitively_rejected test_geometry.MetricTests.test_inconsistent_dilation_has_no_metric test_geometry.MetricTests.test_non_euclidean_metric_recovered_from_conjugated_cubic_family test_observations.ObservationTests.test_large_counts_are_rejected_before_float_rounding test_observations.ObservationTests.test_mixed_boolean_counts_are_rejected test_observations.ObservationTests.test_counts_validation test_observations.ObservationTests.test_calibration_recovers_known_detector_from_counts
```

Result: **9 tests passed**, exit status 0, with warnings promoted to errors. No full-suite rerun and no unrelated probes were performed. Only this report was written during re-review.
