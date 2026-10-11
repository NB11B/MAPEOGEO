# SOVCTX-KG

SOVCTX-KG is a source-grounded knowledge graph for reconstructing Soviet/Russian scientific and engineering concepts in their native historical context before any Western comparison.

## Core rule

```
SOURCE_NATIVE != LATER_INTERPRETATION != MODERN_COMPARISON != OUR_SYNTHESIS
```

Western material is maintained in a separate namespace. `PARALLEL_TO` and `STRUCTURALLY_ANALOGOUS_TO` never imply correctness, equivalence, or shared physics.

## Canonical layout

- `ontology/` node, edge, provenance, and namespace contracts
- `corpus/` source registry and source fragments
- `graph/` entities, claims, equations, experiments, and edges
- `operator_atlas/` reusable operator grammar
- `cases/grebennikov/` Grebennikov/Zolotarev/Rodimov case subgraph
- `western_parallel/` quarantined comparison track
- `modern_derivatives/` modern engineering work, never historical evidence
- `unresolved/` explicit open research questions
- `audits/` qualification outputs
- `tests/` fail-closed validation

## Epistemic boundary

A claim node records that a source made a claim. It does not promote the claimed phenomenon to fact.

```
CLAIMED_OBSERVATION != VERIFIED_OBSERVATION
CANDIDATE_INFLUENCE != DOCUMENTED_INFLUENCE
STRUCTURAL_ANALOGY != SAME_OPERATOR
USES_SIMILAR_TERM != USES_SAME_CONCEPT
PARALLEL_TO != EQUIVALENT_TO
```

## Seed policy

Conversation-derived material is a research seed only. Seed records must use `verification_status: needs_primary_verification` unless independently promoted from an inspected primary source.

## Qualification gates

- KG-1 Provenance: every claim has a source or is explicitly marked inference.
- KG-2 Temporal validity: historical influence cannot originate after its target.
- KG-3 Semantic boundary: analogy cannot promote itself to equivalence.
- KG-4 Operator completeness: physical mechanism claims expose state/coupling/invariant/observable slots or mark them unresolved.
- KG-5 Comparison isolation: Western comparison nodes cannot become evidence for Soviet source-native claims.

Run:

```bash
python sovctx/tools/validate_graph.py
pytest sovctx/tests -q
```

## Status

v0.1 scaffold. Mainline MAPEOGEO is intentionally untouched; development occurs on `research/sovctx-kg`.


## Source-fragment evidence contract

Primary content claims are now claim-addressable.

```
PUBLICATION / ARCHIVAL_DOCUMENT
        |
        | EXTRACTED_FROM
        v
SOURCE_FRAGMENT
        |
        | SUPPORTS
        v
CLAIM
```

A `verified_primary` claim is invalid unless:
1. it lists one or more `source_fragment_ids`;
2. each fragment is `verified_primary` or `verified_scan`;
3. each fragment belongs to a source cited by the claim;
4. a typed `SUPPORTS` edge exists;
5. the fragment has a matching `EXTRACTED_FROM` edge.

Bibliographic verification alone cannot promote content claims.

## Materialized query graph

Canonical truth remains the JSONL files. A derived SQLite database can be built deterministically:

```bash
python sovctx/tools/build_sqlite.py
```

Useful queries:

```bash
python sovctx/tools/query_graph.py stats
python sovctx/tools/query_graph.py claims --source PUB:GELFAND_TSETLIN_1961_NONLOCAL
python sovctx/tools/query_graph.py operator OP:NONLOCAL_MOVE
python sovctx/tools/query_graph.py open
python sovctx/tools/query_graph.py path \
  PUB:GELFAND_TSETLIN_1961_NONLOCAL PERSON:BERNSTEIN_NA \
  --documented-only --source-native-only
```

The last mode excludes SOVCTX synthesis/analogy edges and is intended for historical genealogy questions.

## End-to-end qualification

```bash
python sovctx/tools/qualify.py
```

The qualification runner:
- runs the fail-closed validator;
- builds a temporary SQLite materialization;
- checks canonical node/edge/fragment counts;
- checks the canonical SHA-256 fingerprint;
- checks claim-fragment materialization;
- verifies a documented/source-native Gelfand-Tsetlin 1961 -> Bernstein path;
- verifies that unresolved questions remain represented.

A GitHub Actions workflow is present at `.github/workflows/sovctx-kg.yml`.

### Runtime qualification state

The end-to-end runner is committed but has not yet been observed executing in GitHub Actions. The assistant's current container cannot resolve github.com, so a local clone-based execution attempt could not run. Do not promote this tooling to runtime-qualified until an actual execution result is captured.
