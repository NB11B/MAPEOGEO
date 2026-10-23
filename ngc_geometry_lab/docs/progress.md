# Progress — plan: docs/superpowers/plans/2026-10-22-geometric-qualification.md

## Preflight

| Interface | Producer / consumer | Resolution |
|---|---|---|
| Real geometry arrays | geometry / observations and campaign | Float64 real; strict shapes; candidate imports no reference |
| Complex oracle | reference / campaign | Independent complex linear algebra; big-endian targets |
| Vendor sources | source inspection / adapters | Exact copied content and hashes; no silent edits |
| Calibration | observations / campaign | Truth isolated from estimator; frozen detector matrix |
| Results | campaign / reporting | All gates and controls preserved; failure exits nonzero |
| Tasks 1–7 | Spec versus task outputs | Consistent; independent file ownership prevents write conflicts |

Decisions: use a new isolated qualification repository because the existing local archives are read-only source snapshots. Use unittest because pytest is unavailable. CPU computational qualification is possible here; CUDA and physical experiments are explicitly unexecuted. The user's instruction authorizes continuous planning, building and testing without another approval stop.

Task 1: complete — pinned NGC_Real and MAPEOGEO imports; 41 source/evidence hashes verified; original selected baseline 23 pass, one independently confirmed bad test expectation retained. CUDA source/header separately pinned for an executable hardware handoff.
Task 2: complete — real geometry and inverse operators, 33 tests; reviewed boundary-classification defect corrected with preserved red/green regression evidence.
Task 3: complete — independent complex reference, 22 tests; additional reviewer bit-index oracle agreed in 60 random-unitary cases.
Task 4: complete — detector calibration, blind count analysis, synthetic generator, external CLI; exact integer count validation corrected before float conversion.
Task 5: complete — first full campaign passed 12/12 frozen gates. Fresh closure: 115 elements, 13225 product checks, 1520875 associativity checks. First combined suite: 96 passing tests.
Task 6: complete — independent core, integration, packaging, and scoped correction reviews approved. Regressions preserve the original defects and corrected behavior.
Task 7: complete — final full suite: 124 tests pass with warnings treated as errors. Fresh release campaign: 12/12 fixed gates pass. Clean extracted archive passes the same 124 tests and reproduces all 22 scientific output files byte for byte. Release and replay manifests each verify all 22 files. Complete source/evidence packaging and standalone visual report are prepared for delivery.
Task 8: complete as a hardware handoff — optional native CUDA runner includes the pinned source/header, independent reference, build instructions, and 14 passing CPU boundary tests. Native GPU execution is unavailable in this environment and remains NOT_RUN.

## Implementation decisions and corrections

- The closure is computed anew from three explicit integer generators using actual MAPEOGEO composition, with an independent signed-partial-permutation enumeration. It is not called recovery of the unresolved historical sealed artifact. The 2017 commuting ordered pairs correspond to 951 distinct unordered pairs after removing self-pairs.
- Metric eigenvalues near zero are unresolved at the requested tolerance, even with a one-dimensional metric solution space; no tolerance was relaxed to pass the SPD counterexample.
- Count values and totals are checked as exact integers before conversion to prevent losing a count above the exact float64 range.
- Vendored sources were moved inside the Python package for installable, self-contained distribution; original source bytes and hashes remain unchanged.
- Final integration guards reject nonfinite measurements before reductions and preserve failed stages. The original known upstream assertion is exempted only at its exact pinned source location and independently disproved expectation.
- Installed-wheel review found a missing CUDA header; package data now includes it, and both installed source hashes match their pinned originals.
- Optional CUDA quantization handles immediately-below-half-bin values correctly and limits phase bins to 2**30 so the unchanged source's signed integer normalization stays in range.
