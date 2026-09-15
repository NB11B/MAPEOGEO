# MAPEOGEO

MAPEOGEO is a source-grounded mathematical knowledge graph whose primary object is the **relationship structure of mathematics**.

A canonical mathematical object `M` can be supported by multiple independent sources and carry multiple distinct representations without collapsing those representations into one confidence label:

- **SOURCE** — provenance-bound mathematical declarations and proof dependencies;
- **EO** — operator / algebraic representation candidates and executable operator forms where implemented;
- **GEO** — geometric / relational representation candidates and executable geometric forms where implemented;
- **EXECUTABLE** — scoped computational evidence and exact contracts;
- **FORMAL** — proof-assistant representations linked to Lean 4;
- **KERNEL_VERIFIED** — the strictly narrower state in which a formal declaration has actually passed the trusted proof kernel.

The governing objective is:

> **Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.**

Mathematical coverage is the default action. Infrastructure is subordinate to coverage and is changed only when it blocks ingestion or invalidates trust.

---

## Core model

MAPEOGEO separates **source identity**, **canonical mathematical identity**, **representation**, **executable evidence**, and **formal verification**.

```text
Source A declaration ─┐
Source B declaration ─┼──> Canonical mathematical object M
Source C declaration ─┤          ├── EO candidate / executable operator view
Source D declaration ─┘          ├── GEO candidate / executable geometric view
                                 ├── executable certificates / computational tests
                                 └── FORMAL representation
                                           └── Lean kernel verification

Source declarations also retain:
  - explicit dependency edges
  - proof-path structure
  - source hashes / locators
  - unresolved references
  - repaired wounds
  - rejected mismatches
```

For a canonical object `M`, cross-source correspondence is not binary. MAPEOGEO distinguishes:

| State | Meaning |
|---|---|
| `CANDIDATE` / direct-view profile | EO/GEO detection or representation assignment; not theorem-level equivalence |
| `SAME_SEMANTICS` | the two source-bound representations are treated as the same mathematical object under an explicit semantic contract |
| `SCOPED_OVERLAP` | the representations agree only on a declared scope, subspace, specialization, or formulation |
| `RELATED_TO` | mathematically related but explicitly not identical |
| `FORMAL_LINKED` | a canonical object is linked to a formal declaration |
| `KERNEL_VERIFIED` | that formal declaration has actually passed the Lean kernel under the declared scope |
| `UNTESTED` | no executable/formal evidence has yet been supplied |
| `WOUND` / `UNRESOLVED` | a source, dependency, proof-path, or semantic mismatch remains visible rather than being silently repaired |

These states are intentionally separate. In particular:

```text
DUAL_CANDIDATE != SAME_SEMANTICS
FORMAL_LINKED != KERNEL_VERIFIED
same invariant != same semantics
shared canonical neighborhood != proof of equivalence
```

---

## Current mathematical coverage snapshot

The current `main` branch is at the v0.15.2 expansion line. The latest replay graph reports:

| Metric | Current replay |
|---|---:|
| Source declarations | **436** |
| Gallier / Quaintance (`S_A`) | **36** |
| Axler LADR4e (`S_B`) | **235** |
| VMLS (`S_C`) | **81** |
| Convex Optimization (`S_D`) | **84** |
| Canonical mathematical objects | **109** |
| Objects with >=2-source support | **53** |
| Objects with >=3-source support | **37** |
| Objects with 4-source support | **15** |
| Mathematical domains | **4** |
| EO candidate views | **276** |
| GEO candidate views | **36** |
| Dual candidate views | **160** |
| Inherited formal links | **7** |
| Average representation richness `r_bar` | **3.382** |
| Total graph edges | **1,710** |
| `SAME_SEMANTICS` bridges | **367** |
| `SCOPED_OVERLAP` bridges | **108** |
| `RELATED_TO` bridges | **6** |
| Total typed cross-source bridges | **481** |

Current domains are:

1. Linear Algebra
2. Applied Linear Algebra
3. Convex Analysis & Optimization
4. Differential Calculus & Real Analysis

Representation richness is tracked as

```text
R(M) subset of {
  abstract,
  algebraic,
  geometric,
  computational,
  formal,
  applied
}
```

so that a canonical object can accumulate qualitatively different mathematical realizations rather than simply a larger count of nearly identical textbook statements.

### Current provenance caveat

