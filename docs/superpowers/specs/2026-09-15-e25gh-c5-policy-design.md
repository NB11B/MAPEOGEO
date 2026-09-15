# E25G–E25H C5 Exact-Morphism and Provenance Policy Design

**Date:** 2026-09-15  
**Branch:** `agent/pct-computational-architecture`  
**Status:** Approved design, frozen before implementation

## Purpose

E25D–E25F established a closure hierarchy C0–C5 and showed that different fault classes are first detectable at different layers. For the four real source-bound EO/GEO/FORMAL contracts, C0–C2 currently pass, C3/C4 are not applicable, and C5 is not established because exact morphism/provenance evidence has not yet been serialized.

E25G and E25H define what C5 means and test whether a permissive policy can safely substitute for the recommended strict policy.

The governing recommendation is:

```text
C5a = exact morphism equality
C5b = provenance-bound correspondence
C5  = AND of all applicable C5 subgates
```

If a subgate is genuinely not applicable, it is recorded `NOT_APPLICABLE`; it is never silently counted as evidence. The alternative policies are experimental counterfactuals only.

## Governing C5 semantics

### C5a — Exact morphism equality

C5a asks whether independent EO/GEO/FORMAL routes induce the same **normalized witness-bearing transformation**, not merely the same final scalar or Boolean result.

A C5a adapter must therefore return a canonical record whose equality is exact under the declared bounded contract domain. Endpoint equality without witness equality is insufficient.

Allowed verdicts remain:

`PASS`, `FAIL`, `NOT_APPLICABLE`, `NOT_ESTABLISHED`, `INVALID`, `ERROR`.

### C5b — Provenance-bound correspondence

C5b asks whether the exact morphism record is bound to the correct source identity and evidence lineage. A passing record must bind at least:

- source statement SHA-256;
- contract name;
- formal scope;
- source artifact digest and audited source commit;
- EO/GEO/FORMAL representation ids;
- relevant certificate ids;
- exact adapter identifier/version;
- adapter/content digest;
- E25C/E25G evidence lineage.

A mathematically correct morphism copied from the wrong source object, wrong formal scope, or altered adapter lineage fails C5b even if C5a passes.

## Strict C5 policy

The production candidate policy is:

```text
STRICT_AND:
    C5 = PASS iff every applicable C5 subgate is PASS.
```

For the four current real source-bound contracts, both C5a and C5b are applicable, so both must pass.

No C5 result changes repository semantic edge types automatically. A passing E25G/E25H stage produces only `strict_c5_eligible=true` evidence for later closure-atlas promotion.

# E25G — Exact Morphism Contract Audit

E25G executes C5a and C5b independently for each of the four real source-bound contracts.

## 1. Rank-nullity contract

### Bounded execution domain

Reuse the E25C finite GF(2) matrix domain: all matrices with `1 <= m,n <= 3`.

### Canonical exact morphism

For each matrix `A`, every route must return the same normalized record:

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

The RREF and nullspace basis are exact over GF(2). The nullspace basis ordering is canonical: free columns ascending, basis vectors serialized in ascending free-column order.

C5a passes only if EO, GEO, and FORMAL adapters produce identical normalized records for every bounded input.

This is stronger than E25C, which compared the rank-nullity identity result rather than the full canonical witness structure.

## 2. Convexity contract

### Bounded execution domain

Reuse the E25C finite one-dimensional real-rational control family: nonempty subsets of `{-2,-1,0,1,2}` and half-integer query points in `[-2,2]`.

### Canonical exact morphism

For each `(point_set, x)`, every route returns:

```text
{
  hull_lo,
  hull_hi,
  member,
  witness_type,
  witness
}
```

If `member=true` and the hull is nondegenerate, `witness` is the exact reduced rational barycentric record:

```text
lambda = (x-lo)/(hi-lo)
coefficients = [1-lambda, lambda]
endpoints = [lo, hi]
```

For a singleton hull, the canonical witness is the singleton identity witness.

If `member=false`, the witness records the canonical side (`LEFT` or `RIGHT`) and exact rational gap to the nearest hull endpoint.

C5a therefore distinguishes equal membership decisions from different or malformed witness maps.

## 3. Positive one-dimensional LP duality contract

### Bounded execution domain

Reuse the E25C domain with positive integer coefficients in `{1,2,3}` and dimensions `m in {1,2,3}`.

### Canonical exact morphism

For each `(a,b,c)`, return:

```text
{
  ratios = [b_i/a_i],
  optimum,
  active_indices,
  canonical_active_witnesses
}
```

`active_indices` contains **all** minimizers, sorted ascending; the exact morphism must not depend on an arbitrary first-minimizer choice. `canonical_active_witnesses` contains the exact primal/dual equality witness for every active index, serialized by ascending index.

This explicitly tests a stronger notion than E25C's scalar optimum agreement.

## 4. Gaussian exponent identity contract

### Exact symbolic domain

Use the persisted scalar real Gaussian exponent identity.

### Canonical exact morphism

Normalize all three routes into the exact rational coefficient map over basis

```text
[nx/s2, ny/s2, dot/s2]
```

with canonical vector

```text
[-1/2, -1/2, 1]
```

and an exact symbolic normal-form expression. C5a requires equality of both canonical coefficient vector and normalized expression.

## C5b provenance record

For each of the four contracts, E25G creates a canonical provenance record:

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

The record is hashed canonically. C5b passes only if all expected bindings are present, internally consistent, and tied to the same component identity as the C5a record.

## E25G outputs

```text
evidence/pct_e25g_exact_morphism_audit.json
evidence/pct_e25g_provenance_bindings.json
```

Each component records C5a and C5b separately. E25G does not mutate `pct_e25d_closure_atlas.json`.

