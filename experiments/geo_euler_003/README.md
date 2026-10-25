# GEO-EULER-003 — Blind symbolic operator identification

## Local qualification, 2026-10-25
10/10 corrected Python tests passed. Domain 0..30 was encoded with randomly shuffled opaque symbol IDs. A successor map, zero/one anchors and two unnamed, bounded binary-operation tables were exposed to the inference module; numerical decoding and prime reference lists were not. Recurrence checks identified the addition-like and multiplication-like tables; subsequent factor-witness enumeration recovered the ten primes through 30, matching an independent primality oracle.

## Adversarial qualification
Five fresh symbol permutations succeeded. A nonmultiplicative impostor was refused; duplicate addition candidates were refused as ambiguous; corrupted addition observations were refused; malformed cyclic successor maps were rejected.

## Defect preservation
Original local test run: 8/10 tests passed, with two failures caused by the **test oracle incorrectly expecting 11 primes <=30**. The correct number is 10; after correcting only that reference expectation, the same test suite passed 10/10. Original and corrected logs remain local artifacts.

## Reproducibility
The local source and results are available as conversation sandbox artifacts. This README does not claim that executable source or GitHub CI has yet been published for GEO-EULER-003.

## Claim boundaries
The recognizer is supplied with successor, anchors, full (truncated) operation tables, addition/multiplication recurrence grammars and finite-domain bounds. It does not learn arithmetic recurrences from arbitrary raw streams, synthesize new nonlinear operator grammar, or produce a formal prime-factorization theorem. An independent native-MAPEOGEO discovery adapter remains unqualified.

## Next gates
1. Commit executable source and verify GitHub CI.
2. Hold out nontrivial operation-table entries and predict them using inferred recurrence rules.
3. Replace the supplied recurrence grammar by enumerated candidate recurrences and systematic falsification.
4. Evaluate arbitrary symbol renamings, ambiguous anchor choices, partial observations and observational nonidentifiability.
5. Connect qualified relational equivalence classes with native MAPEOGEO operator-discovery contracts.