The v0.15.2 confirmatory workflow itself reproduces successfully and its numerical coverage/graph invariants pass. However, the present expansion reconstruction introduced a temporary Gallier ingestion table in `scripts/import_gallier_v0_12.py` whose generated statement hashes do **not** preserve the earlier source-bound Gallier identities frozen in v0.11.

For example, the v0.11 source identity for `srcdecl:proposition:3_14` is frozen as:

```text
6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e
```

The expansion baseline must therefore be corrected once so that v0.12+ consumes the accepted source-bound Gallier graph rather than recreating Gallier declarations synthetically.

Accordingly, the current state is best read as:

```text
MATHEMATICAL COVERAGE:          PASS
CLEAN REPLAY OF CURRENT CHAIN:  PASS
CROSS-SOURCE STRUCTURE:         PASS
SOURCE-IDENTITY PRESERVATION:   PENDING BASELINE CORRECTION
FINAL SOURCE-BOUND SEAL:        WITHHELD
```

This is a provenance correction, not a reason to reopen the mathematical architecture or begin another continuous-improvement loop.

---

## Source corpora

### Source A — Gallier & Quaintance

Jean Gallier and Jocelyn Quaintance, *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning*.

Reference source:

https://www.cis.upenn.edu/~jean/math-deep.pdf

The accepted early pipeline downloads the source transiently, extracts numbered declarations and proof blocks, stores structural metadata/hashes rather than source prose, and deletes the source PDF after processing.

### Source B — Axler

Sheldon Axler, *Linear Algebra Done Right*, 4th edition, corrected release dated 16 August 2026.

The v0.12+ linear-algebra slice covers vector spaces, span, independence, basis, dimension, linear maps, null spaces/ranges, matrix representations, eigenstructure, inner-product geometry, orthogonal projection, and related results.

### Source C — VMLS

Stephen Boyd and Lieven Vandenberghe, *Introduction to Applied Linear Algebra — Vectors, Matrices, and Least Squares* (2018).

This source adds computational and applied formulations including least squares, QR factorization, matrix algorithms, data fitting, regularization, and constrained least-squares structures.

### Source D — Convex Optimization

Stephen Boyd and Lieven Vandenberghe, *Convex Optimization* (2004).

This source extends the graph into convex sets, cones, duality, KKT conditions, PSD structure, projection, LP/QP/SDP families, and optimization geometry.

Source prose and page images are not intended to persist in graph artifacts.

---

# Development history

## v0.3 — executable cross-domain fixtures

The first executable graph used 20 registered cross-domain semantic fixtures.

```text
OVERALL: PASS
SOURCE CHAPTERS SCAFFOLDED: 57
DIRECTLY TESTED CHAPTERS: 20
DUAL EO/GEO SEMANTIC OBJECTS: 20
EXECUTABLE CHECKS: 23,711
GRAPH NODES: 138
GRAPH EDGES: 159
```

Every registered v0.3 fixture passed its declared EO<->GEO executable equivalence contract. This established a working representation architecture, not whole-corpus equivalence.

---

## v0.4 — real source ingestion

The source importer moved the project from hand-built fixtures to real mathematical source structure.

Accepted v0.4 source run:

```text
DEDUPLICATED DECLARATIONS: 891
PROOF BLOCKS: 587
RESOLVED DEPENDENCY REFERENCES: 626
MERGED GRAPH: 1,616 nodes / 2,889 edges
```

The important architectural change was the separation of mathematical content from persisted provenance: numbered declarations, hashes, locators, and proof-reference edges were retained while source prose was not.

See `docs/SOURCE_INGESTION_SPEC.md`.

---

## v0.5 — corpus dualization audit

v0.5 repaired the declaration parser and tested a controlled EO/GEO ontology across the full source corpus.

```text
OVERALL: PASS
DECLARATIONS: 1,355
DEFINITIONS: 463
CHAPTERS WITH DECLARATIONS: 55 / 57
PROOF BLOCKS: 609
RESOLVED DEPENDENCY REFERENCES: 638
UNRESOLVED REFERENCE RATE: 9.38%
DIRECT CONTROLLED SEMANTIC-TAG COVERAGE: 98.52%
EO/GEO DUAL-CANDIDATE COVERAGE: 100.00%
GRAPH: 2,183 nodes / 18,189 edges
```

`DUAL_CANDIDATE` was deliberately kept weaker than theorem-level semantic equivalence.

---

## v0.6 — independent EO/GEO detector audit

v0.6 removed the shared concept-to-view crosswalk from the pass metrics. EO and GEO were detected with separately authored, identifier-disjoint detector banks using declaration statements rather than proof text or chapter priors.

