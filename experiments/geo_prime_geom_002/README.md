# GEO-PRIME-GEOM-002 — Pell recurrence and prime qualification
A full bounded test of the consecutive-leg right-triangle candidate generator. Starting (n,c)=(3,5), update n'=3n+2c+1, c'=4n+3c+2. Independent brute-force integer-square-root enumeration over 1<=n<200000 matches **exactly** the seven candidate pairs.

**Local corrected test run:** 10/10 pass; 4 prime and 3 composite hypotenuses. All legs coprime and all candidates satisfy (2n+1)^2−2c^2=−1. The nonsquare composites 985 and 195025 falsify a square-only prime detector.

**Preserved failure:** original unit test expected one nonsquare composite; discovered two. The initial 9/10 result reflects an incorrect reference expectation, not a generator failure. Preserve the original failure separately from the corrected run.

Run: `cd experiments/geo_prime_geom_002 && python -m unittest discover -v && python experiment.py`.

## Formal and architectural bounds
Lean proves the recurrence's algebraic negative Pell invariant and a concrete primitive composite counterexample, conditional on CI success. Independent primality remains an additional filter. This does NOT generate all primes and is not a theorem that no other integer triangle solutions exist unless global Pell solution classification is also proved. The finite brute comparison is not a universal completeness proof.

## Program completion plan
1. G0: freeze the recurrence, numeric oracle and provenance (this gate).
2. G1: formal Pell invariant and primitive composite witness (Lean module).
3. G2: typed recurrence AST derived from **unlabeled geometric observations**, not a hardcoded update.
4. G3: infer the affine coefficient matrix and offset; test withheld larger terms, alternate seeds, coordinate labels and countermodels.
5. G4: compile the *selected* AST and prove it preserves the negative Pell norm; mutate coefficients and require Lean rejection.
6. G5: connect candidate output c to GeoEulerPrime / GeoPrimeInteraction: factor witnesses or a provable Nat.Prime certificate, never mere square screening.
7. G6: native MAPEOGEO R/operator quotient representation: distinguish same numerical candidate, same operator graph and equivalent computational work.
8. G7: formal global classification of positive solutions to x²−2c²=−1 with parity/boundary constraints; compare recurrence coverage.
9. G8: geometry-vs-prime benchmarks, generator ablations, density and efficiency controls against ordinary sieving.
10. G9: provenance hash, mutation audit, independent CI, and merge only on explicit signed qualification.

Mark G2–G9 pending rather than interpreting reference algebra as autonomous discovery. Kernel proofs, numerical verification and inference claims must be reported separately.
