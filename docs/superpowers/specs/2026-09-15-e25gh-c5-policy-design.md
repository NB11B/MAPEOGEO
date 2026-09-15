# E25G–E25H C5 Exact-Morphism and Provenance Policy Design

**Date:** 2026-09-15  
**Branch:** `agent/pct-computational-architecture`  
**Status:** Approved design, self-reviewed and frozen before implementation

## Purpose

E25D–E25F established the C0–C5 closure hierarchy. For the four real source-bound EO/GEO/FORMAL contracts, C0–C2 pass, C3/C4 are not applicable, and C5 is not established because exact morphism/provenance evidence has not been serialized.

E25G and E25H define C5 and test whether either half of C5 can safely substitute for the recommended strict conjunction.

The governing recommendation is:

```text
C5a = exact morphism equality
C5b = provenance-bound correspondence
C5  = AND of all applicable C5 subgates
```

If a subgate genuinely does not apply, it is `NOT_APPLICABLE`; it is never silently counted as evidence.

## C5 semantics

### C5a — Exact morphism equality

C5a asks whether independent EO, GEO, and FORMAL routes induce the same **normalized witness-bearing transformation**, not merely the same final scalar or Boolean result.

The three route implementations must be algorithmically independent at the witness-generation layer. They may share only:

- immutable input fixtures;
- canonical serialization;
- exact equality comparison; and
- common primitive data types.

They may **not** call one shared helper that computes the mathematical witness being compared. Otherwise C5a would test one implementation three times.

A C5a adapter returns an exact canonical record. Endpoint equality without witness equality is insufficient.

Allowed verdicts remain:

`PASS`, `FAIL`, `NOT_APPLICABLE`, `NOT_ESTABLISHED`, `INVALID`, `ERROR`.

### C5b — Provenance-bound correspondence

C5b asks whether the C5a morphism is bound to the correct source identity and evidence lineage. A passing record must bind:

- component id;
- source statement SHA-256;
- contract name;
- formal scope;
- source artifact digest and audited source commit;
- EO/GEO/FORMAL representation ids;
- relevant certificate ids;
- adapter id/version;
- adapter/content SHA-256; and
- predecessor evidence ids from the C1/C2 chain.

A mathematically correct morphism copied from the wrong source object, wrong formal scope, or altered adapter lineage fails C5b even when C5a passes.

Canonical provenance JSON uses sorted keys, UTF-8, no timestamps or machine paths, and compact separators before hashing.

## Strict C5 policy

The production candidate is:

```text
STRICT_AND:
    C5 = PASS iff every applicable C5 subgate is PASS.
```

For all four current real contracts, both C5a and C5b are applicable.

E25G/E25H do not rewrite semantic edge types or the E25D closure atlas. A component becomes `strict_c5_eligible=true` only if:

1. its own C5a passes;
2. its own C5b passes; and
3. E25H finds `STRICT_AND` acceptable under the preregistered policy safety criterion.

That flag is evidence for a later atlas update, not automatic promotion.

# E25G — Exact Morphism Contract Audit

## Inputs

E25G consumes only the four `REAL_SOURCE_BOUND` entries from `evidence/pct_e25d_real_component_manifest.json`, plus the existing source/certificate/formal lineage and E25C executable evidence. Synthetic E25B calibration triangles are excluded from real C5 coverage.

## 1. Rank-nullity

### Domain

All GF(2) matrices with `1 <= m,n <= 3`, matching the bounded E25C contract.

### Canonical morphism

For every matrix `A`:

```text
{
  matrix,
  rank,
  rref,
  pivot_columns,
  nullity,
  canonical_nullspace_basis
}
```

The nullspace basis is canonical: free columns ascending, basis vectors serialized in that order.

### Independent routes

- **EO:** exact GF(2) row elimination directly computes RREF, pivots, rank, and free-variable kernel basis.
- **GEO:** enumerate the linear map on all domain vectors to determine image size/kernel points, then reconstruct a canonical kernel basis independently; RREF is independently reconstructed from row-space closure rather than calling EO elimination.
- **FORMAL:** a separate exact matrix routine computes canonical RREF/kernel witnesses from the formal matrix object.

Shared code may serialize the final record but may not compute the witness.

## 2. Convexity

### Domain

Every nonempty subset of `{-2,-1,0,1,2}` and every half-integer query in `[-2,2]`, matching E25C.

### Canonical morphism

For `(point_set, x)`:

```text
{
  hull_lo,
  hull_hi,
  member,
  witness_type,
  witness
}
```

If membership is true and `lo < hi`:

```text
lambda = (x-lo)/(hi-lo)
coefficients = [1-lambda, lambda]
endpoints = [lo, hi]
```

