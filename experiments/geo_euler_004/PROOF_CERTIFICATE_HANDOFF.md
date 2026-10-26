# GEO-EULER-LEAN-003 — Discovery-to-proof certificate contract

## Verified components
- `GeoEuler.lean`: recursively specified successor addition and repeated-addition multiplication equal Nat operations.
- `GeoEulerPrime.lean`: relational irreducibility ↔ `Nat.Prime`. CI success https://github.com/NB11B/MAPEOGEO/actions/runs/40233964193.
- `GeoEulerCertificate.lean`: generic recurrence-law contract parameterized over arbitrary implementation functions A and M. If four **universal** recurrence obligations are certified, Lean derives full arithmetic semantics and the relational factor criterion. CI must verify this new module independently.

## Important trust boundary
`GEO-EULER-004` empirically selects rule names by finite table checks. Its current output **cannot** be promoted to a theorem by identifying strings such as `opaque-Y|shift=1` with `addR`. A genuine proof-carrying integration requires an extractor for a typed operator AST, serialization of that AST with witnesses for its four recurrence equations, and a Lean checker rejecting unknown operators or missing proofs.

A finite sample match or untrusted JSON output is *not* a universal certificate. This phase establishes the verifier's mathematical contract, not the final extraction pipeline.

## Remaining engineering gates
1. Define typed, total operator AST (successor, zero, first projection, second projection, recursion, composition).
2. Build a deterministic parser for actual discovery output; refuse unsupported grammar and malformed cases.
3. Produce Lean code defining the *selected AST* with explicit proofs of every recurrence law.
4. Run a clean subprocess compilation; capture kernel axioms, compare theorem statements, archive candidate hash, exact test input and compiler version.
5. Mutation/falsification: swap operation roles, corrupt a recurrence, inject a finite-fit impostor, and verify rejection.
6. Once the extractor is certified, prove prime generator correspondence for the emitted code and extend to finite closure completeness/unique factorization and an Euler product theorem.

The last two number-theoretic statements remain distinct proof obligations. Do not interpret empirical prime-zeta and Euler-product comparisons as formal proofs of their limiting identities.
