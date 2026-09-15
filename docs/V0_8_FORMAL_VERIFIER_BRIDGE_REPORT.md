# MAPEOGEO v0.8 — Formal-Verifier Bridge Report

**Status: PASS**

## Governing MAP objective

v0.8 was intentionally kept subordinate to the larger project goal. MAPEOGEO is not an EO-vs-GEO benchmark and Lean is not introduced as a replacement mathematical representation. The target remains one source-grounded mathematical graph in which source/proof topology, EO operator structure, GEO relational geometry, executable certificates, and formal proof terms are interoperable layers over the same mathematics.

The v0.8 question was therefore narrow and decisive:

```text
source declaration
  -> EO/GEO representations
  -> executable certificate
  -> FORMAL / Lean representation
  -> trusted kernel verification
```

The scientific specification was preregistered at commit:

`8879aed581bd721c3b41694a501b9cf3ee887ef2`

## Accepted result

```text
OVERALL: PASS
SOURCE-BOUND DECLARATIONS: 4
SOURCE HASHES MATCHED: 4 / 4
LEAN KERNEL CHECK: PASS
INDEPENDENT CHECKER: leanchecker — PASS
PROHIBITED PROOF ESCAPE HATCHES: 0
KERNEL-VERIFIED CERTIFICATES: 4 / 4
FORMAL COVERAGE OF V0.7 SOURCE-BOUND SET: 100.00%
GRAPH: 2,234 nodes / 23,321 edges
LEAN: 4.33.1
MATHLIB: v4.33.1
```

All accepted v0.8 gates passed.

## Formal source bindings

The four declarations are bound to the exact statement SHA-256 values accepted in v0.7, rather than to mutable source prose:

- Theorem 6.16 — rank-nullity — `9bb700afa17cb554b5d6962f561b2a75778073461cf7836eb19d894d06005a98`
- Definition 44.6 — convex hull — `98a05b33d579fb592b4b6cd34be92d14088eee7b7cdc4c20e0024a8a55cbad3a`
- Theorem 47.9 — linear-programming duality — `40f6f2ced2811e74cf5ba7e189488b6f415e0e3980e06d3806aaddcfd364bbfb`
- Definition 53.4 — Gaussian kernel — `7fd9b72cf464870a2a937fc0ae981b170ac307e935ca034aaa31867ef7f12514`

All four regenerated source hashes matched exactly.

## Lean formal contracts

### Theorem 6.16 — rank-nullity

`MAPEOGEOFormal.theorem_6_16_rank_nullity` formalizes the general finite-dimensional rank-nullity identity over a division ring using Mathlib's verified linear-map theorem. This formal contract is stronger in domain coverage than the bounded GF(2) executable certificate used in v0.7.

### Definition 44.6 — convex hull

`MAPEOGEOFormal.definition_44_6_two_point_convex_interval` verifies the exact real two-point convex-combination interval contract. This is a formal scope under the source-bound definition; it does not claim that the complete general convex-hull development in the source has already been autoformalized.

### Theorem 47.9 — linear-programming duality

`MAPEOGEOFormal.theorem_47_9_one_dim_positive_lp` verifies the positive one-dimensional LP contract: `b / a` is feasible under the stated positivity conditions and dominates every feasible point for a nonnegative objective coefficient. This remains a deliberately scoped formal theorem rather than a claim of complete formalization of the book's general LP duality theorem.

### Definition 53.4 — Gaussian kernel

`MAPEOGEOFormal.definition_53_4_gaussian_exponent_identity` verifies the exact scalar identity connecting the squared-distance Gaussian exponent to its inner-product-factorized form.

## Trust boundary

The accepted CI path used pinned Lean and Mathlib `v4.33.1`.

Normal `lake build` completed successfully. `#print axioms` for all four declarations reported only:

```text
[propext, Classical.choice, Quot.sound]
```

No `sorry`, `admit`, custom `axiom` declaration, or `unsafe` declaration is present in the source-bound formalization file.

The bundled Lean `leanchecker` independently checked the compiled environment and returned success. This is a separate environment-checking pass after normal Lean compilation.

