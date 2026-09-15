# PCT E25G–E25H — C5 Exact-Morphism and Provenance Policy Report

**Branch:** `agent/pct-computational-architecture`  
**Stage:** E25G–E25H  
**Status:** PASS on the frozen four-component source-bound evaluation set  
**Scope:** Experimental PCT evidence only; no automatic semantic promotion

## Executive result

E25G and E25H tested the top closure layer proposed by the PCT verification architecture:

```text
C5a = exact witness-bearing morphism equality
C5b = provenance-bound correspondence
C5  = C5a AND C5b for every applicable subgate
```

The four real source-bound EO/GEO/FORMAL contracts all passed C5a and C5b on their preregistered bounded domains. The strict conjunction policy then rejected every preregistered single-axis adversarial control, while every permissive single-axis alternative false-accepted at least one fault.

The evidence therefore supports `STRICT_AND` as the production candidate C5 policy **for these four contracts and these controls**. It does not establish universal C5 closure for MAPEOGEO.

## Source-bound components

The evaluation is restricted to the four real components already isolated by E25D:

| Contract | Source component | Formal scope |
|---|---|---|
| Rank-nullity | `source-bound:rank:theorem_6_16` | `GENERAL_FINITE_DIMENSIONAL_DIVISION_RING` |
| Convexity | `source-bound:convex:definition_44_6` | `TWO_POINT_REAL_CONVEX_COMBINATION` |
| Positive 1D LP duality | `source-bound:lp:theorem_47_9` | `POSITIVE_ONE_DIMENSIONAL_LINEAR_PROGRAM` |
| Gaussian exponent identity | `source-bound:gauss:definition_53_4` | `SCALAR_REAL_GAUSSIAN_EXPONENT_IDENTITY` |

All are bound to the frozen audited v0.9 source artifact:

- commit `9420f19953f56198630f86eb25fa5d6eb0828ea7`
- workflow run `34933361147`
- artifact id `10382242654`
- artifact digest `sha256:d487602dd3c0b3a3c5302edde108758eda2b11975f5e0c2c4e659db63da2aabc`

No synthetic E25B calibration component is counted as real C5 evidence.

## E25G-A — Exact morphism audit

E25G-A strengthens the E25C comparison. E25C established agreement of the declared executable contract result; E25G-A requires EO, GEO, and FORMAL routes to independently construct the same **canonical witness-bearing transformation record**.

The three route implementations do not share mathematical witness construction. They share only canonical serialization and equality comparison.

### Rank-nullity

For every GF(2) matrix with `1 <= m,n <= 3`, the canonical record includes:

- input matrix;
- rank;
- reduced row-echelon form;
- pivot columns;
- nullity; and
- canonical nullspace basis.

Inputs tested: **682**.  
EO/GEO/FORMAL disagreements: **0**.

### Convexity

For every nonempty subset of `{-2,-1,0,1,2}` and each half-integer query in `[-2,2]`, the record includes hull endpoints, membership, and an exact barycentric or separation witness.

Inputs tested: **279**.  
EO/GEO/FORMAL disagreements: **0**.

### Positive one-dimensional LP duality

For positive coefficients in `{1,2,3}` and dimensions `m in {1,2,3}`, the record includes exact ratios, optimum, **all active minimizers**, and the exact primal/dual equality witness for every active index.

Inputs tested: **2,457**.  
Tie cases with multiple active minimizers: **603**.  
Tie cases preserving all active minimizers across all three routes: **603/603**.  
EO/GEO/FORMAL disagreements: **0**.

This is materially stronger than an implementation that chooses only the first minimizer: the C5 record preserves the complete exact correspondence class represented by tied active constraints.

### Gaussian exponent identity

The three routes independently normalize the scalar symbolic identity to the coefficient basis

```text
[nx/s2, ny/s2, dot/s2]
```

with exact coefficient vector

```text
[-1/2, -1/2, 1]
```

and the same canonical symbolic normal form.

Exact symbolic cases: **1**.  
Route disagreements: **0**.

### E25G-A aggregate

Total exact inputs: **3,419**.  
Contracts passing exact witness equality: **4/4**.  
Total route-disagreement count: **0**.

The per-route content digests are equal within every contract and are frozen in `evidence/pct_e25g_exact_morphism_audit.json`.

## E25G-B — Provenance-bound correspondence

C5b is independent of mathematical output equality. It binds the exact morphism evidence to the identity and lineage that authorize the correspondence claim.

Each real component binds:

- source statement SHA-256;
- contract name;
- formal scope;
- source artifact digest and audited commit;
- EO, GEO, and FORMAL representation ids;
- relevant v0.7/v0.8 certificate ids;
- C5 adapter id;
- SHA-256 of the actual C5a adapter implementation; and
- predecessor evidence lineage.

