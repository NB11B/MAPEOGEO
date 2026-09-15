# MAPEOGEO

MAPEOGEO is a dual-representation mathematical knowledge graph.

A canonical mathematical object `M` can carry simultaneous:

- **EO** — operator/algebraic representation;
- **GEO** — geometric/relational representation;
- **FORMAL** — proof-assistant representation tied to a trusted verifier.

The project goal is broader than comparing those views: build a source-grounded mathematical graph in which source/proof topology, EO, and GEO help organize and navigate mathematical structure, then progressively promote claims through executable and formal certificates toward trusted proof verification.

The current architectural target is:

```text
source / proof topology
        +
EO operator structure
        +
GEO relational geometry
        +
executable certificates
        +
FORMAL proof representations
        ↓
trusted mathematical graph / proof verification
```

`SAME_SEMANTICS` is reserved for representations that have passed an explicit equivalence contract. Formal-verifier evidence is carried separately so that source provenance, semantic structure, executable evidence, and proof-kernel acceptance are not collapsed into one confidence label.

## v0.3 — executable cross-domain fixtures

Reference corpus: Jean Gallier and Jocelyn Quaintance, *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning*.

Source: https://www.cis.upenn.edu/~jean/math-deep.pdf

```text
OVERALL: PASS
SOURCE CHAPTERS SCAFFOLDED: 57
DIRECTLY TESTED CHAPTERS: 20
DUAL EO/GEO SEMANTIC OBJECTS: 20
EXECUTABLE CHECKS: 23,711
GRAPH NODES: 138
GRAPH EDGES: 159
```

Every registered v0.3 semantic fixture passed its EO↔GEO executable equivalence contract.

## v0.4 — real source ingestion

The source importer downloads the book transiently, identifies numbered mathematical declarations and proof blocks, records provenance/hashes/page locators, resolves explicit numbered proof references into dependency edges, and then deletes the source PDF. Source prose is not persisted in repository or workflow artifacts.

The accepted v0.4 full-source run produced 891 deduplicated declarations, 587 proof blocks, 626 resolved dependency references, and a 1,616-node / 2,889-edge merged graph.

See `docs/SOURCE_INGESTION_SPEC.md`.

## v0.5 — corpus dualization audit

v0.5 repaired the declaration parser and tested one controlled EO/GEO ontology over the full source corpus under preregistered fail-closed gates.

```text
OVERALL: PASS
DEDUPLICATED DECLARATIONS: 1,355
DEFINITIONS RECOVERED: 463
CHAPTERS WITH DECLARATIONS: 55 / 57
PROOF BLOCKS: 609
EXPLICIT PROOF CROSS-REFERENCES: 704
RESOLVED DEPENDENCY REFERENCES: 638
UNRESOLVED REFERENCE RATE: 9.38%
DIRECT CONTROLLED SEMANTIC-TAG COVERAGE: 98.52%
EO/GEO DUAL-CANDIDATE COVERAGE: 100.00%
V0.3 FIXTURE ONTOLOGY RECOVERY: 20 / 20
GRAPH: 2,183 nodes / 18,189 edges
```

`DUAL_CANDIDATE` is intentionally weaker than `SAME_SEMANTICS`: it means the controlled ontology supplies both EO and GEO candidate operator families for the declaration. It does not claim theorem-level executable equivalence.

## v0.6 — independent dual-view audit

v0.6 removes the shared concept-to-view crosswalk from the pass metrics. EO and GEO are detected by separately authored, identifier-disjoint detector banks using statement text only; proof text and chapter priors are excluded from the coverage gates.

```text
OVERALL: PASS
DECLARATIONS: 1,355
EO STATEMENT-DIRECT COVERAGE: 87.68%
GEO STATEMENT-DIRECT COVERAGE: 81.48%
INDEPENDENT DUAL-DIRECT COVERAGE: 73.43%
EO-ONLY DIRECT: 14.24%
GEO-ONLY DIRECT: 8.04%
NO DIRECT VIEW: 4.28%
V0.3 FIXTURE INDEPENDENT RECOVERY: 20 / 20
GRAPH: 2,214 nodes / 23,289 edges

EO PROOF-DEPENDENCY ALIGNMENT DELTA: +0.09148, p=0.001996
GEO PROOF-DEPENDENCY ALIGNMENT DELTA: +0.11368, p=0.001996
```

Both independently derived representation spaces show significantly greater similarity on real source dependency edges than on chapter-matched random controls.

See `docs/V0_6_INDEPENDENT_DUAL_VIEW_REPORT.md` and `evidence/v0_6_acceptance_manifest.json`.

## v0.7 — MAP-goal utility + equivalence promotion

v0.7 freezes the v0.6 EO/GEO views, tests them on held-out explicit source proof dependencies, measures a dual-view candidate filter, and promotes four real source declarations through preregistered executable cross-view contracts.

