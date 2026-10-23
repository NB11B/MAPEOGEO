"""Explicitly synthetic observations from the independent complex reference.

The generated observation file contains no held-out truth. The second return
value is a separate evaluator-only record. The source uses the Born rule, so
successful recovery validates the computation, not an independent physical law.
"""

from numbers import Integral

import numpy as np

from . import reference


def _integer(value, name, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def generate_dataset(seed=20261022, *, calibration_count=24, case_count=128, shots=65536):
    seed = _integer(seed, 'seed', 0)
    calibration_count = _integer(calibration_count, 'calibration_count', 4)
    case_count = _integer(case_count, 'case_count')
    shots = _integer(shots, 'shots')
    if shots > 2**53:
        raise ValueError('shots must not exceed 2**53')
    children = np.random.SeedSequence([seed, 4]).spawn(3)
    calibration_rng, preparation_rng, sampling_rng = [np.random.default_rng(s) for s in children]
    detector = .84 * np.eye(4) + .10 * np.roll(np.eye(4), 1, axis=0) + .06 * np.ones((4, 4)) / 4
    directions = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3)
    states, counts = [], []
    for index in range(calibration_count):
        rho = (reference.density_from_bloch(.8 * directions[index]) if index < 4
               else reference.random_density(2, calibration_rng))
        state = reference.bloch_from_density(rho)
        p = detector @ reference.tetra_probabilities(rho)
        states.append(state.tolist())
        counts.append(calibration_rng.multinomial(shots, p).tolist())
    cases, truth_cases = [], []
    for index in range(case_count):
        rho = reference.random_density(2, preparation_rng, pure=index % 2 == 0)
        initial = reference.bloch_from_density(rho)
        initial_p = detector @ reference.tetra_probabilities(rho)
        record = sampling_rng.multinomial(shots, initial_p)
        operations = []
        for _ in range(1 + index % 5):
            axis = preparation_rng.normal(size=3)
            angle = float(preparation_rng.uniform(-np.pi, np.pi))
            operations.append({'axis': axis.tolist(), 'angle': angle})
            rho = reference.evolve_density(rho, reference.rotation_unitary(axis, angle))
        verification_p = detector @ reference.tetra_probabilities(rho)
        verification = sampling_rng.multinomial(shots, verification_p)
        identifier = f'heldout-{index:04d}'
        cases.append({'id': identifier, 'counts': record.tolist(), 'operations': operations,
                      'verification_counts': verification.tolist()})
        truth_cases.append({'id': identifier, 'initial_state': initial.tolist(),
                            'final_state': reference.bloch_from_density(rho).tolist(),
                            'initial_observed_probabilities': initial_p.tolist(),
                            'final_observed_probabilities': verification_p.tolist()})
    observations = {
        'schema': 'ngc_geometry_lab.observations.v1',
        'provenance': {'kind': 'synthetic',
                       'description': 'Independent complex density-matrix Born model with multinomial counts and fixed detector cross-talk.',
                       'metadata': {'seed': seed, 'counts_per_record': shots,
                                    'fresh_ensemble_for_verification': True}},
        'calibration': {'states': states, 'counts': counts}, 'cases': cases,
    }
    truth = {'schema': 'ngc_geometry_lab.synthetic_truth.v1', 'seed': seed,
             'detector_matrix': detector.tolist(), 'cases': truth_cases,
             'warning': 'Evaluator-only synthetic ground truth. Never an input to analyze_dataset.'}
    return observations, truth
