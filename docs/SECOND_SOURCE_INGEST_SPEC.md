# MAPEOGEO — Second-Source Ingestion Specification

Copyright © 2026 NB11B. All rights reserved. See `LICENSE.md`.

## Purpose

This specification is frozen **before any second mathematical source is downloaded or parsed**.

The second source exists to test whether the trusted skeleton generalizes across provenance. It is not a license to ingest more prose. Coverage expands; the MAPEOGEO architecture does not change.

```text
source declaration
  -> EO / GEO candidate views
  -> executable test (optional, scoped)
  -> FORMAL statement
  -> kernel check
  -> graph promotion or refusal
```

Mathlib remains a verifier/library used by the kernel layer. It is not treated as a source corpus.

## Source-selection rule

A second source is eligible only if it provides enough source structure to support the same intake law used on the Gallier–Quaintance corpus:

- stable source identity and version;
- numbered or otherwise stable mathematical declarations;
- explicit proof references or locally recoverable declaration dependencies;
- substantial overlap with already identified interface/pinch mathematics;
- lawful access for transient analysis without repository redistribution of the source text.

Priority goes to a compact linear-algebra or convex-optimization source that reuses existing interface nodes. The purpose is to test cross-source identity before widening into unrelated domains.

No second PDF/text may be fetched by CI until a concrete source/version is added to this specification or a source-specific child specification with its URL, version identity, and reuse boundary.

## Object invariant

Every admitted source object must have all four fields, or it remains outside the trusted graph:

1. **Identity** — source locator plus frozen statement hash.
2. **Deps** — explicit source references only; unresolved-reference rate measured.
3. **Views** — independently detected EO and/or GEO candidates; views are never truth labels.
4. **Test** — executable contract, kernel certificate, or explicit `UNTESTED`.

`UNTESTED` is a first-class state. Missing evidence must never be converted into confidence by default.

## Strata

### S0 — source topology

Ingest stable declarations and explicit proof-reference edges. Persist source identity, locators, hashes, declaration kind/number, proof presence/hash, and derived graph structure. Do not persist copyrighted source prose or page images.

Stop if unresolved explicit references exceed the preregistered bound for the source.

### S1 — independent dual views

Run statement-only, identifier-disjoint EO and GEO detector banks. Proof text and source-location priors are excluded from the representation-coverage gate.

Stop if EO-direct, GEO-direct, or dual-direct coverage falls below source-specific preregistered bounds.

### S2 — dependency recovery

Hold out explicit source dependencies and compare:

- source locality;
- EO similarity;
- GEO similarity;
- dual-union routing.

Dual-union remains a candidate filter with fallback. It may not become exact pruning without a separate exact-safe certificate.

### S3 — executable certificates

Selected interface/pinch nodes may receive exact or residual-bounded computational contracts over a declared finite domain. A finite-slice result may write `EQUIVALENT_TO`; it may write scoped `SAME_SEMANTICS` only when the declared equivalence contract actually covers the promoted scope.

### S4 — formal/kernel verification

Formal statements remain separate `FORMAL` representation nodes bound to frozen source hashes and declared scopes. Only successful kernel verification may write `KERNEL_VERIFIED`.

No `sorry`, `admit`, custom `axiom`, or `unsafe` escape hatch is allowed in accepted source-bound formalizations.

### S5 — proof paths

For selected source declarations, traverse the source's explicit cited dependency chain. Every path vertex in the accepted path scope must be source-bound and kernel checked at its declared formal scope. Every source-reference edge must be accounted for independently of the kernel check.

Missing or incorrect source references become `WOUND` objects. They are not patched invisibly.

## Cross-source identity

The second-source experiment is specifically required to test whether two provenances can converge on one semantic/formal object without destroying either provenance.

Title/name similarity is never sufficient for merging.

A cross-source identity may be promoted only when there is an explicit equivalence contract. The graph should prefer:

```text
source A declaration --REPRESENTS--> canonical object
source B declaration --REPRESENTS--> canonical object
canonical object     --FORMAL------> verified representation
```

or an equivalent provenance-preserving structure.

Statement hashes are source identities, not universal semantic hashes. Two differently worded source statements may be mathematically equivalent without having the same statement hash. Conversely, equal-looking titles do not prove semantic identity.

The promotion ladder remains distinct:

- `DUAL_CANDIDATE`
- `EQUIVALENT_TO`
- `SAME_SEMANTICS`
- `KERNEL_VERIFIED`

## Interface-first sampling

The first second-source batch must overlap the current graph's high-value interface/pinch nodes before sampling broad page order. At minimum it should deliberately seek source declarations corresponding to several already-certified or high-pinch structures.

This lets the experiment measure:

- cross-source declaration alignment;
- whether EO/GEO views recover the same necks independently;
- whether one formal representation can serve multiple provenances without collapsing source identity;
- whether proof paths reuse already trusted support nodes;
- and whether new wounds expose source-specific differences.

## Required batch ledger

Every accepted second-source batch emits the same five-number family used by the existing intake process:

1. declarations added / proof blocks added / unresolved-reference rate;
2. EO-direct / GEO-direct / dual-direct coverage;
3. held-out dependency recall for the dual-union router, with fallback retained;
4. certificates added by class;
5. kernel-accepted proof paths, not only kernel-verified endpoints.

In addition, second-source batches must report cross-source identity outcomes:

- candidate cross-source matches;
- rejected matches;
- `EQUIVALENT_TO` promotions;
- `SAME_SEMANTICS` promotions;
- shared FORMAL nodes with two or more provenances;
- cross-source wounds.

## Stop rules

A batch fails closed if any of the following occurs:

- identity/version cannot be frozen;
- source reuse policy is incompatible with the no-prose repository boundary;
- unresolved explicit-reference rate exceeds its frozen bound;
- independent dual-view coverage collapses below its frozen gate;
- held-out routing is represented as exact pruning without an exact certificate;
- a finite executable slice is promoted beyond its tested domain;
- a formal node is attached to the wrong source hash;
- a kernel failure is promoted anyway;
- a source dependency is invented to fill a missing proof path;
- cross-source nodes are merged by title/string similarity without a semantic contract.

## Copyright and licensing boundary

MAPEOGEO repository content remains governed by `LICENSE.md`. External mathematical sources remain under their own copyright/license terms.

Unless a selected source explicitly permits redistribution, source files are transient inputs. Persistent MAPEOGEO artifacts may store source identity, hashes, locators, independently derived graph structure, EO/GEO candidates, independently authored executable/formal contracts, and verifier results. They must not redistribute source prose or page images.

## Acceptance condition before source selection

This specification itself satisfies the requirement to freeze second-source intake rules before touching another corpus. Selecting a concrete second source is a later action and must not alter these rules merely to make that source pass.
