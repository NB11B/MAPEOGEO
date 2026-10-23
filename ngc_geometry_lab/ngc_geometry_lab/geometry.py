"""Real geometric coordinates, operator constraints, and observation maps.

This module has no dependency on quantum backends or the independent complex
reference. Joint correlation coordinates describe tetrahedral probabilities;
their validity alone does not establish density-matrix positivity.
"""
from itertools import combinations

import numpy as np

_TOL = 1e-10


def _real(value, name, shape=None):
    """Validate before conversion so imaginary components are never discarded."""
    try:
        array = np.asarray(value)
        if np.iscomplexobj(array):
            if np.any(array.imag != 0):
                raise ValueError(f'{name} must be real')
            array = array.real
        array = np.asarray(array, dtype=float)
    except (TypeError, OverflowError, ValueError) as exc:
        raise ValueError(f'{name} must contain finite real numbers') from exc
    if not np.all(np.isfinite(array)):
        raise ValueError(f'{name} must contain finite real numbers')
    if shape is not None and array.shape != shape:
        raise ValueError(f'{name} must have shape {shape}, got {array.shape}')
    return array


def _positive_scalar(value, name):
    scalar = _real(value, name, ())
    if scalar <= 0:
        raise ValueError(f'{name} must be positive')
    return float(scalar)


def _positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value <= 0:
        raise ValueError(f'{name} must be a positive integer')
    return int(value)


def _unit(value, name):
    array = _real(value, name, (3,))
    # Scaling first avoids overflow when a finite axis has very large entries.
    scale = np.max(np.abs(array))
    if scale == 0:
        raise ValueError(f'{name} must be nonzero')
    scaled = array / scale
    return scaled / np.linalg.norm(scaled)


def _probabilities(value, shape):
    array = _real(value, 'probabilities', shape)
    if np.any(array < -_TOL) or not np.isclose(array.sum(), 1, rtol=0, atol=_TOL):
        raise ValueError('probabilities must be nonnegative and sum to one')
    return array


def tetra_directions():
    """Return fresh tetrahedral unit vectors in the declared vertex order."""
    return np.array([[1.,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]) / np.sqrt(3)


def tetra_probabilities(state):
    """Evaluate a physical Bloch vector in tetrahedral observation coordinates."""
    state = _real(state, 'state', (3,))
    if np.linalg.norm(state) > 1 + _TOL:
        raise ValueError('state must be inside the unit ball')
    return (1 + tetra_directions() @ state) / 4


def tetra_reconstruct(probabilities, *, enforce_physical=True):
    """Invert tetrahedral observations without normalization or projection."""
    probabilities = _probabilities(probabilities, (4,))
    state = 3 * probabilities @ tetra_directions()
    if enforce_physical and np.linalg.norm(state) > 1 + _TOL:
        raise ValueError('probabilities reconstruct outside the unit ball')
    return state


def tetra_transformation_matrix(rot_matrix):
    """Return the 4x4 transfer matrix M(R) acting directly on tetrahedral probabilities.

    For rotation R in SO(3), M(R)_{ij} = (1 + 3 * n_i . (R @ n_j)) / 4.
    Satisfies M(R2 @ R1) = M(R2) @ M(R1) and p' = M(R) @ p.
    """
    rot = _real(rot_matrix, 'rotation matrix', (3, 3))
    dirs = tetra_directions()
    return (1.0 + 3.0 * (dirs @ rot @ dirs.T)) / 4.0


def affine_channel_transfer_matrix(affine_A, translation_c=None):
    """Return the 4x4 transfer matrix M(A, c) acting on tetrahedral probabilities.

    For single-qubit affine Bloch channel r' = A @ r + c:
    M(A, c)_{ij} = (1 + n_i . c + 3 * n_i . (A @ n_j)) / 4.
    Preserves channel composition: M(E2 o E1) = M(E2) @ M(E1).
    """
    A_mat = _real(affine_A, 'affine matrix A', (3, 3))
    c_vec = np.zeros(3) if translation_c is None else _real(translation_c, 'translation c', (3,))
    dirs = tetra_directions()
    return (1.0 + dirs @ c_vec[:, None] + 3.0 * (dirs @ A_mat @ dirs.T)) / 4.0


def bloch_channel_from_kraus(kraus_list):
    """Extract affine Bloch parameters (A, c) from a list of 2x2 Kraus operators.

    Satisfies r' = A @ r + c for rho' = sum_k K_k rho K_k^dagger.
    """
    # Standard Pauli matrices
    paulis = [
        np.eye(2, dtype=complex),
        np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex),
        np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex),
        np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex),
    ]
    sigmas = paulis[1:]

    def apply_channel(mat):
        out = np.zeros((2, 2), dtype=complex)
        for k in kraus_list:
            k_mat = np.asarray(k, dtype=complex)
            out += k_mat @ mat @ k_mat.conj().T
        return out

    # c_i = 1/2 Tr(sigma_i E(I))
    e_identity = apply_channel(paulis[0])
    c = np.array([0.5 * np.trace(s @ e_identity).real for s in sigmas])

    # A_ij = 1/2 Tr(sigma_i E(sigma_j))
    A = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            e_sigma_j = apply_channel(sigmas[j])
            A[i, j] = 0.5 * np.trace(sigmas[i] @ e_sigma_j).real

    return A, c


def tetra_purity_bound(probabilities):
    """Evaluate sum_i p_i^2; physical Bloch ball states satisfy sum_i p_i^2 <= 1/3."""
    probs = _probabilities(probabilities, (4,))
    return float(np.sum(probs**2))


def rotation(axis, angle):
    """Active right-handed Rodrigues rotation, normalizing a nonzero axis."""
    x,y,z = _unit(axis, 'axis')
    angle = float(_real(angle, 'angle', ()))
    cross = np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    return np.eye(3) + np.sin(angle)*cross + (1-np.cos(angle))*(cross @ cross)


def projection_transmission(state, axes, *, exponent=2.0):
    """Apply rank-one projectors without renormalizing intermediate vectors.

    The initial state must be unit length. Axes may have arbitrary nonzero
    length and are normalized before constructing their projectors. Exponent
    selection is an explicit readout hypothesis, not a derived probability law.
    """
    vector = _real(state, 'state', (3,)).copy()
    if not np.isclose(np.linalg.norm(vector), 1, rtol=0, atol=_TOL):
        raise ValueError('initial state must have unit norm')
    exponent = _positive_scalar(exponent, 'exponent')
    try:
        axes = list(axes)
    except TypeError as exc:
        raise ValueError('axes must be an iterable of three-vectors') from exc
    for axis in axes:
        unit = _unit(axis, 'axis')
        vector = unit * np.dot(unit, vector)
    return float(np.linalg.norm(vector)**exponent), vector


