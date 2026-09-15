# MAPEOGEO v0.3 — Cross-Domain Corpus Test

## Registered question

Can one core knowledge graph represent the same mathematical semantic objects simultaneously as EO/operator objects and GEO/geometric-relational objects across materially different mathematical domains?

## Result

**PASS**

- 57 source chapters scaffolded.
- 20 chapters directly exercised.
- 20 dual EO/GEO semantic objects.
- 23,711 executable checks.
- 138 graph nodes.
- 159 graph edges.

## Test matrix

| # | Semantic object | Chapter | Checks | Result | Max error |
|---:|---|---:|---:|---|---:|
| 1 | Cyclic group composition | 2 | 8,554 | PASS | 0.000e+00 |
| 2 | Rank-nullity | 3 | 350 | PASS | 0.000e+00 |
| 3 | Determinant as oriented volume | 7 | 600 | PASS | 2.665e-15 |
| 4 | QR decomposition | 13 | 500 | PASS | 2.665e-15 |
| 5 | SO(3) rotation | 16 | 3,000 | PASS | 1.554e-15 |
| 6 | Eigenpairs | 15 | 2,250 | PASS | 7.105e-15 |
| 7 | Graph Laplacian | 20 | 700 | PASS | 0.000e+00 |
| 8 | Singular value decomposition | 22 | 1,637 | PASS | 1.132e-14 |
| 9 | Projective homogeneous equivalence | 26 | 900 | PASS | 2.763e-11 |
| 10 | Tensor/Kronecker composition | 33 | 500 | PASS | 3.553e-15 |
| 11 | Exterior product / area | 34 | 1,000 | PASS | 1.354e-14 |
| 12 | Frechet derivative | 39 | 450 | PASS | 4.457e-04 |
| 13 | Newton step | 41 | 600 | PASS | 0.000e+00 |
| 14 | Strict quadratic minimization | 42 | 400 | PASS | 4.996e-15 |
| 15 | Schur complement elimination | 43 | 350 | PASS | 2.220e-16 |
| 16 | Convex hull | 44 | 450 | PASS | -2.784e-02 |
| 17 | Linear-programming duality | 47 | 220 | PASS | 1.155e-14 |
| 18 | Orthogonal projection | 48 | 500 | PASS | 1.199e-14 |
| 19 | Ridge regression | 53 | 400 | PASS | 6.495e-15 |
| 20 | Gaussian positive-definite kernel | 54 | 350 | PASS | 4.552e-15 |

## Interpretation

The registered fixtures span groups, linear algebra, determinant geometry, QR, SO(3), eigenstructure, graph Laplacians, SVD, projective geometry, tensor products, exterior algebra, differential calculus, Newton methods, quadratic optimization, Schur complements, convexity, LP duality, orthogonal projection, ridge regression, and positive-definite kernels.

All twenty fixtures passed. This supports the architectural proposition that EO and GEO can be maintained as two simultaneous views of one semantic mathematical graph.

This is not an EO-vs-GEO benchmark. `SAME_SEMANTICS` is the governing invariant.

## Evidence discipline

- **A**: direct native project parity already established in EO/GEO repositories.
- **B**: independent executable mathematical equivalence between operator and geometric/relational formulations.
- **C**: graph-only representability.

The present suite is primarily class B; the SO(3) fixture overlaps prior class-A project evidence.

## Boundary

Not established by v0.3:

- extraction of every declaration and proof from the source;
- universal EO closure;
- universal GEO closure;
- native GEO execution of every fixture;
- Lean proof emission or kernel verification;
- complete source proof-dependency reconstruction.

The next stage should therefore be a real source importer into this unchanged graph schema.
