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

An explicit `SAME_SEMANTICS` edge binds the views under a declared verification contract.

## v0.3 status

Reference corpus:

Jean Gallier and Jocelyn Quaintance, *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning*

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

The source hierarchy fits the same ontology without changing the graph model, and every registered v0.3 semantic fixture passed its declared EO↔GEO executable equivalence contract.

## v0.4 source ingestion

v0.4 adds a real source importer rather than another hand-authored ontology layer.

The importer:

1. downloads the Gallier/Quaintance PDF transiently in CI;
2. identifies numbered `Definition`, `Proposition`, `Theorem`, `Lemma`, `Corollary`, `Claim`, and `Fact` declarations;
3. records declaration type/number, chapter, PDF-page locator, span hashes, and proof-presence metadata;
4. scans detected proof blocks for explicit numbered mathematical cross-references;
5. converts resolved proof references into `PREMISE`, `DEPENDS_ON`, and `PRODUCES` graph edges;
6. merges the source declaration layer into the existing v0.3 EO/GEO graph;
7. keeps imported declarations `dualization_status = UNCLASSIFIED` until a separate EO/GEO semantic-equivalence stage validates them.

The source PDF and source prose are **not** committed or uploaded as workflow artifacts. Persistent artifacts contain only locators, types, hashes, counts, explicit numbered references, graph structure, and audit results.

Run locally with a legally obtained copy of the reference PDF:

```bash
python -m pip install -r requirements-source-ingest.txt
python scripts/import_math_deep.py /path/to/math-deep.pdf \
  --base-graph data/gallier_quaintance_graph_v0_3.json.gz \
  --out-dir artifacts/source_ingest \
  --min-declarations 100 \
  --min-chapters 30
python tests/validate_source_ingest.py artifacts/source_ingest
```

The GitHub Actions workflow `.github/workflows/source-ingest.yml` performs the same ingestion against the public source URL and publishes only derived metadata/graph evidence as an ephemeral Actions artifact.

See `docs/SOURCE_INGESTION_SPEC.md` for the exact extraction, dependency, copyright, and fail-closed contracts.

## Reproduce v0.3

```bash
python tests/run_v0_3.py
python tests/validate_v0_3.py
```

`tests/run_v0_3.py` executes the preserved compressed implementation and regenerates the plain JSON graph and results. The repository also stores the accepted graph snapshot as `data/gallier_quaintance_graph_v0_3.json.gz`; the validator reads either the plain or compressed form.

## Layout

- `schema/mapeogeo-core.schema.json`
- `data/gallier_quaintance_graph_v0_3.json.gz`
- `data/gallier_quaintance_results_v0_3.json`
- `docs/V0_3_CROSS_DOMAIN_REPORT.md`
- `docs/SOURCE_INGESTION_SPEC.md`
- `scripts/import_math_deep.py`
- `scripts/import_math_deep_impl.py.gz`
- `requirements-source-ingest.txt`
- `tests/run_v0_3.py`
- `tests/run_v0_3_impl.py.gz`
- `tests/validate_v0_3.py`
- `tests/test_source_importer.py`
- `tests/validate_source_ingest.py`
- `.github/workflows/source-ingest.yml`

## Claim boundary

v0.3 demonstrates dual representability and executable equivalence for the registered fixtures. v0.4 adds source-grounded declaration and explicit proof-reference ingestion.

Neither stage yet establishes full-book autoformalization, universal EO/GEO closure, native GEO-kernel execution for every imported theorem, automatic Lean generation, or complete proof reconstruction.

## Licensing

The repository snapshot is copyright © 2026 NB11B and is currently distributed with **all rights reserved**; see `LICENSE.md`.

The Gallier/Quaintance reference book is an external copyrighted work and is not redistributed here. The April 14, 2025 source displays `© Jean Gallier`; no separate permissive license was identified for the source used in this research. See `THIRD_PARTY_NOTICES.md` for provenance and reuse boundaries.
