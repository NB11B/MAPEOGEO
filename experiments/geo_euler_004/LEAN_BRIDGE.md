# GEO-EULER-LEAN-001 — Formal operator-semantics bridge

## Scope
Lean 4 v4.33.1 (repository toolchain), Mathlib. Define addition by successor recursion and multiplication by iteration of that addition; prove equality to standard Nat arithmetic, commutativity, square/cube interaction identities, and soundness/equivalence of the nontrivial-factor witness relation.

This formalizes the **semantic reference** used by GEO-EULER-002/003/004 and GEO-OPR, not the machine-learning / grammar search routine. It does not establish completeness of a finite closure execution, prime equivalence to `Nat.Prime`, Euler product, Basel convergence, or autonomous discovery. These require separate proofs.

## Commands
```bash
lake env lean MAPEOGEOFormal/GeoEuler.lean
```

CI prints Lean axioms of three critical theorems. Standard Mathlib foundational axioms may appear; no new axioms or `sorry` are introduced in this module.

## Gate status
Committed for CI qualification; see the dedicated GitHub Actions workflow. Do not promote to verified until compile succeeds.
