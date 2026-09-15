# MAPEOGEO v0.15.1 — Confirmatory Real Analysis and Multivariable Differential Calculus Specification

## 1. Governing Law & Epistemic Framework

$$\boxed{\text{Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.}}$$

MAPEOGEO v0.15.1 establishes the **Frozen Confirmatory Replay** of the Real Analysis and Multivariable Differential Calculus Quad-Source Mathematical Expansion across all four source corpora:
- **Source A ($S_A$)**: Gallier & Quaintance, *Algebra, Topology, Differential Calculus, and Optimization Theory for Computer Science and Machine Learning* (2020)
- **Source B ($S_B$)**: Sheldon Axler, *Linear Algebra Done Right*, 4th Edition (2026-08-16)
- **Source C ($S_C$)**: Stephen Boyd & Lieven Vandenberghe, *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (2018)
- **Source D ($S_D$)**: Stephen Boyd & Lieven Vandenberghe, *Convex Optimization* (2004)

### Distinction Between Exploratory v0.15 and Confirmatory v0.15.1
- **v0.15**: Exploratory pilot stage mapping cross-domain alignments and establishing empirical distribution bounds.
- **v0.15.1**: Confirmatory stage executing under frozen preregistration commit `ccd6424` with clean-room end-to-end reconstruction from `data/gallier_quaintance_graph_v0_3.json.gz` $\to$ v0.12 $\to$ v0.13 $\to$ v0.14 $\to$ v0.15.1.

---

## 2. The Cross-Domain Mathematical Spine

The cross-domain spine establishes the rigorous transition from algebraic operator theory to geometric analysis and optimization:
$$
\mathcal{L}(V, W)\ (\text{Linear Maps}) \longrightarrow Df(x)\ (\text{Fréchet Derivatives}) \longrightarrow \nabla f(x)\ (\text{Gradients via Riesz}) \longrightarrow \nabla^2 f(x)\ (\text{Hessians}) \longrightarrow \nabla^2 f(x) \succeq 0\ (\text{Convexity}) \longrightarrow \text{Optimality}
$$

$$
\begin{array}{ccccc}
S_A\ (\text{Gallier: Geometric / Structural / Topology}) & \longrightarrow & & \longleftarrow & S_B\ (\text{Axler: Abstract / Operators / Inner Products}) \\
& & M\ (\text{Canonical Object}) & & \\
S_C\ (\text{VMLS: Computational / Multi-Variable}) & \longrightarrow & & \longleftarrow & S_D\ (\text{CVX: Cones / Hessians / Optimization})
\end{array}
$$

---

## 3. Representation Diversity Profile $R(M)$ and Metric $\bar{r}$

Each canonical mathematical object $M$ is evaluated across 6 qualitative representation modalities:

$$
R(M) \subseteq \{\text{abstract}, \text{algebraic}, \text{geometric}, \text{computational}, \text{formal}, \text{applied}\}
$$

The **Average Representation Richness** is defined as:

$$
\bar{r} = \frac{1}{|M|} \sum_{M} |R(M)|
$$

Frozen preregistered threshold: $\bar{r} \ge 2.75$.

---

## 4. Frozen Preregistered Acceptance Criteria

1. **Total Source Declarations**: $N_{\text{source}} \ge 400$
2. **Canonical Mathematical Objects**: $N_{\text{canonical}} \ge 85$
3. **Two-Source Multi-Bridge Objects**: $N_{\text{2-source}} \ge 45$
4. **Three-Source Multi-Bridge Objects**: $N_{\text{3-source}} \ge 30$
5. **Quad-Source Convergence Objects**: $N_{\text{4-source}} \ge 8$
6. **Distinct Mathematical Domains**: $D_{\text{domains}} \ge 4$
7. **Average Representation Richness**: $\bar{r} \ge 2.75$
8. **Same-Semantics Semantic Bridges**: $N_{\text{SAME\_SEMANTICS}} \ge 300$
9. **Total Cross-Source Bridges**: $N_{\text{cross-bridges}} \ge 400$
10. **Inherited Formal Links**: $N_{\text{formal-linked}} \ge 6$ (inherited formal links; $\text{FORMAL\_LINKED} \neq \text{KERNEL\_VERIFIED}$)
11. **Zero-Prose Persistence Policy**: Strict fail-closed verification that no raw copyrighted text, proof text, source prose, or page images are persisted in graph artifacts.
