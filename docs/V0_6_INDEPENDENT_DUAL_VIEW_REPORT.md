# MAPEOGEO v0.6 — Independent Dual-View Audit Report

**Status: PASS**

## Scientific question

v0.5 showed broad EO/GEO candidate coverage, but both views were generated from one shared controlled concept crosswalk. v0.6 removes that coupling and asks a stronger question:

> Does the full source corpus independently expose EO-like operator structure and GEO-like relational/geometric structure directly in declaration statements, and do those two independently derived spaces carry non-random information about source proof dependencies?

## Preregistered design

The full Gallier–Quaintance corpus was processed with two separately authored and identifier-disjoint detector banks:

- EO: algebraic composition, linear transforms, factorization, spectral operations, rotations, multilinear products, differential operators, optimization updates, dual/adjoint operations, kernels, graph operators, topological maps, convex operators, and scalar invariants.
- GEO: actions/relations, subspaces, metric/angle structure, oriented volume, rotations/isometries, graph geometry, principal axes, affine/projective structure, topology, tangent structure, convex/polyhedral geometry, Hilbert projection, similarity geometry, margins, objective landscapes, tensor/oriented-subspace geometry, and module actions.

Pass metrics used **statement-only** source spans. Proof text and chapter priors were excluded from the representation-coverage gates.

For dependency alignment, each explicit source `DEPENDS_ON` edge was compared with a target-chapter-matched random control over 500 deterministic permutations, independently for EO and GEO family sets.

## Full-source result

```text
OVERALL: PASS
DECLARATIONS: 1,355
DEFINITIONS: 463
PROOF BLOCKS: 609
EXPLICIT PROOF CROSS-REFERENCES: 704
RESOLVED DEPENDENCY REFERENCES: 638
UNRESOLVED DEPENDENCY REFERENCES: 66
UNRESOLVED REFERENCE RATE: 9.375%

EO STATEMENT-DIRECT: 1,188 / 1,355 = 87.68%
GEO STATEMENT-DIRECT: 1,104 / 1,355 = 81.48%
INDEPENDENT DUAL DIRECT: 995 / 1,355 = 73.43%
EO-ONLY DIRECT: 193 / 1,355 = 14.24%
GEO-ONLY DIRECT: 109 / 1,355 = 8.04%
NO DIRECT VIEW: 58 / 1,355 = 4.28%

V0.3 FIXTURE INDEPENDENT RECOVERY: 20 / 20
GRAPH: 2,214 nodes / 23,289 edges
```

Every preregistered gate passed.

## Proof-dependency alignment

### EO

- explicit dependency edges: 638
- edges with EO evidence on both ends: 490
- actual mean Jaccard: **0.592108**
- chapter-matched random mean Jaccard: **0.500631**
- delta: **+0.091477**
- one-sided matched permutation p: **0.001996**

### GEO

- explicit dependency edges: 638
- edges with GEO evidence on both ends: 399
- actual mean Jaccard: **0.519513**
- chapter-matched random mean Jaccard: **0.405838**
- delta: **+0.113676**
- one-sided matched permutation p: **0.001996**

Both independently derived representation spaces therefore preserve statistically detectable structure associated with the source's explicit proof-dependency graph, relative to the preregistered chapter-matched control.

## Interpretation

This is materially stronger than v0.5.

The result no longer follows automatically from one concept being mapped to both EO and GEO. On statement text alone, independently defined detectors recover both views for **73.43%** of all imported declarations, while only **4.28%** have neither direct view.

The asymmetric residual is also informative rather than something to erase:

- 14.24% are EO-direct without GEO-direct evidence under the frozen detectors;
- 8.04% are GEO-direct without EO-direct evidence;
- 4.28% are unclassified by either direct detector bank.

Those residual sets are the natural target for the next stage. They may contain detector limitations, genuinely one-sided mathematical presentations, or mathematical structures requiring a higher-level composition of primitive operator families.

The dependency result adds a separate signal. Proof-linked declarations are more similar than chapter-matched random declaration pairs in **both** EO and GEO representation spaces. That supports the hypothesis that these views are not merely arbitrary labels attached to the corpus; each captures organization related to mathematical dependency.

## Engineering provenance

The scientific code and gates were preregistered at commit:

`e8302407eb1e06fc9e82099847cb55bbc5476c2b`

The first three full scientific executions returned the same PASS headline metrics, but the external artifact validator contained filename/schema-shape mistakes. Only the validator was repaired; detector banks, corpus thresholds, permutation test, and scientific gates were not changed after observing the full-corpus result.

The first fully green CI execution completed at head:

`1d4739b959fa86174205793872dceffdbb7d50a9`

GitHub Actions run: `34925243825`  
Job: `104241796667`  
Artifact: `10379556657`

## Copyright and source boundary

The source PDF was downloaded transiently and removed after processing. The accepted evidence artifact contains hashed statement metadata, family identifiers, graph structure, counts, and audit results; it does not redistribute source statement/proof prose or page images.

## Claim boundary

v0.6 supports:

- independent EO evidence can be recovered directly from a large real mathematical corpus at high coverage;
- independent GEO evidence can be recovered directly from the same corpus at high coverage;
- a large majority of declarations carry both independent views under the frozen detector banks;
- both representation spaces show non-random alignment with explicit source proof dependencies.

v0.6 does **not** establish:

- executable theorem-level EO↔GEO equivalence for all 1,355 declarations;
- semantic precision of every detector assignment;
- universal mathematical closure of EO or GEO;
- complete reconstruction of implicit proof dependencies;
- automatic Lean generation or proof-kernel verification.

The next decisive stage should focus on the residual 360 declarations that are not independently dual-direct and on promoting selected source declarations from `DUAL_CANDIDATE`/direct evidence to formally or executably verified `SAME_SEMANTICS` pairs.
