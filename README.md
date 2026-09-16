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

The accepted expansion baseline on `main` is at **v0.18 + Foundation Backfill** (Differential Geometry, Lie Groups & Smooth Manifolds + Complete 8-Layer Primitive Grounding Substrate). The latest replay graph reports:

| Metric | Foundation Backfill + v0.18 Baseline |
|---|---:|
| Total Source Declarations ($N_{\text{source}}$) | **2,067** |
| Foundation Base (`S_0`) | **176** |
| Gallier & Quaintance (`S_A`) | **1,360** |
| Axler LADR4e (`S_B`) | **235** |
| Boyd & Vandenberghe VMLS (`S_C`) | **81** |
| Boyd & Vandenberghe CVX (`S_D`) | **84** |
| Patrick Billingsley (`S_E`) | **64** |
| John M. Lee (`S_F`) | **67** |
| Disjoint Partition Invariant | **2,067 == 2,067 (Exact Equality)** |
| Source Section Anchors (segregated) | **5** |
| Canonical mathematical objects ($N_{\text{canonical}}$) | **234** |
| Foundation Canonical Objects | **29** |
| Advanced Canonical Objects | **205** |
| Foundation Reachability | **100.0%** (205 / 205) |
| Vertical Mathematical Depth ($d_{\text{foundation}}$) | $\min=1,\; \bar{d}=2.439,\; \max=8$ |
| Upward Foundation Structural Bridges | **119** |
| Objects with >=2-source support | **131** (63.9% of advanced) |
| Objects with >=3-source support | **72** (35.1% of advanced) |
| Objects with >=4-source support | **32** (15.6% of advanced) |
| Objects with >=5-source support | **12** (5.9% of advanced) |
| Objects with 6-source universal convergence | **1** (0.5% of advanced) |
| Mathematical domains | **7 Advanced + 8 Foundational Layers** |
| Candidate EO views | **609** |
| Candidate GEO views | **170** |
| Candidate Dual views | **1,209** |
| Inherited formal links | **8** |
| Average representation richness `r_bar` | **3.141** |
| Total typed cross-source bridges | **912** |
| Total graph nodes | **3,212** |
| Total graph edges | **26,432** |
| Executable Dual Contracts | **100% Pass (8/8 Domains)** |

### Foundational Layers & Upward Grounding

The 8 foundational layers establish an unbroken mathematical dependency chain upwards into advanced mathematics:

$$
\boxed{
\text{logic}
\longrightarrow
\text{sets}
\longrightarrow
\text{relations/functions}
\longrightarrow
\text{numbers}
\longrightarrow
\text{arithmetic/algebra}
\longrightarrow
\text{order/sequences}
\longrightarrow
\text{Euclidean geometry/trig}
\longrightarrow
\text{elementary calculus}
}
$$

| Layer | Declarations | Canonical Objects | Upward Connections into Advanced Graph |
|---|---|---|---|
| **1. Logic & Proofs** | 20 | 3 | Propositional calculus, inference rules (Modus Ponens/Tollens), quantifiers $\forall, \exists \longrightarrow$ Vector spaces, Topologies, Measurable spaces |
| **2. Set Theory** | 22 | 3 | Set algebra, power sets, Cartesian products, partitions, indicator functions $\longrightarrow$ Product topology, Borel $\sigma$-algebras, $L^p$ spaces |
| **3. Relations & Functions** | 22 | 3 | Equivalence relations, quotient sets, partial/total orders, function composition, invertibility $\longrightarrow$ Quotient spaces, Linear maps, Diffeomorphisms |
| **4. Number Systems** | 20 | 5 | Peano axioms & $\mathbb{N}$, induction, $\mathbb{Z}$, division algorithm, $\mathbb{Q}$, $\mathbb{R}$ completeness/Dedekind cuts, $\mathbb{C}$ & $i \longrightarrow$ Normed spaces, Banach spaces, Spectral theorems |
| **5. Elementary Algebra** | 22 | 4 | Groups, rings, fields, polynomials $F[x]$, division algorithm, roots, binomial theorem $\longrightarrow$ Lie groups & algebras, Matrix groups, Eigenvalues |
| **6. Order & Sequences** | 22 | 4 | Bounds, $\sup/\inf$, absolute value, triangle inequality, sequence convergence $\epsilon-N$, Cauchy sequences, series $\longrightarrow$ Completeness, Heine-Borel, Matrix exponential |
| **7. Euclidean Geometry & Trig** | 22 | 3 | Euclidean space $\mathbb{R}^n$, distance, dot product $\langle u, v \rangle$, norm, Cauchy-Schwarz, Pythagorean theorem, unit circle, $\sin/\cos$, rotations $R_\theta \longrightarrow$ Riemannian metrics, $O(n)$, $SO(n)$ |
| **8. Elementary Calculus** | 26 | 4 | Limits $\epsilon-\delta$, continuity, IVT, EVT, difference quotients, product/chain rules, MVT, Riemann sums, FTC Parts 1 & 2 $\longrightarrow$ Multivariable differentials, Stokes' Theorem |

