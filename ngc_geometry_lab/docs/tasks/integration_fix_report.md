# Integration failure-detection corrections

## Outcome

The reported nonfinite-value defect and overly broad upstream-failure exemption are corrected. The focused verification passed **35 tests with zero failures or errors**. The unchanged nominal experiment summaries, every returned evidence payload hash, and the selected upstream baseline results are identical before and after this correction.

A separate saved campaign with the reviewer's final-gate NaN injection now returns `qualified: false`, passes 11 of 12 gates, and records the dual-lane stage failure at qubits 1, circuit 0, step 20. It completes publication of its failure checkpoint, traceback, results, report, and manifest. The injected run is explicitly diagnostic evidence; it does not show that the pinned backend produces NaN in ordinary operation.

## Changes

- `repository.py` validates the actual backend's output shape, real numeric type, finiteness, and normalization before returning a complex state. It preserves the existing normalization tolerance and never renormalizes or replaces invalid values.
- `experiments.py` checks both candidate and reference values, matching shapes, and computed errors before the single-system, joint-system, and dual-lane maximum reductions. Errors include the experiment, case/circuit, step, and offending indices/values. The finite-shot evaluator checks its estimated states, predicted probabilities, verification metrics, detector comparison, and computed errors. Readout scores must be finite before choosing the calibration winner and before publishing held-out scores.
- `campaign.py` validates each stage's summary, tables, and auxiliary artifacts together inside the stage exception boundary. Rejected nonfinite values appear as explicitly tagged path/value diagnostics in the failed stage. Rejected returned payloads are retained in a clearly labeled `*_invalid_evidence.txt` file when saving. Failed stages roll back their pending normal CSV/JSON publication while preserving the error checkpoint and traceback; later stages continue.
- `tests/test_campaign_failures.py` adds focused fault injections and failure-publication regressions. `tests/test_repository.py` adds upstream-output postcondition checks. Existing analytic and independent-reference algorithm tests remain intact.

No campaign thresholds, sample counts, generator matrices, RNG streams, seed, vendor bytes, or fitted/predicted nominal values changed. The parent's earlier correction freezing the readout winner before held-out scoring remains in place.

## Exact upstream exception classification

The exemption now requires every one of the following:

1. MAPEOGEO's expected test name and exact package-relative file.
2. A terminal traceback frame in that same file and function, at line 13, with the exact assertion source `assert not w.equivalent_for_work`.
3. The exact `AssertionError` type with an empty argument tuple.
4. The pinned source SHA-256 `d6eca4324d88e344ea007bb4a80eab0088cadb9c1a482e5702311ecd11d0686c`, from commit `ac63dde9da6dca2c000aa53ee6ffb9365e2388a1`.
5. An independent integer matrix countercalculation verifying the supplied matrices do not commute globally but do agree after the supplied projection.

For the literal fixture, `AB=[[1,1],[0,2]]`, `BA=[[1,2],[0,2]]`, and both projected products equal `[[0,2]]`. The original unchanged baseline is still executed and still fails visibly at line 13. The earlier legitimate assertion at line 8 and a different assertion substituted under the same test name are both classified as unexpected failures. The ordinary baseline outcome remains **24 executed, 23 passed, 1 known incorrect expectation, 0 unexpected failures**.

## Red/green evidence

The tests were added before the implementation correction. The red run reproduced silent/nonclassified nonfinite outcomes, publication exceptions outside the stage boundary, permissive adapter returns, and the broad upstream exemption. Its 14 test methods produced 23 failing subtests and 16 error subtests; the nominal campaign and genuine pinned baseline control passed.

The green command covered the new failure regressions and the affected existing suites:

```bash
python -m unittest -v tests.test_campaign_failures tests.test_repository tests.test_campaign
```

The recorded run used `unittest.TextTestRunner` on those same three suites to save the full transcript. It ran 35 tests in 6.918 seconds: all passed. `git diff --check` also passed. The root agent is responsible for the final full suite, new nominal campaign, and extracted-archive replay; those are not claimed by this focused correction report.

Evidence under `evidence/development/`:

| File or directory | Purpose |
|---|---|
| `integration_fix_red.log` / `.json` | Preserved failing regression run before implementation |
| `integration_fix_green.log` / `.json` | Focused passing regression and existing-suite run |
| `integration_fix_nominal_before.json` | All five affected experiment summaries, eight evidence payload hashes, and upstream baseline results before correction |
| `integration_fix_nominal_after.json` | The same measurements after correction |
| `integration_fix_nominal_comparison.json` | Equality checks for every recorded section; all true |
| `integration_fix_verification.json` | Nominal equality and retained fault-injected campaign summary |
| `integration_fix_injected_nan_campaign/` | Complete saved campaign using the actual experiments and the final-gate diagnostic NaN injection |

The injected saved campaign rejects its first damaged state after exactly 20 adapter calls. Its checkpoint preserves this error:

```text
dual_lane qubits=1 circuit=0 step=20 state candidate: nonfinite values at [((0,), '(nan+0j)'), ((1,), '(nan+0j)')]
```

The regression suite additionally checks NaN and infinity in memory-only and saved-output runs, malformed summary/table/auxiliary data, single/joint final-rotation probabilities, finite-shot verification metrics, readout calibration scores, and invalid adapter return shapes/types/norms. Invalid values are neither clipped nor converted into plausible numeric results.
