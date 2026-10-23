# Release verification — 2026-10-22

## Result

The computational qualification is complete. All 124 package tests pass with warnings promoted to errors. A fresh saved campaign passes all 12 fixed gates. The same suite and campaign were executed from a clean extraction of the release candidate, outside the development directory and without an inherited PYTHONPATH. All 22 scientific output files, including results, calibration, observations, truth, per-case comparisons, checkpoints, and the generated report, are byte-identical to the release baseline.

Native CUDA execution and physical measurements remain **NOT_RUN**. The optional CUDA adapter has 14 passing CPU boundary tests; those are included within the 124 tests and are not counted as native kernel execution.

## Commands and evidence

| Verification | Result | Preserved evidence |
|---|---|---|
| `python -W error -m unittest discover -s tests -v` | 124 tests, no failures or errors | `evidence/development/full_suite_release.txt` |
| `python -W error -m ngc_geometry_lab run --seed 20261022 --out results/release_20261022` | 12/12 fixed gates | `evidence/development/campaign_release.txt`, full `results/release_20261022/` |
| Same test suite from extracted candidate | 124 tests, no failures or errors | `evidence/development/archive_replay_suite.txt` |
| Same campaign from extracted candidate | 12/12 fixed gates | `evidence/development/archive_replay_campaign.txt` |
| Independent archive member hashes | 252 project files verified in the tested candidate | `evidence/development/archive_replay.json` |
| Scientific output comparison | 22/22 files byte-identical | `evidence/development/archive_replay.json` |
| Campaign manifest checks | 22/22 files match in each of release and replay | `evidence/development/archive_replay.json` |
| Import provenance from extracted candidate | Resolves to the extracted package | `evidence/development/archive_replay_import.txt` |
| Final environment/source probe | NOT_RUN; 0 native gates; source/header hashes match | `evidence/development/cuda_release_probe.json` |

The numerical environment is Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, Linux x86-64. The dependency lock file records the exact NumPy and SciPy versions. Last-bit floating-point reproducibility on another platform is not promised; use the fixed absolute error gates and retain the generated environment record.

`manifest.json` itself is excluded from byte comparison because it intentionally records the run timestamp and environment. Each manifest's listed scientific file hashes was verified independently.

## Review and retained failures

Core, integration, packaging, and focused correction reviews are preserved in `docs/tasks/`. The final scoped integration review is approved with no remaining critical or important finding in its scope. Original development failures, the exact bad upstream assertion, a demonstrably failed nonfinite-output campaign, and all correction logs remain in the evidence tree.

The selected unchanged upstream baseline executes 24 functions: 23 pass, one known incorrect assertion remains visible, and no unexpected failures occur. The exemption requires the exact pinned file hash, function, line, assertion text, exception signature, and independent countercalculation. It does not suppress arbitrary assertions under that test name.

The first saved nominal campaign is preserved under `results/qualification_20261022/`. Its scientific values remain unchanged in the corrected release. Later differences in report wording and scope labels are documented; no threshold, RNG stream, seed, sample count, or vendor byte was altered to obtain a pass.

## Archive completion

The final archive adds this verification record, the replay evidence, and updated delivery documentation to the tested candidate. A final assembly check verifies that every executable Python/CUDA/header file, dependency/build configuration, and vendored source or manifest is byte-identical to the tested extraction. The check also verifies every final archive member against its included `ARCHIVE_MANIFEST.json`.

The final assembly receipt is delivered beside the archive. It contains the final archive SHA-256, final member count, tested-code identity check, and source commit. This receipt is external to the archive so that its archive checksum is not self-referential.

No remote repository was modified, pushed, merged, or published. The local work remains on branch `work/geometric-qualification`.
