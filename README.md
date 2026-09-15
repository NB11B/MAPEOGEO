# MAPEOGEO

MAPEOGEO is a dual-representation mathematical knowledge graph.

A canonical mathematical object `M` can carry simultaneous:

- **EO** — operator/algebraic representation;
- **GEO** — geometric/relational representation.

The core invariant is:

```text
semantic object M
├── EO(M)
└── GEO(M)
```

An explicit `SAME_SEMANTICS` edge is reserved for representations that have passed a declared equivalence contract.

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

The proof-dependency control fixes the source declaration and compares its actual referenced target against random targets from the same target chapter over 500 deterministic permutations. Both independently derived representation spaces show significantly greater similarity on real source dependency edges than on the matched random control.

See:

- `docs/V0_6_INDEPENDENT_DUAL_VIEW_SPEC.md`
- `docs/V0_6_INDEPENDENT_DUAL_VIEW_REPORT.md`
- `evidence/v0_6_acceptance_manifest.json`
- `.github/workflows/independent-dual-view.yml`

## Reproduce

v0.3:

```bash
python tests/run_v0_3.py
python tests/validate_v0_3.py
```

v0.4 source ingestion:

```bash
python -m pip install -r requirements-source-ingest.txt
python scripts/import_math_deep.py /path/to/math-deep.pdf \
  --base-graph data/gallier_quaintance_graph_v0_3.json.gz \
  --out-dir artifacts/source_ingest \
  --min-declarations 100 \
  --min-chapters 30
python tests/validate_source_ingest.py artifacts/source_ingest
```

v0.5 corpus dualization:

```bash
python -m pip install -r requirements-corpus-dualization.txt
python scripts/corpus_dualize_v0_5.py /path/to/math-deep.pdf \
  --base-graph data/gallier_quaintance_graph_v0_3.json.gz \
  --out-dir artifacts/corpus_dualization_v0_5 \
  --min-declarations 891 \
  --min-chapters 55 \
  --min-proofs 587 \
  --min-resolved-deps 626 \
  --max-unresolved-rate 0.101 \
  --min-direct-tag-coverage 0.60 \
  --min-dual-candidate-coverage 0.95
python tests/validate_corpus_dualization_v0_5.py artifacts/corpus_dualization_v0_5
```

v0.6 independent dual-view audit:

```bash
python scripts/independent_dual_view_v0_6.py /path/to/math-deep.pdf \
  --base-graph data/gallier_quaintance_graph_v0_3.json.gz \
  --out-dir artifacts/independent_dual_view_v0_6 \
  --min-declarations 1355 \
  --min-definitions 463 \
  --min-proofs 609 \
  --min-resolved-deps 638 \
  --max-unresolved-rate 0.0938 \
  --min-eo-direct 0.70 \
  --min-geo-direct 0.70 \
  --min-dual-direct 0.60 \
  --max-no-direct 0.15 \
  --max-permutation-p 0.05
python tests/validate_independent_dual_view_v0_6.py artifacts/independent_dual_view_v0_6
```

## Current claim boundary

The project has demonstrated:

- executable EO↔GEO equivalence for 20 registered cross-domain fixtures;
- source-grounded declaration/proof-reference ingestion over a large real mathematics corpus;
- broad candidate EO/GEO representability under a controlled ontology;
- broad **independently derived** EO and GEO evidence directly in source declaration statements;
- statistically significant within-view alignment between both independent representation spaces and explicit proof dependencies.

It has not yet established executable EO↔GEO equivalence for all 1,355 imported declarations, universal mathematical closure, complete implicit proof reconstruction, or automatic Lean proof generation/kernel verification.

## Licensing

The repository snapshot is copyright © 2026 NB11B and is currently distributed with **all rights reserved**; see `LICENSE.md`.

The Gallier/Quaintance reference book is an external copyrighted work and is not redistributed here. See `THIRD_PARTY_NOTICES.md` for provenance and reuse boundaries.
