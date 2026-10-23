# Geometry implementation report

Implemented all 12 public interfaces in `ngc_geometry_lab/geometry.py` with NumPy and stdlib only. No reference, adapter, backend, network, or oracle imports are used.

## Test-first evidence

Tests were written against explicit `NotImplementedError` interface stubs before production implementation. Tests use independent analytic expectations: tetrahedral dot products and vertex probabilities, active quarter rotations and order dependence, crossed/inserted polarizers, conjugated cubic rotations, Lorentz-invariant indefinite metric, shear ambiguity, fixed-point centers, Cartesian Gram volume, sequential observability, singlet probabilities, product coordinates, and CHSH `2*sqrt(2)`. Shape, normalization, complex, nonfinite, singular, and invalid-projector cases are included.

Commands executed from the project root:

1. `python -m unittest discover -s tests -p test_geometry.py -v > evidence/development/geometry_red.log 2>&1` — exit 1; 31 tests, 75 subtest errors, all caused by the intentional missing implementations (`NotImplementedError`).
2. `python -m unittest discover -s tests -p test_geometry.py -v > evidence/development/geometry_green.log 2>&1` — exit 0; 31 tests passed. This original log was preserved as `geometry_green_initial.log` because one invalid-input test fixture emitted a NumPy warning while constructing an infinite diagonal. The fixture was changed to an all-infinite matrix; production behavior was unchanged.
3. `python -W error -m unittest discover -s tests -p test_geometry.py -v > evidence/development/geometry_green.log 2>&1` — exit 0; 31 tests passed with warnings promoted to errors.
4. `python -W error -m unittest discover -s tests -v > evidence/development/geometry_full_suite.log 2>&1` — exit 0; all 64 tests available at verification time passed, with warnings promoted to errors. Other workers may add further tests later; the root owner must run final integration verification.

## Interface decisions

- Real APIs check imaginary components before float conversion; nonzero imaginary data is rejected. Zero-imaginary complex representations are accepted as mathematically real.
- Probability normalization/nonnegativity and Bloch-ball boundaries use absolute tolerance `1e-10`. Materially invalid data is rejected; values are never silently renormalized or projected.
- Rodrigues axes and projection/CHSH axes are explicitly normalized. Projection requires a unit initial vector and preserves the complete unnormalized vector through every projector. Empty projection sequences preserve the input. Alternate readout exponents remain explicit hypotheses.
- Metric inference solves homogeneous constraints in a Frobenius-orthonormal symmetric basis. `space_dimension` is homogeneous nullity before trace normalization. Numerical nullity uses threshold `tol * max(1, largest singular value)`; candidate SPD eigenvalues must exceed `tol`. Trace is normalized to the declared coordinate dimension.
- Nullity zero is numerically infeasible. Nullity one is classified only when its spectrum is resolved: an SPD candidate above tolerance is unique up to scale, a negative eigenvalue separated from zero rules out the unique trace-normalized metric, and eigenvalues within tolerance of zero return `unresolved_feasibility`. A near-zero candidate trace is infeasible only when both positive and negative eigenvalues are separated from zero. Higher-nullity spaces return `underdetermined` only with a positive-definite projected-identity witness; failed witness search returns `unresolved_feasibility`. No general semidefinite feasibility solver or unsupported no-SPD conclusion is introduced.
- Metric `residual` is the Euclidean norm of stacked homogeneous constraints evaluated on the trace-normalized candidate. With no nullspace it is evaluated on the identity as a contradiction diagnostic. With zero candidate trace it remains zero, reflecting the homogeneous candidate rather than a trace-normalized witness.
- Center residual is `norm(stacked_constraints @ center - stacked_offsets)`. Inconsistency uses a relative scale `tol * max(1, norm(offsets))`. Underdetermined solutions explicitly return the least-norm representative.
- `tetra_geometry` returns translation-invariant quantities from row displacements using Cholesky-transformed vectors; origin is validated. Edges follow pairs `01,02,03,12,13,23`.
- One-row observation vectors are accepted along with multirow matrices. Steps and metric dimension must be positive integers; booleans are rejected.
- Joint-coordinate inversion accepts every normalized nonnegative 16-outcome distribution, including distributions outside the quantum-state set. `joint_probabilities` validates its resulting distribution without independently imposing quantum positivity. This limitation is documented in module and function docstrings.

## Remaining limits

Metric identifiability and positive definiteness are numerical, tolerance-dependent determinations. Higher-nullity feasibility is intentionally incomplete, and very ill-conditioned operators/metrics can cross rank or eigenvalue thresholds. Joint probability validity is not a density-matrix positivity certificate. These interfaces do not establish a physical readout law or experimental Bell violation.

Only scoped geometry source, geometry tests, this report, and `evidence/development/geometry_*` files were modified. No commits or remote writes were performed.

## Independent-review correction: unresolved spectral boundary

The reviewer supplied an exact counterexample to the initial nullity-one classification. For `s=2**20`, projectors `diag(1,0)` and `[[.5,s/2],[1/(2*s),.5]]` are exactly idempotent and self-adjoint under `G=2*diag(s**-2,1)/(1+s**-2)`. Its minimum eigenvalue is positive, about `1.8189894e-12`, below the default tolerance. Original code incorrectly called this infeasible because it conflated failure to certify SPD (`eigmin <= tol`) with a certificate of a negative eigenvalue. The reproduction is preserved in `geometry_metric_boundary_reproduction.log`.

Added two regression tests before the fix: this ill-conditioned SPD counterexample and a unique semidefinite boundary from `diag(2,1)`. Both now require `unresolved_feasibility` at default tolerance; the SPD example resolves normally if the caller explicitly requests `tol=1e-13`. No existing test was weakened or removed. The existing clear indefinite Lorentz example and zero-nullity dilation continue to require infeasibility. Tolerance was not relaxed; the classification was corrected to retain uncertainty near zero.

Additional exact commands:

1. `python -W error -m unittest discover -s tests -p test_geometry.py -v > evidence/development/geometry_metric_boundary_red.log 2>&1` — exit 1; 33 tests, exactly two expected assertion failures in the new boundary regression tests.
2. `python -W error -m unittest discover -s tests -p test_geometry.py -v > evidence/development/geometry_metric_boundary_green.log 2>&1` — exit 0; all 33 geometry tests passed.
3. `python -W error -m unittest discover -s tests -v > evidence/development/geometry_metric_boundary_full_suite.log 2>&1` — exit 1; 71 tests, eight errors in the concurrently developing workflow suite, caused by its intentional `generate_dataset` / `run_campaign` stubs. All geometry tests passed. Exact affected test names are preserved in that full-suite log and reported to the root owner for final integration verification.