### Provenance & Substrate Architecture

The historical v0.11 substrate is preserved as an immutable sealed checkpoint (`data/mapeogeo_v0_11_graph.json.gz`), containing authentic Gallier source structure, formal certificates, proof paths, and visible wounds. All mathematical expansions proceed forward cleanly from this verified foundation without re-deriving historical stages:

```text
SEALED v0.11 TRUSTED SUBSTRATE
  source provenance
  EO / GEO structure
  executable evidence
  formal certificates
  proof paths
  wounds
        │
        ↓
v0.12 Axler
        ↓
v0.13 VMLS
        ↓
v0.14 Convex Optimization
        ↓
v0.15.2 Analysis / Calculus
        ↓
v0.16 Topology, Metric Spaces & Functional Structure
        ↓
v0.17 Measure Theory, Integration & Probability
        ↓
v0.18 Differential Geometry, Lie Groups & Smooth Manifolds
        │
        ↓
FOUNDATION BACKFILL (8 Primitive Grounding Layers)
```

Provenances and frozen statement identities are 100% verified (0 drift against `formal/pinch_bindings_v0_11.json` and `formal/source_identity_amendments.json`), and clean-room reconstruction runs in ~18 seconds locally and ~50 seconds on GitHub Actions runners with strict fail-closed checking:

```text
MATHEMATICAL COVERAGE:          PASS (2,067 declarations, 5 section anchors, 234 canonical objects, 7 domains + 8 foundation layers)
FOUNDATION GROUNDING:           PASS (100.0% reachability across all 205 advanced objects, 119 upward bridges)
DUAL EXECUTABLE CONTRACTS:      PASS (100% pass across all 8 foundational domains)
CLEAN REPLAY OF CURRENT CHAIN:  PASS (~18s locally, ~50s in GitHub Actions)
CROSS-SOURCE STRUCTURE:         PASS (912 bridges across 6 sources)
SOURCE-IDENTITY PRESERVATION:   PASS (0 drift; sealed v0.11 checkpoint + audited amendments)
FINAL SOURCE-BOUND SEAL:        ACCEPTED (v0.18 + Foundation Backfill green on main)
```

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

### Source E — Billingsley

Patrick Billingsley, *Probability and Measure*, 3rd edition (1995), John Wiley & Sons.

Source E introduces 64 curated, source-attributed declaration transcriptions with cryptographic statement hashes, providing the foundation for measure theory, Lebesgue integration, $L^p$ spaces, probability triples, random variables, conditional expectations, and limit theorems (LLN, CLT).

### Source F — Lee

John M. Lee, *Introduction to Smooth Manifolds*, 2nd edition (2013), Springer GTM 218 / Jean Gallier & Jocelyn Quaintance, *Differential Geometry and Lie Groups* (2020), Springer.

