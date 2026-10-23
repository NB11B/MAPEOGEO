# Optional native CUDA qualification

**Current native status: NOT_RUN.** The current environment has no available `nvcc` or `nvidia-smi` command. CPU boundary tests and the environment probe do not count as a GPU test. The CPU campaign does not silently invoke or substitute for this optional runner.

## Build on a CUDA host

Run these commands from the extracted project root on a host with the NVIDIA driver, CUDA toolkit, and a usable CUDA device. The original source and header remain unchanged.

```bash
mkdir -p build
nvcc -O2 -std=c++14 -Xcompiler=-fPIC -shared \
  ngc_geometry_lab/_vendor/ngc_cuda_2/cuda/ngc_rcs_geometric.cu \
  -I ngc_geometry_lab/_vendor/ngc_cuda_2/cuda \
  -o build/libngc_rcs_geometric.so
python -m ngc_geometry_lab.cuda_check \
  --library build/libngc_rcs_geometric.so \
  --out cuda-native-result.json --seed 20261022 --phase-bins 48
```

Use a new result filename for each run. Result files are opened with exclusive creation; an existing file is never replaced. Missing library/device, ABI errors, API errors, and numerical mismatches return a nonzero exit code. Loading a caller-supplied shared library executes native code, so use your own build from the supplied source.

For inventory without running kernels:

```bash
python -m ngc_geometry_lab.cuda_check --probe --out cuda-probe-new.json
```

Probe mode records command paths, exit codes, bounded command output, and pinned source hashes. It always reports `status: NOT_RUN` and `native_execution: NOT_RUN`. Probe exit zero means its diagnostic report was written, regardless of CUDA availability. It does not demonstrate that a compiled kernel works. A qualification invocation without a usable library/device reports `NOT_RUN` and exits 2.

## What the native run checks

The runner loads the simple C ABI directly through `ctypes`: diagnostic, create/free/reset, RX/RZ/CZ, phase resolution, probabilities, and real/imaginary statevector getters. Handles use ablation mode zero and are freed in `finally` blocks. Phase resolution is set explicitly. Every API return code is checked. The source probability getter synchronizes its stream and is called before retrieving the statevector.

Five registers, with 1 through 5 qubits, execute 24 seeded gates each: **120 gates** total, containing 48 RX, 40 RZ, and 32 CZ gates. Single-qubit registers use RX in place of CZ. Each reset and every resulting state/probability vector is checked, giving 125 observations. Source CUDA qubit `q` denotes the least-significant bit; the independent complex reference receives target `n-1-q`. Arrays retain their ordinary numeric basis-index order.

The exposed primary `F+` state and probabilities are compared directly against the independently implemented complex reference in `reference.py`, with maximum absolute tolerance `1e-10`. The complementary `F-` core is not exposed by these getters and is outside this bounded qualification. Sampling, profiling, performance, memory scaling, and speedup are outside this check.

### Quantized numerical equivalence

The original CUDA source normalizes each RX/RZ angle with `fmod` into `[0,2*pi)`, rounds `bins * (normalized_angle/(2*pi))` using C++ round-half-away-from-zero, applies modulo bins, and uses the resulting positive angle. The runner duplicates only that gate-parameter quantization for its expected quantized reference. Python's ties-to-even `round` is not used. Intermediate floating-point normalization can place a mathematical tie just below the tie; for example, `-pi/8` at eight bins falls into bin seven under the source calculation. Exact representable normalization ties and near-boundary cases are covered in CPU tests.

All wrapper entry points accept phase-bin counts from 1 through **`2**30`**, inclusive. This is a host-derived safety bound for the unchanged source's signed-integer expression `((k % n_bins) + n_bins) % n_bins`: its intermediate sum can reach `2*n_bins-1`, which must fit a 32-bit signed `int`. Larger counts are rejected before loading a library or creating an output file. An independent host UBSan review reproduced overflow at `2**31-1` bins; that finding is source/arithmetic evidence, not a CUDA device run. The wrapper avoids the unsafe range without modifying the pinned source.

`quantized_state_max_abs_error` and `quantized_probability_max_abs_error` determine native numerical equivalence. A mismatch reports `FAIL` and stops after preserving the failing step, before computing continuous-target fidelity or norms. If corrupt but finite amplitudes overflow the comparison metrics, their error field is `null`, `comparison_metrics_finite` is false, and a JSON-safe failure reason is retained. Each per-step record includes the gate, original angle, quantized angle, register size, and errors. Continuous approximation fields are present only after a successful quantized comparison and finite approximation-metric validation.

### Continuous-target approximation

A second independent-reference trajectory uses the **original continuous angles**. The JSON separately records its fidelity, phase-invariant state distance, and probability difference relative to native output. Angle wrapping by `2*pi` can change a global statevector sign, so this comparison uses phase-invariant distance rather than treating a global phase as an approximation failure. Fidelity is `abs(vdot(continuous, native))**2`, and distance is `sqrt(max(0, norm(native)**2 + norm(continuous)**2 - 2*abs(overlap)))`.

`PASS` means equivalence to the phase-quantized model. It does not mean equivalence to the original continuous target; inspect `continuous_approximation` and the per-step records for that distinction. No continuous-target accuracy threshold is asserted.

## Provenance and limits

Before qualification, the runner checks the local source/header SHA-256 against pinned commit `e825ade2c033ffb9d83a4cd4f89252136443664b`:

| File | SHA-256 |
|---|---|
| `ngc_rcs_geometric.cu` | `e9ef40c34398eaeeb4d0a11f567495042b56b9855e233a6812c16b1d9c5515c4` |
| `ngc_rcs_api.h` | `bc62266586146096a14f70c5f0779fbf6e3928be0f8b4ba9a97b41db557267ce` |

It also records the loaded binary's SHA-256. That binary is a **caller-supplied build**; a binary hash and matching local source snapshot do not cryptographically establish which source generated it. Retain your compiler version and build command alongside the result when establishing build provenance. Original API code omits checks for some internal CUDA errors; getter outputs are therefore initialized to NaNs, validated for finiteness, and checked numerically, but this runner does not repair the original kernel implementation.

## CPU boundary tests

```bash
python -W error -m unittest discover -s tests -p test_cuda_check.py -v
```

These tests exercise phase quantization (including immediately-below-half-bin floating boundaries and the safe source integer bound), analytic LSB basis-index mapping, invalid arguments, source hashes, missing-library status, probe semantics, exclusive result creation, and CLI errors. A CPU-only mocked API injects huge finite corrupt amplitudes to verify failure-record serialization and handle cleanup; it provides no hardware evidence. The 14 tests do not load a CUDA library or run a kernel. Native execution remains `NOT_RUN` until the hardware command above succeeds on a CUDA host.
