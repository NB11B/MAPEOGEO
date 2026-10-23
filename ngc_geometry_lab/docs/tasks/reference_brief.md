# Independent complex reference task

Work in `/workspace/scratch/f4c8fe3fa7f4/ngc_geometry_lab`.
Own only `ngc_geometry_lab/reference.py`, `tests/test_reference.py`, `docs/tasks/reference_report.md`, and `evidence/development/reference_*`.
Use Python/NumPy, stdlib unittest. No imports from geometry, calibration, NGC, or MAPEOGEO code. No subagents. Do not commit other workers' files.

Tests first with preserved red then green output. All interfaces validate finite inputs, dimensions, trace/positivity for density matrices, normalization for states and unitary structure where appropriate. Use rtol=0 with explicitly bounded atol. Big-endian qubit ordering: qubit0 is first tensor factor, targets order determines local basis order.

## Interface

- `paulis()` -> (4,2,2) complex array ordered I,X,Y,Z.
- `validate_density(rho, *, atol=1e-10)` -> validated complex ndarray (power-of-two not required, square); reject non-Hermitian, negative eigenvalue below tolerance, nonunit trace, nonfinite.
- `density_from_bloch(state)` -> (2,2); validate real Bloch vector norm<=1.
- `bloch_from_density(rho)` -> (3,) via Pauli traces.
- `tetra_effects()` -> (4,2,2) with directions (+++),(+--),(-+-),(--+)/sqrt3 and E=(I+n.sigma)/4.
- `tetra_probabilities(rho)` -> (4,) via traces of rho E, no direct geometric shortcut.
- `rotation_unitary(axis, angle)` -> cos(angle/2)I - i sin(angle/2) axis.sigma; finite nonzero real axis normalized.
- `evolve_density(rho, unitary)` -> U rho U† with validation.
- `random_density(dimension, rng, *, pure=False)` -> normalized complex Wishart density (pure rank1 or full rank).
- `local_gate(state, gate, targets, num_qubits)` -> complex state using reshape/tensor-axis permutation and matrix multiply, NOT source NGC block-index algorithm. Validate normalized state, integer unique in-range targets, gate dimensions/unitarity; support reversed and nonadjacent target order.
- `joint_tetra_probabilities(rho)` -> (4,4) from tr(rho kron(Ei,Ej)).
- `joint_parameters(rho)` -> `(a,b,C)` via Pauli tensor traces, 4x4 density required.
- `density_from_joint(a,b,correlations)` -> 4x4 density via Pauli expansion; validate PSD including examples where valid tetra probabilities alone are insufficient.

## Tests

Explicit |0>,|1>,|+>,|+i>, maximally mixed, singlet, product |01>; effects sum to I, analytic probabilities; RX(pi) maps |0> to |1> probabilities; RZ phase; nonadjacent/reversed targets on explicit basis (independently hand-derived); arbitrary unitary vs dense kron small case; invalid shapes/complex axes/nonfinite/nonunitary/non-PSD. Include density trace checks and a CHSH expectation analytic singlet if helpful.

Report exact commands/results and any concerns. Do not call the geometric model to construct expected values.