def infer_metric(isometries, projectors=(), *, dimension=3, tol=_TOL):
    """Infer symmetric metrics satisfying isometry/self-adjointness constraints.

    Symmetric coordinates use a Frobenius-orthonormal basis. The homogeneous
    nullspace is computed first; trace normalization is applied afterwards.
    In a multidimensional nullspace only the projected-identity SPD witness is
    attempted. Its failure is explicitly unresolved, never an infeasibility proof.
    Even in a one-dimensional nullspace an eigenvalue within ``tol`` of zero
    is numerically unresolved: failure to certify SPD does not certify its absence.
    """
    dimension = _positive_integer(dimension, 'dimension')
    tol = _positive_scalar(tol, 'tol')
    shape = (dimension, dimension)
    try:
        rotations = [_real(r, 'isometry', shape) for r in isometries]
        projections = [_real(p, 'projector', shape) for p in projectors]
    except TypeError as exc:
        raise ValueError('operators must be iterables of square matrices') from exc
    for p in projections:
        if np.linalg.norm(p @ p-p) > tol*max(1.,np.linalg.norm(p)):
            raise ValueError('projector must be idempotent')
    basis = []
    for i in range(dimension):
        for j in range(i,dimension):
            b = np.zeros(shape)
            b[i,j] = b[j,i] = 1 if i == j else 1/np.sqrt(2)
            basis.append(b)
    blocks = []
    for r in rotations:
        blocks.append(np.stack([(r.T @ b @ r-b).ravel() for b in basis], axis=1))
    for p in projections:
        blocks.append(np.stack([(p.T @ b-b @ p).ravel() for b in basis], axis=1))
    count = len(basis)
    if blocks:
        constraints = np.concatenate(blocks, axis=0)
        if not np.all(np.isfinite(constraints)):
            raise ValueError('operators overflow metric constraints')
        _,singular,vh = np.linalg.svd(constraints, full_matrices=True)
        cutoff = tol * max(1., singular[0] if singular.size else 0.)
        rank = int(np.count_nonzero(singular > cutoff))
        nullspace = vh[rank:].T
    else:
        constraints = np.zeros((0,count))
        nullspace = np.eye(count)
    nullity = nullspace.shape[1]
    result = {'status':'no_positive_definite_metric', 'space_dimension':nullity,
              'metric':None, 'residual':0.}
    if nullity == 0:
        # Residual of the trace-normalized identity is a useful contradiction diagnostic.
        identity_coeff = np.array([np.trace(b) for b in basis])
        result['residual'] = float(np.linalg.norm(constraints @ identity_coeff))
        return result
    identity_coeff = np.array([np.trace(b) for b in basis])
    if nullity == 1:
        coeff = nullspace[:,0]
    else:
        coeff = nullspace @ (nullspace.T @ identity_coeff)
    candidate = np.einsum('i,ijk->jk', coeff, np.asarray(basis))
    trace = np.trace(candidate)
    if abs(trace) <= tol:
        eigenvalues = np.linalg.eigvalsh(candidate)
        # Both signs, separated from zero, rule out either scalar orientation.
        # A near-zero trace alone is not used as an infeasibility certificate.
        indefinite = eigenvalues[0] < -tol and eigenvalues[-1] > tol
        if nullity > 1 or not indefinite:
            result['status'] = 'unresolved_feasibility'
        return result
    candidate *= dimension / trace
    coeff *= dimension / trace
    result['residual'] = float(np.linalg.norm(constraints @ coeff))
    smallest_eigenvalue = np.linalg.eigvalsh(candidate)[0]
    if smallest_eigenvalue <= tol:
        # Only a negative eigenvalue separated from zero proves infeasibility
        # for the unique trace-normalized candidate. Tiny positive, zero, and
        # tiny negative values all remain unresolved at the requested tolerance.
        if nullity > 1 or smallest_eigenvalue >= -tol:
            result['status'] = 'unresolved_feasibility'
        return result
    result['status'] = 'unique_up_to_scale' if nullity == 1 else 'underdetermined'
    result['metric'] = candidate
    return result


def infer_center(affine_operators, *, tol=_TOL):
    """Solve (I-A)o=b; underdetermined centers use a least-norm representative."""
    tol = _positive_scalar(tol, 'tol')
    try:
        operators = list(affine_operators)
    except TypeError as exc:
        raise ValueError('affine_operators must be iterable') from exc
    if not operators:
        raise ValueError('at least one affine operator is required')
    matrices, offsets = [], []
    dimension = None
    for operator in operators:
        try:
            a,b = operator
        except (TypeError,ValueError) as exc:
            raise ValueError('each affine operator must be (matrix, offset)') from exc
        a = _real(a, 'affine matrix')
        if a.ndim != 2 or a.shape[0] != a.shape[1] or a.shape[0] == 0:
            raise ValueError('affine matrix must be nonempty and square')
        if dimension is None:
            dimension = a.shape[0]
        if a.shape != (dimension,dimension):
            raise ValueError('affine operator dimensions must agree')
        b = _real(b, 'affine offset', (dimension,))
        matrices.append(np.eye(dimension)-a)
        offsets.append(b)
    matrix = np.concatenate(matrices,axis=0)
    rhs = np.concatenate(offsets)
    center,_,rank,_ = np.linalg.lstsq(matrix,rhs,rcond=tol)
    residual = float(np.linalg.norm(matrix @ center-rhs))
    inconsistent = residual > tol * max(1.,np.linalg.norm(rhs))
    status = 'inconsistent' if inconsistent else ('unique' if rank == dimension else 'underdetermined')
    return {'status':status,'center':None if inconsistent else center,
            'rank':int(rank),'residual':residual}


def tetra_geometry(origin, displacements, metric=None):
    """Compute edge lengths and Gram volume from three row displacements."""
    _real(origin, 'origin', (3,))
    displacements = _real(displacements, 'displacements', (3,3))
    metric = np.eye(3) if metric is None else _real(metric, 'metric', (3,3))
    if not np.allclose(metric,metric.T,rtol=0,atol=_TOL):
        raise ValueError('metric must be symmetric positive definite')
    try:
        factor = np.linalg.cholesky(metric)
    except np.linalg.LinAlgError as exc:
        raise ValueError('metric must be symmetric positive definite') from exc
    transformed = displacements @ factor
    if np.linalg.matrix_rank(transformed) < 3:
        raise ValueError('tetrahedron must be nondegenerate')
    gram = transformed @ transformed.T
    vertices = np.vstack([np.zeros(3),transformed])
    edges = np.array([np.linalg.norm(vertices[j]-vertices[i]) for i,j in combinations(range(4),2)])
    volume = abs(float(np.linalg.det(transformed))) / 6
    return {'edges':edges,'volume':volume,'gram':gram}


