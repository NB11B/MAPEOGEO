# NGC / MAPEOGEO geometric reconstruction qualification

## Authorized purpose

The user requested: “Plan, build, and test this all the way through,” and explicitly authorized the connected operators in MAPEOGEO. Build a reproducible computational experiment connecting actual repository operators, reconstruction of geometry, tetrahedral observation, held-out transformations, and joint-system correlations. Deliver complete runnable code and preserved evidence.

This package qualifies finite mathematical representations and prediction procedures. Synthetic observations are labeled as synthetic. It does not claim a physical origin, a derivation of the Born rule, a laboratory Bell experiment, or a quantum computational speedup. The user's tetrahedral model and a standard tetrahedral qubit measurement are compared through explicit maps; they are not presumed identical.

## Architecture

1. Preserve exact source snapshots and hashes for the actual NGC real dual-lane backend and connected MAPEOGEO operators. Test adapters against independent NumPy implementations. Source-only CUDA material is separately identified; this environment has no NVIDIA device or CUDA compiler.
2. Recover metric constraints from explicit operator actions, centers from affine fixed-point equations, and observability rank from sequences. Report uniqueness, ambiguity, inconsistency, and unresolved positive-definite feasibility separately.
3. Implement real three-dimensional tetrahedral probabilities, inversion, rotations, projection sequences, and two-system correlation coordinates independently of the complex reference.
4. Implement an independent complex density-matrix reference with Pauli operators, POVMs, unitaries, and explicit local tensor ordering.
5. Calibrate a detector response only on calibration preparations; freeze the fitted response; reconstruct unknown held-out states from counts; predict new operation sequences before comparing with verification counts. Keep truth outside estimator inputs. Include an external-counts JSON interface.
6. Run deterministic campaigns with exact and finite-shot controls, report every predeclared gate, preserve raw JSON/CSV evidence, and ship a complete archive.

## Decisions and constraints

- Python 3.11+, NumPy and SciPy; use stdlib unittest so no network install is needed for tests.
- Independent reference code may share constants/conventions, but must not call the geometric functions or NGC backend it checks.
- All qubit tensor indexing in the qualification interface is big-endian. Source CUDA uses a different bit convention and is not executed here.
- Invalid shapes, complex input to real APIs, nonfinite values, invalid probabilities, rank-deficient calibration, and singular detector inversion must fail explicitly.
- Do not silently normalize away loss, discard failed controls, fit on held-out truth, or replace original evidence.
- A finite-shot estimate outside the Bloch ball may be explicitly radially projected; record the raw estimate and correction. This is an estimator choice, not a physical discovery.
- The real dual-lane state has 2*2**n real entries. Demonstrate equivalence and retained resources without claiming compression or hardware parallelism.
- Preserve baseline source behavior. Any upstream defect found is documented and reproduced; corrections belong to a separately named adapter with tests.
- No unrequested remote publication or shared-branch mutation.

## Frozen campaign gates (before execution)

Use master seed 20261022 with distinct named RNG streams. Numerical exact-equivalence tolerance is 1e-10 unless a stricter analytic check is stated. All cases and resource counts are recorded.

| Experiment | Required evidence / gate |
|---|---|
| Operator algebra | Execute imported composition and projection; independent action agrees within 1e-10; preserve any upstream contract discrepancy |
| Metric | Known conjugated rotation/projection family recovers metric up to scale within 1e-9; insufficient and contradictory controls correctly classified |
| Common center | Recover known affine center within 1e-10; incompatible and nonunique controls recognized |
| Tetrahedron | Sum directions zero, pair overlaps -1/3, full observation rank 3; 256 pure/mixed states reconstruct within 1e-10 |
| Held-out operations | 256 states with 12 independent rotations each; geometric predictions vs complex reference within 1e-10 |
| Dual-lane backend | At least 1000 local gate applications, 1–6 qubits, reversed/nonadjacent target order; state and probability errors <=1e-10 |
| Projection/readout | Crossed direct transmission 0 and inserted 45-degree transmission 1/4 under squared norm; alternate exponents remain explicitly different hypotheses |
| Finite-shot reconstruction | 24 calibration preparations and 128 held-out states; 65536 counts per preparation/verification; mean Bloch error <0.035; detector-calibrated error improves over uncorrected error |
| Readout selection | Exponents 1, 2, 4 scored on calibration angles, frozen winner evaluated on distinct held-out angles; synthetic truth explicitly squared norm |
| Joint systems | 128 mixed/pure two-qubit states and local rotations; 16-outcome reconstruction and predictions within 1e-10 |
| Correlation control | Same local marginals but distinct joint predictions; CHSH singlet 2*sqrt(2), all 16 local deterministic assignments <=2 |
| Identifiability | Duplicate/mirrored observation directions fail to add missing rank; initially indistinguishable states separate under a permitted operation |
| Reproducibility | Identical seed/config gives identical scientific result JSON; archive passes full tests and campaign when extracted in a fresh directory |

These gates determine computational qualification only. Negative controls are successful when they expose the expected limitation. Finite-shot error is a preregistered engineering threshold for synthetic data, not a universal confidence guarantee.

## Deliverables

Complete source, provenance and notices, unit/integration tests, campaign and external-data CLI, synthetic example with separate truth, configuration, machine-readable results and per-case data, an explanatory report, development failures and corrections, independent review, and a reproducible archive.
