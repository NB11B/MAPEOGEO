# GEO-PRIME-UNIVERSAL — Formal qualification closeout (2026-10-25)

## Verified formal record
- Cyclic coprimality characterization (GeoPrimeCycle.lean): https://github.com/NB11B/MAPEOGEO/actions/runs/40239812423 — success.
- Operational iterate (GeoPrimeOrbit.lean) and orbit↔coprimality (GeoPrimeOrbitCoprime.lean): https://github.com/NB11B/MAPEOGEO/actions/runs/40241123922 — success.
- Actual operational reachability ↔ Nat.Prime (GeoPrimeOperationalPrime.lean): https://github.com/NB11B/MAPEOGEO/actions/runs/40241124000 — success.
- Finite first-n coverage and n=9, step=3 noncoverage (GeoPrimeBoundedOrbit.lean, GeoPrimeOrbitNegative.lean): https://github.com/NB11B/MAPEOGEO/actions/runs/40242287033 — success, including direct Lean compilation of the negative theorem.
- Native PSMSL graph reconstruction and arbitrary relabeling tests: https://github.com/NB11B/MAPEOGEO/actions/runs/40240250930 — success.
- Native bounded traversal cross-check (3160 pairs, n=2..80): https://github.com/NB11B/MAPEOGEO/actions/runs/40240876260 — success.

## Exact theorem boundary
For n≥2, every k with 1≤k<n reaches every residue by repeated addition of k modulo n iff n is prime. The bounded lemma shows a complete orbit, if present, appears among the first n iterates. These are standard cyclic-group facts formalized in Lean, not a novel prime generator or improved primality test.

## Failure history
Original ZMod proof failed on an unavailable lemma; subsequent corrections addressed residue casts and the nonzero-modulus assumption. Orbit/coprimality proof failed on argument-order mismatch. Bounded orbit proof failed on an unavailable cast simp lemma. Negative example initially left contradiction cases open. Failed runs are retained; successful run IDs above supersede them, not erase them.

## Remaining research/engineering
1. Review Lean #print axioms for relevant theorems and ensure no sorryAx or custom axioms.
2. Add standalone clean-branch CI combining every final theorem and native tests, with versioned evidence.
3. Integrate native graph semantics into the primary MAPEOGEO relational quotient/work-equivalence subsystem rather than only directly using vendor APIs.
4. Test discovery from opaque graph transitions without supplying n, k, or cyclic topology in advance, and require abstention under non-identifiability.
5. Benchmark complexity against standard primality methods with honest input size/cost accounting. Current exhaustive k and orbit enumeration is not competitive with fast primality testing.
6. Keep π / Euler product and operator-expression approximation studies separate until formal bridges are exhibited.
