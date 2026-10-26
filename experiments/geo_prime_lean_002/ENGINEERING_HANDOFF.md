# GEO-PRIME-LEAN — Full qualification and engineering handoff
Date: 2026-10-25. Working branch: `experiments/geo-bsl-001`.

## Governing hypothesis
Arithmetic operators with distinct construction histories (successor/repeated addition and square-interaction residual) recover the same natural-number multiplication; their relationally irreducible elements are exactly primes; prime generators reproduce the Basel zeta structure. Separate **theorems** about mathematical semantics from **empirical** claims about automatically discovering the relevant grammar.

## Contracts
- Observational state: ordered pairs of natural-number inputs with exact operator outputs, a fixed partition of discovery and validation observations, and provenance including seed and generator.
- Operator grammar: `S, +, ×, square, cube` as independently typed constructors; do not silently rewrite an unrecognized AST into the reference expression.
- Interaction: `I₂(a,b) = (a+b)^2 − a² − b²`. In natural numbers this subtraction is well-defined as the intended exact residual because `(a+b)^2 ≥ a²+b²`; the reference theorem proves `I₂=2ab`.
- Reconstructed multiplication `M_I(a,b)=I₂(a,b)/2` (natural division), and recursion-defined `M_R` from GeoEuler.
- Irreducible criterion for n≥2: no a,b>1 with M(a,b)=n. A prime certificate must rule out all such factors, not merely lack a witness in an incomplete graph.
- Mathematical equality of outputs does not imply equal execution histories or work costs.

## Gates and stopping conditions
| Gate | Requirement | Evidence | Exit criteria |
|---|---|---|---|
| P0 | Freeze source and external theorem dependencies | commit SHA and Lean toolchain | pinned Lean 4.33.1 and Mathlib |
| P1 | Derive square interaction coefficient from only 1,2,3 | exact rational/integer discovery | sole inferred coefficient 2 |
| P2 | Independent held-out arithmetic | 441 ordered pairs including zeros | zero mismatch vs repeated addition |
| P3 | Exact universal interaction identity | GeoPrimeInteraction.lean | Lean kernel passes, no sorryAx |
| P4 | Same multiplication as successor construction | interactionMul_eq_recursive | Lean kernel passes |
| P5 | Prime correspondence on arbitrary naturals | interactionIrreducible_iff_prime | Lean kernel passes |
| P6 | Independent finite primality witness classification | 2..200 and separate primality oracle | 46 primes; 0 errors |
| P7 | Actual inferred coefficient to Lean | generated GeoPrimeInferred.lean | theorem checks for coefficient 2 |
| P8 | Adversarial mutation | wrong coefficient 3 emitted unchanged | Lean rejects theorem, diagnostics audited |
| P9 | Source-to-certificate trace | AST normalization, SHA, data hash, replay | prospective follow-on, not complete |
| P10 | Work-equivalence / relational quotient | native MAPEOGEO work machinery and operator paths | prospective follow-on, not complete |
| P11 | Finite closure + generator ablation | compare Euler partial sum and finite product, exact domains | prospective follow-on, not complete |
| P12 | Global Euler-product/prime-zeta semantics | formal Dirichlet-series and infinite-product convergence | prospective follow-on, not complete |
| P13 | Open-world operator grammar | unknown primitives, noise, alternate bases, domain shift | prospective follow-on, not complete |

## Execution
```bash
cd experiments/geo_prime_lean_002
python -m unittest discover -v
python experiment.py
python emit_lean.py
cd ../..
lake build MAPEOGEOFormal.GeoEuler MAPEOGEOFormal.GeoEulerPrime
lake env lean MAPEOGEOFormal/GeoPrimeInteraction.lean
lake env lean MAPEOGEOFormal/GeoPrimeInferred.lean
python experiments/geo_prime_lean_002/negative_kernel.py
```

## Trust and falsification
1. The mathematical proof makes no claim that finite experimental selection generalizes beyond the typed, proven definition.
2. The emitted coefficient is **not** silently repaired: changing 2→3 must fail Lean. The reference multiplication operator uses a separately written, audited Lean specification.
3. Do not use a numerical partial sum to claim an infinite zeta equality without a convergence theorem and control for distinct truncation domains.
4. Preserve failed proof logs and corrected reruns separately; distinguish a reference/test bug from a theorem counterexample.
5. If the new CI job fails, the whole formal qualification is **blocked**; do not describe the theorem as Lean verified.
6. Source-provenance and arbitrary grammar inference remain distinct from kernel verification.

## Links and dependencies
- `MAPEOGEOFormal/GeoEuler.lean`: recursively defined + and ×.
- `MAPEOGEOFormal/GeoEulerPrime.lean`: irred ↔ Nat.Prime.
- `MAPEOGEOFormal/GeoPrimeInteraction.lean`: independent interaction route.
- `experiments/geo_prime_lean_002/emit_lean.py`: inferred coefficient → executable Lean definition.
- `experiments/geo_prime_lean_002/negative_kernel.py`: fail-closed adversarial proof mutation.
- `.github/workflows/geo-prime-interaction.yml`: reproducible GitHub qualification.

## Research disposition
When P0–P8 all pass: two independently defined multiplication operations are universally equal and preserve prime irreducibility; this is a *formal mathematical result*. The prime/zeta and open-grammar extensions remain separately scoped until P9–P13 have independent evidence.
