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
