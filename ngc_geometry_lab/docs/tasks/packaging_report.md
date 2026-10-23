# Standalone packaging verification

## Final result

**PASS for standalone CPU wheel packaging and installed command-line workflow.** The original candidate omitted the CUDA header; after the parent added the header package-data pattern, a fresh build/install included every vendored file and both CUDA source hashes matched. CUDA native execution is still **NOT_RUN**, with zero native gates; this check establishes source inclusion and diagnostic-hook presence only.

## Scope and environment

Read-only packaging checks used a copied source tree and fresh build, extraction, and install locations under `/tmp/ngc-packaging-pa_p32zn`. Production files were not modified. All external execution happened with working directory `/tmp/ngc-packaging-pa_p32zn`, outside the repository. The installation was a normal wheel installation into an isolated target directory, not an editable install; existing runtime NumPy/SciPy were reused with `--no-deps`. No network access, dependency download, upstream test rerun, or full-suite rerun was used.

Python 3.12.14; pip 26.2.1; setuptools 84.0.0; wheel 0.48.0; NumPy 2.3.5; SciPy 1.17.0. The `build` frontend was absent, so pip's PEP 517 wheel command was used. Exact inventory: `evidence/development/packaging_environment.json`.

## Original candidate: reproducible missing-header finding

The initial wheel built and installed successfully, and all installed CPU source adapters passed integrity verification. Archive inspection found one missing vendored file:

`ngc_geometry_lab/_vendor/ngc_cuda_2/cuda/ngc_rcs_api.h`

The original package-data patterns included `*.cu` but did not include `*.h`. The CUDA source and its provenance manifest were present while its required header was missing. Archive inventory is preserved in `packaging_contents.json`. The installed CUDA probe demonstrated the consequence independently: CUDA source SHA-256 matched its pinned value, the header hash was `null`, and `source_snapshot.matches_pinned` was `false` (`packaging_cuda_before.json`).

This failure was not caught by CPU `verify_sources()`, whose three manifest groups exclude the CUDA snapshot. It reported 41 verified CPU/audit files, zero mismatches (MAPEOGEO 15, MAPEOGEO audit 4, NGC real 22). Direct installed adapter execution via `connected_operator_demo()` returned `qualified=true`. Exact imported paths and outcomes are in `packaging_verify.json`.

## Build and installation commands

After copying the project to `/tmp/ngc-packaging-pa_p32zn/source` with `shutil.copytree` (excluding git metadata, bytecode caches, prior evidence, and build products), these commands ran from `/tmp/ngc-packaging-pa_p32zn`:

```bash
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir /tmp/ngc-packaging-pa_p32zn/wheels /tmp/ngc-packaging-pa_p32zn/source
python -m pip install --no-index --no-deps --target /tmp/ngc-packaging-pa_p32zn/installed /tmp/ngc-packaging-pa_p32zn/wheels/ngc_geometry_lab-0.1.0-py3-none-any.whl
```

Both exited 0. Logs: `packaging_build.txt`, `packaging_install.txt`. The initial wheel was 113,885 bytes with SHA-256 `481b6580fa476ac6a0e530678863d24c97cfd1dc87768e804bb251f2f20f25fd`. pip emitted only its normal root-user warning while installing to the explicit temporary target.

Installed verification used `PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed`, imported `ngc_geometry_lab.repository`, asserted package paths were below that installed target, called `verify_sources()`, and called `connected_operator_demo()`. None of the adapter module paths resolved to the checkout. The complete result and Python path are preserved in `packaging_verify.json`.

## Installed CLI smoke test

From `/tmp/ngc-packaging-pa_p32zn`, using the installed console entry point and only the installed target in `PYTHONPATH`:

```bash
PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed /tmp/ngc-packaging-pa_p32zn/installed/bin/ngc-geometry-lab generate --seed 20261022 --cases 8 --shots 65536 --out /tmp/ngc-packaging-pa_p32zn/observations.json --truth-out /tmp/ngc-packaging-pa_p32zn/truth.json
PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed /tmp/ngc-packaging-pa_p32zn/installed/bin/ngc-geometry-lab analyze --input /tmp/ngc-packaging-pa_p32zn/observations.json --out /tmp/ngc-packaging-pa_p32zn/analysis.json
PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed python -m ngc_geometry_lab.cuda_check --probe --out /tmp/ngc-packaging-pa_p32zn/cuda_probe.json
```

