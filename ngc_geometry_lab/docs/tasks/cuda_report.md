# Optional native CUDA runner report

**Native status: NOT_RUN. No CUDA kernel was compiled or executed.** The actual probe records no available `nvcc` or `nvidia-smi` executable. Fourteen CPU boundary tests pass with warnings promoted to errors after independent-review corrections; these are not hardware evidence.

Implemented `python -m ngc_geometry_lab.cuda_check` with mutually exclusive `--library` and `--probe` modes, required new `--out`, and validated seed/phase-bin options. The native path reads the pinned header's exact simple ctypes signatures, checks device diagnostic return, sets mode zero and phase resolution, frees handles, and compares exposed primary states/probabilities after 120 gates across 1–5 qubits plus resets. CUDA LSB targets map to big-endian reference target `n-1-q`. Quantized equivalence and continuous-target approximation are reported separately. Source/header hashes are checked; loaded binary hash is recorded with an explicit caller-supplied-build provenance limitation. No CPU candidate fallback exists. `docs/CUDA_CHECK.md` provides direct original-source nvcc and execution commands.

## Preserved development evidence

Exact commands, from project root:

1. `python -W error -m unittest discover -s tests -p test_cuda_check.py -v > evidence/development/cuda_red.log 2>&1` — exit 1; nine tests, 35 intentional missing-stub errors, before production implementation.
2. Initial implementation run used the same test command, temporarily writing `cuda_green.log`; exit 1 with one assertion failure. Its output was preserved as `cuda_quantization_float_boundary.log`. Investigation showed that floating-point normalization of negative `-pi/8` at eight bins lands just below the mathematical half-bin, so source-style rounding chooses bin seven. The incorrect mathematical-tie fixture was corrected, exact four-bin positive/negative ties were added, and the actual eight-bin floating boundary is now explicitly tested. Quantization implementation was not changed to force a mathematical tie.
3. `python -W error -m unittest discover -s tests -p test_cuda_check.py -v > evidence/development/cuda_green.log 2>&1` — exit 0; **nine tests passed**.
4. `python -m ngc_geometry_lab.cuda_check --probe --out evidence/development/cuda_probe.json` — exit 0; status `NOT_RUN`, native execution `NOT_RUN`, gate count zero, both tool commands unavailable, source/header hashes match.
5. `python -m ngc_geometry_lab.cuda_check --library /tmp/nonexistent-ngc-qualification.so --out evidence/development/cuda_absent_library.json` — exit 2; status `NOT_RUN`, native execution `NOT_RUN`, gate count zero, missing-library reason recorded.

The CPU scope covers positive/negative/tie/wrap quantization, 1–5-qubit analytic basis-index mapping, input/index/C-integer boundaries, absent library, probe-only semantics, source snapshot hashes, argument errors, and output no-overwrite. No broader suite/campaign was rerun for this bounded addition. The native ABI/launch path is implemented but remains unverified on hardware, and no binary-source-origin proof or performance claim is made.

## Exact next hardware command

After the original-source build documented in `docs/CUDA_CHECK.md`:

```bash
python -m ngc_geometry_lab.cuda_check --library build/libngc_rcs_geometric.so --out cuda-native-result.json --seed 20261022 --phase-bins 48
```

Only assigned CUDA runner/test/docs/evidence files were changed. Main CLI, campaign, upstream CUDA source, and root report were untouched.

## Focused independent-review corrections

Root independently reproduced a rounding defect immediately below half-bin boundaries: for four bins and `angle=nextafter(pi/4,0)`, the scaled value is `0.49999999999999994`. Adding `.5` first rounds the sum to `1.0`, so `floor(x+.5)` disagreed with actual C/C++ `round(x)`. Added a regression for both four and eight bins before modifying code. The implementation now computes `lower=floor(x)` and increments only when `x-lower >= .5`; this avoids addition-induced rounding and retains the source normalization and previously tested negative wrapped behavior.

Root also identified that huge finite corrupt native amplitudes reached continuous fidelity/norm calculation before the quantized mismatch branch, causing overflow and invalid JSON evidence. Added a CPU-only mocked API fault test before the fix, injecting both real `1e308` amplitudes and finite complex amplitudes with `1.7e308` real/imaginary components. The test requires `FAIL`, one preserved record, no premature continuous fidelity, successful strict JSON serialization, and handle cleanup. This is protocol fault injection, not a native device test.

The native loop now records and validates comparison metrics first. Finite mismatches stop before approximation calculations. Overflowed comparison metrics are represented with `null` plus `comparison_metrics_finite: false` and an explicit failure reason. Continuous approximation metrics are also checked before insertion, preventing nonfinite values from entering strict result JSON.

Exact focused verification commands:

1. `python -W error -m unittest discover -s tests -p test_cuda_check.py -v > evidence/development/cuda_review_boundaries_red.log 2>&1` — exit 1; 11 tests, two assertion failures and one overflow error, reproducing both defects before production changes.
2. `python -W error -m unittest discover -s tests -p test_cuda_check.py -v > evidence/development/cuda_review_boundaries_green.log 2>&1` — exit 0; **11 tests passed**.

No full suite was rerun. No CUDA compilation or execution occurred; native status remains `NOT_RUN`.

## Source signed-integer safety bound

Independent integration review reproduced signed overflow with a host C++/UBSan test at `phase_bins=2**31-1`, `theta=pi`, in the original source expression `((k % n_bins) + n_bins) % n_bins`. Since `k % n_bins` is between zero and `n_bins-1`, its addition can reach `2*n_bins-1`; bounding bins to `2**30` keeps that sum within a 32-bit signed integer. The initial wrapper's C-int upper bound was therefore insufficient. The vendor source remains unchanged.

Added three regression tests before the fix, separately verifying acceptance of `2**30` and rejection of `2**30+1` by `quantize_angle`, `run_check`, and CLI `main`. The CLI rejects unsafe counts before output-file creation. All three production validation sites now use the shared `_MAX_PHASE_BINS=2**30` bound.

Exact focused commands:

1. `python -W error -m unittest discover -s tests -p test_cuda_check.py -v > evidence/development/cuda_phase_bins_red.log 2>&1` — exit 1; 14 tests, exactly three new regression assertion failures.
2. `python -W error -m unittest discover -s tests -p test_cuda_check.py -v > evidence/development/cuda_phase_bins_green.log 2>&1` — exit 0; **14 tests passed**.

Only the CUDA suite was run. The independent host arithmetic finding and these CPU argument tests do not constitute native CUDA execution; status remains `NOT_RUN`.