```text
OVERALL: PASS
DECLARATIONS: 1,355
EO STATEMENT-DIRECT COVERAGE: 87.68%
GEO STATEMENT-DIRECT COVERAGE: 81.48%
INDEPENDENT DUAL-DIRECT COVERAGE: 73.43%
EO-ONLY DIRECT: 14.24%
GEO-ONLY DIRECT: 8.04%
NO DIRECT VIEW: 4.28%
GRAPH: 2,214 nodes / 23,289 edges

EO PROOF-DEPENDENCY ALIGNMENT DELTA: +0.09148, p=0.001996
GEO PROOF-DEPENDENCY ALIGNMENT DELTA: +0.11368, p=0.001996
```

Both independently derived spaces aligned with real source proof dependencies more strongly than chapter-matched random controls.

See:

- `docs/V0_6_INDEPENDENT_DUAL_VIEW_REPORT.md`
- `evidence/v0_6_acceptance_manifest.json`

---

## v0.7 — MAP-goal utility and semantic promotion

v0.7 froze the v0.6 EO/GEO views, evaluated them on held-out explicit proof dependencies, measured routing utility, and promoted a small source-bound set through executable cross-view contracts.

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
```

The main negative result is retained: EO/GEO similarity is statistically non-random but weak as a stand-alone global proof-dependency ranker. Source/proof locality remains much stronger. The dual-view union is therefore a routing aid with fallback, not exact-safe pruning.

See:

- `docs/V0_7_MAP_GOAL_REPORT.md`
- `evidence/v0_7_acceptance_manifest.json`

---

## v0.8 — formal-verifier bridge

v0.8 established a separate correctness layer by linking selected source-bound declarations to pinned Lean/Mathlib `v4.33.1` formalizations.

```text
OVERALL: PASS
SOURCE-BOUND DECLARATIONS: 4
SOURCE HASHES MATCHED: 4 / 4
LEAN KERNEL CHECK: PASS
INDEPENDENT CHECKER: leanchecker — PASS
PROHIBITED PROOF ESCAPE HATCHES: 0
KERNEL-VERIFIED CERTIFICATES: 4 / 4
```

The formal layer is deliberately separate from EO/GEO classification and from executable semantic evidence.

The source-bound Lean files contain no `sorry`, `admit`, custom `axiom`, or `unsafe` declarations. `#print axioms` reports only the standard dependencies `propext`, `Classical.choice`, and `Quot.sound` for the accepted declarations.

Nanoda was attempted as an additional checker but was blocked by tooling limits on the exported Mathlib environment. That condition is recorded as `TOOLING_BLOCKED`, not as a mathematical failure or a pass.

See:

- `docs/V0_8_FORMAL_VERIFIER_BRIDGE_SPEC.md`
- `docs/V0_8_INDEPENDENT_CHECKER_AMENDMENT.md`
- `docs/V0_8_FORMAL_VERIFIER_BRIDGE_REPORT.md`
- `evidence/v0_8_acceptance_manifest.json`
- `MAPEOGEOFormal/SourceBound.lean`

---

## v0.9 — S5 proof-path and pinch audit

v0.9 moved beyond isolated verified endpoints and asked whether a cited support structure could itself become a kernel-accepted path.

```text
OVERALL: PASS
S5 AUDITED PROOF PATHS: 1
PATH STATUS: KERNEL_ACCEPTED_WITH_REPAIRED_WOUND
SUPPORT NODES VERIFIED: 6 / 6
LEAN KERNEL CHECK: PASS
INDEPENDENT CHECKER: leanchecker — PASS
REPAIRED CITATION WOUNDS: 1
PRESERVED PARSED-PATH WOUNDS: 1
```

The audited rank-nullity path is:

```text
Thm 6.16
  -> {Prop 6.15, Prop 6.7}
  -> Prop 6.11
  -> {Prop 3.15, Thm 3.7}
  -> Lemma 3.6
```

The distinction introduced here remains permanent:

```text
KERNEL_VERIFIED node != KERNEL_ACCEPTED source proof path
```

See:

- `docs/V0_9_S5_PROOF_PATH_AND_PINCH_SPEC.md`
- `docs/V0_9_S5_PROOF_PATH_AND_PINCH_REPORT.md`
- `evidence/v0_9_acceptance_manifest.json`
- `MAPEOGEOFormal/ProofPaths.lean`

---

## v0.10 — parallel tracks: pinch promotion and PCT

