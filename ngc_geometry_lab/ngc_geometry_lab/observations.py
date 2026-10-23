"""Detector calibration and blind reconstruction from observed counts.

The assumed instrument is a fixed, memoryless, four-output classical response
matrix after an ideal tetrahedral measurement. The column-stochastic response
is fitted only on known calibration preparations. It is frozen for prediction.
This model does not by itself calibrate unknown measurement axes or source drift.
"""

from __future__ import annotations

from numbers import Integral, Real

import numpy as np
from scipy.optimize import nnls

from .geometry import rotation, tetra_directions, tetra_probabilities


SCHEMA = 'ngc_geometry_lab.observations.v1'
TOL = 1e-10
MAX_CONDITION = 1e6


def _real(value, name):
    raw = np.asarray(value)
    if np.iscomplexobj(raw) or not np.issubdtype(raw.dtype, np.number):
        raise ValueError(f'{name} must contain real numbers')
    result = raw.astype(float)
    if not np.all(np.isfinite(result)):
        raise ValueError(f'{name} must be finite')
    return result


def validate_counts(counts):
    """Validate one four-channel record without normalizing or rounding it."""
    # Preserve arbitrary-size Python integers and mixed booleans until checked.
    # A float conversion first would silently turn 2**53+1 into 2**53.
    raw = np.asarray(counts, dtype=object)
    if raw.shape != (4,):
        raise ValueError('counts must be four nonnegative integers')
    values = []
    for value in raw:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise ValueError('counts must be real integers, not booleans')
        if not isinstance(value, Integral) and (not np.isfinite(value) or value != np.floor(value)):
            raise ValueError('counts must be finite integers')
        number = int(value)
        if number < 0 or number > 2**53:
            raise ValueError('counts must be nonnegative and at most 2**53')
        values.append(number)
    total = sum(values)
    if not 0 < total <= 2**53:
        raise ValueError('counts total must be positive and at most 2**53')
    return np.array(values, dtype=np.int64)


def _detector(calibration):
    if not isinstance(calibration, dict) or 'matrix' not in calibration:
        raise ValueError('calibration requires a detector matrix')
    matrix = _real(calibration['matrix'], 'detector matrix')
    if matrix.shape != (4, 4) or np.any(matrix < -TOL):
        raise ValueError('detector matrix must be nonnegative and 4 by 4')
    if not np.allclose(matrix.sum(axis=0), 1, atol=TOL, rtol=0):
        raise ValueError('detector matrix columns must sum to one')
    condition = float(np.linalg.cond(matrix))
    if not np.isfinite(condition) or condition > MAX_CONDITION:
        raise ValueError('detector is singular or too ill-conditioned to invert')
    return matrix


def calibrate_detector(states, counts):
    """Fit four nonnegative response rows, then normalize each output column.

    Counts are converted to empirical frequencies. Every calibration setting has
    equal fitting weight; shot counts need not be equal. This is a transparent
    constrained least-squares estimator, not a maximum-likelihood instrument fit.
    """
    states = _real(states, 'calibration states')
    if states.ndim != 2 or states.shape[1] != 3 or len(states) < 4:
        raise ValueError('calibration requires at least four Bloch states')
    ideal = np.vstack([tetra_probabilities(state) for state in states])
    if len(counts) != len(states):
        raise ValueError('calibration states/counts lengths differ')
    records = np.vstack([validate_counts(record) for record in counts])
    frequencies = records / records.sum(axis=1, keepdims=True)
    rank = int(np.linalg.matrix_rank(ideal, tol=TOL))
    if rank < 4 or np.linalg.cond(ideal) > MAX_CONDITION:
        raise ValueError('calibration design lacks full rank or is ill-conditioned')
    unconstrained = np.linalg.lstsq(ideal, frequencies, rcond=None)[0].T
    fitted = np.vstack([nnls(ideal, frequencies[:, row])[0] for row in range(4)])
    sums = fitted.sum(axis=0)
    if np.any(sums <= TOL):
        raise ValueError('calibration produced an empty detector column')
    fitted /= sums[None, :]
    _detector({'matrix': fitted})
    return {
        'matrix': fitted,
        'unconstrained_matrix': unconstrained,
        'design_rank': rank,
        'design_condition_number': float(np.linalg.cond(ideal)),
        'condition_number': float(np.linalg.cond(fitted)),
        'training_rmse': float(np.sqrt(np.mean((ideal @ fitted.T - frequencies)**2))),
        'method': 'nonnegative row least squares, then column normalization',
        'calibration_records': len(states),
    }