Each exited 0. Generation produced eight explicitly synthetic observations with separate evaluator truth. Analysis processed eight synthetic records with mean verification total variation **0.004623** (printed precision). Evidence includes the command output and copied observations, truth, and analysis JSON under the `packaging_` prefix. The optional CUDA module was present and its diagnostic CLI worked. CUDA execution remained **NOT_RUN**, with zero gates, because neither `nvcc` nor `nvidia-smi` was available. The diagnostic command never claimed native GPU execution.

## Header fix regression verification

The parent added `"_vendor/**/*.h"` to package data. A second fresh copied source tree, `/tmp/ngc-packaging-pa_p32zn/source_fixed`, was built into `wheels_fixed` and installed into `installed_fixed` with the same offline flags:

```bash
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir /tmp/ngc-packaging-pa_p32zn/wheels_fixed /tmp/ngc-packaging-pa_p32zn/source_fixed
python -m pip install --no-index --no-deps --target /tmp/ngc-packaging-pa_p32zn/installed_fixed /tmp/ngc-packaging-pa_p32zn/wheels_fixed/ngc_geometry_lab-0.1.0-py3-none-any.whl
```

Both exited **0**. Fixed wheel size: **115,298 bytes**. SHA-256: `c3fd5ef36db0b1e5b0eac78a018717fc02661a2efad02c648637a600bb50e81c`. Logs: `packaging_build_fixed.txt` and `packaging_install_fixed.txt`.

The fixed archive was extracted to `/tmp/ngc-packaging-pa_p32zn/extracted_fixed` and compared with the copied source tree. **All 52 vendored files were included; no vendored file was missing.** Verification then imported the installed fixed package and CUDA hook from outside the repository, checked the actual imported paths, ran all three CPU source-manifest groups and the connected operator demo, and evaluated the installed CUDA probe. Results are preserved in `packaging_verify_fixed.json`:

- CPU source verification: **41 verified files, zero mismatches**.
- Installed connected source adapter demo: **qualified=true**.
- Installed CUDA hook: `/tmp/ngc-packaging-pa_p32zn/installed_fixed/ngc_geometry_lab/cuda_check.py`.
- CUDA pinned commit: `e825ade2c033ffb9d83a4cd4f89252136443664b`.
- `.cu` SHA-256: `e9ef40c34398eaeeb4d0a11f567495042b56b9855e233a6812c16b1d9c5515c4`.
- `.h` SHA-256: `bc62266586146096a14f70c5f0779fbf6e3928be0f8b4ba9a97b41db557267ce`.
- CUDA `source_snapshot.matches_pinned`: **true**.
- Native execution remains **NOT_RUN**, zero gates, no CUDA compiler or device tooling detected.

Finally, the actual fixed installed console script and diagnostic CLI ran from `/tmp/ngc-packaging-pa_p32zn`:

```bash
PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed_fixed /tmp/ngc-packaging-pa_p32zn/installed_fixed/bin/ngc-geometry-lab generate --seed 20261022 --cases 8 --shots 65536 --out /tmp/ngc-packaging-pa_p32zn/observations_fixed.json --truth-out /tmp/ngc-packaging-pa_p32zn/truth_fixed.json
PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed_fixed /tmp/ngc-packaging-pa_p32zn/installed_fixed/bin/ngc-geometry-lab analyze --input /tmp/ngc-packaging-pa_p32zn/observations_fixed.json --out /tmp/ngc-packaging-pa_p32zn/analysis_fixed.json
PYTHONPATH=/tmp/ngc-packaging-pa_p32zn/installed_fixed python -m ngc_geometry_lab.cuda_check --probe --out /tmp/ngc-packaging-pa_p32zn/cuda_probe_fixed.json
```

All three exited **0**. The fixed installation's observations, evaluator truth, and analysis files were each **byte-identical** to the first installed candidate's outputs for the same seed and arguments. Evidence: `packaging_generate_fixed.txt`, `packaging_analyze_fixed.txt`, `packaging_cuda_fixed.txt`, `packaging_cuda_fixed.json`, and `packaging_reproduction.json`.

## Boundaries

This was a focused packaging regression and installed-workflow check, not another full test or campaign run. Dependencies were already available and reused; the build/install performed no network lookup or dependency resolution. The wheel is installable independent of the checkout but still requires its declared NumPy/SciPy dependencies. Source inclusion is verified for every vendored file, including all provenance manifests; native CUDA binary compilation and device execution were not attempted on this CPU environment. No production code was changed by this task.
