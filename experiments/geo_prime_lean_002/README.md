# GEO-PRIME-LEAN-002 — End-to-end engineering qualification

**Question:** Can an operation inferred from the square-addition interaction recover multiplication and preserve prime irreducibility, with universal Lean proofs and adversarial checks?

## Stage boundaries

1. **Semantic construction:** define the squared-addition residual on Nat, with truncated subtraction handled by an exact polynomial identity.
2. **Operator equivalence:** prove interaction-derived multiplication equals ordinary multiplication and successor-derived mulR on *all* Nat inputs.
3. **Prime equivalence:** prove factor-witness irreducibility from this new operator iff Nat.Prime.
4. **Empirical checks:** derive square-interaction coefficient 2 from observations on 1..3; verify withheld 4..20, zero-operand, reversed-operand and multiple factor domains.
5. **Counterexamples:** deliberately alter coefficient, division factor, or interaction expression; require failure against trusted independent oracles/Lean.
6. **CI:** build GeoEuler, GeoEulerPrime, GeoPrimeInteraction in pinned Lean 4.33.1, run Python tests and print Lean theorem axioms. Preserve failing run and corrections.
7. **Future extensions:** generate the *exact* inferred coefficient into the Lean AST rather than use the fixed 2, certify it; cubic-derived reconstruction with domain/zero preconditions; finite relational closure confluence, unique factorization, Euler product bridge and an end-to-end generator-removal theorem. None of these later steps is silently claimed here.

## Reproduce

```bash
cd experiments/geo_prime_lean_002
python -m unittest discover -v
python experiment.py
cd ../..
lake build MAPEOGEOFormal.GeoEuler MAPEOGEOFormal.GeoEulerPrime
lake env lean MAPEOGEOFormal/GeoPrimeInteraction.lean
```

## Claim discipline
The Lean proof establishes arithmetic equivalence given the displayed operator definition; it **does not prove** data-driven inference was universally sound. Mathematically equal output is **not** proof of equal computational work. No Euler product identity is asserted by this module.