def observability_matrix(observation, transition, steps):
    """Stack C, CA, ..., CA**(steps-1), including multirow observations."""
    steps = _positive_integer(steps, 'steps')
    transition = _real(transition, 'transition')
    if transition.ndim != 2 or transition.shape[0] != transition.shape[1] or transition.shape[0] == 0:
        raise ValueError('transition must be a nonempty square matrix')
    observation = _real(observation, 'observation')
    if observation.ndim == 1:
        observation = observation[None,:]
    if observation.ndim != 2 or observation.shape[0] == 0 or observation.shape[1] != transition.shape[0]:
        raise ValueError('observation columns must match transition dimension')
    blocks = [observation.copy()]
    for _ in range(1,steps):
        blocks.append(blocks[-1] @ transition)
    result = np.concatenate(blocks,axis=0)
    if not np.all(np.isfinite(result)):
        raise ValueError('observability sequence overflowed')
    return result


def joint_probabilities(a,b,correlations):
    """Evaluate correlation coordinates; this is not a quantum positivity test.

    General valid 16-outcome distributions can reconstruct coordinates outside
    the quantum-state set. Only shape, finiteness, and output probabilities are
    required here; local vectors are not independently constrained to unit balls.
    """
    a = _real(a, 'a', (3,))
    b = _real(b, 'b', (3,))
    correlations = _real(correlations, 'correlations', (3,3))
    n = tetra_directions()
    p = (1+(n @ a)[:,None]+(n @ b)[None,:]+n @ correlations @ n.T)/16
    return _probabilities(p, (4,4))


def joint_reconstruct(probabilities):
    """Invert a 16-outcome distribution, without assuming quantum physicality."""
    p = _probabilities(probabilities, (4,4))
    n = tetra_directions()
    return 3*p.sum(axis=1) @ n, 3*p.sum(axis=0) @ n, 9*n.T @ p @ n


def chsh_value(correlations,a0,a1,b0,b1):
    """Compute E00+E01+E10-E11 with explicitly normalized measurement axes."""
    c = _real(correlations, 'correlations', (3,3))
    a0,a1,b0,b1 = [_unit(axis,'measurement axis') for axis in (a0,a1,b0,b1)]
    return float(a0 @ c @ b0+a0 @ c @ b1+a1 @ c @ b0-a1 @ c @ b1)


# =============================================================================
# Qutrit (d = 3) Geometry and Minimal 9-Outcome SIC-POVM
# =============================================================================

def gell_mann_matrices():
    """Return the 8 traceless Hermitian Gell-Mann matrices for SU(3).

    Normalized such that Tr(lambda_a lambda_b) = 2 delta_{ab}.
    """
    gm = []
    # 1: X_01
    m = np.zeros((3, 3), dtype=complex); m[0, 1] = 1; m[1, 0] = 1; gm.append(m)
    # 2: Y_01
    m = np.zeros((3, 3), dtype=complex); m[0, 1] = -1j; m[1, 0] = 1j; gm.append(m)
    # 3: Z_01
    m = np.zeros((3, 3), dtype=complex); m[0, 0] = 1; m[1, 1] = -1; gm.append(m)
    # 4: X_02
    m = np.zeros((3, 3), dtype=complex); m[0, 2] = 1; m[2, 0] = 1; gm.append(m)
    # 5: Y_02
    m = np.zeros((3, 3), dtype=complex); m[0, 2] = -1j; m[2, 0] = 1j; gm.append(m)
    # 6: X_12
    m = np.zeros((3, 3), dtype=complex); m[1, 2] = 1; m[2, 1] = 1; gm.append(m)
    # 7: Y_12
    m = np.zeros((3, 3), dtype=complex); m[1, 2] = -1j; m[2, 1] = 1j; gm.append(m)
    # 8: diag(1, 1, -2)/sqrt(3)
    m = np.diag([1.0, 1.0, -2.0]) / np.sqrt(3); gm.append(m)
    return np.array(gm)


def qutrit_sic_vectors():
    """Return the 9 standard Weyl-Heisenberg fiducial SIC-POVM unit vectors in C^3.

    Satisfies |<psi_j | psi_k>|^2 = 1/4 for all j != k, and sum 1/3 |psi_k><psi_k| = I_3.
    """
    omega = np.exp(2j * np.pi / 3.0)
    tau = np.exp(4j * np.pi / 3.0)
    v0 = np.array([0.0, 1.0, -1.0], dtype=complex) / np.sqrt(2.0)
    X = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=complex)
    Z = np.diag([1.0, omega, omega**2])

    vectors = []
    for j in range(3):
        for k in range(3):
            op = (tau ** (j * k)) * (np.linalg.matrix_power(X, j) @ np.linalg.matrix_power(Z, k))
            vectors.append(op @ v0)
    return np.array(vectors)


def qutrit_sic_directions():
    """Return the 8D real coordinates of the 9 SIC vectors: n_{k,a} = Tr(Pi_k lambda_a).

    Satisfies:
      sum_k n_k = 0  (centroid zero-sum)
      sum_k n_k n_k^T = 3/2 I_8  (8D frame resolution of identity)
      ||n_k||^2 = 4/3
    """
    gm = gell_mann_matrices()
    vecs = qutrit_sic_vectors()
    directions = []
    for v in vecs:
        proj = np.outer(v, v.conj())
        coords = [float(np.trace(proj @ g).real) for g in gm]
        directions.append(coords)
    return np.array(directions)


def qutrit_probabilities(bloch_vec_8d):
    """Evaluate 8D qutrit state vector in 9-outcome SIC observation coordinates.

    p_k = 1/3 Tr(rho Pi_k) = (1 + 3/2 n_k . r) / 9.
    """
    r = _real(bloch_vec_8d, 'qutrit 8D Bloch vector', (8,))
    n_mat = qutrit_sic_directions()
    p = (1.0 + 1.5 * (n_mat @ r)) / 9.0
    if np.any(p < -_TOL) or not np.isclose(np.sum(p), 1.0, atol=_TOL):
        raise ValueError('qutrit probabilities must be nonnegative and sum to 1')
    return p


def qutrit_reconstruct(probabilities_9):
    """Invert 9-outcome SIC probabilities to the 8D generalized Bloch vector: r = 4 sum_k p_k n_k."""
    p = _real(probabilities_9, 'qutrit 9 probabilities', (9,))
    if not np.isclose(np.sum(p), 1.0, atol=_TOL):
        raise ValueError('probabilities must sum to 1')
    n_mat = qutrit_sic_directions()
    return 4.0 * (p @ n_mat)


def qutrit_transformation_matrix(su3_unitary):
    """Return the 9x9 transfer matrix M(U) acting directly on qutrit SIC probabilities.

    For U in SU(3), M(U)_{ij} = (1 + 6 * n_i . (R_8 @ n_j)) / 9,
    where R_8 is the 8x8 adjoint representation (R_8)_{ab} = 1/2 Tr(lambda_a U lambda_b U^dagger).
    Preserves composition: M(U2 @ U1) = M(U2) @ M(U1).
    """
    U = np.asarray(su3_unitary, dtype=complex)
    if U.shape != (3, 3):
        raise ValueError('U must have shape (3, 3)')
    gm = gell_mann_matrices()
    R_8 = np.zeros((8, 8))
    for a in range(8):
        for b in range(8):
            R_8[a, b] = 0.5 * np.trace(gm[a] @ U @ gm[b] @ U.conj().T).real

    n_mat = qutrit_sic_directions()
    return (1.0 + 6.0 * (n_mat @ R_8 @ n_mat.T)) / 9.0


