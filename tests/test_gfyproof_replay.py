"""Independent local replay: literal witnesses and fail-closed regressions."""
import copy
import importlib
import importlib.util

import pytest


def replay(name, payload):
    # A missing implementation fails an assertion during the initial red run.
    assert importlib.util.find_spec('mapeogeo.gfyproof_replay') is not None
    return importlib.import_module('mapeogeo.gfyproof_replay').verify_proof_payload('GFY.' + name + '.v1', payload)


CASES = [
    ('ROBDD_EQUIVALENCE', {'left': ['not', ['and', ['var', 'p'], ['var', 'q']]], 'right': ['or', ['not', ['var', 'p']], ['not', ['var', 'q']]], 'variable_order': ['p', 'q']}),
    ('FARKAS_IMPLICATION', {'certificate_type': 'implication', 'matrix': [[1, 0], [0, 1]], 'bounds': [1, 2], 'target_coefficients': [1, 2], 'target_bound': 5, 'multipliers': [1, 2]}),
    ('CYCLIC_GROUP_COMPOSITION', {'modulus': 17, 'order': 16, 'generator': 3, 'exp_a': 5, 'val_a': 5, 'exp_b': 7, 'val_b': 11, 'exp_sum': 12, 'val_product': 4}),
    ('SO3_ROTATION', {'matrix': [[0, -1, 0], [1, 0, 0], [0, 0, 1]], 'tolerance': 1e-6}),
    ('EIGENPAIR_RESIDUAL', {'matrix': [[2, 1], [1, 2]], 'eigenpairs': [{'value': 3, 'vector': [1, 1]}, {'value': 1, 'vector': [1, -1]}]}),
    ('GRAPH_LAPLACIAN_EQUIVALENCE', {'adjacency': [[0, 1], [1, 0]], 'incidence': [[-1], [1]]}),
    ('PROJECTIVE_HOMOGENEOUS_EQUIVALENCE', {'matrix': [[1, 2, 0], [0, 1, 1], [1, 0, 1]], 'point': [1, 2, 3], 'scale': 5}),
    ('LP_STRONG_DUALITY_1D', {'coefficient_values': [1, 2, 3], 'constraint_counts': [1, 2, 3]}),
    ('ORTHOGONAL_PROJECTION', {'matrix': [[0.5, 0.5], [0.5, 0.5]], 'test_vector': [3, 1]}),
    ('GAUSSIAN_KERNEL_EQUIVALENCE_PSD', {'points': [[0, 0], [1, 0], [0, 1]], 'sigma_sq': 1, 'psd_tolerance': 1e-12}),
]


@pytest.mark.parametrize('name,payload', CASES)
def test_literal_valid_witness(name, payload):
    assert replay(name, payload) is True


@pytest.mark.parametrize('name,payload', CASES)
def test_missing_fields_fail_closed(name, payload):
    assert replay(name, {}) is False


BAD = [
    (0, 'right', ['var', 'p']), (0, 'variable_order', ['p', 'p']),
    (0, 'left', ['not', ['var', 'p'], ['var', 'q']]),
    (0, 'left', ['execute', 'code']), (0, 'variable_order', list(map(str, range(30)))),
    (1, 'target_bound', '499999999999999999/100000000000000000'),
    (1, 'multipliers', [-1, 2]), (1, 'matrix', [[1], [1]]),
    (1, 'multipliers', [1.9, 2]), (1, 'certificate_type', 'infeasibility'),
    (2, 'val_product', 5), (2, 'order', 16.9), (2, 'order', 32), (2, 'generator', 1),
    (3, 'matrix', [[1, 0, 0], [0, 1, 0], [0, 0, -1]]), (3, 'tolerance', 1),
    (4, 'eigenpairs', []), (4, 'eigenpairs', [{'value': 3, 'vector': [0, 0]}]),
    (4, 'eigenpairs', [{'value': 2, 'vector': [1e-100, 1e-100]}]),
    (4, 'eigenpairs', [{'value': 3, 'vector': [1]}]),
    (5, 'incidence', [[0], [0]]), (5, 'adjacency', [[0, 1.1], [1.1, 0]]),
    (6, 'scale', 0), (6, 'point', [0, 0, 0]), (6, 'matrix', [[0]*3]*3),
    (7, 'coefficient_values', [0, 1]), (7, 'constraint_counts', [1.2]),
    (7, 'constraint_counts', [100]), (7, 'coefficient_values', list(range(1, 100))),
    (8, 'matrix', [[1, 1], [0, 0]]), (8, 'test_vector', [1]),
    (9, 'sigma_sq', 0), (9, 'points', []), (9, 'psd_tolerance', 0.1),
]


@pytest.mark.parametrize('index,key,value', BAD)
def test_false_or_malformed_witness(index, key, value):
    name, original = CASES[index]
    payload = copy.deepcopy(original)
    payload[key] = value
    assert replay(name, payload) is False


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf'), True, 'nan'])
@pytest.mark.parametrize('index,key', [(1, 'target_bound'), (2, 'order'), (3, 'tolerance'), (9, 'sigma_sq')])
def test_invalid_numeric_values(index, key, value):
    name, original = CASES[index]
    payload = copy.deepcopy(original)
    payload[key] = value
    assert replay(name, payload) is False


def test_exact_rational_implication():
    assert replay('FARKAS_IMPLICATION', {'certificate_type': 'implication', 'matrix': [['1/3']], 'bounds': ['2/3'], 'multipliers': [3], 'target_coefficients': [1], 'target_bound': 2})


def test_bounded_boolean_depth():
    expr = ['var', 'x']
    for _ in range(100):
        expr = ['not', expr]
    assert not replay('ROBDD_EQUIVALENCE', {'left': expr, 'right': expr, 'variable_order': ['x']})


def test_unknown_id_and_nondictionary_payload():
    assert not replay('UNKNOWN', {})
    for name, _ in CASES:
        assert not replay(name, None)


def test_public_fixtures():
    from mapeogeo.semantic_contracts_v03 import FIXTURE_SPECS
    for spec in FIXTURE_SPECS:
        assert replay(spec.semantic_id[4:-3], dict(spec.payload))


def test_unsupported_foundation_alias_is_not_advertised():
    from mapeogeo.gfyproof_replay import LOCAL_SEMANTIC_IDS
    assert 'GFY.FOUNDATION_DEPENDENCY.v1' not in LOCAL_SEMANTIC_IDS
    assert not replay('FOUNDATION_DEPENDENCY', CASES[1][1])


def test_gaussian_negligible_off_diagonal_underflow_is_safe():
    # exp(-800) rounds to zero far below the 1e-12 PSD tolerance.
    assert replay('GAUSSIAN_KERNEL_EQUIVALENCE_PSD', {'points': [[0], [40]], 'sigma_sq': 1})
