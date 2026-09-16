# MAPEOGEO v0.15.2 — Confirmatory Real Analysis and Multivariable Differential Calculus Specification

> **Historical report / specification — superseded.** Preserved preregistration counts are not current claims; see [`V0_20_MATHEMATICAL_INTEGRITY_REPORT.md`](V0_20_MATHEMATICAL_INTEGRITY_REPORT.md).

## 1. Governing Law & Epistemic Framework

$$\boxed{\text{Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.}}$$

MAPEOGEO v0.15.2 establishes the **Frozen Confirmatory Replay with Strict Fail-Closed Provenance and Authentic Source-Ingested Gallier Base Graph** of the Real Analysis and Multivariable Differential Calculus Quad-Source Mathematical Expansion across all four source corpora:
- **Source A ($S_A$)**: Gallier & Quaintance, *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning* (2020)
- **Source B ($S_B$)**: Sheldon Axler, *Linear Algebra Done Right*, 4th Edition (2026-08-16)
- **Source C ($S_C$)**: Stephen Boyd & Lieven Vandenberghe, *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (2018)
- **Source D ($S_D$)**: Stephen Boyd & Lieven Vandenberghe, *Convex Optimization* (2004)

### Evolution and Provenance Hardening: v0.15 $\to$ v0.15.1 $\to$ v0.15.2
- **v0.15**: Exploratory pilot stage mapping cross-domain alignments and establishing empirical distribution bounds.
- **v0.15.1**: Confirmatory stage executing under frozen preregistration.
- **v0.15.2**: Hardened confirmatory replay resolving all provenance defects:
  1. **Strict Source-Bound Gallier Provenance**: Gallier declarations are extracted directly from `data/math-deep.pdf` via `scripts/independent_dual_view_v0_6.py` producing 1356-1360 authentic declarations matching frozen v0.11 statement hashes. Synthetic Gallier importers are completely removed.
  2. **Strict Disjoint Source Partitions**: The total source declaration count must equal the exact sum of independent source buckets:
     $$\sum_{k \in \{A,B,C,D\}} N_{S_k} = N_{\text{source\_total}}$$
  3. **Strict Fail-Closed Source Identity**: Zero synthesized or placeholder nodes. Any missing source declaration in alignment references causes immediate fail-closed abort.
  4. **Strict ID Namespace Integrity**: Source IDs strictly reflect their corpus origin (`srcdecl:axler:...` for $S_B$, `srcdecl:vmls:...` for $S_C$, `srcdecl:cvx:...` for $S_D$, `srcdecl:...` for $S_A$).
  5. **Full Section 6A Inclusion**: Complete extraction of Axler inner products, norms, orthogonality, and Cauchy-Schwarz relations.
  6. **Clean-Room End-to-End Reconstruction**: Deterministic replay from clean checkout (`data/math-deep.pdf` + `data/gallier_quaintance_graph_v0_3.json.gz` $\to$ v0.6 $\to$ v0.12 $\to$ v0.13 $\to$ v0.14 $\to$ v0.15.2) under frozen preregistration commit `c97b16afb3ca27eda723ce31040da72566d204de`.

---

## 2. The Cross-Domain Mathematical Spine

The cross-domain spine establishes the rigorous transition from algebraic operator theory to geometric analysis and optimization:

$$\mathcal{L}(V, W)\ (\text{Linear Maps}) \longrightarrow Df(x)\ (\text{Fréchet Derivatives}) \longrightarrow \nabla f(x)\ (\text{Gradients via Riesz}) \longrightarrow \nabla^2 f(x)\ (\text{Hessians}) \longrightarrow \nabla^2 f(x) \succeq 0\ (\text{Convexity}) \longrightarrow \text{Optimality}$$

$$\begin{array}{ccccc}
S_A\ (\text{Gallier: Geometric / Structural / Topology}) & \longrightarrow & & \longleftarrow & S_B\ (\text{Axler: Abstract / Operators / Inner Products}) \\
& & M\ (\text{Canonical Object}) & & \\
S_C\ (\text{VMLS: Computational / Multi-Variable}) & \longrightarrow & & \longleftarrow & S_D\ (\text{CVX: Cones / Hessians / Optimization})
\end{array}$$

---

## 3. Representation Diversity Profile $R(M)$ and Metric $\bar{r}$

Each canonical mathematical object $M$ is evaluated across 6 qualitative representation modalities:

$$R(M) \subseteq \{\text{abstract}, \text{algebraic}, \text{geometric}, \text{computational}, \text{formal}, \text{applied}\}$$

The **Average Representation Richness** is defined as:

$$\bar{r} = \frac{1}{|M|} \sum_{M} |R(M)|$$

Frozen preregistered threshold: $\bar{r} \ge 2.75$.

---

## 4. Frozen Preregistered Acceptance Criteria

1. **Total Source Declarations**: $N_{\text{source}} \ge 400$
2. **Disjoint Partition Invariant**: $\sum N_{\text{bucket}} = N_{\text{source}}$
3. **Canonical Mathematical Objects**: $N_{\text{canonical}} \ge 85$
4. **Two-Source Multi-Bridge Objects**: $N_{\text{2-source}} \ge 45$
5. **Three-Source Multi-Bridge Objects**: $N_{\text{3-source}} \ge 30$
6. **Quad-Source Convergence Objects**: $N_{\text{4-source}} \ge 8$
7. **Distinct Mathematical Domains**: $D_{\text{domains}} \ge 4$
8. **Average Representation Richness**: $\bar{r} \ge 2.75$
9. **Same-Semantics Semantic Bridges**: $N_{\text{SAME\_SEMANTICS}} \ge 300$
10. **Total Cross-Source Bridges**: $N_{\text{cross-bridges}} \ge 400$
11. **Inherited Formal Links**: $N_{\text{formal-linked}} \ge 6$ ($\text{FORMAL\_LINKED} \neq \text{KERNEL\_VERIFIED}$)
12. **Zero-Prose Persistence Policy**: Strict fail-closed verification that no raw copyrighted text, proof text, source prose, or page images are persisted in graph artifacts.
13. **Source Hash Invariant**: For every pre-existing Gallier declaration $s$, $H_{\text{current}}(s) = H_{\text{frozen}}(s)$ matching v0.11 baseline identities.
