# Cyclic primality proof audit

## Verified empirical/native state
- GEO-PRIME-UNIVERSAL-001: exact orbit enumeration and Pascal criterion n=1..300 passed CI 40239191475.
- GEO-PRIME-UNIVERSAL-002: actual native PSMSL permutation-matrix construction, cycle decomposition and independent prime oracle n=1..100 passed CI 40239562784.

## Lean audit and current status
- Original `GeoPrimeCycle.lean` proof failed at CI 40239562941: an elaboration metavariable in the not-coprime witness destructuring, followed by a tactic 'no goals' error. This is a proof-script failure; no counterexample to the theorem.
- Corrected proof on commit `e137613ac4726887220b7a8c7fc27e636ebe1069` uses `Nat.prime_of_coprime` and `Nat.Prime.coprime_iff_not_dvd`. CI run 40239812423 must succeed before promotion.
- IMPORTANT: `FullStep` is currently **defined** using `Nat.Coprime`, not by orbit traversal, so the theorem is a universal coprimality criterion, *not yet* the executable geometric orbit theorem.

## Next independent Lean bridge
Prove for n>=2 and 0<k<n, the directed permutation `step(i)=(i+k)%n` on `Fin n` has exactly n distinct iterates from vertex 0 iff `Nat.Coprime n k`. Preferred route: group-theoretic additive order of `k : ZMod n`; demonstrate orbit cardinality = n/gcd(n,k), or equivalent injectivity of the first n iterates. Do not assume the result via definition.

Then compose that theorem with `geometricPrime_iff_prime`. Add concrete witness tests for 9 step 3 and 25 step 5, arbitrary relabeling controls, and kernel rejection of an intentionally wrong theorem.

## Scope
This is a classical theorem with geometric visualization. No novel universal generator or complexity improvement is claimed. The inference/selection of a cycle model from arbitrary observational data remains a separate open-world gate.