Two v0.10 lines exist in the repository and should be read as parallel experiments rather than one replacing the other.

### v0.10A — pinch quartet promotion

The proof graph's highest `betweenness x view-shear` pinch targets were promoted to scoped formal verification.

```text
PINCH TARGETS CERTIFIED: 4 / 4
LEAN KERNEL CHECK: PASS
INDEPENDENT CHECKER: leanchecker — PASS
PROHIBITED PROOF ESCAPE HATCHES: 0
```

The important result was preservation of representation evidence: EO-only nodes remained EO-only rather than receiving artificial GEO labels merely because their formal statements were verified.

Artifacts include:

- `formal/pinch_quartet_v0_10.json`
- `MAPEOGEOFormal/PinchQuartet.lean`
- `.github/workflows/pinch-quartet-v0-10.yml`

### v0.10B — Probe-Chain Transform (PCT)

PCT is a parallel **computational evidence subsystem**, not a replacement ontology and not a mandatory layer for mathematical intake.

It evaluates finite chain complexes, chain maps, persistent/topological structure, geometric probes, reconstruction, and provenance under strict validity gates. PCT executable evidence is explicitly prohibited from creating `KERNEL_VERIFIED`, and equal Euler/Betti/reconstruction signatures do not automatically create `SAME_SEMANTICS`.

Its baseline hierarchy is:

```text
B0  Euler characteristic
B1  Betti tuple
B2  persistence pairing ledger
B3  parameterized Euler response
B4  exact chain complex
B5  exact chain complex + maps + residual provenance
```

See:

- `docs/V0_10_PCT_SPEC.md`
- `evidence/v0_10_pct_preregistration.json`
- `mapeogeo/pct/`
- `.github/workflows/pct-v0-10.yml`

---

## v0.11 — fail-closed mathematics intake

v0.11 returned to the source-bound graph and promoted the four frozen high-shear interface targets under strict intake rules.

```text
INTAKE BASE: regenerated accepted v0.9 S5 graph
TARGET DECLARATIONS: 4 / 4 formalized under frozen scopes
LEAN STACK: 4.33.1 / Mathlib 4.33.1
INDEPENDENT CHECKER: leanchecker
AUTOMATIC SEMANTIC EQUIVALENCE EDGES FROM LEAN: 0
HISTORICAL VIEW PROFILES: preserved
V0.9 WOUNDS: preserved visible
```

Frozen source identities include:

```text
Proposition 3.14  6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e
Proposition 3.13  0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac
Theorem 27.10      d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa
Proposition 4.4    37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf
```

Three targets also have scoped S3 computational contracts; Proposition 3.14 remains explicitly `UNTESTED` at that layer.

See:

- `docs/V0_11_MATHEMATICS_INTAKE_REPORT.md`
- `formal/pinch_bindings_v0_11.json`
- `MAPEOGEOFormal/PinchV011.lean`
- `evidence/v0_11_acceptance_manifest.json`

---

## v0.12 — Axler cross-source expansion

v0.12 introduced Sheldon Axler's *Linear Algebra Done Right* as Source B and, for the first time, made canonical mathematical identity explicitly independent of a single textbook provenance.

The central pattern became:

```text
Gallier declaration ----> M <---- Axler declaration
```

The stage established 28 canonical linear-algebra objects spanning vector spaces, span, independence, basis, dimension, linear maps, kernel/range, rank-nullity, matrix representation, eigenstructure, orthogonality, projection, and related structures.

Cross-source status was kept typed rather than collapsing every match into equivalence.

See:

- `docs/V0_12_CROSS_SOURCE_EXPANSION_SPEC.md`
- `docs/V0_12_CROSS_SOURCE_EXPANSION_REPORT.md`
- `formal/cross_source_alignments_v0_12.json`

---

## v0.13 — VMLS tri-source expansion

v0.13 added Boyd and Vandenberghe's VMLS as Source C, allowing abstract, geometric, and computational presentations to meet at the same canonical object.

```text
Gallier ----┐
Axler ------┼----> Canonical object M
VMLS -------┘
```

Historical stage output reported:

```text
CANONICAL OBJECTS: 39
TWO-SOURCE OBJECTS: 38
THREE-SOURCE OBJECTS: 19
DOMAINS: 2
```

The stage also introduced a **blinded, non-blocking alignment benchmark** so MAPEOGEO could begin measuring whether graph structure can recover mathematical identity rather than merely store curated alignments. The benchmark remains informational and is not used to block mathematical ingestion.

