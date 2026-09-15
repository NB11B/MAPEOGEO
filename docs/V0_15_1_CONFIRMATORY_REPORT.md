# MAPEOGEO v0.15.1 — Confirmatory Real Analysis Expansion Report

## Executive Summary

$$\boxed{\text{Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.}}$$

MAPEOGEO v0.15.1 completes the **Frozen Confirmatory Replay** of the Real Analysis and Multivariable Differential Calculus Quad-Source Mathematics Expansion, executed under preregistration commit `ccd6424` with end-to-end clean-room reconstruction across all four source corpora:
- **Source A ($S_A$)**: Gallier & Quaintance (2020)
- **Source B ($S_B$)**: Sheldon Axler LADR4e (2026-08-16)
- **Source C ($S_C$)**: Stephen Boyd & Lieven Vandenberghe VMLS (2018)
- **Source D ($S_D$)**: Stephen Boyd & Lieven Vandenberghe CVX (2004)

### The Canonical Mathematical Spine
$$
\mathcal{L}(V, W)\ (\text{Linear Maps}) \longrightarrow Df(x)\ (\text{Fréchet Derivatives}) \longrightarrow \nabla f(x)\ (\text{Gradients via Riesz}) \longrightarrow \nabla^2 f(x)\ (\text{Hessians}) \longrightarrow \nabla^2 f(x) \succeq 0\ (\text{Convexity}) \longrightarrow \text{Optimality}
$$

---

## 1. Confirmatory Dashboard Metrics

| Metric | Symbol | Frozen Preregistered Bound | Actual v0.15.1 Replay | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Total Source Declarations** | $N_{\text{source}}$ | $\ge 400$ | **416** (32 $S_A$ + 220 $S_B$ + 81 $S_C$ + 84 $S_D$) | **PASS** |
| **Canonical Mathematical Objects** | $N_{\text{canonical}}$ | $\ge 85$ | **109** | **PASS** |
| **Two-Source Multi-Bridges** | $N_{\text{2-source}}$ | $\ge 45$ | **53** (48.6% of canonical $M$) | **PASS** |
| **Three-Source Multi-Bridges** | $N_{\text{3-source}}$ | $\ge 30$ | **33** (30.3% of canonical $M$) | **PASS** |
| **Quad-Source Convergence** | $N_{\text{4-source}}$ | $\ge 8$ | **9** ($S_A \cap S_B \cap S_C \cap S_D$) | **PASS** |
| **Distinct Mathematical Domains** | $D_{\text{domains}}$ | $\ge 4$ | **4** (*Linear Algebra*, *Applied Linear Algebra*, *Convex Analysis & Optimization*, *Differential Calculus & Real Analysis*) | **PASS** |
| **Average Representation Richness** | $\bar{r}$ | $\ge 2.75$ | **3.382** | **PASS** |
| **Candidate EO Views** | $N_{\text{EO-candidate}}$ | $> 0$ | **257** | **PASS** |
| **Candidate GEO Views** | $N_{\text{GEO-candidate}}$ | $> 0$ | **27** | **PASS** |
| **Candidate Dual Views** | $N_{\text{DUAL-candidate}}$ | $> 0$ | **159** | **PASS** |
| **Inherited Formal Links** | $N_{\text{formal-linked}}$ | $\ge 6$ | **7** ($\text{FORMAL\_LINKED} \neq \text{KERNEL\_VERIFIED}$) | **PASS** |
| **Total Graph Edges** | $N_{\text{edges}}$ | $> 1000$ | **1616** | **PASS** |
| **Same-Semantics Bridges** | $N_{\text{SAME\_SEMANTICS}}$ | $\ge 300$ | **341** | **PASS** |
| **Scoped-Overlap Bridges** | $N_{\text{SCOPED\_OVERLAP}}$ | $> 0$ | **97** | **PASS** |
| **Related-To Bridges** | $N_{\text{RELATED\_TO}}$ | $> 0$ | **6** | **PASS** |
| **Total Cross-Source Bridges** | $N_{\text{cross-bridges}}$ | $\ge 400$ | **444** | **PASS** |

---

## 2. Clean-Room Dependency Chain Reconstruction

The entire dependency chain reconstructs deterministically from the tracked source baseline:
```
data/gallier_quaintance_graph_v0_3.json.gz
  └── scripts/cross_source_intake_v0_12.py
        └── artifacts/cross_source_v0_12/mapeogeo_v0_12_graph.json.gz (249 decls, 28 canonical, 1 domain)
              └── scripts/tri_source_intake_v0_13.py
                    └── artifacts/tri_source_v0_13/mapeogeo_v0_13_graph.json.gz (332 decls, 39 canonical, 2 domains)
                          └── scripts/convex_intake_v0_14.py
                                └── artifacts/convex_v0_14/mapeogeo_v0_14_graph.json.gz (411 decls, 71 canonical, 3 domains)
                                      └── scripts/analysis_intake_v0_15_1.py
                                            └── artifacts/analysis_v0_15_1/mapeogeo_v0_15_1_graph.json.gz (416 decls, 109 canonical, 4 domains)
```
Execution time for the full end-to-end replay from clean checkout: **4.81s**.

---

## 3. Epistemic Provenance & Wording Integrity

1. **Pre-Execution Freezing**: The preregistration document `evidence/v0_15_1_preregistration.json` was committed to git at SHA `ccd64240b53df33d128f859f8efc1c43a95f588b` prior to confirmatory execution.
2. **Formal Links Distinction**: All 7 formal links are explicitly designated as `FORMAL_LINKED` (inherited formal links connecting canonical objects to Lean declarations). Verification of kernel certificates is maintained as an independent formal layer.
3. **Semantic Edge Fidelity**: The typed semantic taxonomy (`SAME_SEMANTICS`, `SCOPED_OVERLAP`, `RELATED_TO`) is strictly preserved across all 444 emitted bridge edges without node synthesis.
