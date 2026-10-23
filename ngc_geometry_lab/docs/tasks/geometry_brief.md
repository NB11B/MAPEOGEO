# Geometry implementation task

Work in `/workspace/scratch/f4c8fe3fa7f4/ngc_geometry_lab`.
Own only `ngc_geometry_lab/geometry.py`, `tests/test_geometry.py`, `docs/tasks/geometry_report.md`, and `evidence/development/geometry_*`.
Use Python/NumPy/SciPy and stdlib unittest. No network dependencies. Read the spec's constraints and frozen gates. No imports from reference, repository adapters, or quantum backends. No subagents. Do not commit other workers' files.

Write meaningful tests first, run them against stubs to demonstrate missing behavior, preserve red output, then implement and preserve green output. Test independent analytic examples and invalid input, not only round trips.

## Public interface

- `tetra_directions()` -> float array (4,3), rows (+++),(+--),(-+-),(--+) divided by sqrt(3); return fresh data.
- `tetra_probabilities(state)` -> (4,), `p=(1+N@r)/4`; require finite real shape (3,), norm <=1 within 1e-10.
- `tetra_reconstruct(probabilities, *, enforce_physical=True)` -> (3,), `r=3*p@N`; require nonnegative, normalized real (4,). If enforce_physical reject norm >1+tol; otherwise return raw estimate. Do not silently project or normalize materially invalid data.
- `rotation(axis, angle)` -> (3,3), active Rodrigues rotation; axis any finite nonzero real (3,), normalized explicitly; angle finite.
- `projection_transmission(state, axes, *, exponent=2.0)` -> `(weight, final_vector)`; finite real normalized input, each axis normalized, actual unnormalized sequential rank-one projections, final weight `norm(final_vector)**exponent`; exponent positive finite. Preserve attenuation.
- `infer_metric(isometries, projectors=(), *, dimension=3, tol=1e-10)` -> dict with `status`, `space_dimension`, `metric` (ndarray or None), `residual`. Solve symmetric linear constraints R.T G R=G and P.T G=GP; require P idempotent; normalize trace(G)=dimension. Status `unique_up_to_scale`, `underdetermined`, `no_positive_definite_metric`, or `unresolved_feasibility`. In nullity>1, projection of identity into nullspace may find a valid SPD witness; failure to find one MUST be unresolved, not a no-SPD proof. Nullity0 and nullity1 have definitive classification. Validate dimensions/finiteness.
- `infer_center(affine_operators, *, tol=1e-10)` -> dict `status` (unique/underdetermined/inconsistent), `center` (array or None), `rank`, `residual`. Stack (I-A)o=b. At least one operator; incompatible systems return no center. A least-norm representative for underdetermination is labeled as such.
- `tetra_geometry(origin, displacements, metric=None)` -> dict `edges` (6 lengths for pairs 01,02,03,12,13,23), `volume`, `gram`; displacements (3,3) are row vectors. Reject degenerate tetrahedron and non-SPD metric.
- `observability_matrix(observation, transition, steps)` -> stack C,CA,...,CA**(steps-1). Positive integer steps. Observation may be multirow; validate.
- `joint_probabilities(a,b,correlations)` -> (4,4), formula (1+Ni.a+Nj.b+Ni.T C Nj)/16. Validate real dimensions, finite numbers, and output probability validity. This function evaluates correlation coordinates, not a proof of density-matrix positivity; document this.
- `joint_reconstruct(probabilities)` -> `(a,b,C)` using factors3,3,9; valid normalized nonnegative (4,4) probabilities. No assumption that every 16-outcome vector describes a quantum state.
- `chsh_value(correlations,a0,a1,b0,b1)` -> float using unit axes and E00+E01+E10-E11.

## Tests

Analytic tetra vertices, maximally mixed state, invalid one-hot tetra distribution, rotations and order dependence, crossed polarizers (0 and 1/4), conjugated cubic rotations recovering a non-Euclidean coordinate metric, insufficient metric family, inconsistent isometry 2I, common center unique/nonunique/inconsistent, Gram volume, duplicated observations vs sequence rank, singlet joint tensor and CHSH 2sqrt(2), nonfinite/complex/shape failures. Real APIs must reject nonzero imaginary inputs instead of discarding them.

Report exact commands/results, interface decisions, remaining concerns. Keep report concise and preserve red/green logs.
