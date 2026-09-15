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

The parser repair added Unicode NFKC normalization and split-line declaration recognition; this recovered 463 numbered definitions that v0.4 had missed.

`DUAL_CANDIDATE` is intentionally weaker than `SAME_SEMANTICS`: it means the controlled ontology supplies both EO and GEO candidate operator families for the declaration. It does **not** claim theorem-level executable equivalence.

See:

- `docs/V0_5_CORPUS_DUALIZATION_SPEC.md`
- `docs/V0_5_CORPUS_DUALIZATION_REPORT.md`
- `evidence/v0_5_acceptance_manifest.json`
- `.github/workflows/corpus-dualization.yml`

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

## Claim boundary

The project has now demonstrated:

- executable EO↔GEO equivalence for the 20 registered v0.3 fixtures;
- source-grounded declaration/proof-reference ingestion over a broad real mathematics corpus;
- broad simultaneous EO/GEO **candidate** representability under a fixed controlled ontology.

It has not yet established executable EO/GEO equivalence for all 1,355 imported declarations, universal mathematical closure, complete implicit proof reconstruction, or automatic Lean proof generation/kernel verification.

## Licensing

The repository snapshot is copyright © 2026 NB11B and is currently distributed with **all rights reserved**; see `LICENSE.md`.

The Gallier/Quaintance reference book is an external copyrighted work and is not redistributed here. See `THIRD_PARTY_NOTICES.md` for provenance and reuse boundaries.