def estimate_state(counts, calibration, *, project_physical=True):
    """Reconstruct from one count vector and the frozen detector, without truth.

    Inversion can yield signed estimated ideal probabilities because of shot
    noise. Preserve them and the raw Bloch vector. Radial projection to the
    unit ball, when requested, is an explicit biased physical-state estimator.
    """
    records = validate_counts(counts)
    matrix = _detector(calibration)
    frequency = records / records.sum()
    linear_estimate = np.linalg.solve(matrix, frequency)
    raw = 3 * linear_estimate @ tetra_directions()
    norm = float(np.linalg.norm(raw))
    projected = bool(project_physical and norm > 1)
    state = raw / norm if projected else raw.copy()
    return {
        'state': state, 'raw_state': raw, 'raw_norm': norm,
        'linear_probability_estimate': linear_estimate,
        'projected': projected,
        'projection_distance': float(np.linalg.norm(state - raw)),
        'shots': int(records.sum()),
    }


def _keys(value, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError('expected a JSON object')
    unknown = set(value) - set(required) - set(optional)
    missing = set(required) - set(value)
    if unknown or missing:
        raise ValueError(f'unexpected keys {sorted(unknown)}; missing keys {sorted(missing)}')


def predict_after_operations(state, operations, calibration):
    """Apply active rotations, then predict ideal and instrument probabilities."""
    state = _real(state, 'state').copy()
    tetra_probabilities(state)  # Validate physical input before any operation.
    matrix = _detector(calibration)
    if not isinstance(operations, list):
        raise ValueError('operations must be a list')
    for operation in operations:
        _keys(operation, ('axis', 'angle'))
        state = rotation(operation['axis'], operation['angle']) @ state
    ideal = tetra_probabilities(state)
    observed = matrix @ ideal
    return {'state': state, 'ideal_probabilities': ideal, 'observed_probabilities': observed}


def analyze_dataset(payload):
    """Validate and analyze external counts; held-out truth is forbidden.

    A verification record measures a *fresh identically prepared ensemble*
    after the specified operations. It is not the same system after the initial
    destructive tetrahedral measurement. All outcomes must be included.
    """
    _keys(payload, ('schema', 'provenance', 'calibration', 'cases'))
    if payload['schema'] != SCHEMA:
        raise ValueError('unsupported observations schema')
    provenance = payload['provenance']
    _keys(provenance, ('kind', 'description'), ('metadata',))
    if provenance['kind'] not in ('synthetic', 'experimental'):
        raise ValueError('data kind must be synthetic or experimental')
    if not isinstance(provenance['description'], str) or not provenance['description'].strip():
        raise ValueError('provenance requires a nonempty description')
    _keys(payload['calibration'], ('states', 'counts'))
    fit = calibrate_detector(**payload['calibration'])
    if not isinstance(payload['cases'], list) or not payload['cases']:
        raise ValueError('cases must be a nonempty list')
    results, identifiers = [], set()
    for case in payload['cases']:
        _keys(case, ('id', 'counts', 'operations', 'verification_counts'))
        identifier = case['id']
        if not isinstance(identifier, str) or not identifier:
            raise ValueError('case id must be a nonempty string')
        if identifier in identifiers:
            raise ValueError(f'duplicate case id: {identifier}')
        identifiers.add(identifier)
        estimate = estimate_state(case['counts'], fit)
        prediction = predict_after_operations(estimate['state'], case['operations'], fit)
        verification = validate_counts(case['verification_counts'])
        frequency = verification / verification.sum()
        results.append({
            'id': identifier, 'estimate': estimate, 'prediction': prediction,
            'verification_shots': int(verification.sum()),
            'verification_total_variation': float(0.5 * np.sum(np.abs(frequency - prediction['observed_probabilities']))),
        })
    return {
        'schema': 'ngc_geometry_lab.analysis.v1',
        'data_kind': provenance['kind'], 'provenance': dict(provenance),
        'calibration': fit, 'cases': results,
        'mean_verification_total_variation': float(np.mean([r['verification_total_variation'] for r in results])),
        'projected_estimates': sum(r['estimate']['projected'] for r in results),
        'assumptions': [
            'Known tetrahedral measurement axes and calibrated preparation coordinates.',
            'Fixed memoryless four-channel detector response; all counts included.',
            'Verification uses a fresh identical preparation followed by the operations.',
            'An explicit Born-rule forward model; no claim that readout was derived from geometry.',
        ],
    }
