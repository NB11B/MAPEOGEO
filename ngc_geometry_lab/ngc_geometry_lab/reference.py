"""Independent complex Hilbert-space reference calculations.

This module depends only on NumPy and the standard library. Qubit zero is
the first (most significant) tensor factor. In ``local_gate``, the order
of ``targets`` specifies the gate's local tensor-factor order.

Numerical acceptance uses absolute tolerances only. No invalid matrix is
projected, clipped, or renormalized by the validators.
"""
from numbers import Integral

import numpy as np


_ATOL = 1e-10


def _complex_array(value, name):
    try:
        result = np.array(value, dtype=complex, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a numeric array") from exc
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite values")
    return result


def _real_array(value, shape, name):
    try:
        raw = np.asarray(value)
        if np.iscomplexobj(raw):
            raise ValueError(f"{name} must be real")
        result = np.array(value, dtype=float, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a real array of shape {shape}") from exc
    if result.shape != shape or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be finite with shape {shape}")
    return result


def _positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _unitary(value, dimension):
    result = _complex_array(value, "unitary")
    if result.shape != (dimension, dimension):
        raise ValueError(f"unitary must have shape {(dimension, dimension)}")
    if not np.allclose(result.conj().T @ result, np.eye(dimension), rtol=0, atol=_ATOL):
        raise ValueError("matrix must be unitary")
    return result


def paulis():
    """Return complex Pauli matrices in I, X, Y, Z order."""
    return np.array([[[1, 0], [0, 1]], [[0, 1], [1, 0]],
                     [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], dtype=complex)


def validate_density(rho, *, atol=_ATOL):
    """Return a copied density matrix after absolute-tolerance validation.

    General finite-dimensional square matrices are supported, including
    dimensions that are not powers of two. Eigenvalues may be no smaller
    than ``-atol``; Hermiticity and unit trace use the same absolute bound.
    """
    tolerance = _real_array(atol, (), "atol").item()
    if tolerance < 0:
        raise ValueError("atol must be nonnegative")
    result = _complex_array(rho, "density matrix")
    if result.ndim != 2 or result.shape[0] == 0 or result.shape[0] != result.shape[1]:
        raise ValueError("density matrix must be a nonempty square matrix")
    if not np.allclose(result, result.conj().T, rtol=0, atol=tolerance):
        raise ValueError("density matrix must be Hermitian")
    if not np.isclose(np.trace(result), 1, rtol=0, atol=tolerance):
        raise ValueError("density matrix must have unit trace")
    # Use the Hermitian part to avoid privileging either triangle when an
    # otherwise valid input has an accepted, tiny Hermiticity residual.
    hermitian = result / 2 + result.conj().T / 2
    if np.linalg.eigvalsh(hermitian).min() < -tolerance:
        raise ValueError("density matrix must be positive semidefinite")
    return result


def _qubit_density(rho):
    result = validate_density(rho)
    if result.shape != (2, 2):
        raise ValueError("a single-qubit density matrix must have shape (2, 2)")
    return result


def _joint_density(rho):
    result = validate_density(rho)
    if result.shape != (4, 4):
        raise ValueError("a two-qubit density matrix must have shape (4, 4)")
    return result


def density_from_bloch(state):
    """Construct (I + r.sigma)/2 for a finite real Bloch vector."""
    vector = _real_array(state, (3,), "Bloch vector")
    if np.linalg.norm(vector) > 1 + _ATOL:
        raise ValueError("Bloch vector norm must not exceed one")
    matrices = paulis()
    return validate_density((matrices[0] + np.tensordot(vector, matrices[1:], axes=1))/2)


def bloch_from_density(rho):
    """Extract x, y, z via tr(rho sigma_j)."""
    matrix = _qubit_density(rho)
    return np.array([np.trace(matrix @ sigma).real for sigma in paulis()[1:]])


def tetra_effects():
    """Return tetrahedral effects ordered (+++), (+--), (-+-), (--+)."""
    directions = np.array([[1, 1, 1], [1, -1, -1],
                           [-1, 1, -1], [-1, -1, 1]])/np.sqrt(3)
    matrices = paulis()
    return (matrices[0][None, :, :] + np.einsum("ki,ijl->kjl", directions, matrices[1:]))/4


def tetra_probabilities(rho):
    """Evaluate the four Born traces directly, without geometric shortcuts."""
    matrix = _qubit_density(rho)
    return np.array([np.trace(matrix @ effect).real for effect in tetra_effects()])


def rotation_unitary(axis, angle):
    """Construct exp(-i angle axis.sigma/2), normalizing a nonzero axis."""
    vector = _real_array(axis, (3,), "axis")
    theta = _real_array(angle, (), "angle").item()
    scale = np.max(np.abs(vector))
    if scale == 0:
        raise ValueError("axis must be nonzero")
    vector = vector/scale
    vector = vector/np.linalg.norm(vector)
    matrices = paulis()
    return (np.cos(theta/2)*matrices[0]
            - 1j*np.sin(theta/2)*np.tensordot(vector, matrices[1:], axes=1))


def evolve_density(rho, unitary):
    """Apply U rho U-dagger with density and unitary validation."""
    matrix = validate_density(rho)
    operator = _unitary(unitary, matrix.shape[0])
    return validate_density(operator @ matrix @ operator.conj().T)


def random_density(dimension, rng, *, pure=False):
    """Sample a normalized complex Gaussian Wishart density matrix.

    A single Gaussian column gives a rank-one pure state; a square Gaussian
    matrix gives full rank with probability one. ``rng`` must be an explicit
    NumPy Generator or RandomState so sampling is reproducible by the caller.
    """
    size = _positive_integer(dimension, "dimension")
    if not isinstance(rng, (np.random.Generator, np.random.RandomState)):
        raise ValueError("rng must be a NumPy Generator or RandomState")
    if not isinstance(pure, (bool, np.bool_)):
        raise ValueError("pure must be boolean")
    shape = (size, 1 if pure else size)
    gaussian = rng.normal(size=shape) + 1j*rng.normal(size=shape)
    wishart = gaussian @ gaussian.conj().T
    return validate_density(wishart / np.trace(wishart).real)


def local_gate(state, gate, targets, num_qubits):
    """Apply a local unitary using tensor-axis permutation and multiplication.

    Target axes are moved to the front in exactly the supplied order. The
    gate multiplies those axes as a matrix; the inverse permutation restores
    the original big-endian tensor-factor order.
    """
    count = _positive_integer(num_qubits, "num_qubits")
    ket = _complex_array(state, "state")
    if ket.shape != (2**count,):
        raise ValueError("state dimension must equal 2**num_qubits")
    if not np.isclose(np.vdot(ket, ket), 1, rtol=0, atol=_ATOL):
        raise ValueError("state must be normalized")
    try:
        selected = list(targets)
    except TypeError as exc:
        raise ValueError("targets must be an iterable of qubit indices") from exc
    if not selected:
        raise ValueError("targets must contain at least one qubit")
    if any(isinstance(index, (bool, np.bool_)) or not isinstance(index, Integral)
           or index < 0 or index >= count for index in selected):
        raise ValueError("targets must be integer indices in range")
    selected = [int(index) for index in selected]
    if len(set(selected)) != len(selected):
        raise ValueError("targets must be unique")
    operator = _unitary(gate, 2**len(selected))
    axes = selected + [index for index in range(count) if index not in selected]
    tensor = ket.reshape((2,)*count).transpose(axes)
    evolved = operator @ tensor.reshape(2**len(selected), -1)
    return evolved.reshape((2,)*count).transpose(np.argsort(axes)).reshape(-1)


def joint_tetra_probabilities(rho):
    """Evaluate all sixteen traces tr(rho (E_i tensor E_j))."""
    matrix = _joint_density(rho)
    effects = tetra_effects()
    return np.array([[np.trace(matrix @ np.kron(left, right)).real
                      for right in effects] for left in effects])


def joint_parameters(rho):
    """Return local Bloch vectors a,b and Pauli correlations C."""
    matrix = _joint_density(rho)
    matrices = paulis()
    identity, components = matrices[0], matrices[1:]
    a = np.array([np.trace(matrix @ np.kron(sigma, identity)).real for sigma in components])
    b = np.array([np.trace(matrix @ np.kron(identity, sigma)).real for sigma in components])
    correlations = np.array([[np.trace(matrix @ np.kron(left, right)).real
                              for right in components] for left in components])
    return a, b, correlations


def density_from_joint(a, b, correlations):
    """Reconstruct a two-qubit matrix by Pauli expansion and require PSD."""
    left = _real_array(a, (3,), "a")
    right = _real_array(b, (3,), "b")
    corr = _real_array(correlations, (3, 3), "correlations")
    matrices = paulis()
    identity, components = matrices[0], matrices[1:]
    result = np.kron(identity, identity)
    for i in range(3):
        result += left[i]*np.kron(components[i], identity)
        result += right[i]*np.kron(identity, components[i])
        for j in range(3):
            result += corr[i, j]*np.kron(components[i], components[j])
    return validate_density(result/4)