## Nanoda tooling amendment

The original preregistration named Nanoda as the independent backstop. That path was actually attempted; it is **not** silently recorded as a pass.

On Lean/Mathlib `v4.33.1`, the Nanoda export path produced approximately 6.07 GB / 107.8 million lines and then the external checker failed while parsing the export with:

```text
Error: invalid digit found in string
```

The Lean project had already compiled successfully before that external parser failure. Nanoda is therefore recorded as `TOOLING_BLOCKED`, not PASS and not a formalization failure.

The post-preregistration substitution to bundled `leanchecker` is documented explicitly in `docs/V0_8_INDEPENDENT_CHECKER_AMENDMENT.md`. No source binding, formal statement, formal scope, EO/GEO relation, or MAP scientific claim was changed by that tooling amendment.

## Graph result

v0.8 extends the accepted v0.7 graph rather than creating a separate formal-mathematics database.

For each of the four source-bound declarations the graph now contains:

```text
source declaration
  <- REPRESENTS - FORMAL / Lean node
                     |
                     +-- VERIFIED_BY --> KERNEL_VERIFIED certificate
                     |
                     +-- EQUIVALENT_TO --> EO representation [declared formal scope]
                     |
                     +-- EQUIVALENT_TO --> GEO representation [declared formal scope]
```

The graph grew from 2,226 nodes / 23,305 edges to **2,234 nodes / 23,321 edges** while preserving unique IDs and valid endpoints.

This is the important architectural result: formal verification fits into the same semantic graph used for source topology, EO, GEO, and executable certificates. It does not require replacing the graph with a Lean-specific architecture.

## Accepted CI provenance

- accepted CI head: `2d0f83da16f651a3e535a98cef2f333d2cc61f0b`
- GitHub Actions run: `34930240957`
- job: `104256751991`
- artifact: `10381262672`
- artifact ZIP SHA-256: `2e6ca6856178404927dc1515ab3aa24a6835e02b11df68536f3148e72c43a777`

Accepted artifact files:

- `V0_8_SUMMARY.md` — `7b994347b534c68d7ae8ebe7d78c677b82f37e058b8b70d7294dc3f8f1e0c0c1`
- `formal_bridge_v0_8_report.json` — `751096f8e48a2af6cbb8eaf4ce84cd15696238ce6f2460f65422a04e3c55034d`
- `formal_kernel_certificates_v0_8.json` — `93cb69d763b4946c438c8b85e203cc43c2fb19aa856fe333f0f69b26aad8e8fe`
- `mapeogeo_formal_v0_8_graph.json.gz` — `4c4937cae15fb8313a486eefea2787fd536bb82235dbd9f27b12cf522193a7e5`

## Copyright and source boundary

The Gallier/Quaintance source PDF is downloaded transiently in CI and deleted after processing. Persistent formal evidence contains source identity/hash metadata, independently authored Lean formalizations, graph structure, and verifier/certificate results. Source prose and page images are not redistributed.

See `LICENSE.md` and `THIRD_PARTY_NOTICES.md`.

## What v0.8 establishes

v0.8 supports that the existing MAPEOGEO graph can carry a trusted formal-verification layer: source-bound declarations can coexist with EO and GEO representations, receive independently authored Lean formalizations, and acquire kernel-verified certificates without changing the core graph ontology.

This matters to the MAP objective because executable equivalence tests alone are not sufficient to establish general mathematical truth. A formal proof checker provides the fail-closed correctness layer needed as the graph scales from mathematical organization toward machine-verifiable mathematics.

## Claim boundary

v0.8 does **not** establish:

- whole-corpus autoformalization;
- theorem-wide EO↔GEO equivalence for all imported declarations;
- automatic proof synthesis;
- complete implicit proof-dependency reconstruction;
- or universal mathematical closure of EO or GEO.

The next major stage should therefore address the actual remaining MAP problem rather than add another representation layer: **automatically translate a substantial stratified subset of source graph nodes and candidate proof paths into Lean, measure kernel-accepted autoformalization coverage, and identify exactly which mathematical structures remain outside the EO/GEO/formal bridge.**