See:

- `docs/V0_13_TRI_SOURCE_EXPANSION_REPORT.md`
- `formal/tri_source_alignments_v0_13.json`
- `scripts/blinded_alignment_benchmark_v0_13.py`

---

## v0.14 — convex analysis and optimization expansion

v0.14 added Boyd and Vandenberghe's *Convex Optimization* as Source D and expanded the graph from linear algebra into convex geometry, duality, and mathematical optimization.

```text
Gallier ----┐
Axler ------┼----> M
VMLS -------┤
CVX --------┘
```

Historical stage output established:

```text
CANONICAL OBJECTS: 71
THREE-SOURCE OBJECTS: 29
FOUR-SOURCE OBJECTS: 11
DOMAINS: 3
AVERAGE REPRESENTATION RICHNESS: 3.281
```

The semantic edge taxonomy was made explicit:

```text
CROSS_SOURCE_SAME              -> SAME_SEMANTICS
CROSS_SOURCE_SCOPED_OVERLAP    -> SCOPED_OVERLAP
CROSS_SOURCE_RELATED_NOT_SAME  -> RELATED_TO
UNRESOLVED                     -> no identity edge
```

The domain expansion includes convex sets/cones, separating/supporting geometry, convex functions, duality, KKT conditions, projection, PSD structure, LP/QP/SDP families, and related optimization objects.

See:

- `docs/V0_14_CONVEX_EXPANSION_REPORT.md`
- `formal/convex_alignments_v0_14.json`

---

## v0.15 — exploratory analysis / differential-calculus expansion

v0.15 extended the canonical spine into differential calculus and real analysis:

```text
Linear maps
  -> Frechet derivatives
  -> gradients
  -> Jacobians
  -> Hessians
  -> PSD Hessian convexity conditions
  -> optimization / optimality
```

The initial v0.15 run was later reclassified correctly as an **exploratory pilot**, because its acceptance bounds and clean-runner dependency envelope had not been frozen strongly enough before execution.

The old exploratory workflow is now manual-dispatch only.

---

## v0.15.1 — clean-room confirmatory replay

v0.15.1 separated exploratory calibration from confirmation, froze bounds in git before execution, and rebuilt the expansion dependency chain in a clean CI runner.

That replay succeeded computationally but exposed a deeper source-provenance defect in the newer Gallier expansion baseline. The stage is therefore retained as a useful confirmatory engineering milestone, not the final source-bound seal.

---

## v0.15.2 — provenance-hardened quad-source replay

v0.15.2 added fail-closed checks for source partitioning, namespace consistency, missing alignment nodes, and `REPRESENTS` corpus consistency. The authoritative v0.15.2 workflow reconstructs the chain cleanly and validates the resulting graph.

Current replay metrics are the dashboard shown near the top of this README:

```text
SOURCE DECLARATIONS: 436
CANONICAL OBJECTS: 109
2-SOURCE OBJECTS: 53
3-SOURCE OBJECTS: 37
4-SOURCE OBJECTS: 15
DOMAINS: 4
AVERAGE REPRESENTATION RICHNESS: 3.382
SAME_SEMANTICS: 367
SCOPED_OVERLAP: 108
RELATED_TO: 6
TOTAL CROSS-SOURCE BRIDGES: 481
```

The workflow passes its own preregistered engineering/provenance gates, but the later audit identified that the temporary Gallier table used by the expansion chain does not preserve the frozen source hashes established earlier. For that reason, v0.15.2 is the current **coverage and clean-replay baseline**, while final source-identity acceptance awaits one baseline correction.

See:

- `docs/V0_15_2_CONFIRMATORY_SPEC.md`
- `docs/V0_15_2_CONFIRMATORY_REPORT.md`
- `evidence/v0_15_2_preregistration.json`
- `evidence/v0_15_2_acceptance_manifest.json`
- `.github/workflows/analysis-expansion-v0-15-2.yml`

---

# Reproduction

## Trusted Gallier source pipeline

The accepted source-bound Gallier lineage uses the real source PDF transiently rather than reconstructing declarations from labels:

```text
Gallier/Quaintance PDF
  -> source ingestion / declaration extraction
  -> v0.6 independent EO/GEO representation
  -> v0.7 MAP-goal graph
  -> v0.8 formal bridge
  -> v0.9 proof-path graph
```

The v0.9 GitHub workflow documents this path and downloads the source transiently before deleting it.

The intended expansion chain is therefore:

