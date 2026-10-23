# NGC / MAPEOGEO Geometry Lab

A complete computational qualification connecting **actual MAPEOGEO operators**, **the actual NGC real dual-lane backend**, an independent real geometric model, an independent complex reference, and count-based observation.

The default CPU campaign qualifies a bounded mathematical and computational chain. Its data are explicitly synthetic. The optional native CUDA check runs separately on a GPU host. The package does not treat either numerical agreement or a computed CHSH value as a physical experiment.

## Delivered qualification

The release suite passes **124 tests** with warnings treated as errors. The saved CPU campaign in `results/release_20261022/` passes **12 of 12 fixed gates**. Its `REPORT.md`, per-case records, and manifest contain the measured results. The standalone visual report is in `deliverables/`. Development failures and correction reviews remain in `evidence/development/` and `docs/tasks/`.

A fresh extraction of the deliverable passes the same 124 tests and reproduces all **22 scientific output files byte for byte** in the recorded numerical environment. Both campaign manifests verify every listed file. See `docs/RELEASE_VERIFICATION.md` and `evidence/development/archive_replay.json` for the exact scope and evidence.

Native CUDA and physical measurements are **NOT_RUN** here. The optional CUDA runner is ready for execution on a suitable GPU host; its 14 CPU boundary tests validate adapter behavior only.

## Quick start

Requires Python 3.11 or newer, NumPy and SciPy. The tests use the Python standard library; pytest is unnecessary.

```bash
python -m pip install -r requirements.txt
python -W error -m unittest discover -s tests -v
python -m ngc_geometry_lab run --seed 20261022 --out results/my_run
```

For the exact dependency versions used in the delivered campaign, use `requirements-lock.txt`. Every run records its Python, NumPy, SciPy and platform versions. The results folder must be new or empty so previous evidence survives.

The package can also be installed with `python -m pip install .`; the console command is `ngc-geometry-lab`. The bundled source snapshots and manifests are included in the installed package.

## What runs

| Experiment | Scope |
|---|---|
| Actual MAPEOGEO operator connection | Composition order, rank/nullity, equality after an observation, initial-state recovery from a sequence |
| Fresh exact closure | Three explicit integer generators; complete multiplication table and independently checked associativity |
| Metric and center inference | Known conjugated action, uniqueness, insufficient constraints, contradiction, numerical boundary controls |
| Tetrahedral reconstruction | 256 pure/mixed states and 3,072 new rotation predictions |
| Actual NGC dual-lane execution | 1,440 local gates over 1–6 qubits, including nonadjacent/reversed targets |
| Detector calibration and observation | 24 calibration preparations, 128 held-out states, 65,536 counts per record |
| Readout hypotheses | Exponents 1, 2, 4; calibration selection frozen before scoring distinct held-out angles |
| Joint systems | 128 states and 1,024 local-rotation predictions; 16-outcome reconstruction |
| Correlation and identifiability controls | All 16 local deterministic CHSH assignments, equal-marginal/different-joint example, rank-deficient repeated views |

The full criteria were written in `docs/superpowers/specs/2026-10-22-geometric-qualification-design.md` before the campaign ran. Results contain every gate and its criterion. A failed gate produces a failed campaign and a nonzero CLI exit; it is not removed from the report.

The exact closure is **newly computed** using real MAPEOGEO multiplication. It is not labeled as recovery of the unresolved historical sealed artifact. The full matrix set is also compared with an independent enumeration of signed partial permutations.

## Analyze count data

Generate a runnable example with truth in a separate file:

```bash
python -m ngc_geometry_lab generate --seed 20261022 \
  --out observations.json --truth-out truth.json
python -m ngc_geometry_lab analyze --input observations.json --out analysis.json
```

