# MAPEOGEO v0.8 — Formal-Verifier Bridge

## Governing goal

MAPEOGEO is not being extended with Lean as a separate mathematics system. The project goal remains one source-grounded mathematical knowledge graph in which source structure, EO operator structure, GEO relational geometry, executable certificates, and formal proof terms are interoperable views of the same mathematics.

A formal verifier is necessary for the MAP endpoint because executable tests and semantic similarity can support or falsify candidate equivalence, but they cannot provide the trusted proof-kernel acceptance required for machine-checkable mathematics.

v0.8 therefore tests the smallest decisive bridge:

```text
source declaration
  -> EO/GEO representations
  -> executable certificate
  -> Lean FORMAL representation
  -> kernel-checked certificate
```

The stage does **not** attempt whole-corpus autoformalization. It asks whether the existing graph can accept formal representations and verifier certificates without changing its core ontology, and whether the four source-bound v0.7 declarations can all be carried through that path.

## Frozen source bindings

The source identities and statement hashes are frozen from the accepted v0.7 artifact:

- Theorem 6.16, rank-nullity — `9bb700afa17cb554b5d6962f561b2a75778073461cf7836eb19d894d06005a98`
- Definition 44.6, convex hull — `98a05b33d579fb592b4b6cd34be92d14088eee7b7cdc4c20e0024a8a55cbad3a`
- Theorem 47.9, linear-programming duality — `40f6f2ced2811e74cf5ba7e189488b6f415e0e3980e06d3806aaddcfd364bbfb`
- Definition 53.4, Gaussian kernel — `7fd9b72cf464870a2a937fc0ae981b170ac307e935ca034aaa31867ef7f12514`

## Formal contracts

The Lean declarations are deliberately conservative about scope.

1. **Theorem 6.16 — rank-nullity.** Formalize the general finite-dimensional rank-nullity identity over a division ring using Mathlib's kernel-checked theorem. This is stronger than the bounded GF(2) executable certificate from v0.7, but the graph still records the formal node separately rather than silently relabeling all EO/GEO candidate edges as theorem-wide equivalence.
2. **Definition 44.6 — convex hull.** Formalize the exact two-point/one-parameter convex-combination interval contract over the reals. This is a formally verified scope under the source-bound definition, not a claim that the entire general convex-hull definition has been reconstructed from source prose.
3. **Theorem 47.9 — LP duality.** Formalize the exact positive one-dimensional LP contract: a feasible optimizer exists at `b/a`, and every feasible point has objective at most its objective value. This remains a scoped theorem contract.
4. **Definition 53.4 — Gaussian kernel.** Formalize the exact scalar exponent identity connecting squared-distance and inner-product factorized forms.

## Trusted-verifier boundary

The CI environment is pinned to Lean/Mathlib `v4.33.1` and must:

- build the Lean project successfully;
- reject `sorry`, `admit`, custom `axiom`, or `unsafe` escape hatches in the project formalization file;
- run Lean's kernel checker through normal compilation;
- run `nanoda` with `nanoda-allow-sorry: false` as an independent type-checking backstop;
- bind every formal declaration to the expected source statement SHA-256;
- add a `FORMAL` representation node and `KERNEL_VERIFIED` certificate for all four source declarations;
- preserve graph ID and endpoint integrity.

## Preregistered gates

v0.8 passes only if:

- all four v0.7 source hashes match the accepted graph snapshot;
- Lean build succeeds;
- no prohibited proof escape hatch is present;
- all four formal declarations are present;
- all four kernel-verification certificates are emitted;
- the accepted v0.7 graph is extended, not replaced;
- all graph node IDs and edge IDs are unique and every endpoint exists;
- no copyrighted source prose/page images are persisted.

## Overall MAP direction

The purpose of this stage is to establish the graph's correctness layer, not to maximize the number of Lean files. If it passes, the next major problem becomes **autoformalization coverage and proof-path construction**: progressively turning source graph nodes and EO/GEO-guided candidate proof paths into formal statements and kernel-accepted proofs, while preserving source topology and provenance as separate evidence layers.

A PASS does not establish whole-corpus formalization, full semantic equivalence between every EO/GEO pair, or automated theorem proving.
