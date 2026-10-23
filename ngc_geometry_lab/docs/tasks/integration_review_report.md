# Integration and scientific interpretation review

## Scope and verdict

Reviewed the integration at commit `62d83a0` against `docs/superpowers/specs/2026-10-22-geometric-qualification-design.md`, the preserved campaign `results/qualification_20261022`, and the core correction re-review. This review covers repository integration, campaign orchestration, blind analysis, reporting, source distinctions, failure visibility, and a focused installed-wheel probe. It does not repeat the core geometry/reference approval or review the concurrently developing CUDA checker.

**Scientific interpretation: approved for the stated finite computational qualification.** The observed source-backed computations support the report's limited constructive conclusions. I found no estimator access to held-out truth, use of verification counts in fitting/prediction, claim of deriving the Born rule, physical Bell experiment claim, state compression claim, or recovery claim for the historical sealed 115-element artifact.

**Code-quality verdict at the reviewed commit: changes requested for one important failure-detection defect, with additional packaging and minor reporting/exception-classification corrections below.** These defects do not show that the saved 12/12 result is numerically wrong: the saved evidence has finite values and consistent hashes. They concern whether the qualification machinery reliably rejects future bad outputs and whether its distributed source is complete. Corrections made after this review's snapshot require focused verification; this report does not automatically approve those later changes.

## Findings

### Important: NaN comparisons can disappear from the dual-lane qualification maxima

`experiments.py`, function `dual_lane`, accumulates errors with `max(previous, error)`. Python's `max(0.0, float('nan'))` returns `0.0`, so a nonfinite comparison can leave the summary looking successful. The same accumulation idiom appears in single-qubit and joint-system experiments and should be considered when fixing this failure class.

**Reproduction:** patch `repository.dual_lane_apply` with a wrapper that calls the original adapter and replaces the returned state with NaN on every twentieth invocation, the final gate of each circuit. Run only `experiments.dual_lane(20261022)`. There are 1,440 applications and **72 nonfinite comparison rows**, but the returned summary reports maximum state/probability/norm errors of `6.684427777288334e-16`, `8.881784197001252e-16`, and `2.6645352591003757e-15`. The frozen dual-lane gate predicate evaluates to **True**.

The circuit-boundary injection avoids a subsequent input validation catching the damaged state. This is a focused fault-injection test of the harness, not evidence that the actual pinned backend produces NaN. When no output directory is requested, per-case tables are not included in the returned scientific result, so their NaNs cannot be caught by final result serialization. When output is requested, CSV serialization rejects NaN outside the stage exception handler, aborting publication rather than preserving a properly classified failed stage.

**Requested correction:** enforce finite candidate outputs and comparison errors before reduction, and validate returned stage evidence inside the exception-capture boundary. A regression should inject a nonfinite final circuit output and require explicit failure, with failed-stage evidence retained when output is enabled. Do not merely change the displayed maximum or omit damaged rows.

### Packaging: wheel omits the CUDA header required by its included source

At the reviewed commit, `pyproject.toml` package-data patterns include `.cu` but not `.h`. A clean wheel built with `pip wheel --no-build-isolation --no-deps --no-index` contains `ngc_rcs_geometric.cu`, whose first line includes `ngc_rcs_api.h`, but contains **no `.h` members**. The source header is present in the checkout.

This does not break the reviewed CPU campaign: its 41-file verifier deliberately covers the MAPEOGEO and NGC real source manifests, and those installed files all verify. It does make the packaged CUDA source incomplete. Add the header pattern and verify wheel contents together with the separate CUDA work. This finding evaluates distribution completeness, not native CUDA execution.

### Minor: readout selection's temporal claim is stronger than its implementation order

`readout_selection` computes held-out scores within the candidate loop, then assigns `winner = min(scores, key=scores.get)`, but returns `selection_frozen_before_heldout_scoring=True`.

The winner depends exclusively on calibration scores, so I found **no statistical selection leakage**. Nevertheless, the Boolean and report state a literal ordering that the code does not implement. Select/freeze the winner after calibration scoring and before held-out scoring, preserving the RNG draws, candidate definitions, and gate thresholds.

### Minor: known upstream assertion exemption is broader than the known defect