```text
accepted source-bound Gallier graph
  -> v0.12 Axler
  -> v0.13 VMLS
  -> v0.14 Convex Optimization
  -> v0.15+ Analysis / Differential Calculus
```

The current `scripts/reconstruct_pipeline.py` still needs the one baseline correction described above before it should be treated as the final source-identity-preserving reproducer.

## Formal library

Lean/Mathlib versions are pinned in:

- `lean-toolchain`
- `lakefile.lean`
- `lake-manifest.json`

Typical formal verification commands are:

```bash
lake exe cache get
lake build
lake env lean MAPEOGEOFormal/SourceBound.lean
lake env lean MAPEOGEOFormal/ProofPaths.lean
lake env lean MAPEOGEOFormal/PinchV011.lean
```

The formal layer remains a verifier, not a source corpus. Mathlib is used to test/verify formal statements; it is not ingested as mathematical provenance for the source graph.

---

# What MAPEOGEO has demonstrated

MAPEOGEO has demonstrated:

- executable EO<->GEO equivalence on the original 20 registered cross-domain fixtures;
- real-source declaration and proof-reference ingestion over a large mathematics corpus;
- independently derived EO and GEO evidence directly from source declaration statements;
- statistically significant alignment between EO/GEO representation spaces and explicit proof dependencies;
- non-random proof-navigation utility plus useful but non-exact dual-view candidate reduction;
- source-bound executable semantic promotion on scoped declarations;
- a working source -> EO/GEO -> executable evidence -> FORMAL/Lean -> kernel-verification bridge;
- multi-hop source-bound proof-path verification with repaired and unresolved wounds kept visible;
- fail-closed intake for selected graph pinch points without artificial GEO inflation;
- canonical mathematical objects shared across independent textbooks and presentation styles;
- typed cross-source relationships separating identity, scoped overlap, and related-but-not-same structure;
- tri-source and quad-source convergence across abstract, geometric, computational, and optimization presentations;
- representation-diversity tracking across abstract, algebraic, geometric, computational, formal, and applied modalities;
- a clean-room reproducible four-source expansion pipeline at the engineering level;
- a 109-object cross-domain map spanning linear algebra, applied linear algebra, convex optimization, and differential calculus / real analysis.

---

# What MAPEOGEO has not demonstrated

MAPEOGEO has **not** established:

- universal mathematical closure;
- automatic proof synthesis over arbitrary mathematics;
- whole-corpus autoformalization;
- exact-safe pruning from the current EO/GEO semantic filters;
- executable EO/GEO equivalence for every candidate view;
- `SAME_SEMANTICS` from invariant equality alone;
- automatic semantic discovery at a reliability level that replaces curated/source-grounded correspondence;
- kernel verification for every `FORMAL_LINKED` object;
- that PCT or any other computational tester replaces Lean's proof kernel;
- a final source-identity seal for the current 436-declaration v0.15.2 replay until the Gallier expansion baseline is reconnected to the accepted real-source ingestion chain.

---

# Near-term direction

The next infrastructure action is intentionally narrow:

1. remove the synthetic Gallier declaration reconstruction from the v0.12+ scientific chain;
2. start expansion from the accepted source-bound Gallier graph / hashes;
3. rerun the existing expansion chain once;
4. bind the final acceptance receipt to the actual CI artifact hashes.

This is a **baseline correction**, not a new research stage.

After that, the default action returns to mathematics expansion rather than validator refinement. Likely domain waves include topology / metric spaces, probability / measure, abstract algebra, combinatorics / graph theory, and additional analysis, with new sources converging on the same canonical graph where mathematically justified.

---

# Repository map

Important locations:

```text
MAPEOGEOFormal/        Lean formalizations
formal/                source bindings, proof paths, cross-source alignments
mapeogeo/pct/          Probe-Chain Transform computational evidence subsystem
scripts/               ingestion, graph mutation, reconstruction, experiment runners
tests/                 unit, integration, fail-closed, and artifact validators
evidence/              preregistrations, manifests, scientific-result records
docs/                  stage specifications and scientific reports
.github/workflows/     reproducible CI workflows
```

---

# Licensing and third-party sources

The repository snapshot is copyright © 2026 NB11B and is currently distributed with **all rights reserved**; see `LICENSE.md`.

External mathematical books and papers remain third-party works. MAPEOGEO does not intend to redistribute their prose or page images. See `THIRD_PARTY_NOTICES.md` for provenance and reuse boundaries.