The analyzer accepts the same schema for experimental records. It requires known calibration preparations, a fixed four-output detector model, and fresh identical preparations for the later verification measurements. See [the experimental protocol](docs/EXPERIMENT_PROTOCOL.md) for the complete schema and assumptions. It refuses embedded held-out truth, malformed/noninteger counts, duplicate identifiers, rank-deficient calibration, singular detector inversion, and existing output files.

The analysis returns the fitted detector, raw reconstructed vectors, explicit physical-state corrections, predicted ideal/instrument probabilities, and comparison with the verification counts. It does not receive the separate truth file.

## Native CUDA qualification

The pinned original `NGC_CUDA_2` source and header are included under `ngc_geometry_lab/_vendor/ngc_cuda_2/`. Build and run the optional check on a machine with the CUDA toolkit and a suitable NVIDIA device, following [CUDA_CHECK.md](docs/CUDA_CHECK.md).

```bash
python -m ngc_geometry_lab.cuda_check --probe --out cuda_environment.json
```

A probe is not a GPU qualification. The delivered environment has no device or compiler, so native CUDA execution remains **NOT_RUN**. The optional runner compares the kernel to its phase-quantized reference and reports error against the original continuous-angle target separately.

## Structure

| Path | Responsibility |
|---|---|
| `ngc_geometry_lab/geometry.py` | Independent real geometry, metrics, projections, tetrahedral and joint coordinates |
| `ngc_geometry_lab/reference.py` | Independent complex density-matrix and tensor-axis reference |
| `ngc_geometry_lab/repository.py` | Validated adapters to unchanged upstream code, source verification, exact closure |
| `ngc_geometry_lab/observations.py` | Detector fit and blind reconstruction/prediction |
| `ngc_geometry_lab/synthetic.py` | Declared complex Born-model count generator; separate truth |
| `ngc_geometry_lab/experiments.py` | Experiment inputs, controls and per-case comparisons |
| `ngc_geometry_lab/campaign.py` | Frozen gates and evidence output |
| `ngc_geometry_lab/cuda_check.py` | Optional native CUDA qualification, explicitly separate from CPU evidence |
| `ngc_geometry_lab/_vendor/` | Pinned source snapshots, original tests, notices and provenance |
| `tests/` | Qualification and regression tests |
| `docs/tasks/` | Independent reviews and implementation reports |
| `evidence/development/` | Original failing runs, corrections, and passing verification |
| `results/` | Delivered campaign results, per-case CSVs and synthetic inputs |

Development logs are historical snapshots. Some full-suite logs were captured while other modules were intentional stubs. The release verification record identifies the final suite and exact delivered code. Original failures are retained rather than overwritten.

## Source provenance

- `NB11B/NGC_Real`: `3d9e8ffed3811c9a9f043a6eed30a7a23e18bcab`.
- `NB11B/MAPEOGEO` operator algebra: `ac63dde9da6dca2c000aa53ee6ffb9365e2388a1`.
- `NB11B/MAPEOGEO` observability: `2e12009413488f34c8d7e411f3239d240ce19ade`.
- `NB11B/NGC_CUDA_2` CUDA source: `e825ade2c033ffb9d83a4cd4f89252136443664b`.

Every selected raw file has a Git blob SHA-1, SHA-256, commit and original URL. The MAPEOGEO snapshot combines explicitly identified files from two research branches; it is not described as a full repository checkout. Upstream notices and source bytes are preserved.

One selected upstream MAPEOGEO test has an incorrect expected answer: two noncommuting operators become equal under its supplied observation. The original failure, its exact integer countercalculation, and the corrected qualification expectation are all retained. The repository code itself is not modified.

## Reading the result

Geometric/complex equivalence is a substantive result about a representation. The detector experiment shows prediction under a declared source/instrument model. Both can be useful without identifying one unique underlying physical mechanism.

The Bloch-ball restriction, Born readout, composition rule, and retained joint correlation coordinates are explicit assumptions. A common coordinate origin, a common fixed point, and a common historical source remain distinct claims. The software reports mathematical ambiguity rather than filling it with an assumed cause.
