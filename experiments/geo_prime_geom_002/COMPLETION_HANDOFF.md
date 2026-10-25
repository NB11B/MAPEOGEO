# GEO-PRIME-GEOM — End-to-end completion specification

## Scientific proposition
Given consecutive natural legs n,n+1, an integer hypotenuse c is admissible when n²+(n+1)²=c². The admissible family is parametrized by the negative Pell norm x²−2c²=−1 for x=2n+1. This supplies a **sparse candidate generator**, not a universal prime generator. Prime qualification is a distinct multiplicative irreducibility proof.

## Contracts
- `GeometryCandidate(n,c)`: n>=1; c>0; exact equality n²+(n+1)²=c².
- `GeneratorStep(n,c)`: n'=3n+2c+1, c'=4n+3c+2. It preserves the quadratic norm; an independently proven completeness theorem is required before claiming every solution is generated.
- `OperatorDiscovery`: data consist of ordered `((n,c),(n',c'))` transition pairs; solve affine map over rationals; rank deficiency must refuse; reserve untouched future transitions.
- `PrimeCertificate(c)`: prove `Nat.Prime c` or produce a nontrivial multiplication witness. Coprime triangle legs, prime Pell index, and nonsquare hypotenuse are NOT sufficient.
- `EulerSubset(S)`: `S` is only qualified Pell hypotenuse primes. The finite Euler product over S enumerates the S-generated multiplicative semigroup; it cannot equal the full zeta product unless every prime is present.
- `NativeOperator`: operator matrix T = [[3,4],[2,3]], quadratic form J = diag(1,-2). Check TᵀJT=J, det T=1, native PSMSL invertibility, operator-basis rank and redundancy. Equality of operator outputs does not certify equality of work.

## Completed empirical gates
- 7/7 Pell candidates for 1<=n<200000 agree with an independent exhaustive integer-square-root oracle.
- 4 prime and 3 composite hypotenuses; 169 is a square composite, 985 and 195025 are nonsquare composites.
- Exact affine map inferred from 3 training transitions and validated on 3 withheld transitions.
- Integer Pell numbers P_k, k=3,5,...,101: 25 composite odd indices carry explicit P_d divisibility witnesses. The prime odd index k=7 gives P_7=169, disproving sufficiency of prime index.
- The four qualified Pell primes in this finite search are 5,29,5741,33461. Their Euler subset product is approximately 1.042906778605685, not zeta(2). Removing 5 changes the finite subset product by the exact ratio 24/25.
- Original early test mistake expecting one nonsquare composite preserved. Corrected tests ran 27/27 locally before native integration; the native module adds 7 regression tests run through GitHub CI.

## Formal gates and CI
- Quadratic Pell invariance and a primitive composite hypotenuse example compiled in Lean 4.33.1: verified workflow 40237028109.
- Proof of inferred transformation's quadratic invariance, and deliberate coefficient mutation rejected by Lean: verified workflow 40237228455.
- Native PSMSL algebra integration: verified workflow 40237526047.
- Latest aggregate (including Euler subset) requires its own CI success; never infer this from earlier successful commits.

## Outstanding gates, required for full research closure
1. **Global solution exhaustiveness**: Lean theorem every positive solution n,c of n²+(n+1)²=c² is reachable by finite iterations from (3,5), including the correct boundary/uniqueness specification.
2. **Pell-index divisibility**: a universal Lean proof P_d | P_k whenever d|k, and the consequent necessary prime-index restriction for odd k>1.
3. **Generated-AST provenance**: full deterministic source-data hashing, versioned typed affine AST and byte-for-byte emitted Lean theorem; lock the proof to the selected rather than substituted AST.
4. **Native work-equivalence semantics**: connect transformation equivalence, relational quotient, path histories, and measured computational work; do not equate these prematurely.
5. **Open-world adequacy**: blind alternative Pythagorean constraints, mislabeled coordinates, perturbations, missing steps, other quadratic forms, and explicit refusal for nonidentifiable data.
6. **Infinite-product bridge**: if desired, formal convergence and Euler-subset interpretation; this is distinct from the standard Euler zeta identity and cannot imply it without complete prime coverage.
7. **Independent audit**: freeze failing log, corrected log, GitHub CI revision, Lean `#print axioms`, hashes, reviewer signoff and merge only on explicitly passed gates.

## Reproduction
```bash
cd experiments/geo_prime_geom_002
python -m unittest discover -v
python experiment.py
python infer.py
python index_sieve.py
python euler_subset.py
python emit_lean.py
cd ../..
lake env lean MAPEOGEOFormal/GeoPrimePell.lean
lake env lean MAPEOGEOFormal/GeoPrimePellInferred.lean
python experiments/geo_prime_geom_002/negative_kernel.py
```

## Final claim discipline
We have tested and Lean-verified a Pell-isometry candidate generator and recovered its affine operator from finite observations, and separately linked primality to the earlier MAPEOGEO irreducibility theorem. We have **not** demonstrated autonomous discovery of all primes or completion of global Pell-solution classification; these remain falsifiable research requirements.
