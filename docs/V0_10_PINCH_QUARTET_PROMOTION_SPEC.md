# MAPEOGEO v0.10 — Pinch Quartet Promotion Specification

Copyright © 2026 NB11B. All rights reserved. See `LICENSE.md`.

## Governing Goal

Following the accepted v0.9 S5 proof-path and pinch audit, the next batch of mathematical objects is determined deterministically by graph centrality and independent-view shear:

$$\text{Pinch Score} = \text{Dependency Betweenness Centrality} \times \text{Independent-View Shear}$$

```text
source declaration
  -> EO / GEO candidate views
  -> S3 executable test (optional, scoped)
  -> FORMAL statement (Lean 4)
  -> kernel check
  -> graph promotion or refusal
```

Coverage expands to the top four pinch bottlenecks; the machine does not change.

## Intake Invariant & State Machine

Every source object traverses the strict semantic state machine:

$$\boxed{\texttt{UNTESTED} \longrightarrow \texttt{DUAL\_CANDIDATE} \longrightarrow \texttt{EQUIVALENT\_TO} \longrightarrow \texttt{SAME\_SEMANTICS} \longrightarrow \texttt{KERNEL\_VERIFIED}}$$

Promotion occurs strictly along edges justified by empirical executable evidence or kernel verification:
- `KERNEL_VERIFIED`: Assigned only when a source-bound Lean 4 formalization compiles and passes kernel checking without escape hatches (`sorry`, `admit`, custom `axiom`, or `unsafe`).
- `kernel-verified node` $\neq$ `kernel-accepted source proof path`: A formal certificate verifies the mathematical statement; it does not certify that a source citation chain is complete or free of missing references.

## The Pinch Quartet (v0.9 Frozen Targets)

| Priority | Source ID | Declaration | Page | View State | Statement SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `srcdecl:proposition:3_14` | Proposition 3.14 | 88 | `EO_ONLY_DIRECT` | `6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e` |
| 2 | `srcdecl:proposition:3_13` | Proposition 3.13 | 87 | `EO_ONLY_DIRECT` | `0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac` |
| 3 | `srcdecl:theorem:27_10` | Theorem 27.10 | 975 | `DUAL_DIRECT` | `b99a4e9f7dcafc31774208c2d21485e59a23b3ae76f6fd3748babdefd41093e2` |
| 4 | `srcdecl:proposition:4_4` | Proposition 4.4 | 126 | `EO_ONLY_DIRECT` | `37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf` |

### Target 1: Proposition 3.14 (Matrix Column Independence $\iff$ Invertibility)
- **Source Statement**: A square matrix $A \in M_n(K)$ is invertible iff its columns $(A_1, \dots, A_n)$ are linearly independent.
- **Formal Scope**: `SQUARE_MATRIX_INVERTIBLE_IFF_COLUMNS_LINEAR_INDEPENDENT`
- **View Shear Assessment**: Strictly algebraic/operator-theoretic (`EO_ONLY_DIRECT`). Formalization does not artificially inject GEO relations.

### Target 2: Proposition 3.13 (One-Sided Matrix Inverses are Two-Sided)
- **Source Statement**: If a square matrix $A \in M_n(K)$ has a left inverse $B$ ($BA = I_n$) or right inverse $C$ ($AC = I_n$), then $A$ is invertible and $B = C = A^{-1}$.
- **Formal Scope**: `SQUARE_MATRIX_ONE_SIDED_INVERSE_IS_TWO_SIDED`
- **View Shear Assessment**: Strictly algebraic (`EO_ONLY_DIRECT`).

### Target 3: Theorem 27.10 (Euclidean Affine Isometry Canonical Decomposition)
- **Source Statement**: Every affine isometry $f : E \to E$ on a finite-dimensional Euclidean affine space decomposes uniquely as $f = t_\tau \circ g = g \circ t_\tau$ with $\vec{f}(\tau) = \tau$ and non-empty fixed point affine subspace $\text{Fix}(g) \neq \emptyset$.
- **Formal Scope**: `EUCLIDEAN_AFFINE_ISOMETRY_CANONICAL_DECOMPOSITION`
- **View Shear Assessment**: `DUAL_DIRECT` control (EO rotation/derivative action + GEO affine isometry/subspace).

### Target 4: Proposition 4.4 (Subspace Basis & Matrix Invertibility)
- **Source Statement**: A square matrix $A \in M_n(K)$ is invertible iff its column vectors form a basis of $K^n$.
- **Formal Scope**: `SQUARE_MATRIX_INVERTIBLE_IFF_COLUMNS_FORM_BASIS`
- **View Shear Assessment**: Strictly algebraic (`EO_ONLY_DIRECT`).

---

## Wound Preservation Invariant

The graph must preserve all historical wounds:
1. `srcdecl:theorem:47_9`: Recorded as `WOUND_NO_PARSED_SOURCE_PROOF_PATH` because the source contains no parsed explicit proof block.
2. `srcdecl:proposition:6_11` $\to$ `srcdecl:proposition:3_15`: Preserved as repaired citation wound with legacy mismatch edge `REJECTED_REFERENCE_MISMATCH`.

No implicit dependencies may be fabricated.
