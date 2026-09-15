# MAPEOGEO v0.5 Corpus Dualization Audit — Preregistered Specification

## Question

Can the full Gallier–Quaintance reference corpus be ingested into the existing MAPEOGEO graph and assigned **controlled EO and GEO candidate operator families** without storing source prose, while improving the v0.4 declaration parser and preserving or improving the source-dependency evidence already measured?

This is a single corpus-wide test. It is not an EO-vs-GEO comparison and it is not a theorem-by-theorem sequence of ad hoc experiments.

## Baseline frozen from v0.4

The accepted v0.4 full-source run produced:

- 2,204 PDF pages;
- 891 deduplicated numbered declarations;
- declarations in 55 of 57 chapters;
- 587 detected proof blocks;
- 696 explicit proof cross-references;
- 626 resolved proof-reference dependencies;
- 70 unresolved proof references (10.06%);
- 0 recovered numbered `Definition` declarations;
- a merged graph of 1,616 nodes and 2,889 edges.

The zero-Definition result is treated as an extraction defect to be tested directly, not as evidence that the book contains no definitions.

## Parser change under test

v0.5 makes two bounded parser repairs before the corpus run:

1. Unicode NFKC normalization, specifically to expand mathematical/text ligatures such as `ﬁ` in `Deﬁnition`.
2. Recognition of declaration headings split across adjacent extracted lines, for example `Definition` followed by `2.1 ...`.

No thresholds may be weakened after seeing the v0.5 result.

## Controlled semantic ontology

During the transient full-text pass, each declaration span is mapped to a fixed vocabulary of mathematical concepts spanning algebraic structure, linear maps, matrices, metric/spectral structure, rotations, graphs, tensor/exterior algebra, topology, differential calculus, convexity, optimization, duality, Hilbert projection, regression, kernels, and margin geometry.

Each controlled concept has a preregistered crosswalk to one or more EO candidate families and one or more GEO candidate families.

The persistent artifact stores only controlled labels, candidate-family identifiers, source locators, hashes, counts, and graph structure. It does not store source prose.

## Evidence levels

`DIRECT_TEXT` means at least one fixed controlled pattern matched the transient declaration span.

`CHAPTER_PRIOR` is used only when no direct controlled pattern matched; the fallback comes from the preregistered chapter-domain map and is reported separately.

`DUAL_CANDIDATE` means the controlled ontology supplies at least one EO family and at least one GEO family for the selected concept set. It **does not** mean the two representations have been formally or numerically proven equivalent for that theorem.

## Graph contract

The existing v0.3 verified fixture layer remains unchanged.

Imported source declarations receive source/provenance nodes, controlled concept edges, `CANDIDATE_EO` edges, `CANDIDATE_GEO` edges, explicit proof-reference dependency edges, and proof-block nodes where detected.

No new `SAME_SEMANTICS` edge is created for a source declaration merely because it has EO and GEO candidates. `SAME_SEMANTICS` remains reserved for a later verification stage.

## Preregistered gates

The v0.5 run passes only if all gates pass:

1. `deduplicated_declarations >= 891`
2. `chapters_with_declarations >= 55`
3. `proof_blocks_detected >= 587`
4. `resolved_dependency_references >= 626`
5. `unresolved_reference_rate <= 0.101`
6. `Definition count > 0`
7. `direct_semantic_tag_coverage >= 0.60`
8. `dual_candidate_coverage >= 0.95`
9. v0.3 fixture ontology recovery = `20 / 20`
10. graph node IDs unique
11. graph edge IDs unique
12. no dangling graph edges
13. no persistent source-prose payload fields

## Claim boundary

A PASS would support that the corpus can be represented in one graph with broad simultaneous EO/GEO **candidate** coverage and preserved source dependency structure.

It would not establish executable EO/GEO equivalence for all declarations, universal mathematical closure, formal proof reconstruction, Lean generation, or proof-kernel acceptance.
