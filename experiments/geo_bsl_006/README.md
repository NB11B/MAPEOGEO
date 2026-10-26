# GEO-BSL-006: native PSMSL operator-basis integration

Uses the *actual* repository vendored `mapeogeo.psmsl_operator_basis_v1.discover_linear_operator_basis` and `psmsl_operator_algebra_v1.ordering_semantics` methods; no reimplementation of their rank or commutator algorithms.

## Scope
Given **unlabeled vector input/output pairs**, infer finite-dimensional linear maps with least squares and evaluate untouched holdouts. Admit only identifiable and accurate operators to the native basis selector. Test an independent pair of 2x2 matrices, a redundant scalar multiple, nonlinear (quadratic) outputs, rank-deficient observations, and operator noncommutation.

## Execute
From this directory:
```bash
python -m unittest discover -v
python adapter.py
```

Requires numpy. The parent repository's vendor tree must be present. Native basis import is mandatory; no silent fallback.

## Claims boundary
This is a **real native operator API integration** but **not unrestricted grammar discovery**. Linear state coordinates are supplied, matrix dimension is two in reference tests, and the task partitions are supplied. It does not establish the Basel continuum identity or general nonlinear composition. Holdout verification is performed *before* passing an operator to the native basis selector; this is intentionally fail-closed.

Next: unknown task segmentation, nonlinearity grammar search, independent generator tests, and MD2 adequacy integration. Preserve all test failures and corrected reruns.