All rationals are reduced exactly. A singleton hull uses the singleton identity witness. A rejected point records `LEFT` or `RIGHT` plus the exact rational gap to the nearest endpoint.

### Independent routes

- **EO:** solve exact barycentric coefficients and validate their simplex constraints.
- **GEO:** construct the one-dimensional convex hull interval first, decide containment geometrically, then derive the canonical geometric witness.
- **FORMAL:** decide the pair of endpoint inequalities and derive the witness from those exact inequalities.

No route may call another route's witness generator.

## 3. Positive one-dimensional LP duality

### Domain

Positive integer coefficients in `{1,2,3}` with dimensions `m in {1,2,3}`, matching E25C.

### Canonical morphism

For `(a,b,c)` define exact ratios `r_i=b_i/a_i` and `r*=min_i r_i`. Return:

```text
{
  ratios,
  optimum = c*r*,
  active_indices = [i : r_i = r*],
  canonical_active_witnesses
}
```

For each active index `i`, the witness is exactly:

```text
{
  index: i,
  ratio: b_i/a_i,
  dual_multiplier: c/a_i,
  primal_value: c*(b_i/a_i),
  dual_value: b_i*(c/a_i),
  equality_holds: true
}
```

`active_indices` contains **all** minimizers sorted ascending. `canonical_active_witnesses` uses the same index order. An arbitrary first-minimizer choice is not a valid C5a morphism.

### Independent routes

- **EO:** calculate all exact ratios and their algebraic minimum directly.
- **GEO:** identify every active supporting constraint/facet and compute its equality witness from the active geometry.
- **FORMAL:** independently evaluate the finite exact objective candidate set and construct all minimizer certificates.

## 4. Gaussian exponent identity

### Domain

The persisted scalar real Gaussian exponent identity.

### Canonical morphism

Normalize every route over basis:

```text
[nx/s2, ny/s2, dot/s2]
```

with exact coefficient vector:

```text
[-1/2, -1/2, 1]
```

and canonical normal-form expression ordered by that basis.

### Independent routes

- **EO:** collect exact algebraic coefficients from the expanded bilinear form.
- **GEO:** expand the squared-distance geometry `-(nx+ny-2dot)/(2s2)` independently.
- **FORMAL:** normalize the symbolic equality through a separate exact simplification route.

C5a requires equality of both coefficient vector and canonical expression.

## C5b provenance record

For each component:

```text
{
  component_id,
  source_statement_sha256,
  contract,
  formal_scope,
  source_artifact_digest,
  source_commit_sha,
  eo_id,
  geo_id,
  formal_id,
  certificate_ids,
  adapter_id,
  adapter_sha256,
  predecessor_evidence_ids
}
```

`adapter_sha256` is computed from the exact UTF-8 bytes of the route-adapter source participating in E25G, not from a manually entered digest. The canonical provenance record is then separately hashed.

C5b passes only when all required bindings exist, agree on component identity, and point back to the frozen audited source lineage.

## E25G outputs

```text
evidence/pct_e25g_exact_morphism_audit.json
evidence/pct_e25g_provenance_bindings.json
```

Each component records C5a and C5b separately. E25G never mutates `pct_e25d_closure_atlas.json`.

## E25G acceptance

E25G passes only if:

1. all four real components are evaluated;
2. all three route implementations are independent at witness generation;
3. every C5a comparison is exact and witness-bearing;
4. every C5b record is source-, scope-, certificate-, artifact-, and adapter-digest-bound;
5. valid controls have zero exact-morphism disagreement;
6. no synthetic fixture contributes real C5 evidence; and
7. fresh execution reproduces frozen evidence byte-for-byte after canonical serialization.

# E25H — C5 Policy Comparison

E25H tests the strict recommendation against permissive alternatives instead of assuming the recommendation is correct.

## Policies

### STRICT_AND

```text
PASS iff C5a == PASS and C5b == PASS
```

### MAP_ONLY

```text
PASS iff C5a == PASS
```

This represents any contract policy that omits provenance as a required C5 axis.

### PROVENANCE_ONLY

```text
PASS iff C5b == PASS
```

This represents any contract policy that omits exact-morphism equality.

### ANY_AXIS — diagnostic only

```text
PASS iff C5a == PASS or C5b == PASS
```

`ANY_AXIS` is never a production candidate; it quantifies the weakness of treating either axis as sufficient.

A type-dependent single-axis policy can be considered safe for a contract only if the selected axis has zero false accepts on **that contract's complete preregistered adversarial set**. E25H evaluates MAP_ONLY and PROVENANCE_ONLY separately for every contract; it does not choose an axis after seeing results.

## Adversarial controls per contract

