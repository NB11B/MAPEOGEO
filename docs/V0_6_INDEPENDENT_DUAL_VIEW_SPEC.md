# MAPEOGEO v0.6 Independent Dual-View Audit — Preregistered Specification

## Question

Does the full source corpus show **independent, statement-level evidence** for both EO and GEO representations, rather than receiving both views from one shared concept-to-view crosswalk?

v0.5 established broad controlled-ontology candidate coverage. That result is useful but not independent: each controlled concept had a preregistered mapping to both an EO family and a GEO family. v0.6 removes that coupling.

## Independence contract

v0.6 uses two separately authored detector banks:

- **EO detector bank:** algebraic composition, linear transforms, factorization, spectral operations, rotations, multilinear products, differential operators, optimization updates, dual/adjoint operations, kernels, graph operators, topological maps, convex operators, and scalar invariants.
- **GEO detector bank:** action/relational geometry, subspaces, metric/angle structure, oriented volume, rotations/isometries, graph geometry, principal axes, affine/projective structure, topology, tangent structure, convex/polyhedral geometry, Hilbert projection, similarity geometry, margins, objective landscapes, tensor/oriented-subspace geometry, and module actions.

The banks do not share a concept-to-view crosswalk and their family identifiers are disjoint.

## Statement-only contract

Pass metrics are computed only from the source span before `Proof.`. Proof text is excluded from representation detection so that cited background mathematics cannot inflate the semantic profile of the statement being classified.

No chapter prior is used in pass metrics.

Only hashes, character counts, family identifiers, source locators, and graph structure are persisted. Source prose is transient and is not included in artifacts.

## Dependency-alignment control

For each explicit source `DEPENDS_ON` edge, v0.6 measures within-view Jaccard similarity of independently detected family sets.

The control holds the source declaration fixed and replaces the referenced declaration with a random declaration drawn from the **same target chapter** when possible. Five hundred deterministic permutations are run separately for EO and GEO.

This tests whether proof-linked declarations are structurally closer in each independent representation than chapter-matched random pairs.

## Baseline frozen from accepted v0.5

- declarations: 1,355
- definitions: 463
- proof blocks: 609
- resolved dependency references: 638
- unresolved reference rate: 9.38%
- v0.3 verified fixture layer: 20 fixtures

## Preregistered gates

The run passes only if all gates pass:

1. declarations >= 1,355
2. definitions >= 463
3. proof blocks >= 609
4. resolved dependencies >= 638
5. unresolved reference rate <= 0.0938
6. EO statement-direct coverage >= 70%
7. GEO statement-direct coverage >= 70%
8. independent dual statement-direct coverage >= 60%
9. no-direct-view rate <= 15%
10. v0.3 fixture independent dual recovery = 20/20
11. EO dependency alignment delta > 0 with one-sided matched permutation p <= 0.05
12. GEO dependency alignment delta > 0 with one-sided matched permutation p <= 0.05
13. unique node IDs
14. unique edge IDs
15. no dangling edges
16. no persistent source-prose payload fields

Thresholds are frozen before the full-source run and must not be weakened after observing the result.

## Claim boundary

A PASS would establish that the corpus exhibits broad, independently derived EO and GEO evidence directly in declaration statements, and that both representation spaces carry non-random structure with respect to explicit proof dependencies.

It would still not establish theorem-level executable EO↔GEO equivalence for every source declaration, universal mathematical closure, semantic-family precision for every assignment, or Lean proof verification.