All four component bindings passed with no source-hash, scope, certificate, or representation-identity conflict.

The adapter implementation digest for this frozen evaluation is:

```text
0b918f7588cc99966a87e1ef0f3456fb011824d679a89805e92e1d4645dc38a8
```

The full binding records and their canonical provenance digests are frozen in `evidence/pct_e25g_provenance_bindings.json`.

## E25H — Policy comparison

E25H tested four policies:

```text
STRICT_AND      = C5a AND C5b
MAP_ONLY        = C5a
PROVENANCE_ONLY = C5b
ANY_AXIS        = C5a OR C5b
```

Every real valid component was accepted by all policies, so the decisive question is adversarial false acceptance rather than valid-case acceptance.

Each of the four contracts received five preregistered adversarial cases:

1. correct exact morphism + wrong provenance;
2. wrong exact morphism + correct provenance;
3. same lower-layer endpoint + wrong witness map;
4. correct lineage + altered exact transformation; and
5. valid exact map copied across source identities.

That produced **20 adversarial cases** total.

### Aggregate policy results

| Policy | Valid accepted | Valid rejected | Adversarial false accepts | False-accept rate |
|---|---:|---:|---:|---:|
| `STRICT_AND` | 4/4 | 0 | **0/20** | **0%** |
| `MAP_ONLY` | 4/4 | 0 | **8/20** | **40%** |
| `PROVENANCE_ONLY` | 4/4 | 0 | **12/20** | **60%** |
| `ANY_AXIS` | 4/4 | 0 | **20/20** | **100%** |

The same pattern occurs contract-by-contract: each `MAP_ONLY` policy false-accepts the two provenance-axis faults, and each `PROVENANCE_ONLY` policy false-accepts the three exact-map-axis faults. No single-axis policy survives all preregistered controls.

The result therefore empirically distinguishes the two evidence dimensions:

```text
exact mathematical transformation ≠ provenance identity
```

and neither dimension subsumes the other.

## C5 eligibility consequence

All four real components satisfy:

```text
C5a valid-component result = PASS
C5b valid-component result = PASS
STRICT_AND policy safety on preregistered controls = PASS
```

Therefore E25H records:

```text
strict_c5_eligible = true
```

for all four components.

This is **eligibility evidence**, not an automatic mutation of `pct_e25d_closure_atlas.json` and not an automatic promotion of any MAPEOGEO semantic edge. Promotion remains a separate governed action.

C3 and C4 remain `NOT_APPLICABLE` for these four scalar/decision contracts. C5 eligibility does not retroactively make chain-map or homology evidence applicable.

## Interpretation

The central result is not merely that the strict policy performed better. The experiment isolates why C5 needs two axes.

A correct exact map with the wrong source identity is mathematically valid but semantically misbound. A correctly bound provenance chain with a corrupted witness map is historically authentic but mathematically wrong. Lower closure layers can remain intact in either case.

C5 therefore serves a different role from C0–C4:

```text
C0: Are these the intended identities?
C1: Is the claimed evidence/certificate chain valid?
C2: Do independent executable routes agree on the declared contract result?
C3: Does an explicit chain map commute, where applicable?
C4: Does its induced homology action match, where applicable?
C5a: Is the exact witness-bearing transformation the same?
C5b: Is that exact transformation bound to the intended source/provenance lineage?
```

For applicable subgates, the evidence from E25H supports the conjunction rather than substitution.

## Reproducibility

The branch CI regenerates all three E25G/E25H evidence files into a separate candidate directory before running regression tests. The committed frozen JSON is then compared to fresh in-process execution. Candidate evidence is also uploaded as a CI artifact.

This prevents a committed result file from serving as its own oracle and detects stale or manually altered evidence. During implementation this gate caught a one-character identity transcription error in the frozen LP GEO id; the final frozen provenance blob then matched the fresh generated blob exactly.

## Claim boundary

E25G/E25H establishes exact witness-bearing C5 adapters and a strict-versus-permissive policy comparison for the four frozen source-bound contracts and their preregistered synthetic adversarial controls.

It does **not** establish:

- universal categorical equality of arbitrary MAPEOGEO paths;
- completeness of these normal forms for all mathematics;
- whole-repository C5 closure;
- applicability of C3/C4 to contracts where those structures are absent;
- automatic theorem proof or formal verification; or
- permission to promote graph semantics without the existing evidence/formalization process.

The supported engineering conclusion is narrower and useful: when exact morphism equality and provenance binding are both meaningful, the tested evidence supports requiring both before C5 closure is considered eligible.
