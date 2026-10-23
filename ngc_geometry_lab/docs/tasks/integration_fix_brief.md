# Integration review correction wave

Own only `ngc_geometry_lab/repository.py`, `ngc_geometry_lab/experiments.py`, `ngc_geometry_lab/campaign.py`, `tests/test_campaign_failures.py`, optional regression additions to `tests/test_repository.py`, `docs/tasks/integration_fix_report.md`, and `evidence/development/integration_fix_*`. Work at `/workspace/scratch/f4c8fe3fa7f4/ngc_geometry_lab`. No subagents or commits. Do not touch README, reporting, CUDA runner or packaging.

Read docs/tasks/integration_review_report.md. User requires failures independently checked and preserved. Fix actual failure detection, without changing thresholds, data, RNG streams, or nominal scientific results.

## Important: NaN reductions hide failure

Reviewer patched repository.dual_lane_apply to call original then replace returned output with NaN on every20th call (last gate in each circuit). dual_lane experiment returned1440 applications,72 NaN comparison rows, but summary max errors unchanged below tolerance because max(previous,nan) returns previous. A no-output campaign could report qualifiedTrue. Saved output failed later during serialization outside stage handling.

Tests first: reproduce a final-gate nonfinite result and require explicit failed experiment/gate, both memory-only and saved evidence. Add a focused direct adapter postcondition test by replacing underlying upstream return with NaN/wrongshape. This is an intentional fault-injection test, not a substitute for true algorithm tests.

Fix with explicit finite output/error validation before max reductions (single, joint and dual comparisons), and strict source adapter postconditions. Also validate each stage's returned JSON payload inside the try/except before publishing it, so any nonfinite result becomes a recorded failed stage. Ensure corrupted output/metric cannot silently qualify; preserve failed checkpoint/exception/report. Audit finite-shot/readout metrics gates for NaN propagation; don't silently nan_to_num or clip errors away. Tests should directly cover NaN and infinity and original nominal behavior.

## Minor: known upstream failure exemption is too broad

upstream_baselines currently considers any AssertionError from the named test knownbad. Original unchanged file `tests/test_psmsl_work_equivalence_v1.py` has legitimate earlier assertion line8 and incorrect assertion line13. Limit the exemption to its exact pinned file/failure location plus expected exception signature, backed by existing independent semantic countercalculation. An unrelated assertion in the named function must count unexpected. Add regression; don't skip original test or alter vendor source.

## Already addressed by root

The header package-data *.h pattern is added. Readout winner assignment now occurs before any heldout scoring, preserving scores/RNG. Do not undo these changes. CPU scope string is now `not_run_cpu_only_campaign` for truthful portability.

Run only meaningful new regression tests and affected existing campaign/repository tests, preserve red/green logs. Return exact changes, regression outcomes, and nominal result comparison. Independent reviewer will recheck the correction wave.
