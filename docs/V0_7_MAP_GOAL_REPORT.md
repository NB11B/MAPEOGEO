# MAPEOGEO v0.7 — MAP Goal Utility + Equivalence Promotion Report

**Status: PASS**

## Governing goal

MAPEOGEO is not an EO-vs-GEO benchmark. The goal is a source-grounded mathematical knowledge graph in which the same mathematics can carry simultaneous EO and GEO representations, those representations help organize and navigate mathematical structure, and correctness can be promoted through explicit executable/formal certificates toward trusted proof verification.

v0.7 therefore asked two integrated questions:

1. Do the frozen, independently derived v0.6 EO/GEO views provide useful held-out proof-dependency navigation signal?
2. Can real source declarations begin moving from candidate/direct evidence to certified cross-view relations without changing the core graph ontology?

The design and gates were preregistered at commit `40ecceb359ec62b675804e136f1dc85385a7c703` before any full v0.7 scientific result was observed.

## Accepted result

```text
OVERALL: PASS
HELD-OUT EXPLICIT PROOF DEPENDENCIES: 126
HELD-OUT SOURCE QUERIES: 113

EO MRR: 0.0233076
GEO MRR: 0.0262003
DUAL-MAX MRR: 0.0212911
SOURCE-PAGE PROXIMITY MRR: 0.238163

DUAL-UNION FILTER RECALL: 88.89%
MEAN CANDIDATE REDUCTION: 36.03%
MEDIAN CANDIDATE REDUCTION: 28.10%

SOURCE-BOUND EXECUTABLE CERTIFICATES: 4 / 4 PASS
SAME_SEMANTICS PROMOTIONS: 2
GRAPH: 2,226 nodes / 23,305 edges
```

All preregistered gates passed.

## Held-out proof-navigation test

The holdout split was fixed by hashing source dependency-edge IDs:

```text
sha256("MAPEOGEO-V0.7-HOLDOUT|" + dependency_edge_id) mod 5 == 0
```

No learned weights were fit. EO and GEO similarity were derived from the frozen v0.6 family assignments. `dual` used the maximum of the EO and GEO similarities. Each method was compared against target-chapter-matched random targets over 500 deterministic permutations.

### EO

- MRR: **0.0233076**
- Hits@10: **8.73%**
- Hits@50: **25.40%**
- median rank: **210.75**
- matched-random MRR: **0.0134089**
- delta: **+0.0098987**
- one-sided permutation p: **0.01996**

### GEO

- MRR: **0.0262003**
- Hits@10: **9.52%**
- Hits@50: **22.22%**
- median rank: **677.5**
- matched-random MRR: **0.0160166**
- delta: **+0.0101836**
- one-sided permutation p: **0.01597**

### Dual-max

- MRR: **0.0212911**
- Hits@10: **7.14%**
- Hits@50: **29.37%**
- median rank: **164.0**
- matched-random MRR: **0.0135924**
- delta: **+0.0076987**
- one-sided permutation p: **0.01198**

All three frozen semantic representations carried non-random held-out proof-navigation signal under the preregistered control.

The combined score did **not** outperform both individual views in MRR, and no such superiority gate was preregistered. The dual view instead showed its clearest utility as a candidate filter: the EO/GEO union removed **36.03%** of candidate declarations on average while retaining **88.89%** of the actual held-out proof dependencies.

This is useful routing evidence, but it is not safe pruning: an 88.89% recall filter would exclude roughly one held-out true dependency in nine. Until an exact certificate is available, the graph must preserve a fallback path rather than treating this filter as fail-closed exclusion.

## Source locality is a major signal

The source-page proximity control achieved MRR **0.238163**, much higher than the EO, GEO, or dual semantic scores alone.

This is an important architectural result, not a reason to discard EO/GEO. Mathematical exposition is strongly local: definitions and lemmas are often introduced near their uses. The result says the MAP graph should not throw away provenance/order/topological locality when it adds semantic operator structure.

A better overall architecture is therefore multi-signal:

```text
source/proof topology + EO operator structure + GEO relational geometry + certificates
```

EO/GEO provide semantic structure that is non-randomly aligned with proof dependencies; locality provides a strong routing prior; exact/formal certificates decide what can safely be promoted or excluded.

## Cross-view equivalence promotion

