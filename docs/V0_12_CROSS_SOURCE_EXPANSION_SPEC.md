# MAPEOGEO v0.12 Specification: Cross-Source Mathematics Expansion

## 1. Governing Objective

$$\boxed{\text{Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.}}$$

MAPEOGEO v0.12 executes the first multi-corpus expansion stage by ingesting a substantial linear-algebra slice from **Sheldon Axler's *Linear Algebra Done Right* (Fourth Edition, 16 August 2026 corrected PDF)** as Source B ($S_B$).

The primary scientific objective of v0.12 is to demonstrate **canonical cross-source convergence**:
> *Two independently authored mathematical treatments ($S_A = \text{Gallier--Quaintance}$ and $S_B = \text{Axler}$) converge on shared canonical mathematical objects ($M$) while preserving distinct provenance, locators, statement hashes, and dependency structures.*

$$S_A \longrightarrow M \longleftarrow S_B$$

---

## 2. Source B Provenance and Licensing

- **Source ID**: `AXLER_LADR4E_2026_08_16`
- **Author**: Sheldon Axler
- **Title**: *Linear Algebra Done Right*
- **Edition**: Fourth Edition (CC BY-NC 4.0 Open Access)
- **Source Version**: Official corrected PDF, dated 16 August 2026
- **Acquisition URL**: `https://linear.axler.net/LADR4e.pdf`
- **Persistence Boundary**: Zero source prose, proof narrative, or page image redistribution. Graph nodes record source locators, declaration types, statement SHA-256 hashes, character counts, structural dependency edges, and semantic alignment links.

---

## 3. Selected Ingestion Slice

The v0.12 ingestion slice covers the foundational and interface linear algebra structures across Chapters 1, 2, 3, 5, 6, and 7:

| Section | Domain Focus | Canonical Object Targets ($M$) |
| :--- | :--- | :--- |
| **1A–1C** | Vector spaces, subspaces, sums, direct sums | $M_{\text{vector\_space}}$, $M_{\text{subspace}}$, $M_{\text{subspace\_sum}}$, $M_{\text{direct\_sum}}$ |
| **2A** | Linear combinations, span, linear independence | $M_{\text{linear\_combination}}$, $M_{\text{span}}$, $M_{\text{linear\_independence}}$, $M_{\text{linear\_dependence\_lemma}}$ |
| **2B** | Bases, reduction/extension to a basis | $M_{\text{basis}}$, $M_{\text{basis\_unique\_representation}}$, $M_{\text{basis\_extension}}$ |
| **2C** | Dimension and subspace dimension formulas | $M_{\text{dimension}}$, $M_{\text{subspace\_dimension}}$, $M_{\text{dimension\_sum\_formula}}$ |
| **3A** | Linear maps, vector space of linear maps | $M_{\text{linear\_map}}$, $M_{\text{linear\_map\_space}}$, $M_{\text{operator}}$ |
| **3B** | Null spaces, ranges, rank-nullity theorem | $M_{\text{kernel}}$, $M_{\text{range}}$, $M_{\text{rank\_nullity\_theorem}}$, $M_{\text{injective\_trivial\_kernel}}$ |
| **3C** | Matrix of a linear map | $M_{\text{matrix\_representation}}$, $M_{\text{matrix\_multiplication\_composition}}$ |
| **3D** | Invertibility and isomorphisms | $M_{\text{isomorphism}}$, $M_{\text{invertible\_map}}$, $M_{\text{isomorphic\_equal\_dim}}$ |
| **3E** | Products and quotients of vector spaces | $M_{\text{product\_space}}$, $M_{\text{quotient\_space}}$, $M_{\text{quotient\_dimension}}$ |
| **5A/5D** | Invariant subspaces, eigenvalues, diagonalizability | $M_{\text{invariant\_subspace}}$, $M_{\text{eigenvalue}}$, $M_{\text{eigenspace}}$, $M_{\text{diagonalizability}}$ |
| **6B–6C** | Orthonormal bases, Gram-Schmidt, projections | $M_{\text{orthonormal\_basis}}$, $M_{\text{gram\_schmidt}}$, $M_{\text{orthogonal\_complement}}$, $M_{\text{orthogonal\_projection}}$, $M_{\text{pseudoinverse}}$ |
| **7A–7B** | Self-adjoint/normal operators, Spectral Theorems | $M_{\text{adjoint\_map}}$, $M_{\text{self\_adjoint}}$, $M_{\text{normal\_operator}}$, $M_{\text{real\_spectral\_theorem}}$, $M_{\text{complex\_spectral\_theorem}}$ |

---

## 4. Semantic Alignment Model

Cross-source convergence is established through explicit semantic alignment edges between source declarations and canonical objects:

```text
srcdecl:gallier:theorem:6_16   --REPRESENTS--> canonical:linear_algebra:rank_nullity_theorem
srcdecl:axler:theorem:3_21     --REPRESENTS--> canonical:linear_algebra:rank_nullity_theorem
canonical:linear_algebra:...   --FORMAL------> MAPEOGEOFormal.theorem_6_16_rank_nullity
```

### Semantic Alignment Classification States:
1. `CROSS_SOURCE_SAME`: Exact semantic equivalence of mathematical assertion or definition.
2. `CROSS_SOURCE_SCOPED_OVERLAP`: Overlapping mathematical claim with minor scope differences (e.g. general field vs $\mathbb{F} \in \{\mathbb{R}, \mathbb{C}\}$, finite vs arbitrary dimension).
3. `CROSS_SOURCE_RELATED_NOT_SAME`: Structural property, specialization, or lemma directly related to the canonical object.
4. `UNRESOLVED`: Declaration ingested from $S_B$ without a confirmed $S_A$ counterpart.

---

## 5. Metric Dashboard

The v0.12 dashboard derives all metrics dynamically:
- $N_{\text{source}}$: Total source-bound declarations ($S_A + S_B$).
- $N_{\text{canonical}}$: Total canonical mathematical concepts ($M$).
- $N_{\text{cross-source}}$: Canonical concepts confirmed by both $S_A$ and $S_B$.
- $N_{\text{EO}}$: Algebraic/executable representations.
- $N_{\text{GEO}}$: Geometric/constraint representations.
- $N_{\text{formal}}$: Kernel-verified formalizations linked to canonical nodes.
- $N_{\text{paths}}$: Multi-hop verified proof paths.
- $D_{\text{domains}}$: Domain coverage count.