def qutrit_purity_bound(probabilities_9):
    """Evaluate sum_k p_k^2; physical qutrit states satisfy sum_k p_k^2 <= 1/6.

    Pure states attain sum p_k^2 = 1/6 (||p - u_9|| = 1/(3*sqrt(2)));
    the maximally mixed center u_9 = (1/9)*1 has sum p_k^2 = 1/9.
    """
    p = _real(probabilities_9, 'probabilities', (9,))
    return float(np.sum(p**2))


# ---------------------------------------------------------------------------
# Observable Lie / Jordan Algebra & Geometric Uncertainty
# ---------------------------------------------------------------------------

def pauli_matrices_2x2():
    """Return standard 2x2 Pauli matrices (I, X, Y, Z) as complex arrays."""
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return I, X, Y, Z


def bloch_observable(a0, a_vec):
    """Construct 2x2 complex Hermitian observable A = a0 * I_2 + a . sigma."""
    a0_val = float(_real(a0, 'a0', ()))
    a = _real(a_vec, 'a_vec', (3,))
    I, X, Y, Z = pauli_matrices_2x2()
    return a0_val * I + a[0] * X + a[1] * Y + a[2] * Z


def bloch_observable_decomposition(matrix_2x2):
    """Decompose 2x2 Hermitian matrix into scalar a0 and 3D Bloch vector a.

    a0 = 1/2 Tr(A), a_k = 1/2 Tr(A sigma_k).
    """
    m = np.asarray(matrix_2x2, dtype=complex)
    if m.shape != (2, 2):
        raise ValueError('matrix must have shape (2, 2)')
    if not np.allclose(m, m.conj().T, atol=_TOL):
        raise ValueError('matrix must be Hermitian')
    I, X, Y, Z = pauli_matrices_2x2()
    a0 = float(0.5 * np.trace(m).real)
    ax = float(0.5 * np.trace(m @ X).real)
    ay = float(0.5 * np.trace(m @ Y).real)
    az = float(0.5 * np.trace(m @ Z).real)
    return a0, np.array([ax, ay, az])


def jordan_product(A, B):
    """Return symmetric Jordan product 1/2 (A @ B + B @ A)."""
    A_mat = np.asarray(A, dtype=complex)
    B_mat = np.asarray(B, dtype=complex)
    if A_mat.shape != B_mat.shape or A_mat.ndim != 2:
        raise ValueError('matrices must be square and of identical shape')
    return 0.5 * (A_mat @ B_mat + B_mat @ A_mat)


def lie_bracket(A, B):
    """Return Lie commutator bracket [A, B] = A @ B - B @ A."""
    A_mat = np.asarray(A, dtype=complex)
    B_mat = np.asarray(B, dtype=complex)
    if A_mat.shape != B_mat.shape or A_mat.ndim != 2:
        raise ValueError('matrices must be square and of identical shape')
    return A_mat @ B_mat - B_mat @ A_mat


def geometric_jordan_product(a0, a_vec, b0, b_vec):
    """Compute Jordan product coordinates in R x R^3 directly:

    (a0 I + a . sigma) o (b0 I + b . sigma) = (a0 b0 + a . b) I + (a0 b + b0 a) . sigma.
    """
    a0_val = float(_real(a0, 'a0', ()))
    b0_val = float(_real(b0, 'b0', ()))
    a = _real(a_vec, 'a_vec', (3,))
    b = _real(b_vec, 'b_vec', (3,))
    c0 = a0_val * b0_val + float(np.dot(a, b))
    c_vec = a0_val * b + b0_val * a
    return c0, c_vec


def geometric_lie_bracket(a_vec, b_vec):
    """Compute real 3D generator 2 * (a x b) representing the Lie bracket:

    [a . sigma, b . sigma] = 2i (a x b) . sigma.
    """
    a = _real(a_vec, 'a_vec', (3,))
    b = _real(b_vec, 'b_vec', (3,))
    return 2.0 * np.cross(a, b)


def geometric_uncertainty_bound(a_vec, b_vec, bloch_state, tol=_TOL):
    """Compute the Oriented-Volume Uncertainty Bound (Geometric Robertson Bound).

    For traceless observables A = a . sigma, B = b . sigma in state rho = 1/2 (I + r . sigma),
    1/(2i) <[A, B]>_rho = (a x b) . r = det([a, b, r]).
    
    The uncertainty product Delta(A) * Delta(B) is bounded below by the oriented-volume magnitude:
      Delta(A) * Delta(B) >= |(a x b) . r| = |det([a, b, r])|.

    Note: The actual variance product Delta(A) * Delta(B) is NOT generally equal to the volume.
    It saturates this lower bound on specific pure states (e.g. pure states with r along a x b),
    but on general states Delta(A) * Delta(B) > |(a x b) . r|.

    Returns:
        dict containing 'bound', 'oriented_volume', 'actual_product', 'gap', and 'is_saturated'.
    """
    a = _real(a_vec, 'a_vec', (3,))
    b = _real(b_vec, 'b_vec', (3,))
    r = _real(bloch_state, 'bloch_state', (3,))
    if np.linalg.norm(r) > 1.0 + _TOL:
        raise ValueError('bloch_state norm cannot exceed 1')

    oriented_vol = float(np.dot(np.cross(a, b), r))
    bound = abs(oriented_vol)

    # Actual quantum standard deviations for single-qubit observables:
    # Delta(A)^2 = <A^2> - <A>^2 = ||a||^2 - (a . r)^2
    var_a = max(0.0, float(np.dot(a, a) - np.dot(a, r)**2))
    var_b = max(0.0, float(np.dot(b, b) - np.dot(b, r)**2))
    actual_product = np.sqrt(var_a * var_b)
    gap = float(actual_product - bound)
    is_saturated = bool(abs(gap) <= tol)

    return {
        'bound': bound,
        'oriented_volume': oriented_vol,
        'cross_product': np.cross(a, b),
        'actual_product': actual_product,
        'gap': gap,
        'is_saturated': is_saturated,
    }



# ---------------------------------------------------------------------------
# Real Dual-Lane Representation & Peres-Mermin Contextuality Square
# ---------------------------------------------------------------------------

def real_dual_lane_operator(complex_matrix):
    """Convert complex matrix M = A + iB to real dual-lane block form [[A, -B], [B, A]].

    Preserves matrix multiplication: Phi(M1 @ M2) = Phi(M1) @ Phi(M2).
    """
    m = np.asarray(complex_matrix, dtype=complex)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise ValueError('operator must be a square 2D matrix')
    a = m.real
    b = m.imag
    return np.block([[a, -b], [b, a]]).astype(float)


