# Independent core review

Reviewed commit `121628385606e38affbe26e63334d00f3b5a94ac` against base `77d3230`, the supplied core patch, geometry/reference briefs, and the frozen qualification design. Scope: `geometry.py`, `reference.py`, `observations.py`, and their three test files. Review was read-only except this report. The previously reported 64-test pass was not rerun.

## Verdict

**Spec compliance: changes requested for one important classification error. Code quality: otherwise acceptable within the declared computational model, with a small count-validation correction also required before delivery.** No critical issue found. The review findings below concern the reviewed head; owners have been informed and are preparing corrections, which this report does not yet verify.

The tetrahedral factors, Rodrigues sign, attenuation-preserving projection sequences, center equations, Gram construction, joint Pauli expansion, and CHSH convention are consistent with the stated model. Reference calculations import neither geometry nor the source backend. Big-endian tensor ordering and supplied target order are correct in the inspected implementation. Joint-coordinate probability validity is correctly distinguished from quantum PSD validation. Calibration uses calibration preparations/counts only; estimation consumes unknown counts and the fitted detector, and verification counts are used after prediction for scoring. Raw unphysical estimates and radial corrections are retained.

## Findings

### P2 — A small positive eigenvalue becomes a false no-SPD conclusion

Location: `ngc_geometry_lab/geometry.py:177-180`.

In a one-dimensional constraint nullspace, `eigmin <= tol` returns `no_positive_definite_metric`, including when the candidate is strictly SPD. The tolerance boundary cannot substantiate an infeasibility claim. This affects coordinate systems with large but finite anisotropy; it does not require noisy or non-idempotent input.

Reproduction from the repository root:

```python
import numpy as np
from ngc_geometry_lab.geometry import infer_metric
s = 2.**20
ps = [np.diag([1., 0.]), np.array([[.5, s/2], [1/(2*s), .5]])]
g = 2*np.diag([s**-2, 1.])/(1+s**-2)
print(infer_metric([], ps, dimension=2))
print(np.linalg.eigvalsh(g))
print([np.linalg.norm(p@p-p) for p in ps])
print([np.linalg.norm(p.T@g-g@p) for p in ps])
```

Observed: `space_dimension=1`, `status='no_positive_definite_metric'`, `metric=None`. The analytic metric has eigenvalues approximately `[1.8189894e-12, 2.]`; all printed projector and metric-constraint residuals are exactly zero. Independently, write a symmetric metric as `[[x,y],[y,z]]`: the first projector forces `y=0`, and the second forces `x*s=z/s`. Thus every solution is proportional to `diag(s**-2,1)`, including the explicit SPD witness. This hand derivation double-checks the numerical oracle. Setting `tol=1e-13` also recovers the metric with residual `1.4973568522298576e-22`.

Required correction: do not infer mathematical nonexistence from a positive eigenvalue below the numerical acceptance margin. Distinguish unresolved/ill-conditioned cases or certify definiteness with an appropriate error bound. Preserve definitive rejection for a genuinely indefinite or singular unique form. Add this analytic regression, covering the classification rather than only recovered entries.

### P3 — Float conversion changes oversized integer count evidence before validation

Location: `ngc_geometry_lab/observations.py:34-43`.

`validate_counts([2**53+1,0,0,0])` currently succeeds and returns first count `9007199254740992`, silently reducing the supplied integer by one. `validate_counts([2**53,1,0,0])` also succeeds although the exact integer total exceeds its documented `2**53` bound. Float conversion and float summation occur before the exact-integer checks. The first result is directly inconsistent with the function's promise to avoid rounding; this boundary does not affect the planned 65536-shot synthetic campaign.

Required correction: check integer values and the total exactly before float conversion, retaining the documented range and rejection policy. Parent owner acknowledged this finding and is adding boundary regressions.

## Focused verification and test assessment

Two small direct Python probes reproduced the findings above. No existing suite was repeated. A separate deterministic probe checked the tensor-order risk more strongly than the existing norm-only arbitrary-unitary check for reversed targets: it generated 60 random-unitary cases over 1–4 qubits and every ordered target tuple of length up to 3, and compared `reference.local_gate` with an independent amplitude sum using integer extraction/replacement of big-endian bits. All passed at absolute threshold `1e-12`; maximum absolute error was `2.237726045655905e-16`. This oracle used no tensor permutation, backend call, or geometric function.

Existing analytic fixtures adequately cover common cases and the crucial separation between valid joint probabilities and PSD. Several geometry tests use NumPy's default relative tolerance (for example the metric check at `tests/test_geometry.py:85`), so those assertions alone do not establish the frozen absolute error gates. The final campaign should enforce those gates directly, with `rtol=0` or explicit maximum absolute errors. Reference tests already use `rtol=0`.

## Explicitly not judged

- Campaign gate execution, named RNG separation, finite-shot performance, readout model selection, reproducibility, packaging, archive extraction, and final evidence preservation: these were still being built and are outside this review.
- Repository adapters, exact closure enumeration, vendored behavior, source provenance hashes, licensing, and CUDA claims.
- General SPD feasibility in multidimensional nullspaces: the intentionally incomplete witness search is acceptable when failure is labeled unresolved.
- Physical correctness of experimental preparation coordinates, stationarity or memorylessness of a real detector, laboratory Bell assumptions, or derivation of a readout law. The modules state their assumptions and support computational comparison only.
- Robustness at arbitrary near-overflow floating-point scales beyond the specific reproduced metric/count issues. No general numerical certification is implied.

