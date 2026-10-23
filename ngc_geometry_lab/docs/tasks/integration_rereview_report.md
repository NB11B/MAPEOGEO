# Scoped integration correction and optional CUDA boundary re-review

## Verdict

**Approved within this review's scope.** The important nonfinite-error failure-detection finding, the overly broad upstream assertion exemption, and the readout temporal-claim mismatch from `integration_review_report.md` are resolved. The package-data header omission is corrected, with separate installed-package evidence. The optional CUDA runner's ABI mapping, reference target conversion, quantization, JSON-safe failure handling, and honest `NOT_RUN` boundary are approved by source inspection and CPU-only checks. A newly found signed-integer phase-bin boundary issue was corrected and independently rechecked.

No remaining critical or important finding was identified in these changes. This is not a native CUDA execution approval or final archive/release certification. The original review's approval of the limited scientific interpretation continues to apply; the corrections do not expand those claims.

## Integration corrections

### Nonfinite numerical evidence now fails explicitly

The repository adapter checks returned real-vector shape, real numeric dtype, finiteness, complex-state shape/finiteness, and normalization. It does not normalize damaged output into an apparent success.

Experiment comparisons validate candidate and reference values and their matching shapes before computing differences. They validate the differences before maximum reductions. Dual-lane norm errors, finite-shot errors, and readout scores are checked explicitly as well. The reproduced final-gate NaN failure can no longer disappear through Python `max` behavior.

Campaign stage handling now serializes the complete pending summary, tables, and auxiliary artifacts **inside** its exception boundary. Rejected evidence receives a failed-stage record; pending normal artifacts are rolled back; tagged nonfinite locations and a separately labeled diagnostic representation remain available. This fixes both memory-only false success and saved-output exceptions outside stage capture. The failure is reported rather than replaced with plausible numbers.

I independently ran the five `NonfiniteComparisonTests`, all three `KnownUpstreamFailureTests`, the adapter output-postcondition regression, and the two saved-output failure-publication regressions: **11 tests passed with warnings promoted to errors**. To avoid repeating a full unchanged campaign, I supplied the preserved nominal experiment results to the test helper's `nominal_campaign` fixture. The damaged target stages and publication logic remained real. This exercise covered final-gate NaN/infinity, single/joint final-operation probabilities, finite-shot/readout nonfinite metrics, malformed adapter outputs, saved failure checkpoints/reports, and nonfinite tables/auxiliary artifacts.

I also inspected the separately preserved actual fault-injected campaign. It returns `qualified=false`, passes 11 of 12 gates, and records the dual-lane failure at qubits 1, circuit 0, step 20. Every file in its manifest matched its SHA-256. The before/after nominal evidence JSON files compare equal directly, including all five affected experiment sections and upstream baseline results; this confirms the supplied comparison summary rather than merely trusting its `all_equal` flag. These checks are consistent with the implementer's 35-test focused green run.

### Known assertion suppression is narrowly pinned

The known incorrect expectation now requires the exact project, test name, pinned test-file path and SHA-256, terminal traceback function and line 13, assertion text, and exact empty-argument `AssertionError`, plus the independent integer countercalculation. The legitimate earlier assertion at line 8 remains unexpected, as does an unrelated substituted assertion under the same test name. Both regressions passed independently. The original baseline remains visible as 24 executed, 23 passed, 1 documented incorrect expectation, and 0 unexpected failures.

### Readout ordering and packaging

Calibration scores are now completed before `winner` is assigned. Held-out scoring starts only afterward, so the frozen-before-scoring statement is literal. The winner still uses calibration data only, and the preserved nominal before/after evidence is identical.

The package-data list now includes `_vendor/**/*.h`. I inspected the change and the separate `packaging_report.md` evidence showing a rebuilt installed wheel with the header present and matching CUDA source/header hashes. I did not repeat that independent wheel build. Final archive assembly remains the release owner's gate.

## Optional CUDA runner

### Source and ABI inspection

