# MAPEOGEO v0.18 — Differential Geometry, Lie Groups & Smooth Manifolds Specification

> **Historical report / specification — superseded.** Preserved preregistration counts are not current claims; see [`V0_20_MATHEMATICAL_INTEGRITY_REPORT.md`](V0_20_MATHEMATICAL_INTEGRITY_REPORT.md).

## 1. Governing Objective

$$
\boxed{\text{Build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object.}}
$$

## 2. Scope & Source Ingestion

v0.18 introduces **Source F** ($S_F$):
- **Source Corpus**: John M. Lee, *Introduction to Smooth Manifolds*, 2nd ed. (2013), Springer GTM 218 / Jean Gallier & Jocelyn Quaintance, *Differential Geometry and Lie Groups* (2020) (`LEE_SMOOTH_MANIFOLDS_2013`).
- **Source Grounding Mode**: 67 curated, source-attributed mathematical declaration transcriptions with cryptographic statement SHA-256 hashes covering 6 foundational areas:
  1. *Smooth Manifolds, Atlases & Smooth Maps* (topological manifolds, smooth structures, maximal atlases, smooth maps, diffeomorphisms, partitions of unity, submanifolds, Whitney embedding)
  2. *Tangent Spaces, Pushforwards & Vector Fields* (derivations, tangent space $T_p M$, pushforward/differential $df_p$, tangent bundle $TM$, vector fields $\mathfrak{X}(M)$, Lie bracket $[X, Y]$, Jacobi identity, flows, Frobenius theorem)
  3. *Cotangent Spaces, Differential Forms & Exterior Calculus* (cotangent space $T_p^* M$, differential $df$, tensor bundles, differential $k$-forms $\Omega^k(M)$, wedge product $\wedge$, exterior derivative $d$, $d^2 = 0$, pullbacks $f^* \omega$, closed/exact forms, Poincaré lemma, de Rham cohomology $H^k_{\text{dR}}(M)$)
  4. *Orientability, Integration of Forms & Generalized Stokes' Theorem* (orientations, volume forms, manifolds with boundary $\partial M$, integration of differential forms, Generalized Stokes' Theorem $\int_{\partial M} \omega = \int_M d\omega$, Green, classical Stokes, Gauss divergence)
  5. *Riemannian Geometry, Metrics, Connections & Geodesics* (Riemannian metric $g$, Riemannian manifold $(M, g)$, musical isomorphisms $\flat/\sharp$, gradient $\operatorname{grad}_g f$, Riemannian volume form, geodesic distance metric space $(M, d_g)$, Hopf-Rinow theorem, Levi-Civita connection $\nabla$, geodesics, exponential map $\exp_p$, Riemann curvature tensor $R(X,Y)Z$, Ricci & scalar curvature)
  6. *Lie Groups, Lie Algebras & Matrix Groups* (Lie group $G$, left-invariant vector fields, Lie algebra $\mathfrak{g} \cong T_e G$, matrix Lie groups $GL, SL, SO, SE$, Lie group exponential map $\exp: \mathfrak{g} \to G$, Lie correspondence, adjoint representations $\operatorname{Ad}/\operatorname{ad}$, Baker-Campbell-Hausdorff formula, homogeneous spaces $G/H$)

## 3. Strict Architectural Guarantees

1. **Zero-Prose Persistence**: Mathematical statements are processed strictly in memory to compute cryptographic SHA-256 digests. Only hashes, locators (chapter, section, page), representation tags, and relational edges are persisted.
2. **Disjoint Partition Invariant**:
   $$
   N_{\text{source}} = N_{S_A} + N_{S_B} + N_{S_C} + N_{S_D} + N_{S_E} + N_{S_F} = 1360 + 235 + 81 + 84 + 64 + 67 = 1891
   $$
3. **Section Anchor Segregation**: 5 topological/convex section anchors remain segregated under `SOURCE_SECTION_ANCHOR`.
4. **Immutable Baseline**: The historical sealed checkpoint (`data/mapeogeo_v0_11_graph.json.gz`) is never re-derived or mutated.
5. **Fail-Closed Verification**: All dependency chains, alignments, and representations must validate without warning or bypass flags.

## 4. Preregistered Quantitative Targets

| Metric | Symbol | Preregistered Minimum |
| :--- | :---: | :---: |
| Source Declarations | $N_{\text{source}}$ | $\ge 1,885$ |
| Source Corpora | $|S|$ | $6$ ($S_A, S_B, S_C, S_D, S_E, S_F$) |
| Mathematical Domains | $D_{\text{domains}}$ | $7$ |
| Canonical Objects | $N_{\text{canonical}}$ | $\ge 200$ |
| Multi-Source (2-Source) Objects | $N_{\ge 2}$ | $\ge 125$ |
| Multi-Source (3-Source) Objects | $N_{\ge 3}$ | $\ge 65$ |
| Multi-Source (4-Source) Objects | $N_{\ge 4}$ | $\ge 30$ |
| Multi-Source (5-Source) Objects | $N_{5}$ | $\ge 8$ |
| Multi-Source (6-Source) Objects | $N_{6}$ | $\ge 1$ |
| Total Cross-Source Bridges | $N_{\text{bridges}}$ | $\ge 850$ |
| Average Representation Richness | $\bar{r}$ | $\ge 3.10$ |
| Clean Replay Execution Time | $T_{\text{replay}}$ | $\le 60\text{ s}$ |
