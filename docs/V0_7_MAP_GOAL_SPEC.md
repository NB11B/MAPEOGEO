# MAPEOGEO v0.7 — MAP Goal Utility + Equivalence Promotion

## Governing goal

MAPEOGEO is not an EO-vs-GEO benchmark. The project goal is a source-grounded mathematical knowledge graph in which the same mathematics can carry simultaneous EO and GEO representations, those representations are useful for navigating/composing mathematics, and correctness ultimately closes through explicit executable/formal certificates and a trusted proof verifier.

v0.7 therefore tests two things in one preregistered stage:

1. **Proof-navigation utility.** Freeze the independently derived v0.6 EO/GEO views and ask whether they retrieve held-out explicit proof dependencies better than chapter-matched random controls. Also measure whether the union of both views reduces the candidate set while retaining true dependencies. This is heuristic retrieval only; it is not exact-safe pruning.
2. **Cross-view promotion.** Bind four real source declarations by kind, number, and accepted v0.6 statement SHA-256. Run predeclared executable equivalence contracts. Only contracts meeting the promotion policy add verified representation/certificate nodes. `SAME_SEMANTICS` is reserved here for Definition 44.6 and Definition 53.4; the two theorem contracts remain scoped `EQUIVALENT_TO` evidence because their executable domains are bounded subsets of the full theorem domains.

## Frozen inputs

The v0.6 detector banks and source parser are not modified by this experiment. v0.7 regenerates the accepted v0.6 representation from the transient source PDF, then consumes its derived graph/profiles.

The holdout split is fixed before execution:

```text
sha256("MAPEOGEO-V0.7-HOLDOUT|" + dependency_edge_id) mod 5 == 0
```

No learned weights are fit. EO, GEO, dual-mean, dual-max, and source-page proximity are reported. Main non-random tests use EO, GEO, and dual-max against target-chapter-matched random targets over 500 deterministic permutations.

## Preregistered gates

- v0.6 input status must be PASS.
- at least 100 held-out explicit source proof dependencies;
- dual-view union candidate-filter recall >= 0.75;
- mean candidate reduction >= 0.20;
- EO, GEO, and dual-max retrieval each have positive MRR delta vs chapter-matched random and one-sided permutation p <= 0.05;
- all four source-bound executable certificates pass;
- at least two declarations are promoted to `SAME_SEMANTICS` under the stated policy;
- graph IDs/endpoints and copyright-payload audit pass.

These gates do **not** require the combined score to beat both individual views. That is not the project thesis. Complementary views may be valuable even when one dominates a particular retrieval slice.

## Source-bound contracts

- Theorem 6.16 — rank/nullity: exhaustive GF(2) coordinate instances for matrices of dimensions 1..3; scoped `EQUIVALENT_TO`.
- Definition 44.6 — convex hull: definitional source recognizer plus exhaustive one-dimensional rational convex-combination/hull-membership contract; `SAME_SEMANTICS` under the declared contract.
- Theorem 47.9 — linear-programming duality: exact positive one-dimensional rational LP family with 1..3 constraints and coefficients 1..3; scoped `EQUIVALENT_TO`.
- Definition 53.4 — Gaussian kernel: symbolic identity between distance exponent and inner-product factorized exponent; `SAME_SEMANTICS`.

The source PDF is transient and is never stored in repository/artifact outputs. Persisted source binding is by locator/hash only.

## Claim boundary

A PASS supports that the dual graph is already useful for proof-dependency navigation and can begin source-bound equivalence promotion without changing the ontology. It does not establish universal EO/GEO closure, complete proof synthesis, exact-safe search pruning, or whole-corpus Lean/kernel verification.