Every real contract receives all five control families.

### A. Correct morphism + wrong provenance

Keep C5a unchanged; alter source hash, component binding, formal scope, certificate lineage, or adapter digest.

Expected:

```text
C5a PASS
C5b FAIL
STRICT_AND FAIL
MAP_ONLY false-accepts
PROVENANCE_ONLY rejects
```

### B. Wrong morphism + correct provenance

Keep provenance valid while corrupting one canonical witness field without changing the C2 endpoint when possible.

Expected:

```text
C5a FAIL
C5b PASS
STRICT_AND FAIL
MAP_ONLY rejects
PROVENANCE_ONLY false-accepts
```

### C. Same endpoint + wrong witness map

- rank: preserve rank/nullity but corrupt RREF, pivot, or kernel witness;
- convexity: preserve membership but corrupt barycentric/separation witness;
- LP: preserve optimum but corrupt the complete active-index/witness set;
- Gaussian: preserve one sampled endpoint evaluation while altering the canonical coefficient/normal-form map.

Expected first failure: C5a.

### D. Correct lineage + altered transformation

Keep all source/certificate/provenance bindings valid while altering the executable exact transformation.

Expected first failure: C5a.

### E. Exact map rebound across identities

Use a valid exact record but bind it to another source component/contract identity.

Expected first failure: C5b.

## Metrics

For every `(contract, policy)` pair:

```text
valid_accepts
valid_rejects
false_accepts
false_rejects
adversarial_cases
false_accept_rate
false_reject_rate
```

Primary production-policy criterion:

```text
false_accepts == 0
for every contract on every preregistered adversarial case
```

Secondary criterion:

```text
valid_rejects == 0
```

`STRICT_AND` is empirically preferred only if it meets both criteria and one or more permissive policies false-accept a case that STRICT_AND rejects. If a single-axis policy genuinely has zero false accepts for a contract, the report must state that rather than forcing a strict-policy victory.

## E25H outputs

```text
evidence/pct_e25h_policy_comparison.json
docs/PCT_E25G_E25H_C5_POLICY_REPORT.md
```

Results are reported per contract and per policy, not only in aggregate.

# Architecture and files

```text
experiments/pct_e25gh/
    __init__.py
    rank_morphism.py
    convex_morphism.py
    lp_morphism.py
    gaussian_morphism.py
    provenance.py
    policies.py
    adversaries.py
    test_e25gh.py

evidence/
    pct_e25g_exact_morphism_audit.json
    pct_e25g_provenance_bindings.json
    pct_e25h_policy_comparison.json

docs/
    PCT_E25G_E25H_C5_POLICY_REPORT.md
```

Separate morphism files make route independence inspectable and keep each contract small enough to review. The existing PCT CI workflow compiles and executes the new suite.

# Data flow

```text
E25D real component manifest
        |
        +--> independent EO/GEO/FORMAL exact adapters --> C5a
        |
        +--> source/certificate/formal/adapter lineage --> C5b
                                                        |
                                                        v
                                             E25G C5a/C5b audit
                                                        |
                         +------------------------------+------------------------------+
                         |                              |                              |
                      STRICT_AND                     MAP_ONLY                  PROVENANCE_ONLY
                         |                              |                              |
                         +------------- preregistered adversarial matrix -------------+
                                                        |
                                                        v
                                             E25H policy comparison
```

# Fail-closed rules

1. Missing exact witness data yields `NOT_ESTABLISHED`, never inferred `PASS`.
2. Missing provenance yields `NOT_ESTABLISHED`; contradictory provenance yields `FAIL`.
3. Endpoint equality cannot substitute for exact witness equality.
4. Correct provenance cannot repair a wrong morphism.
5. Correct morphism cannot repair wrong provenance.
6. C5 does not imply C3/C4 applicability.
7. Synthetic controls validate policy behavior but never promote real component closure.
8. E25G/H may mark `strict_c5_eligible`; they do not rewrite the atlas or graph.
9. No floating tolerance is introduced into exact C5a equality.
10. EO/GEO/FORMAL witness generators must remain independent; a shared witness-producing implementation invalidates the C5a test.

# Scientific question

E25H answers:

```text
Can a contract safely omit either exact-morphism equality or provenance binding at C5?
```

The recommendation is `STRICT_AND`, but the result is not predetermined.

# Claim boundary

A passing E25G/E25H stage establishes exact witness-bearing C5 adapters and a policy comparison on the four frozen source-bound contracts and their synthetic adversarial controls. It does not establish universal categorical equality of all MAPEOGEO paths, universal completeness of the chosen normal forms, whole-repository C5 closure, or permission to promote semantic relations without the existing evidence/formalization process.