`upstream_baselines` classifies any `AssertionError` from the known test name as `known_bad_expectation`. The test has both a legitimate earlier assertion (`assert not exact.exact_equal`, line 8) and the documented incorrect assertion (`assert not w.equivalent_for_work`, line 13). The exemption does not distinguish them or verify the originating file/frame.

A focused probe wrapped `runpy.run_path` to replace only that returned test callable with one raising a different `AssertionError`. The runner still reported `known_bad_test_expectations=1`, `unexpected_failures=0`. Pin the exemption to the documented failure site/signature so a different defect cannot be excused. The actual saved failure is the documented incorrect expectation; the existing 23-pass/1-known-failure evidence is honest.

## Evidence supporting compliance

- **Source versus fixture:** actual package-relative pinned MAPEOGEO modules execute composition, projection/inverse/observability checks and closure multiplication. The closure's fresh integer generators, word convention, independent product checks, and historical-artifact disclaimer are explicit. The NGC adapter executes the pinned real dual-lane backend. The report distinguishes CPU execution from source-only CUDA and retained state-storage cost from compression.
- **Blind reconstruction:** `generate_dataset` uses the independent complex reference and returns separate observation/truth objects. `analyze_dataset` has a strict case schema and calibrates only from the calibration block. Estimation and predictions use no truth object. Verification is evaluated only after prediction. A focused probe replaced both selected cases' verification counts with `[65536,0,0,0]`: detector fit, estimated states, and predicted probabilities each changed by exactly **0.0**. This checks verification-data independence, not physical instrument validity.
- **Joint systems and Bell language:** the code retains all nine correlation coordinates in addition to local vectors, reconstructs the joint density matrix, checks local rotations in explicit tensor order, enumerates all 16 deterministic assignments, and contrasts equal marginals with different joint probabilities. It labels CHSH as a computed model prediction and rejects the positive-tetrahedral-table/non-PSD control. The report does not promote a centralized calculation into a local physical realization.
- **Frozen criteria:** the implemented thresholds and actual sample counts agree with the design for this campaign. The finite-shot mean error threshold is explicitly an engineering criterion for synthetic observations. Gate configuration is duplicated in several experiment literals, which merits care in future changes, but no current mismatch was found.
- **Ordinary failed-stage handling:** using the saved valid stage outputs as stubs, I injected `RuntimeError('review-injected-source-failure')` in the source-verification stage. Campaign output had `qualified=False`, retained the error in `stage_errors`, wrote `results.json` and the exception file, and rendered `Result: FAIL`. This avoided rerunning unchanged scientific stages and establishes that ordinary exceptions are not silently converted into success.
- **Evidence consistency:** every file listed in the saved manifest matched its SHA-256; no mismatch was found. Regenerating Markdown from the saved result reproduced `REPORT.md` exactly.
- **Installed CPU packaging:** a clean archive of commit `62d83a0` was built into a wheel in `/tmp/ngc-review-ezlc9maq`, extracted, and imported from outside the repository. `verify_sources()` returned 41 verified files with no mismatches. Selected installed upstream baselines returned 24 executed, 23 passed, 1 known failure, and 0 unexpected failures. This was a focused wheel/import probe, not a fresh full campaign or archive-replay certification.

## Declined to judge / outstanding delivery checks

- Native CUDA compilation, GPU execution, physical parallelism, and hardware speedup: unavailable here and outside this review. The optional CUDA checker was still being implemented.
- The final distribution archive, final documentation, extracted-archive full test/campaign replay, and cross-run byte equality: these were still delivery work, not evidence supplied by this review. The design's reproducibility delivery gate remains subject to those checks.
- Independent external verification of Git-hosted source URLs or historical sealed-artifact availability: source audit/provenance is accepted within its documented scope; I verified bundled bytes and code usage, not a fresh remote history investigation.
- Physical validity of the measurement law, detector stationarity, experimental counts, causality, physical Bell violation, or quantum advantage: the campaign deliberately does not establish these.
- New proof of the geometry/reference mathematics already reviewed, arbitrary-platform numerical stability, unrestricted ill-conditioned SPD feasibility, or arbitrary adversarial input certification: no such approval is implied.

No full-suite rerun was performed. No project source or preserved evidence was edited by this reviewer; only this review report was added.