def peres_mermin_square():
    """Construct the 3x3 grid of 2-qubit observables as complex 4x4 matrices.

    Grid layout:
      [X (x) I,   I (x) X,   X (x) X]
      [I (x) Y,   Y (x) I,   Y (x) Y]
      [X (x) Y,   Y (x) X,   Z (x) Z]
    """
    I, X, Y, Z = pauli_matrices_2x2()
    row0 = [np.kron(X, I), np.kron(I, X), np.kron(X, X)]
    row1 = [np.kron(I, Y), np.kron(Y, I), np.kron(Y, Y)]
    row2 = [np.kron(X, Y), np.kron(Y, X), np.kron(Z, Z)]
    return [row0, row1, row2]


def peres_mermin_dual_lane_square():
    """Construct the 3x3 grid of Peres-Mermin observables in 8x8 real dual-lane form."""
    c_square = peres_mermin_square()
    return [[real_dual_lane_operator(c_square[i][j]) for j in range(3)] for i in range(3)]


def verify_peres_mermin_algebra(square_8x8):
    """Verify algebraic properties of the Peres-Mermin square in real dual-lane coordinates.

    Verifies:
      1. Involutory: O^2 = I_8 for all 9 operators.
      2. Commutation: all 3 elements in each row and column mutually commute ([O_a, O_b] = 0).
      3. Row products: O_{i0} @ O_{i1} @ O_{i2} = +I_8 for i = 0, 1, 2.
      4. Col products: O_{0j} @ O_{1j} @ O_{2j} = +I_8 for j = 0, 1.
      5. Col 2 product: O_{02} @ O_{12} @ O_{22} = -I_8.
      6. Classical non-contextuality contradiction:
         Product of row products = (+1)^3 = +1 != Product of col products = (+1)^2 * (-1) = -1.
         Exhaustive search over all 2^9 = 512 classical valuations confirms max satisfaction is 5/6.
    """
    I8 = np.eye(8)
    max_inv_err = 0.0
    for i in range(3):
        for j in range(3):
            op = square_8x8[i][j]
            inv_err = np.max(np.abs(op @ op - I8))
            if inv_err > max_inv_err:
                max_inv_err = inv_err

    max_comm_err = 0.0
    for i in range(3):
        for a, b in [(0, 1), (1, 2), (0, 2)]:
            c_err = np.max(np.abs(square_8x8[i][a] @ square_8x8[i][b] - square_8x8[i][b] @ square_8x8[i][a]))
            if c_err > max_comm_err:
                max_comm_err = c_err
    for j in range(3):
        for a, b in [(0, 1), (1, 2), (0, 2)]:
            c_err = np.max(np.abs(square_8x8[a][j] @ square_8x8[b][j] - square_8x8[b][j] @ square_8x8[a][j]))
            if c_err > max_comm_err:
                max_comm_err = c_err

    row_errors = []
    for i in range(3):
        prod = square_8x8[i][0] @ square_8x8[i][1] @ square_8x8[i][2]
        row_errors.append(float(np.max(np.abs(prod - I8))))

    col_errors = []
    for j in range(3):
        prod = square_8x8[0][j] @ square_8x8[1][j] @ square_8x8[2][j]
        expected = -I8 if j == 2 else I8
        col_errors.append(float(np.max(np.abs(prod - expected))))

    # Exhaustive classical non-contextual valuation audit over 2^9 = 512 assignments
    max_classical_sat = 0
    import itertools
    for assignment in itertools.product([-1, 1], repeat=9):
        grid = [list(assignment[k*3:(k+1)*3]) for k in range(3)]
        r_sat = sum(1 for k in range(3) if grid[k][0] * grid[k][1] * grid[k][2] == 1)
        c_sat = (1 if grid[0][0] * grid[1][0] * grid[2][0] == 1 else 0) + \
                (1 if grid[0][1] * grid[1][1] * grid[2][1] == 1 else 0) + \
                (1 if grid[0][2] * grid[1][2] * grid[2][2] == -1 else 0)
        total_sat = r_sat + c_sat
        if total_sat > max_classical_sat:
            max_classical_sat = total_sat

    return {
        'max_involutory_error': float(max_inv_err),
        'max_commutation_error': float(max_comm_err),
        'row_product_errors': row_errors,
        'col_product_errors': col_errors,
        'max_classical_satisfied_contexts': max_classical_sat,
        'total_contexts': 6,
        'classical_contradiction': bool(max_classical_sat < 6),
    }


# ---------------------------------------------------------------------------
# Continuous-Time Lindblad Dissipative Flows in Observation Space
# ---------------------------------------------------------------------------

def lindblad_observation_generator(bloch_drift_matrix, bloch_shift_vector):
    """Construct 4x4 differential generator L_obs on tetrahedral observation coordinates.

    For continuous Bloch flow dr/dt = M r + v, the tetrahedral probability vector
    satisfies dp/dt = L_obs @ p, where:
      (L_obs)_{ij} = (n_i . v + 3 n_i . (M @ n_j)) / 4.

    Guarantees column zero-sum: sum_i (L_obs)_{ij} = 0, preserving sum p_i = 1.
    """
    M = _real(bloch_drift_matrix, 'bloch_drift_matrix', (3, 3))
    v = _real(bloch_shift_vector, 'bloch_shift_vector', (3,))
    n = tetra_directions()
    L_obs = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            L_obs[i, j] = (np.dot(n[i], v) + 3.0 * np.dot(n[i], M @ n[j])) / 4.0

    col_sums = np.sum(L_obs, axis=0)
    if not np.allclose(col_sums, 0.0, atol=_TOL):
        raise ValueError('L_obs generator must have zero column sums to conserve probability')
    return L_obs


def lindblad_finite_time_transfer(bloch_drift_matrix, bloch_shift_vector, duration):
    """Compute finite-time transfer matrix exp(t * L_obs) for dissipative flow."""
    import scipy.linalg
    t = float(_real(duration, 'duration', ()))
    L_obs = lindblad_observation_generator(bloch_drift_matrix, bloch_shift_vector)
    return scipy.linalg.expm(t * L_obs)


# ---------------------------------------------------------------------------
# Physical Admissibility & Adversarial Complete Positivity Tests
# ---------------------------------------------------------------------------

def choi_matrix_from_affine(A, c):
    """Construct 4x4 Choi state C(E) = (E (x) I)(|Phi+><Phi+|) for affine channel r' = A r + c.

    The Bell state |Phi+> has local Bloch vectors r_A = r_B = 0 and correlation tensor
    T_Phi = diag(1, -1, 1). Under (E (x) I), the state parameters transform to:
      r_A' = c
      r_B' = 0
      T' = A @ T_Phi = A @ diag(1, -1, 1)

    The map E is completely positive if and only if C(E) >= 0.
    """
    A_mat = _real(A, 'A', (3, 3))
    c_vec = _real(c, 'c', (3,))
    T_phi = np.diag([1.0, -1.0, 1.0])
    T_prime = A_mat @ T_phi

    I, X, Y, Z = pauli_matrices_2x2()
    sigmas = [X, Y, Z]
    I4 = np.eye(4, dtype=complex)

    rho = I4.copy()
    for i in range(3):
        rho += c_vec[i] * np.kron(sigmas[i], I)
    for i in range(3):
        for j in range(3):
            rho += T_prime[i, j] * np.kron(sigmas[i], sigmas[j])
    return rho / 4.0


