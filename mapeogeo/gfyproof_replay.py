"""Independent, bounded replay of public GFYProof finite payloads.

This is executable evidence, not a universal theorem or a proof-kernel check.
Exact families accept integers and rational strings (no float conversion).
Approximate families use finite real numbers with absolute tolerance at most
1e-6 (default 1e-6), and Gaussian PSD tolerance at most 1e-12 (default 1e-12).
Limits: 10 Boolean variables, depth 32, 256 nodes; matrices at most 32x32;
128-character/512-bit rationals; 10,000 LP grid cases; cyclic order <=10,000.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product
import math
import re

import numpy as np


MAX_DIM = 32


def _require(condition):
    if not condition:
        raise ValueError('unsupported or malformed finite payload')


def _seq(value, limit=MAX_DIM):
    _require(isinstance(value, list) and 0 < len(value) <= limit)
    return value


def _integer(value, limit=10**9):
    _require(type(value) is int and abs(value) <= limit)
    return value


def _rational(value):
    if type(value) is int:
        _require(value.bit_length() <= 512)
    else:
        _require(isinstance(value, str) and len(value) <= 128)
        _require(re.fullmatch(r'[+-]?\d+(?:/[+-]?\d+)?', value) is not None)
    result = Fraction(value)
    _require(max(result.numerator.bit_length(), result.denominator.bit_length()) <= 512)
    return result


def _real(value):
    _require(type(value) in (int, float))
    _require(math.isfinite(value) and abs(value) <= 1e6)
    return float(value)


def _vector(value, scalar):
    return [scalar(x) for x in _seq(value)]


def _matrix(value, scalar):
    rows = [_vector(row, scalar) for row in _seq(value)]
    _require(all(len(row) == len(rows[0]) for row in rows))
    return rows


def _array(value):
    return np.asarray(_matrix(value, _real), dtype=float)


def _square(a):
    _require(len(a) == len(a[0]))


def _tolerance(p, key='tolerance', maximum=1e-6):
    result = _real(p.get(key, maximum))
    _require(0 <= result <= maximum)
    return result


def _boolean(p):
    names = _seq(p['variable_order'], 10)
    _require(all(isinstance(x, str) and 0 < len(x) <= 128 for x in names))
    _require(len(set(names)) == len(names))
    # Bit i denotes assignment i: exhaustive semantics, independent of ROBDDs.
    mask = (1 << (1 << len(names))) - 1
    variables = {name: sum(1 << i for i in range(1 << len(names)) if i & (1 << j))
                 for j, name in enumerate(names)}
    budget = [256]

    def evaluate(expr, depth=0):
        budget[0] -= 1
        _require(depth <= 32 and budget[0] >= 0)
        _require(isinstance(expr, list) and 2 <= len(expr) <= 33)
        op = expr[0]
        _require(isinstance(op, str))
        if op == 'var':
            _require(len(expr) == 2 and isinstance(expr[1], str) and expr[1] in variables)
            return variables[expr[1]]
        if op == 'not':
            _require(len(expr) == 2)
            return mask ^ evaluate(expr[1], depth + 1)
        _require(op in ('and', 'or') and len(expr) >= 3)
        values = [evaluate(x, depth + 1) for x in expr[1:]]
        result = values[0]
        for value in values[1:]:
            result = result & value if op == 'and' else result | value
        return result

    return evaluate(p['left']) == evaluate(p['right'])


def _farkas(p):
    _require(p['certificate_type'] == 'implication')
    a = _matrix(p['matrix'], _rational)
    b = _vector(p['bounds'], _rational)
    c = _vector(p['target_coefficients'], _rational)
    lam = _vector(p['multipliers'], _rational)
    d = _rational(p['target_bound'])
    _require(len(a) == len(b) == len(lam) and len(a[0]) == len(c))
    return (all(x >= 0 for x in lam)
            and all(sum(lam[i] * a[i][j] for i in range(len(a))) == c[j] for j in range(len(c)))
            and sum(x*y for x, y in zip(lam, b)) <= d)


def _cyclic(p):
    m, n, g = (_integer(p[k]) for k in ('modulus', 'order', 'generator'))
    _require(2 <= m and 1 <= n <= 10000 and 0 < g < m)
    _require(math.gcd(g, m) == 1)
    # Establish the stated order, not merely that g**n = 1.
    value = 1
    for k in range(1, n + 1):
        value = value * g % m
        if value == 1:
            _require(k == n)
    _require(value == 1)
    a, b, s = (_integer(p[k]) for k in ('exp_a', 'exp_b', 'exp_sum'))
    va, vb, vp = (_integer(p[k]) for k in ('val_a', 'val_b', 'val_product'))
    _require(all(0 <= x < m for x in (va, vb, vp)))
    return (s == (a+b) % n and va == pow(g, a % n, m)
            and vb == pow(g, b % n, m) and vp == va*vb % m == pow(g, s, m))


def _rotation(p):
    a = _array(p['matrix'])
    _require(a.shape == (3, 3))
    t = _tolerance(p)
    return bool(np.max(np.abs(a.T @ a - np.eye(3))) <= t and abs(np.linalg.det(a)-1) <= t)


def _eigenpairs(p):
    a = _array(p['matrix'])
    _square(a)
    t = _tolerance(p)
    for pair in _seq(p['eigenpairs']):
        _require(isinstance(pair, dict))
        value = _real(pair['value'])
        v = np.asarray(_vector(pair['vector'], _real))
        _require(len(v) == len(a))
        scale = np.max(np.abs(v))
        _require(scale > 0)
        v = v / scale  # Tiny nonzero vectors cannot make a false residual pass.
        if np.max(np.abs(a @ v - value*v)) > t:
            return False
    return True


def _laplacian(p):
    a = _matrix(p['adjacency'], _integer)
    b = _matrix(p['incidence'], _integer)
    _square(a)
    n = len(a)
    _require(len(b) == n)
    _require(all(a[i][i] == 0 for i in range(n)))
    _require(all(a[i][j] in (0, 1) and a[i][j] == a[j][i] for i in range(n) for j in range(n)))
    for column in zip(*b):
        _require(column.count(-1) == column.count(1) == 1 and all(x in (-1, 0, 1) for x in column))
    return all(sum(b[i][k]*b[j][k] for k in range(len(b[0]))) ==
               (sum(a[i]) if i == j else -a[i][j]) for i in range(n) for j in range(n))


def _projective(p):
    a = _matrix(p['matrix'], _rational)
    _square(a)
    x = _vector(p['point'], _rational)
    scale = _rational(p['scale'])
    _require(len(x) == len(a) and any(x) and scale != 0)
    # Require a projective transformation (invertible homogeneous matrix).
    reduced = [row[:] for row in a]
    for j in range(len(a)):
        pivot = next((i for i in range(j, len(a)) if reduced[i][j]), None)
        _require(pivot is not None)
        reduced[j], reduced[pivot] = reduced[pivot], reduced[j]
        for i in range(j+1, len(a)):
            ratio = reduced[i][j] / reduced[j][j]
            reduced[i] = [v-ratio*w for v, w in zip(reduced[i], reduced[j])]
    y = [sum(v*w for v, w in zip(row, x)) for row in a]
    z = [sum(v*(scale*w) for v, w in zip(row, x)) for row in a]
    _require(any(y) and any(z))
    return all(z[i]*y[j] == y[i]*z[j] for i in range(len(y)) for j in range(len(y)))


def _lp(p):
    """Grid of max c*x, a_i*x<=b_i, x>=0; min b*y, a*y>=c, y>=0."""
    values = _vector(p['coefficient_values'], _rational)
    counts = _vector(p['constraint_counts'], lambda x: _integer(x, 8))
    _require(all(x > 0 for x in values) and all(x > 0 for x in counts))
    _require(sum(len(values)**(2*n+1) for n in counts) <= 10000)
    for n in counts:
        for coefficients in product(values, repeat=2*n+1):
            a, b, c = coefficients[:n], coefficients[n:2*n], coefficients[-1]
            x = min(bi/ai for ai, bi in zip(a, b))
            # Extreme dual witnesses each put all weight on one constraint.
            dual = min(bi*c/ai for ai, bi in zip(a, b))
            if c*x != dual:
                return False
    return True


def _projection(p):
    a = _array(p['matrix'])
    _square(a)
    v = np.asarray(_vector(p['test_vector'], _real))
    _require(len(v) == len(a))
    t = _tolerance(p)
    projected = a @ v
    return bool(max(np.max(np.abs(a-a.T)), np.max(np.abs(a@a-a)),
                    np.max(np.abs(a@(v-projected)))) <= t)


def _gaussian(p):
    x = _array(p['points'])
    sigma = _real(p['sigma_sq'])
    _require(sigma >= 1e-6)
    t = _tolerance(p, 'psd_tolerance', 1e-12)
    distances = np.sum((x[:, None, :] - x[None, :, :])**2, axis=2)
    gram = x @ x.T
    squared = np.sum(x*x, axis=1)
    inner_distances = squared[:, None] + squared[None, :] - 2*gram
    # Underflow of a nonpositive exponential safely rounds a negligible kernel
    # entry to zero; invalid/overflow errors still fail closed.
    with np.errstate(under='ignore'):
        k = np.exp(-distances/(2*sigma))
        # Combine logarithms before exponentiation to avoid inf*0 intermediates.
        other = np.exp(-inner_distances/(2*sigma))
    return bool(np.all(np.isfinite(other)) and np.max(np.abs(k-other)) <= 1e-12
                and np.min(np.linalg.eigvalsh(k)) >= -t)


_VERIFIERS = {
    'ROBDD_EQUIVALENCE': _boolean, 'FARKAS_IMPLICATION': _farkas,
    'CYCLIC_GROUP_COMPOSITION': _cyclic,
    'SO3_ROTATION': _rotation, 'EIGENPAIR_RESIDUAL': _eigenpairs,
    'GRAPH_LAPLACIAN_EQUIVALENCE': _laplacian,
    'PROJECTIVE_HOMOGENEOUS_EQUIVALENCE': _projective,
    'LP_STRONG_DUALITY_1D': _lp, 'ORTHOGONAL_PROJECTION': _projection,
    'GAUSSIAN_KERNEL_EQUIVALENCE_PSD': _gaussian,
}
_VERIFIERS = {'GFY.' + key + '.v1': value for key, value in _VERIFIERS.items()}
LOCAL_SEMANTIC_IDS = frozenset(_VERIFIERS)


def verify_proof_payload(semantic_id, payload) -> bool:
    """Replay a supported finite witness; malformed/unknown input fails closed."""
    if not isinstance(semantic_id, str) or not isinstance(payload, dict):
        return False
    verifier = _VERIFIERS.get(semantic_id)
    if verifier is None:
        return False
    try:
        with np.errstate(all='raise'):
            return bool(verifier(payload))
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, np.linalg.LinAlgError):
        return False