```text
OVERALL: PASS
HELD-OUT PROOF DEPENDENCIES: 126
HELD-OUT QUERIES: 113

EO MRR: 0.02331       matched-random delta +0.00990, p=0.01996
GEO MRR: 0.02620      matched-random delta +0.01018, p=0.01597
DUAL-MAX MRR: 0.02129 matched-random delta +0.00770, p=0.01198
SOURCE-PAGE PROXIMITY MRR: 0.23816

DUAL-UNION FILTER RECALL: 88.89%
MEAN CANDIDATE REDUCTION: 36.03%
SOURCE-BOUND CERTIFICATES: 4 / 4 PASS
SAME_SEMANTICS PROMOTIONS: 2
GRAPH: 2,226 nodes / 23,305 edges
```

The EO/GEO signals are statistically non-random but weak as stand-alone global rankers. Source/proof locality is much stronger. The dual union is useful as a routing filter, reducing candidates by 36.03% while retaining 88.89% of held-out true dependencies, but it is **not exact-safe pruning** and must retain a fallback path.

See `docs/V0_7_MAP_GOAL_REPORT.md` and `evidence/v0_7_acceptance_manifest.json`.

## v0.8 — formal-verifier bridge

v0.8 establishes the correctness layer that the MAP endpoint requires. It takes the four source-bound v0.7 declarations through the existing graph into pinned Lean/Mathlib `v4.33.1`, while keeping the formal representation separate from EO/GEO and source provenance.

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
```

The formalized set is:

- Theorem 6.16 — general finite-dimensional rank-nullity over a division ring;
- Definition 44.6 — exact two-point real convex-combination interval scope;
- Theorem 47.9 — exact positive one-dimensional LP scope;
- Definition 53.4 — exact scalar Gaussian-exponent identity.

All four Lean declarations compile. Their `#print axioms` output contains only `propext`, `Classical.choice`, and `Quot.sound`. The source-bound Lean file contains no `sorry`, `admit`, custom `axiom`, or `unsafe` declarations. Lean's bundled `leanchecker` independently checks the compiled environment.

The original preregistration named Nanoda as the independent checker. That path was actually attempted after successful Lean compilation, but the current external checker failed on an approximately 6.07 GB / 107.8-million-line Mathlib export with `invalid digit found in string`. This is explicitly recorded as `TOOLING_BLOCKED`, not PASS or a mathematical failure. The documented tooling amendment substitutes bundled `leanchecker` without changing the four formal statements, source hashes, formal scopes, or project claims.

The graph now supports the full bridge:

```text
source declaration
  ├── EO representation
  ├── GEO representation
  ├── executable certificate
  └── FORMAL / Lean representation
          └── KERNEL_VERIFIED certificate
```

See:

- `docs/V0_8_FORMAL_VERIFIER_BRIDGE_SPEC.md`
- `docs/V0_8_INDEPENDENT_CHECKER_AMENDMENT.md`
- `docs/V0_8_FORMAL_VERIFIER_BRIDGE_REPORT.md`
- `evidence/v0_8_acceptance_manifest.json`
- `MAPEOGEOFormal/SourceBound.lean`
- `.github/workflows/formal-verifier-v0-8.yml`

## Reproduce

Earlier stages are reproducible from their corresponding workflow/spec files. The v0.8 formal layer is pinned by `lean-toolchain`, `lakefile.lean`, and `lake-manifest.json`.

The accepted CI path regenerates v0.6 and v0.7 from a transient source PDF, builds the Lean project, runs bundled `leanchecker`, emits FORMAL/certificate graph nodes, validates graph integrity, deletes the source PDF, and uploads only derived evidence.

For the formal library itself:

```bash
lake build
lake env lean MAPEOGEOFormal/SourceBound.lean
lake env leanchecker
```

## Current claim boundary

The project has demonstrated:

- executable EO↔GEO equivalence for 20 registered cross-domain fixtures;
- source-grounded declaration/proof-reference ingestion over a large real mathematics corpus;
- broad independently derived EO and GEO evidence directly in source declaration statements;
- statistically significant alignment between both representation spaces and explicit proof dependencies;
- non-random held-out proof-navigation utility plus useful but non-exact dual-view candidate reduction;
- source-bound executable `EQUIVALENT_TO` / `SAME_SEMANTICS` promotion;
- a working source → EO/GEO → certificate → FORMAL/Lean → kernel-verification bridge in the same graph.

It has **not** established universal mathematical closure, exact-safe pruning from the current semantic filter, complete proof synthesis, executable/formal equivalence for all 1,355 declarations, or whole-corpus autoformalization.

The next major stage is therefore not another representation layer. It is the central remaining MAP problem: **automatically formalize a substantial stratified subset of the source graph and candidate proof paths, measure kernel-accepted coverage, and identify the residual mathematical structures that require new EO/GEO primitives, better translation, or additional formal context.**

## Licensing

The repository snapshot is copyright © 2026 NB11B and is currently distributed with **all rights reserved**; see `LICENSE.md`.

The Gallier/Quaintance reference book is an external copyrighted work and is not redistributed here. See `THIRD_PARTY_NOTICES.md` for provenance and reuse boundaries.