def partial_transpose_extension_eigenvalues(A, c):
    """Compute eigenvalues of the joint Choi matrix (E (x) I)(|Phi+><Phi+|)."""
    C = choi_matrix_from_affine(A, c)
    return np.linalg.eigvalsh(C)


def is_completely_positive_affine(A, c, tol=_TOL):
    """Determine whether single-qubit affine map r' = A r + c is completely positive (CPTP).

    Returns True iff all eigenvalues of the Choi matrix are >= -tol.
    """
    eigvals = partial_transpose_extension_eigenvalues(A, c)
    return bool(np.all(eigvals >= -tol))


def is_locally_positive_affine(A, c, tol=_TOL):
    """Determine whether affine map r' = A r + c preserves the local Bloch ball B_1.

    Tests whether max_{||r|| <= 1} ||A r + c|| <= 1 + tol.
    """
    A_mat = _real(A, 'A', (3, 3))
    c_vec = _real(c, 'c', (3,))
    op_norm = float(np.linalg.norm(A_mat, 2))
    shift_norm = float(np.linalg.norm(c_vec))
    if op_norm + shift_norm <= 1.0 + tol:
        return True

    # Check across singular vector axes and a sample of directions
    U, S, Vt = np.linalg.svd(A_mat)
    rng = np.random.default_rng(20261022)
    dirs = rng.normal(size=(500, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    test_points = np.vstack([dirs, Vt, -Vt])
    mapped = test_points @ A_mat.T + c_vec
    max_radius = float(np.max(np.linalg.norm(mapped, axis=1)))
    return bool(max_radius <= 1.0 + tol)


def qutrit_density_from_bloch(bloch_vec_8d):
    """Construct 3x3 complex density matrix from 8D generalized Bloch vector:

    rho = 1/3 I_3 + 1/2 sum_{a=1}^8 r_a lambda_a.
    """
    r = _real(bloch_vec_8d, 'bloch_vec_8d', (8,))
    gm = gell_mann_matrices()
    rho = np.eye(3, dtype=complex) / 3.0
    for a in range(8):
        rho += 0.5 * r[a] * gm[a]
    return rho


def qutrit_cubic_invariant(bloch_vec_8d):
    """Evaluate cubic determinant invariant det(rho(r)) for 8D qutrit Bloch vector."""
    rho = qutrit_density_from_bloch(bloch_vec_8d)
    return float(np.linalg.det(rho).real)


def qutrit_is_physical(bloch_vec_8d, tol=_TOL):
    """Rigorous physical admissibility check for 8D qutrit generalized Bloch vector.

    Checks:
      1. Quadratic Casimir / purity bound: ||r||^2 <= 4/3 + tol (Tr(rho^2) <= 1).
      2. Cubic determinant invariant: det(rho(r)) >= -tol.
      3. Complete positive semidefiniteness: min(eigvals(rho)) >= -tol.

    Distinguishes the necessary quadratic bound from the sufficient positivity condition!
    """
    r = _real(bloch_vec_8d, 'bloch_vec_8d', (8,))
    r_norm_sq = float(np.sum(r**2))
    quad_pass = bool(r_norm_sq <= (4.0 / 3.0) + tol)

    rho = qutrit_density_from_bloch(r)
    det_val = float(np.linalg.det(rho).real)
    cubic_pass = bool(det_val >= -tol)

    eigvals = np.linalg.eigvalsh(rho)
    min_eig = float(np.min(eigvals))
    pos_pass = bool(min_eig >= -tol)

    rejection_reason = None
    if not quad_pass:
        rejection_reason = f"Quadratic Casimir violation: ||r||^2 = {r_norm_sq:.5f} > 4/3"
    elif not cubic_pass:
        rejection_reason = f"Cubic determinant violation: det(rho) = {det_val:.5f} < 0"
    elif not pos_pass:
        rejection_reason = f"Negative eigenvalue violation: min(eig) = {min_eig:.5f} < 0"

    is_physical = quad_pass and cubic_pass and pos_pass
    return {
        'physical': is_physical,
        'quadratic_pass': quad_pass,
        'cubic_pass': cubic_pass,
        'positivity_pass': pos_pass,
        'norm_sq': r_norm_sq,
        'determinant': det_val,
        'min_eigenvalue': min_eig,
        'rejection_reason': rejection_reason,
    }


def peres_mermin_hypergraph_audit():
    """Formulate and audit the Peres-Mermin contextuality hypergraph.

    Nodes: 9 observables O_{ij} for i,j in {0,1,2}.
    Hyperedges (Contexts): 6 mutually commuting triples:
      Row 0, 1, 2 with target parity +1 (syndrome 0 in F_2).
      Col 0, 1 with target parity +1 (syndrome 0 in F_2).
      Col 2 with target parity -1 (syndrome 1 in F_2).

    Returns incidence matrix H in {0,1}^{6x9}, syndrome vector b in F_2^6,
    algebraic parity obstruction (sum H_{ek} = 2 = 0 mod 2 vs sum b_e = 1 mod 2),
    and classical valuation maximum satisfaction bound (5/6).
    """
    H = np.zeros((6, 9), dtype=int)
    H[0, [0, 1, 2]] = 1
    H[1, [3, 4, 5]] = 1
    H[2, [6, 7, 8]] = 1
    H[3, [0, 3, 6]] = 1
    H[4, [1, 4, 7]] = 1
    H[5, [2, 5, 8]] = 1

    syndrome = np.array([0, 0, 0, 0, 0, 1], dtype=int)

    node_degrees = np.sum(H, axis=0)
    f2_row_sum = np.sum(node_degrees) % 2
    f2_syndrome_sum = np.sum(syndrome) % 2

    algebraic_obstruction = (f2_row_sum != f2_syndrome_sum)

    import itertools
    max_sat = 0
    for v in itertools.product([-1, 1], repeat=9):
        prods = [
            v[0] * v[1] * v[2],
            v[3] * v[4] * v[5],
            v[6] * v[7] * v[8],
            v[0] * v[3] * v[6],
            v[1] * v[4] * v[7],
            v[2] * v[5] * v[8],
        ]
        sat = sum(1 for e in range(5) if prods[e] == 1) + (1 if prods[5] == -1 else 0)
        if sat > max_sat:
            max_sat = sat

    return {
        'incidence_matrix': H,
        'syndrome_f2': syndrome,
        'node_degrees': node_degrees,
        'f2_incidence_sum': int(f2_row_sum),
        'f2_syndrome_sum': int(f2_syndrome_sum),
        'algebraic_obstruction': algebraic_obstruction,
        'max_satisfied_contexts': max_sat,
        'total_contexts': 6,
    }


def classify_lindblad_generator(bloch_drift_matrix, bloch_shift_vector, test_times=(1e-4, 0.01, 0.1, 0.5, 1.0), tol=_TOL):
    """Classify a continuous differential generator dr/dt = M r + v into the 3-tier hierarchy:

    1. 'VALID_LINDBLAD':
       - Trace-preserving: sum_i (L_obs)_{ij} = 0.
       - Locally positive: ||r(t)|| <= 1 for all t >= 0 and initial ||r(0)|| <= 1.
       - Completely positive: Choi matrix C(e^{t M}, c(t)) >= 0 for all t >= 0.

    2. 'LOCAL_POSITIVITY_VIOLATION':
       - Trace-preserving: sum_i (L_obs)_{ij} = 0.
       - But expands the state ball: ||r(t)|| > 1 for some t > 0.

    3. 'COMPLETE_POSITIVITY_VIOLATION':
       - Trace-preserving: sum_i (L_obs)_{ij} = 0.
       - Locally positive: ||r(t)|| <= 1 for all t >= 0.
       - But violates complete positivity (negative Choi eigenvalue).
    """
    import scipy.linalg
    M = _real(bloch_drift_matrix, 'bloch_drift_matrix', (3, 3))
    v = _real(bloch_shift_vector, 'bloch_shift_vector', (3,))

    L_obs = lindblad_observation_generator(M, v)
    trace_preserving = bool(np.allclose(np.sum(L_obs, axis=0), 0.0, atol=tol))

    local_pos = True
    comp_pos = True
    min_choi_eig = 1.0

    for t in test_times:
        A_t = scipy.linalg.expm(t * M)
        try:
            c_t = np.linalg.solve(M, (A_t - np.eye(3)) @ v)
        except np.linalg.LinAlgError:
            c_t = np.zeros(3)

        if not is_locally_positive_affine(A_t, c_t, tol=tol):
            local_pos = False

        eigvals = partial_transpose_extension_eigenvalues(A_t, c_t)
        m_eig = float(np.min(eigvals))
        if m_eig < min_choi_eig:
            min_choi_eig = m_eig
        if m_eig < -tol:
            comp_pos = False

    if not trace_preserving:
        classification = 'TRACE_VIOLATION'
    elif not local_pos:
        classification = 'LOCAL_POSITIVITY_VIOLATION'
    elif not comp_pos:
        classification = 'COMPLETE_POSITIVITY_VIOLATION'
    else:
        classification = 'VALID_LINDBLAD'

    return {
        'classification': classification,
        'trace_preserving': trace_preserving,
        'local_positivity': local_pos,
        'complete_positivity': comp_pos,
        'min_choi_eigenvalue': min_choi_eig,
    }


# ---------------------------------------------------------------------------
# Measurement Frames Beyond SIC: Projective, Trine, Octahedral, Redundant
# ---------------------------------------------------------------------------

def pauli_projective_frame():
    """Return 6-outcome Pauli projective measurement frame: +/- X, +/- Y, +/- Z.

    Directions: n_k in {+/- e_x, +/- e_y, +/- e_z}.
    Effects: E_k = 1/6 (I + n_k . sigma). Sum E_k = I.
    """
    dirs = np.array([
        [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0], [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0], [0.0, 0.0, -1.0],
    ])
    weights = np.full(6, 1.0 / 3.0)
    return dirs, weights


def trine_povm_frame():
    """Return 3-outcome Trine POVM in the xy-plane (angles 0, 2pi/3, 4pi/3).

    Directions: n_k = (cos(2pi k/3), sin(2pi k/3), 0).
    Effects: E_k = 1/3 (I + n_k . sigma). Sum E_k = I.
    Rank = 2. Kernel = span(e_z). Discards all z-polarization!
    """
    angles = [0.0, 2.0 * np.pi / 3.0, 4.0 * np.pi / 3.0]
    dirs = np.array([[np.cos(th), np.sin(th), 0.0] for th in angles])
    weights = np.full(3, 2.0 / 3.0)
    return dirs, weights


def octahedral_povm_frame():
    """Return 6-outcome regular octahedral POVM frame."""
    return pauli_projective_frame()


def cubic_povm_frame():
    """Return 8-outcome cubic POVM frame (vertices of the unit cube)."""
    dirs = []
    for sx in [1.0, -1.0]:
        for sy in [1.0, -1.0]:
            for sz in [1.0, -1.0]:
                dirs.append([sx, sy, sz])
    dirs = np.array(dirs) / np.sqrt(3.0)
    weights = np.full(8, 1.0 / 4.0)
    return dirs, weights


def analyze_measurement_frame(directions, weights=None, tol=_TOL):
    """Analyze the MAPEOGEO information structure of a measurement frame.

    p_k = w_k (1 + n_k . r) / 2.
    Observation matrix O has rows w_k n_k / 2.

    Returns:
      - rank: dimension of observable subspace
      - null_space: basis for unobservable kernel
      - informationally_complete: bool (rank == 3)
      - frame_operator: sum w_k n_k n_k^T
      - reconstruction_matrix: pseudoinverse for state recovery
      - centroid_zero_sum: bool (sum w_k n_k == 0)
    """
    dirs = np.asarray(directions, dtype=float)
    if dirs.ndim != 2 or dirs.shape[1] != 3:
        raise ValueError('directions must have shape (K, 3)')
    K = dirs.shape[0]
    if weights is None:
        w = np.full(K, 2.0 / K)
    else:
        w = _real(weights, 'weights', (K,))

    O_mat = 0.5 * (dirs * w[:, np.newaxis])
    U, S, Vt = np.linalg.svd(O_mat)
    rank = int(np.sum(S > tol))
    info_complete = bool(rank == 3)

    frame_op = np.zeros((3, 3))
    for k in range(K):
        frame_op += w[k] * np.outer(dirs[k], dirs[k])

    null_basis = Vt[rank:]
    recon_mat = np.linalg.pinv(O_mat)
    centroid = np.sum(dirs * w[:, np.newaxis], axis=0)
    zero_sum = bool(np.allclose(centroid, 0.0, atol=tol))

    return {
        'rank': rank,
        'null_space': null_basis,
        'informationally_complete': info_complete,
        'frame_operator': frame_op,
        'reconstruction_matrix': recon_mat,
        'centroid_zero_sum': zero_sum,
        'num_outcomes': K,
    }


# ---------------------------------------------------------------------------
# Composite-System Channels & Entanglement Breaking
# ---------------------------------------------------------------------------

def bipartite_channel_transfer(rA, rB, T, local_channel_A, local_channel_B):
    """Apply local channels E_A = (A1, c1) and E_B = (A2, c2) to 2-qubit state (rA, rB, T).

    Evolution laws:
      rA' = A1 rA + c1
      rB' = A2 rB + c2
      T'  = A1 T A2^T + c1 (rB')^T + (A1 rA) c2^T
    """
    A1, c1 = local_channel_A
    A2, c2 = local_channel_B
    rA_vec = _real(rA, 'rA', (3,))
    rB_vec = _real(rB, 'rB', (3,))
    T_mat = _real(T, 'T', (3, 3))

    rA_prime = A1 @ rA_vec + c1
    rB_prime = A2 @ rB_vec + c2
    T_prime = A1 @ T_mat @ A2.T + np.outer(c1, rB_prime) + np.outer(A1 @ rA_vec, c2)

    return rA_prime, rB_prime, T_prime


def partial_trace_A(rA, rB, T):
    """Partial trace over qubit A: Tr_A(rho) = 1/2 (I + rB . sigma). Discards (rA, T)."""
    return _real(rB, 'rB', (3,))


def partial_trace_B(rA, rB, T):
    """Partial trace over qubit B: Tr_B(rho) = 1/2 (I + rA . sigma). Discards (rB, T)."""
    return _real(rA, 'rA', (3,))


def bipartite_state_positivity(rA, rB, T, tol=_TOL):
    """Determine whether 15-parameter 2-qubit state (rA, rB, T) is a positive semidefinite state."""
    rA_vec = _real(rA, 'rA', (3,))
    rB_vec = _real(rB, 'rB', (3,))
    T_mat = _real(T, 'T', (3, 3))

    I, X, Y, Z = pauli_matrices_2x2()
    sigmas = [X, Y, Z]
    I4 = np.eye(4, dtype=complex)

    rho = I4.copy()
    for i in range(3):
        rho += rA_vec[i] * np.kron(sigmas[i], I)
        rho += rB_vec[i] * np.kron(I, sigmas[i])
    for i in range(3):
        for j in range(3):
            rho += T_mat[i, j] * np.kron(sigmas[i], sigmas[j])
    rho /= 4.0

    eigvals = np.linalg.eigvalsh(rho)
    min_eig = float(np.min(eigvals))
    return {
        'positive': bool(min_eig >= -tol),
        'min_eigenvalue': min_eig,
        'eigenvalues': eigvals,
    }


def is_entanglement_breaking(A, c, tol=_TOL):
    """Determine whether single-qubit channel (A, c) is entanglement breaking.

    By Horodecki theorem, a channel is entanglement breaking iff its Choi state
    C(E) is separable (PPT).
    """
    C = choi_matrix_from_affine(A, c)
    C_pt = np.zeros((4, 4), dtype=complex)
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    idx_in = (2 * i + j, 2 * k + l)
                    idx_out = (2 * i + l, 2 * k + j)
                    C_pt[idx_out] = C[idx_in]

    pt_eigvals = np.linalg.eigvalsh(C_pt)
    min_pt_eig = float(np.min(pt_eigvals))
    return bool(min_pt_eig >= -tol)


# ---------------------------------------------------------------------------
# General Hamiltonian Flows from Generators
# ---------------------------------------------------------------------------

def qubit_hamiltonian_generator(h_vec):
    """Construct real skew-symmetric generator Omega in so(3) for H = 1/2 h . sigma:

    dr/dt = 2 (h x r) = Omega @ r.
    """
    h = _real(h_vec, 'h_vec', (3,))
    hx, hy, hz = h[0], h[1], h[2]
    return np.array([
        [0.0, -2.0 * hz, 2.0 * hy],
        [2.0 * hz, 0.0, -2.0 * hx],
        [-2.0 * hy, 2.0 * hx, 0.0],
    ])


def su3_structure_constants():
    """Compute the 8x8x8 completely anti-symmetric SU(3) structure constants f_{abc}:

    [lambda_a, lambda_b] = 2i sum_c f_{abc} lambda_c.
    """
    gm = gell_mann_matrices()
    f = np.zeros((8, 8, 8))
    for a in range(8):
        for b in range(8):
            comm = gm[a] @ gm[b] - gm[b] @ gm[a]
            for c in range(8):
                f[a, b, c] = float((np.trace(comm @ gm[c]) / (4.0j)).real)
    return f


def qutrit_hamiltonian_generator(h_8d):
    """Construct real skew-symmetric generator Omega in so(8) for H = 1/2 sum h_b lambda_b:

    dr_a/dt = sum_{b,c} f_{abc} h_b r_c = sum_c Omega_{ac} r_c.
    """
    h = _real(h_8d, 'h_8d', (8,))
    f = su3_structure_constants()
    Omega = np.zeros((8, 8))
    for a in range(8):
        for c in range(8):
            Omega[a, c] = float(np.sum(f[a, :, c] * h))
    return Omega


# ---------------------------------------------------------------------------
# General Relational Context Hypergraph
# ---------------------------------------------------------------------------

class ContextGraph:
    """Formal MAPEOGEO Context Graph: (V, C, sigma).

    V: set of observable indices {0, ..., N-1}
    C: list of compatible-context hyperedges (tuples of vertex indices)
    sigma: required parity products in {+1, -1} for each context
    """

    def __init__(self, num_nodes: int, contexts: list, parities: list):
        self.num_nodes = int(num_nodes)
        self.contexts = [tuple(c) for c in contexts]
        self.parities = [int(p) for p in parities]
        if len(self.contexts) != len(self.parities):
            raise ValueError('contexts and parities must have matching length')

        self.H = np.zeros((len(self.contexts), self.num_nodes), dtype=int)
        for e, c in enumerate(self.contexts):
            for v in c:
                self.H[e, v] = 1

    def audit_valuation(self) -> dict:
        """Audit whether any classical valuation v: V -> {+1, -1} satisfies all contexts."""
        num_contexts = len(self.contexts)
        syndrome_f2 = np.array([0 if p == 1 else 1 for p in self.parities], dtype=int)

        node_degrees = np.sum(self.H, axis=0)
        f2_inc_sum = int(np.sum(node_degrees) % 2)
        f2_syn_sum = int(np.sum(syndrome_f2) % 2)

        has_f2_obstruction = bool(f2_inc_sum != f2_syn_sum)

        max_sat = 0
        is_contextual = True
        if self.num_nodes <= 12:
            import itertools
            for v in itertools.product([-1, 1], repeat=self.num_nodes):
                sat = 0
                for e, c in enumerate(self.contexts):
                    prod = 1
                    for node in c:
                        prod *= v[node]
                    if prod == self.parities[e]:
                        sat += 1
                if sat > max_sat:
                    max_sat = sat
            is_contextual = bool(max_sat < num_contexts)
        else:
            is_contextual = has_f2_obstruction
            max_sat = None

        return {
            'is_contextual': is_contextual,
            'has_f2_obstruction': has_f2_obstruction,
            'max_satisfied_contexts': max_sat,
            'total_contexts': num_contexts,
            'incidence_matrix': self.H,
            'syndrome_f2': syndrome_f2,
        }




