# GEO-BSL-001 — Arithmetic-to-Geometry Reconstruction

**Qualification:** standalone baseline implemented; MAPEOGEO-native operator reconstruction **not yet qualified**.

## Purpose
Infer a finite graph's inverse-Laplacian spectral trace from adjacency only, fit an invariant across training graph sizes, then test unseen sizes and negative controls. The topology constructor, estimator and training fitter do not use pi or Euler's identity. The known coefficients and Basel constant appear only in the independent test/reference checks.

## Execute
From the repository root (requires Python, numpy):

```bash
python -m unittest discover -s experiments/geo_bsl_001 -v
python experiments/geo_bsl_001/benchmark.py --output geo_bsl_001_results.json
```

## Gates
- G1: classify an unlabeled, connected 2-regular finite graph as a cycle; reject paths and disconnected unions.
- G2: build combinatorial Laplacian from adjacency; compute nonzero spectrum; validate null mode and relabeling invariance.
- G3: fit S(N)=a N^2+b from six sizes; verify eight withheld sizes.
- G4: compare inferred finite coefficients to the independently proven cycle result; examine continuum rescaling. **Continuum convergence proof remains an independent mathematical obligation.**
- G5: reject broken, weighted, disconnected and path controls. Negative controls are topology checks, not learned OOD detection.

## Known result and boundaries
For a simple cycle of N>=3 vertices:
S(N)=sum_{nonzero Laplacian eigenvalues} 1/lambda = (N^2-1)/12.
A continuum argument recovers sum_{k>=1} 1/k^2=pi^2/6 after accounting for paired eigenmodes. Computing partial sums of the Basel series is a reference check only, not evidence of discovery.

This benchmark deliberately separates (1) supplied graph topology, (2) computational eigenvalue reconstruction, (3) learned coefficient inference and (4) analytic identity validation. It does **not** demonstrate that MAPEOGEO's domain-neutral operators autonomously identify geometry, spectrum or continuum limits.

## Next integration obligations
- Replace numpy graph reconstruction with a MAPEOGEO adapter using the repository's actual graph and operator contracts.
- Enforce blind, hashed holdouts and a no-oracle feature manifest.
- Add non-cycle positive families (paths, grids, tori) with their own qualified laws.
- Add spectral isospectral counterexamples and identifiability checks.
- Preserve original failing runs, fixes and independent rerun artifacts.
- Establish explicit falsification outcomes before promoting any discovery claim.