The ctypes signatures match the pinned header for create/free/reset, RX/RZ/CZ, phase resolution, state/probability getters, and device diagnostics. Handle/output pointers, integer arguments, double arguments, and diagnostic `size_t` fields are correctly mapped. No profiling-struct layout is assumed.

The source uses bit `q` as the least-significant-bit position. Mapping it to reference tensor target `n-1-q` preserves numeric basis-index order. RX/RZ signs match the reference's active unitary convention; CZ matches the diagonal controlled sign change. The probability getter is called before the state getter, supplying the source stream synchronization that the subsequent copy needs.

The runner checks the exposed primary F+ state; it does not claim access to the complementary F- state. The documentation states that limitation and separates quantized numerical equivalence from continuous-target approximation, physical parallelism, sampling, and performance.

### Rounding and newly corrected integer boundary

The Python quantizer follows the original `fmod`, nonnegative normalization, C++ round-half-away-from-zero, and bin modulo ordering. It compares the fractional part against one half rather than adding `0.5`, avoiding a floating-point near-tie rounding error. Tests distinguish mathematical ties from the actual normalized floating-point value, including negative-angle cases.

During this review I found that allowing phase bins through `2**31-1` was unsafe for the unchanged C++ expression `((k % n_bins) + n_bins) % n_bins`. A host-only fragment preserving that source arithmetic, compiled with `g++ -fsanitize=undefined -fno-sanitize-recover=undefined`, reports signed integer overflow for `n_bins=2147483647`, `theta=pi`: `2147483647 + 1073741824` cannot fit `int`. Full source fragment, flags, exit status 1, and UBSan output are preserved in `evidence/development/cuda_phase_bins_ubsan_review.log`. **This is host arithmetic evidence, not CUDA/GPU execution.**

The adapter now enforces a shared maximum of `2**30` in `quantize_angle`, `run_check`, and CLI validation. The largest modulo-plus-bin intermediate is then `2*bins-1 <= INT_MAX`. The source bytes remain unchanged. I independently ran the three new boundary regressions: each accepts the safe boundary and rejects the next integer; CLI rejection creates no output. All three passed under `-W error`.

### Failure evidence and execution boundary

Native getter buffers begin as NaN and are rejected if unwritten or nonfinite. Strict numerical mismatch and overflowed comparison metrics are handled before continuous fidelity/norm calculations. Invalid numeric fields are represented as `null` with an explicit finite-metrics flag and reason, so failed evidence remains valid JSON. Handles are freed through `finally`.

The diagnostic probe always reports `status=NOT_RUN`, `native_execution=NOT_RUN`, and zero gates. Missing library/device and unavailable ABI remain `NOT_RUN`, with nonzero qualification exit status; no CPU candidate substitutes for native kernels. Caller-supplied binary hashes are explicitly not treated as proof that a binary was built from the local pinned source.

Before the integer-bound correction, I independently ran all 11 existing CUDA boundary tests successfully under `-W error`; after the correction, I ran the three newly added boundary tests. The implementer's final 14-test CUDA log is also available. An initial reviewer invocation guessed three nonexistent test names and produced loader errors; the intended tests were immediately rerun by their actual names and all passed. Those loader errors were an invocation mistake, not a product failure.

## Remaining limits

- No CUDA compiler/device run, native ABI load, or GPU numerical qualification was performed here. Native execution remains **NOT_RUN**.
- CPU/source inspection cannot certify behavior of arbitrary caller-supplied native binaries or repair unchecked internal errors in the unchanged upstream implementation.
- The final full release suite, fresh nominal campaign, archive extraction/replay, rendered deliverables, and final packaged-file hashes are owned by the release task and are not certified by this scoped review.
- No new physical interpretation, Born-rule derivation, experimental Bell violation, source-origin identification, or computational speedup is established.

No full suite or full campaign was rerun by this reviewer during re-review. Only the requested review report and host UBSan evidence were written; production source corrections were made by their assigned owners.
