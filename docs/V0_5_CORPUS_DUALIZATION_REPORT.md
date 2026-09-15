# MAPEOGEO v0.5 — Corpus Dualization Audit Report

**Status: PASS**

## Full-source result

- PDF pages: 2,204
- Deduplicated declarations: 1,355
- Definitions recovered: 463
- Propositions: 654
- Theorems: 195
- Lemmas: 14
- Corollaries: 29
- Chapters with declarations: 55 / 57
- Proof blocks: 609
- Explicit proof cross-references: 704
- Resolved dependency references: 638
- Unresolved dependency references: 66 (9.38%)
- Direct controlled semantic-tag coverage: 98.52%
- Chapter-prior fallback only: 20
- EO/GEO dual-candidate coverage: 100.00%
- v0.3 fixture ontology recovery: 20 / 20
- Graph: 2,183 nodes / 18,189 edges

## Parser repair result

v0.4 detected no numbered definitions. v0.5 added Unicode NFKC normalization and split-line heading recognition. The full rerun recovered **463 numbered definitions** while increasing total deduplicated declarations from 891 to 1,355.

## Controlled ontology

The most frequent controlled concepts were:

- `VECTOR_SPACE`: 717
- `MATRIX_OPERATOR`: 534
- `ALGEBRAIC_STRUCTURE`: 439
- `NORM_METRIC`: 356
- `TOPOLOGY`: 232
- `AFFINE_PROJECTIVE`: 221
- `KERNEL_SIMILARITY`: 201
- `POLYNOMIAL_MODULE`: 199
- `CONVEX_GEOMETRY`: 187
- `DIRECT_SUM`: 170
- `OPTIMIZATION`: 170
- `FACTORIZATION`: 164
- `DUALITY`: 149
- `BILINEAR_FORM`: 144
- `DIFFERENTIAL_TANGENT`: 137

These counts are multi-label: one declaration may carry several concepts.

## Interpretation

The corpus now has a source-grounded graph layer and a controlled dualization layer. For each imported declaration, v0.5 records source provenance, proof-reference structure, controlled mathematical concepts, and candidate EO/GEO operator families.

`DUAL_CANDIDATE` is deliberately weaker than `SAME_SEMANTICS`. It means both operator languages have an ontology family capable of expressing the tagged mathematical structure. It does **not** establish theorem-level executable equivalence.

## What the result supports

The preregistered audit supports broad simultaneous EO/GEO **candidate representability** over the source corpus while preserving the v0.3 verified fixture layer and the v0.4 source-dependency layer. All 13 preregistered gates passed.

## What remains unproven

The audit does not measure semantic-tag precision, does not prove executable EO/GEO equivalence for the 1,355 imported declarations, does not reconstruct implicit proof dependencies, and does not emit or verify Lean proofs. Those are separate next-stage gates.
