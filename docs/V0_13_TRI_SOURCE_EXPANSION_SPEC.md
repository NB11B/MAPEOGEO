# MAPEOGEO v0.13 — Tri-Source Mathematics Expansion Specification

## 1. Mathematical Objective

MAPEOGEO v0.13 establishes **Tri-Source Mathematical Expansion**, ingesting Stephen Boyd and Lieven Vandenberghe's *Introduction to Applied Linear Algebra – Vectors, Matrices, and Least Squares* (VMLS, 2018) as Source C ($S_C$) alongside Gallier–Quaintance ($S_A$) and Sheldon Axler's *Linear Algebra Done Right* ($S_B$).

$$
\begin{array}{ccccc}
S_A\ (\text{Gallier: Geometric/Formal}) & \longrightarrow & M\ (\text{Canonical Concept}) & \longleftarrow & S_B\ (\text{Axler: Abstract/Operators}) \\
& & \uparrow & & \\
& & S_C\ (\text{VMLS: Computational/Least Squares}) & &
\end{array}
$$

This structure tests whether distinct presentations of the same mathematical foundation converge onto unified canonical objects and structural dependencies.

---

## 2. Source Boundaries

- **Source A ($S_A$)**: Gallier & Quaintance (2020), Chapters 1–16, 27.
- **Source B ($S_B$)**: Axler LADR4e (2026-08-16), Chapters 1A–1C, 2A–2C, 3A–3E, 5A/5D, 6B–6C, 7A–7B.
- **Source C ($S_C$)**: Boyd & Vandenberghe VMLS (2018), Chapters 1–16 (Vectors, Linear combinations, Norm & distance, Linear independence, Matrices, Linear equations, Inverses, Least squares, QR factorization, Regularized least squares).

---

## 3. Preregistered Tolerances & Blinded Benchmark

- $N_{\text{source}} \ge 100$
- $N_{\text{canonical}} \ge 35$
- $N_{\text{2-source}} \ge 25$
- $N_{\text{3-source}} \ge 10$
- $D_{\text{domains}} \ge 2$ (`["Linear Algebra", "Applied Linear Algebra & Optimization"]`)
- **Blinded Benchmark**: 20% holdout of curated bridges evaluated against candidate ranker.

---

## 4. Zero-Prose Persistence Policy

Mathematical texts are parsed strictly in memory. Only SHA-256 digests, character lengths, section indices, and representation tags are saved to disk in graph artifacts.