## E25G acceptance

E25G passes only when:

1. all four real source-bound components are evaluated;
2. each C5a comparison is exact and witness-bearing;
3. each C5b record is source-bound and digest-bound;
4. valid controls have zero EO/GEO/FORMAL exact-morphism disagreements;
5. no synthetic control is counted as real C5 evidence; and
6. fresh execution reproduces frozen evidence exactly.

# E25H — C5 Policy Comparison

E25H tests the recommended strict policy against permissive alternatives.

## Policies

Three policies are evaluated for every contract:

### STRICT_AND

```text
PASS iff C5a == PASS and C5b == PASS
```

### MAP_ONLY

```text
PASS iff C5a == PASS
```

This models any type-dependent policy that elects to trust exact map equality without provenance.

### PROVENANCE_ONLY

```text
PASS iff C5b == PASS
```

This models any type-dependent policy that elects to trust provenance lineage without exact map equality.

For completeness, the report may also include the explicitly unsafe `ANY_AXIS` policy (`C5a OR C5b`), but it is never a production candidate.

A type-dependent single-axis policy is considered safe only if the selected axis has zero false acceptance for that contract's adversarial controls. E25H does not preselect an axis to make the result favorable; it evaluates both single-axis possibilities independently for all four contracts.

## Required adversarial controls

Every real contract receives at least these controls:

### A. Correct exact morphism + wrong provenance

The exact C5a record is unchanged, while one provenance binding is altered to a different source hash/component/scope or adapter lineage.

Expected:

```text
C5a PASS
C5b FAIL
STRICT_AND FAIL
MAP_ONLY false-accepts
PROVENANCE_ONLY rejects
```

### B. Wrong exact morphism + correct provenance

Provenance is unchanged, while a canonical witness field is altered without changing the lower-layer endpoint result where possible.

Expected:

```text
C5a FAIL
C5b PASS
STRICT_AND FAIL
MAP_ONLY rejects
PROVENANCE_ONLY false-accepts
```

### C. Same endpoint value + wrong witness map

Contract-specific witness corruption preserves the C2 result but alters C5a structure. Examples:

- rank: rank/nullity unchanged but RREF/nullspace witness corrupted;
- convexity: membership unchanged but barycentric or separation witness corrupted;
- LP: optimum unchanged but active-index/witness set corrupted;
- Gaussian: semantically equivalent endpoint evaluation on a sampled point is not sufficient if canonical coefficient/normal-form map differs.

Expected first failure: C5a.

### D. Correct source lineage + altered executable transformation

The source/certificate/provenance chain remains valid while the exact adapter transformation is altered.

Expected first failure: C5a.

### E. Exact map copied across identities

A valid C5a record from one contract/component is rebound to a different source identity.

Expected first failure: C5b.

## Policy metrics

For each policy and contract, record:

```text
valid_accepts
valid_rejects
false_accepts
false_rejects
adversarial_cases
false_accept_rate
false_reject_rate
```

The primary safety criterion is:

```text
A production C5 policy is acceptable only if false_accepts == 0
on every preregistered single-axis adversarial control.
```

Secondary criterion:

```text
valid_rejects == 0
```

A strict policy is considered empirically justified over a permissive policy if both accept the valid controls but the permissive policy false-accepts at least one preregistered adversarial control that STRICT_AND rejects.

## E25H outputs

```text
evidence/pct_e25h_policy_comparison.json
docs/PCT_E25G_E25H_C5_POLICY_REPORT.md
```

The report must show results per contract and per policy, not only aggregate totals.

# Architecture and files

Implementation extends the experimental surface only:

```text
experiments/pct_e25gh/
    __init__.py
    morphisms.py
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

The existing PCT CI workflow is extended to compile and execute the E25G/H suite.

# Data flow

```text
E25D real component manifest
        |
        +--> exact contract adapters --> C5a exact morphism records
        |
        +--> source/cert/formal lineage --> C5b provenance bindings
                                         |
                                         v
                              E25G C5a/C5b audit
                                         |
                    +--------------------+--------------------+
                    |                    |                    |
                 STRICT_AND           MAP_ONLY          PROVENANCE_ONLY
                    |                    |                    |
                    +---------- adversarial matrix ----------+
                                         |
                                         v
                              E25H policy comparison
```

# Fail-closed rules

1. Missing exact witness data yields `NOT_ESTABLISHED`, never `PASS`.
2. Missing provenance binding yields `NOT_ESTABLISHED` or `FAIL` according to whether evidence is absent or contradictory.
3. Endpoint equality cannot substitute for exact witness equality.
4. Correct provenance cannot repair a wrong exact morphism.
5. Correct exact morphism cannot repair wrong provenance.
6. C5 does not imply applicability of C3 or C4.
7. Synthetic adversarial controls validate the policy but never promote real component closure.
8. E25G/H may mark a component `strict_c5_eligible`; they do not automatically rewrite the E25D atlas or semantic graph.
9. All arithmetic remains exact where the contract is exact; no floating tolerance is introduced into C5a equality.

# Expected scientific question

E25H is designed to answer, not assume:

```text
Can a contract safely omit either exact-morphism equality or provenance binding at C5?
```

The recommendation is `STRICT_AND`, but the result is not predetermined. If a single-axis policy achieves zero false acceptance on all preregistered controls for a contract, the report must state that rather than forcing a strict-policy victory.

# Claim boundary

A passing E25G/E25H stage establishes exact witness-bearing C5 adapters and a policy comparison on the four frozen source-bound contracts and their synthetic adversarial controls. It does not establish universal categorical equality of all MAPEOGEO paths, universal completeness of the witness normal forms, whole-repository C5 closure, or permission to promote semantic relations without the existing evidence/formalization process.