Source F introduces 67 curated, source-attributed declaration transcriptions with cryptographic statement hashes, providing the foundation for smooth manifolds, tangent bundles, vector fields, Lie brackets, exterior calculus, Generalized Stokes' Theorem, Riemannian metrics, connections, geodesics, curvature, and matrix Lie groups.

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
TOTAL CROSS-SOURCE BRIDGES: 483
```

See:

- `docs/V0_15_2_CONFIRMATORY_SPEC.md`
- `docs/V0_15_2_CONFIRMATORY_REPORT.md`
- `evidence/v0_15_2_preregistration.json`
- `evidence/v0_15_2_acceptance_manifest.json`
- `.github/workflows/analysis-expansion-v0-15-2.yml`

---

## v0.16 — Topology, Metric Spaces & Functional Structure Expansion

v0.16 established the fundamental connective topological, metric, and functional bridge linking Linear Algebra, Real Analysis, Convexity, and Geometry. 

Section anchors are explicitly typed as `SOURCE_SECTION_ANCHOR` and segregated from declaration-level source declarations, preserving the exact disjoint partition sum $1360 + 235 + 81 + 84 = 1760$. Bridges to/from section anchors are typed as `SCOPED_OVERLAP`, preventing synthetic inflation of declaration-level `SAME_SEMANTICS`.

```text
SOURCE DECLARATIONS: 1,760
SOURCE SECTION ANCHORS: 5 (segregated)
CANONICAL OBJECTS: 151
2-SOURCE OBJECTS: 91
3-SOURCE OBJECTS: 49
4-SOURCE OBJECTS: 22
DOMAINS: 5
AVERAGE REPRESENTATION RICHNESS: 3.206
SAME_SEMANTICS: 407
SCOPED_OVERLAP: 234
RELATED_TO: 6
TOTAL CROSS-SOURCE BRIDGES: 647
TOTAL GRAPH EDGES: 25,217
```

See:

- `docs/V0_16_TOPOLOGY_SPEC.md`
- `evidence/v0_16_scientific_results.json`
- `artifacts/topology_v0_16/topology_expansion_dashboard.json`
- `.github/workflows/topology-expansion-v0-16.yml`

---

## v0.17 — Measure Theory, Integration & Probability Expansion

v0.17 introduced **Source E** ($S_E$, Patrick Billingsley, *Probability and Measure*, 3rd ed., 1995) via 64 curated, source-attributed declaration transcriptions with cryptographic statement hashes, expanding MAPEOGEO into measure spaces, Lebesgue integration, $L^p$ spaces, probability triples, conditional expectations, and limit theorems.

v0.17 achieves the first **5-source universal convergence** in MAPEOGEO across Cauchy-Schwarz, Inner Product / Hilbert Spaces, Normed Spaces, Orthogonal Projections, and Triangle Inequalities.

```text
SOURCE DECLARATIONS: 1,824 (1360 S_A + 235 S_B + 81 S_C + 84 S_D + 64 S_E)
SOURCE SECTION ANCHORS: 5 (segregated)
CANONICAL OBJECTS: 179 (+18.5% expansion)
2-SOURCE OBJECTS: 113 (63.1%)
3-SOURCE OBJECTS: 63 (35.2%)
4-SOURCE OBJECTS: 28 (15.6%)
5-SOURCE OBJECTS: 5 (2.8%)
DOMAINS: 6
AVERAGE REPRESENTATION RICHNESS: 3.214
SAME_SEMANTICS: 470
SCOPED_OVERLAP: 312
RELATED_TO: 6
TOTAL CROSS-SOURCE BRIDGES: 788
TOTAL GRAPH EDGES: 25,556
```

See:

- `docs/V0_17_MEASURE_SPEC.md`
- `docs/V0_17_MEASURE_REPORT.md`
- `evidence/v0_17_scientific_results.json`
- `artifacts/measure_v0_17/measure_expansion_dashboard.json`
- `.github/workflows/measure-expansion-v0-17.yml`

---

## v0.18 — Differential Geometry, Lie Groups & Smooth Manifolds Expansion

v0.18 introduced **Source F** ($S_F$, John M. Lee, *Introduction to Smooth Manifolds*, 2nd ed., 2013 / Gallier-Quaintance 2020) via 67 curated, source-attributed declaration transcriptions with cryptographic statement hashes, expanding MAPEOGEO into smooth manifolds, tangent bundles, vector fields, Lie brackets, exterior calculus, Generalized Stokes' Theorem, Riemannian metrics, connections, geodesics, curvature, and matrix Lie groups.

v0.18 achieves the first **6-source universal convergence** in MAPEOGEO on Riemannian metric tensors and inner product spaces ($S_A, S_B, S_C, S_D, S_E, S_F$).

```text
SOURCE DECLARATIONS: 1,891 (1360 S_A + 235 S_B + 81 S_C + 84 S_D + 64 S_E + 67 S_F)
SOURCE SECTION ANCHORS: 5 (segregated)
CANONICAL OBJECTS: 205 (+14.5% expansion)
2-SOURCE OBJECTS: 131 (63.9%)
3-SOURCE OBJECTS: 72 (35.1%)
4-SOURCE OBJECTS: 32 (15.6%)
5-SOURCE OBJECTS: 12 (5.9%)
6-SOURCE OBJECTS: 1 (0.5%)
DOMAINS: 7
AVERAGE REPRESENTATION RICHNESS: 3.141
SAME_SEMANTICS: 533
SCOPED_OVERLAP: 373
RELATED_TO: 6
TOTAL CROSS-SOURCE BRIDGES: 912
TOTAL GRAPH EDGES: 25,880
```

See:

- `docs/V0_18_DIFFGEOM_SPEC.md`
- `docs/V0_18_DIFFGEOM_REPORT.md`
- `evidence/v0_18_scientific_results.json`
- `artifacts/diffgeom_v0_18/diffgeom_expansion_dashboard.json`
- `.github/workflows/diffgeom-expansion-v0-18.yml`

---

# Reproduction

## Trusted Source Pipeline

Reconstruction proceeds cleanly from the sealed historical v0.11 substrate:

```text
SEALED v0.11 TRUSTED SUBSTRATE
  -> v0.12 Axler
  -> v0.13 VMLS
  -> v0.14 Convex Optimization
  -> v0.15.2 Analysis / Differential Calculus
  -> v0.16 Topology, Metric Spaces & Functional Structure
  -> v0.17 Measure Theory, Integration & Probability
  -> v0.18 Differential Geometry, Lie Groups & Smooth Manifolds