Four declarations were source-bound by declaration identity and the accepted v0.6 statement SHA-256, then evaluated with preregistered executable contracts.

### Theorem 6.16 — rank/nullity

- source hash: matched
- source recognizer: PASS
- executable contract: **682** exhaustive GF(2) matrix cases over dimensions 1..3
- result: PASS
- graph relation: scoped `EQUIVALENT_TO`

This is not promoted to theorem-wide `SAME_SEMANTICS` because the executable domain is a bounded finite subset of the theorem's full mathematical domain.

### Definition 44.6 — convex hull

- source hash: matched
- source recognizer: PASS
- executable contract: **279** exact rational one-dimensional convex-combination / hull-membership cases
- result: PASS
- graph relation: **`SAME_SEMANTICS`** under the declared definitional/bounded-exhaustive contract

### Theorem 47.9 — linear-programming duality

- source hash: matched
- source recognizer: PASS
- executable contract: **2,457** exact positive one-dimensional rational LP cases
- result: PASS
- graph relation: scoped `EQUIVALENT_TO`

Again, the bounded executable family is not sufficient to claim theorem-wide equivalence.

### Definition 53.4 — Gaussian kernel

- source hash: matched
- source recognizer: PASS
- symbolic exponent identity: PASS
- graph relation: **`SAME_SEMANTICS`**

These promotions demonstrate that the existing ontology can carry the transition:

```text
candidate/direct EO+GEO evidence
        ↓
source-bound executable certificate
        ↓
EQUIVALENT_TO or SAME_SEMANTICS
```

without creating a second graph architecture.

## What v0.7 changes about the project

The result supports moving beyond the question “can EO and GEO both represent the corpus?” That was addressed by v0.5/v0.6. v0.7 shows that:

- EO and GEO independently retain statistically detectable information about held-out proof dependencies;
- their union can reduce the proof-navigation candidate space while retaining most true dependencies;
- selected source declarations can be promoted into certified cross-view relations;
- and source/proof locality is too important to discard from the final MAP architecture.

This points toward a knowledge graph whose retrieval layer is **hybrid**, not purely semantic, while its correctness layer remains certificate/formal-verifier driven.

## Engineering provenance

Preregistered scientific specification:

`40ecceb359ec62b675804e136f1dc85385a7c703`

The first complete scientific execution occurred at head:

`6d3518f481ced65423f3d355a4db84e07e07152e`

GitHub Actions run `34926832447` produced the same PASS headline metrics, but the external artifact validator referenced the output key `dual_max` instead of the emitted key `dual`. No scientific gate, holdout, representation rule, certificate contract, or measured result was changed.

The validator-only correction was committed as:

`4bb0dbf1f149e4ce1cfc5fec08ac4bfab0e5e3ce`

The first fully green accepted execution is:

- CI head: `4bb0dbf1f149e4ce1cfc5fec08ac4bfab0e5e3ce`
- Actions run: `34927089194`
- job: `104247320981`
- artifact: `10379718607`
- artifact ZIP SHA-256: `8d42bcdf9e226bbc67f5eb0b2a715a7894356d199a8501014aaca2c1919708c2`

The packaging/unit-test repairs before the first full scientific execution did not alter the preregistered scientific specification.

## Copyright and source boundary

The Gallier/Quaintance PDF was downloaded transiently during CI and deleted after processing. Persistent evidence contains source hashes/locators, graph structure, measured results, and independently generated certificates. Source prose and page images are not redistributed.

See `LICENSE.md` and `THIRD_PARTY_NOTICES.md`.

## Claim boundary

v0.7 supports:

- non-random held-out proof-navigation utility from frozen EO and GEO structures;
- useful but non-exact candidate reduction from their union;
- source-bound executable cross-view promotion on four real declarations;
- two conservative `SAME_SEMANTICS` promotions;
- continuation of the same graph ontology from source ingestion through certified equivalence.

v0.7 does **not** establish:

- universal EO/GEO theorem equivalence;
- exact-safe proof-search pruning from the current semantic filter;
- complete proof synthesis;
- complete implicit dependency reconstruction;
- or whole-corpus Lean/kernel verification.

The next major stage should move toward the actual MAP endpoint: formal-verifier-backed graph nodes and proof paths, while retaining source topology, EO, GEO, and certificate evidence as distinct but interoperable layers.
