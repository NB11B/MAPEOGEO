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

## Reproduce

```bash
python tests/run_v0_3.py
python tests/validate_v0_3.py
```

## Layout

- `schema/mapeogeo-core.schema.json`
- `data/gallier_quaintance_graph_v0_3.json`
- `data/gallier_quaintance_results_v0_3.json`
- `docs/V0_3_CROSS_DOMAIN_REPORT.md`
- `tests/run_v0_3.py`
- `tests/validate_v0_3.py`

## Claim boundary

v0.3 demonstrates dual representability and executable equivalence for the registered fixtures. It does **not** yet claim full-book autoformalization, universal EO/GEO closure, native GEO-kernel execution for every fixture, automatic Lean generation, or full proof-dependency extraction.

## Licensing

The v0.3 repository snapshot is copyright © 2026 NB11B and is currently distributed with **all rights reserved**; see `LICENSE.md`.

The Gallier/Quaintance reference book is an external copyrighted work and is not redistributed here. The April 14, 2025 source displays `© Jean Gallier`; no separate permissive license was identified for the source used in this milestone. See `THIRD_PARTY_NOTICES.md` for provenance and reuse boundaries.