```

Execute full clean reconstruction with:

```bash
python scripts/reconstruct_pipeline.py --target-stage v0.18
```

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
- multi-source convergence across abstract, geometric, computational, optimization, measure-theoretic, and differential-geometric presentations (131 2-source, 72 3-source, 32 4-source, 12 5-source, 1 6-source);
- representation-diversity tracking across abstract, algebraic, geometric, computational, formal, and applied modalities ($\bar{r} = 3.141$);
- clean-room reproducible seven-domain expansion pipeline running in ~18 seconds;
- a 205-object cross-domain map spanning linear algebra, applied linear algebra, convex optimization, differential calculus / real analysis, topology / metric spaces, measure theory / probability, and differential geometry / Lie groups.

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
- declaration-level equality for section-level topological anchors without extracted source statements.

---

# Active direction: v0.19 Complex Analysis, Several Complex Variables & Riemann Surfaces

With the v0.18 seven-domain differential-geometric and Lie-theoretic baseline settled and accepted, the project advances to **v0.19**:

$$\boxed{\text{v0.19 — Complex Analysis, Several Complex Variables & Riemann Surfaces}}$$

This wave incorporates a dedicated complex-analytic source (e.g., Lars Ahlfors, *Complex Analysis* / Steven G. Krantz / Gallier & Quaintance) to build holomorphic functions, Cauchy-Riemann systems, conformal geometry, contour integration, Cauchy integral formula, residue calculus, harmonic functions, several complex variables ($\mathbb{C}^n$, Hartogs' phenomenon), and 1D complex manifolds (Riemann surfaces):

$$
\text{holomorphic } f(z) \longrightarrow \bar{\partial} f = 0 \longrightarrow \oint_\gamma f(z)\,dz = 0 \longrightarrow \text{Residue Calculus} \longrightarrow \text{Riemann Surfaces } X \longrightarrow \text{Sheaf Cohomology}
$$

The canonical expansion targets:
- Holomorphic functions, Cauchy-Riemann equations $\partial f / \partial \bar{z} = 0$, Wirtinger derivatives;
- Conformal mappings, Möbius transformations $PSL(2, \mathbb{C})$;
- Cauchy's integral theorem, Cauchy's integral formula, Morera's theorem, Liouville's theorem;
- Power series, Laurent series, isolated singularities, residue theorem, argument principle, Rouché's theorem;
- Harmonic functions, maximum modulus principle, Dirichlet problem, Poisson integral formula;
- Riemann mapping theorem, Schwarz lemma, hyperbolic metric on unit disk $\mathbb{D}$;
- Several complex variables, Cauchy-Riemann equations in $\mathbb{C}^n$, Hartogs' extension theorem, domains of holomorphy;
- Riemann surfaces as 1D complex manifolds, holomorphic 1-forms, genus, Euler characteristic, Riemann-Roch theorem.

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
