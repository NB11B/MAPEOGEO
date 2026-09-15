# MAPEOGEO v0.14 — Convex Analysis and Optimization Expansion Specification

## 1. Governing Law & Objective

$$\boxed{\text{Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.}}$$

MAPEOGEO v0.14 executes the **Quad-Source Mathematics Expansion**, ingesting Stephen Boyd and Lieven Vandenberghe's *Convex Optimization* (Cambridge University Press, 2004) as Source D ($S_D$) alongside Gallier–Quaintance ($S_A$), Sheldon Axler's LADR4e ($S_B$), and Boyd & Vandenberghe's VMLS ($S_C$).

$$
\begin{array}{ccccc}
S_A\ (\text{Gallier: Geometric / Structural}) & \longrightarrow & & \longleftarrow & S_B\ (\text{Axler: Abstract / Operators}) \\
& & M\ (\text{Canonical Object}) & & \\
S_C\ (\text{VMLS: Computational / Algorithms}) & \longrightarrow & & \longleftarrow & S_D\ (\text{CVX: Cones / Duality / Optimization})
\end{array}
$$

---

## 2. Source Boundaries

- **Source A ($S_A$)**: Gallier & Quaintance, *Algebra, Topology, Differential Calculus, and Optimization Theory For Computer Science and Machine Learning* (2020).
- **Source B ($S_B$)**: Sheldon Axler, *Linear Algebra Done Right*, 4th edition (2024/2026).
- **Source C ($S_C$)**: Stephen Boyd & Lieven Vandenberghe, *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (2018).
- **Source D ($S_D$)**: Stephen Boyd & Lieven Vandenberghe, *Convex Optimization* (2004), Chapters 2, 3, 4, 5, 6, 8.

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

Preregistered threshold: $\bar{r} \ge 2.5$.

---

## 4. Preregistered Acceptance Criteria

1. **Total Source Declarations**: $N_{\text{source}} \ge 400$
2. **Canonical Mathematical Objects**: $N_{\text{canonical}} \ge 60$
3. **Two-Source Multi-Bridge Objects**: $N_{\text{2-source}} \ge 40$
4. **Three-Source Multi-Bridge Objects**: $N_{\text{3-source}} \ge 20$
5. **Quad-Source Convergence Objects**: $N_{\text{4-source}} \ge 8$
6. **Distinct Mathematical Domains**: $D_{\text{domains}} \ge 3$
7. **Representation Richness**: $\bar{r} \ge 2.5$
8. **Inherited Formal Proof Bindings**: $N_{\text{formal-linked}} \ge 5$ (Lean 4 kernel-verified theorems)
9. **Zero-Prose Persistence Policy**: Strict fail-closed verification that no raw copyrighted text, proof text, source prose, or page images are persisted in graph artifacts.
