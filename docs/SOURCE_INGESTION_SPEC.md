# MAPEOGEO Source Ingestion Specification v0.4

## Purpose

The v0.4 source-ingestion stage converts the Gallier-Quaintance reference corpus into a source-grounded declaration/dependency layer for the existing MAPEOGEO graph.

It is intentionally **not** a natural-language summarizer. Its job is narrower and fail-closed:

1. identify numbered mathematical declarations;
2. preserve source provenance and page locators;
3. identify explicit references appearing inside proof blocks;
4. merge those nodes and edges into the existing EO/GEO graph;
5. avoid redistributing the source book or its prose.

## Source

- Jean Gallier and Jocelyn Quaintance
- *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning*
- https://www.cis.upenn.edu/~jean/math-deep.pdf

The PDF is downloaded only during the ingestion workflow. It is never committed or uploaded as a repository artifact.

## Copyright boundary

The persistent artifacts contain only:

- bibliographic metadata;
- chapter identifiers;
- declaration type and number, e.g. `Theorem 6.16`;
- PDF-page locators;
- SHA-256 hashes and character counts of detected source spans;
- proof-presence flags;
- explicit numbered cross-references found inside proof spans;
- graph structure and audit results.

They do **not** contain source statements, proof text, excerpts, diagrams, or page images.

This policy is enforced by both the importer and the artifact validator.

## Declaration contract

A declaration is recognized only when a non-empty extracted line begins with one of:

```text
Definition
Proposition
Theorem
Lemma
Corollary
Claim
Fact
```

followed by a dotted numeric identifier such as `6.16` or `47.9`.

The graph identity is the pair `(declaration_kind, number)`.

## Duplicate handling

If multiple candidates have the same semantic key, the importer keeps the candidate with the largest detected source span, breaking ties in favor of the later PDF occurrence. Every rejected candidate is written to `duplicate_declaration_audit.json`.

The purpose is to fail visibly on front-matter/index duplication rather than silently multiplying semantic nodes.

## Proof dependency contract

For each declaration, the source span ends at the next numbered declaration. If that span contains a line beginning with `Proof`, the remaining portion is treated as a proof span for structural extraction only.

Inside that proof span, explicit numbered references such as:

```text
Proposition 6.15
Theorem 47.9
Definition 2.1
```

are converted into dependency evidence only when the referenced declaration was also imported.

A resolved source reference creates:

```text
referenced statement --PREMISE--> proof block
source statement     --DEPENDS_ON--> referenced statement
proof block          --PRODUCES--> source statement
```

The dependency edge is tagged:

```text
SOURCE_PROOF_CROSS_REFERENCE
```

Unresolved references are preserved in the ingestion report; they are never guessed or rebound to a similarly named object.

## EO/GEO relationship

Imported declarations enter the graph with:

```text
dualization_status = UNCLASSIFIED
```

This is deliberate. Source ingestion and semantic dualization are separate stages.

The v0.3 fixtures remain the demonstrated EO/GEO layer. v0.4 adds real corpus structure around them without pretending that every theorem has already been compiled into both operator systems.

The subsequent dualization stage may attach:

```text
semantic object
├── EO representation
├── GEO representation
└── SAME_SEMANTICS certificate
```

to an imported source declaration after a separate semantic/equivalence check.

## Outputs

The workflow produces an ephemeral GitHub Actions artifact containing:

- `source_ingest_report.json`
- `source_declarations.json`
- `duplicate_declaration_audit.json`
- `mapeogeo_source_graph.json`
- `SOURCE_INGEST_SUMMARY.md`

The original PDF is excluded.

## Fail-closed gates

The initial corpus run requires:

- at least 100 deduplicated numbered declarations;
- declarations in at least 30 of the 57 chapters;
- successful PDF text extraction;
- valid chapter numbers when inferable from declaration numbering;
- unique graph node IDs;
- unique graph edge IDs;
- no dangling edges;
- no persistent source-prose fields.

These are catastrophic-failure gates, not claims about completeness. After the first full run establishes empirical corpus counts, tighter coverage gates can be preregistered against that observed source version.

## Scientific boundary

A PASS supports only that the corpus can be ingested into the core graph as source-grounded declaration/proof-reference structure while respecting the no-source-prose policy.

It does not establish:

- full theorem semantic parsing;
- complete proof dependency reconstruction;
- EO/GEO closure for every imported declaration;
- Lean autoformalization;
- formal proof verification.
