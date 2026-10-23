"""Independent experiments and controls used by the frozen campaign.

All random streams have explicit numeric labels. Ground truth belongs to the
experiment evaluator, never the reconstruction estimator's argument list.
"""

from __future__ import annotations

import itertools
import hashlib
import runpy
import sys
import traceback
from pathlib import Path

import numpy as np

from . import geometry as geo
from . import reference as ref
from .observations import analyze_dataset, estimate_state
from .synthetic import generate_dataset


def rng_for(seed, label):
    return np.random.default_rng(np.random.SeedSequence([seed, label]))


def _require_finite(value, context):
    """Reject damaged measurements before reductions, retaining their location."""
    array = np.asarray(value)
    finite = np.isfinite(array)
    if not np.all(finite):
        bad = [(tuple(int(i) for i in index), repr(array[tuple(index)].item()))
               for index in np.argwhere(~finite)]
        raise ValueError(f'{context}: nonfinite values at {bad}')
    return array


def _finite_float(value, context):
    _require_finite(value, context)
    return float(value)


def _max_abs_error(candidate, expected, context):
    candidate = _require_finite(candidate, f'{context} candidate')
    expected = _require_finite(expected, f'{context} reference')
    if candidate.shape != expected.shape:
        raise ValueError(f'{context}: comparison shapes differ: {candidate.shape} versus {expected.shape}')
    with np.errstate(over='ignore', invalid='ignore'):
        errors = np.abs(candidate-expected)
    _require_finite(errors, f'{context} comparison error')
    return float(np.max(errors))


def _known_work_expectation(project, path, name, exc, frame, roots):
    """Recognize only the independently disproved assertion in pinned source.

    MAPEOGEO ac63dde9da6dca2c000aa53ee6ffb9365e2388a1, line 13.
    Its earlier noncommutation assertion at line 8 remains a real failure.
    """
    expected_name = 'test_noncommuting_operators_can_be_equivalent_after_work_projection'
    expected_path = (roots / 'mapeogeo/tests/test_psmsl_work_equivalence_v1.py').resolve()
    if not (project == 'mapeogeo' and name == expected_name
            and path.resolve() == expected_path
            and Path(frame.filename).resolve() == expected_path
            and frame.name == expected_name and frame.lineno == 13
            and frame.line == 'assert not w.equivalent_for_work'
            and type(exc) is AssertionError and exc.args == ()):
        return False
    try:
        digest = hashlib.sha256(expected_path.read_bytes()).hexdigest()
    except OSError:
        return False
    if digest != 'd6eca4324d88e344ea007bb4a80eab0088cadb9c1a482e5702311ecd11d0686c':
        return False
    # Independent integer countercalculation of the literal test fixture.
    a, b = np.array([[1,0],[0,2]], dtype=np.int64), np.array([[1,1],[0,1]], dtype=np.int64)
    projection = np.array([[0,1]], dtype=np.int64)
    ab, ba = a@b, b@a
    return not np.array_equal(ab,ba) and np.array_equal(projection@ab,projection@ba)


def upstream_baselines():
    """Execute original zero-argument tests and retain their actual outcomes.

    These selected upstream test files have no fixtures or parametrization.
    Execution is direct; this is not a claim to have run entire upstream suites.
    """
    roots = Path(__file__).parent / '_vendor'
    old_path = sys.path[:]
    sys.path[:0] = [str(roots / 'mapeogeo'), str(roots / 'ngc_real')]
    records = []
    try:
        for project in ('mapeogeo', 'ngc_real'):
            for path in sorted((roots / project / 'tests').glob('test_*.py')):
                module = runpy.run_path(str(path))
                for name, function in sorted(module.items()):
                    if not (name.startswith('test_') and callable(function)):
                        continue
                    record = {'project': project, 'file': path.name, 'test': name, 'status': 'PASS'}
                    try:
                        function()
                    except Exception as exc:
                        record.update(status='FAIL', exception=type(exc).__name__, message=str(exc))
                        # Relative source location, not an execution-path-dependent traceback.
                        frame = traceback.extract_tb(exc.__traceback__)[-1]
                        record['failure_line'] = frame.lineno
                        record['known_bad_expectation'] = _known_work_expectation(project, path, name, exc, frame, roots)
                    records.append(record)
    finally:
        sys.path[:] = old_path
    failures = [r for r in records if r['status'] == 'FAIL']
    known = sum(bool(r.get('known_bad_expectation')) for r in failures)
    return {'tests_executed': len(records), 'passed': len(records)-len(failures),
            'failed': len(failures), 'known_bad_test_expectations': known,
            'unexpected_failures': len(failures)-known, 'tests': records,
            'scope': 'Only the selected unchanged zero-argument baseline tests bundled with the qualified source.'}


def metric_and_center():
    rx = np.array([[1,0,0],[0,0,-1],[0,1,0]], dtype=float)
    rz = np.array([[0,-1,0],[1,0,0],[0,0,1]], dtype=float)
    basis = np.array([[1,.2,0],[0,2,.3],[0,0,.7]])
    inverse = np.linalg.inv(basis)
    rotations = [basis @ op @ inverse for op in (rx, rz)]
    projectors = [basis @ np.diag([1,1,0]) @ inverse]
    expected = inverse.T @ inverse
    expected *= 3 / np.trace(expected)
    recovered = geo.infer_metric(rotations, projectors)
    error = (float(np.max(np.abs(recovered['metric'] - expected)))
             if recovered['metric'] is not None else 1e100)
    insufficient = geo.infer_metric([], [np.diag([1.,0,0])])
    contradiction = geo.infer_metric([2*np.eye(3)])
    s = 2.**20
    ill_conditioned = geo.infer_metric([], [np.diag([1.,0]), np.array([[.5,s/2],[1/(2*s),.5]])], dimension=2)
    center = np.array([1.2,-.3,2.5])
    affine = [(op, center-op@center) for op in rotations]
    found = geo.infer_center(affine)
    center_error = float(np.max(np.abs(found['center']-center)))
    nonunique = geo.infer_center([(np.diag([-1.,1,1]), np.array([2.,0,0]))])
    inconsistent = geo.infer_center([(np.eye(3), np.array([1.,0,0]))])
    n = geo.tetra_directions()
    faces = [(np.eye(3)-np.outer(normal,normal), -normal/3) for normal in n]
    face_center = geo.infer_center(faces)
    tetra = geo.tetra_geometry(center, basis.T, recovered['metric'])
    return {
        'metric': recovered, 'expected_metric': expected, 'max_metric_error': error,
        'insufficient_metric_status': insufficient['status'],
        'contradictory_metric_status': contradiction['status'],
        'ill_conditioned_spd_status': ill_conditioned['status'],
        'common_center': found, 'center_max_error': center_error,
        'nonunique_center_status': nonunique['status'], 'inconsistent_center_status': inconsistent['status'],
        'tetrahedral_face_projections_common_center_status': face_center['status'],
        'tetrahedron_from_origin_and_three_displacements': tetra,
        'meaning': 'Metric up to scale and affine fixed point under declared operator interpretation; neither proves historical common origin.',
    }


def single_qubit(seed):
    rng = rng_for(seed, 2)
    state_error = probability_error = prediction_error = 0.
    rows, wrong_labels = [], []
    for case in range(256):
        rho = ref.random_density(2, rng, pure=case % 2 == 0)
        true_state = ref.bloch_from_density(rho)
        observations = ref.tetra_probabilities(rho)
        reconstructed = geo.tetra_reconstruct(observations)
        context = f'single_qubit case={case} reconstruction'
        state_error = max(state_error, _max_abs_error(reconstructed,true_state,f'{context} state'))
        probability_error = max(probability_error, _max_abs_error(geo.tetra_probabilities(true_state),observations,f'{context} probability'))
        wrong = geo.tetra_reconstruct(observations[[1,0,2,3]])
        for step in range(12):
            axis, angle = rng.normal(size=3), float(rng.uniform(-np.pi,np.pi))
            rotation = geo.rotation(axis,angle)
            reconstructed = rotation @ reconstructed
            wrong = rotation @ wrong
            rho = ref.evolve_density(rho, ref.rotation_unitary(axis,angle))
            reference_p = ref.tetra_probabilities(rho)
            context = f'single_qubit case={case} step={step+1}'
            _require_finite(reconstructed, f'{context} reconstructed state')
            error = _max_abs_error(geo.tetra_probabilities(reconstructed),reference_p,f'{context} probability')
            wrong_error = _max_abs_error(geo.tetra_probabilities(wrong),reference_p,f'{context} wrong-label control')
            prediction_error = max(prediction_error,error)
            wrong_labels.append(wrong_error)
            rows.append({'case':case,'pure':case%2==0,'step':step+1,
                         'max_probability_error':error,'wrong_label_max_error':wrong_error})
    directions = geo.tetra_directions()
    one_hot_rejected = False
    try:
        geo.tetra_reconstruct([1,0,0,0])
    except ValueError:
        one_hot_rejected = True
    return {
        'states':256,'pure_states':128,'mixed_states':128,'rotation_predictions':3072,
        'max_state_error':state_error,'max_probability_error':probability_error,
        'max_prediction_error':prediction_error,
        'observation_rank':int(np.linalg.matrix_rank(directions)),
        'max_direction_sum_error':float(np.max(np.abs(directions.sum(axis=0)))),
        'max_frame_gram_error':float(np.max(np.abs(directions@directions.T-(4*np.eye(4)-np.ones((4,4)))/3))),
        'one_hot_distribution_rejected_as_unphysical':one_hot_rejected,
        'wrong_label_control_mean_error':float(np.mean(wrong_labels)),
        'wrong_label_control_max_error':float(np.max(wrong_labels)),
        'wrong_label_control_description':'Permute observation labels without transforming the subsequent operator frame.',
    }, rows


def dual_lane(seed):
    from .repository import dual_lane_apply
    rng = rng_for(seed,3)
    state_error = probability_error = norm_error = 0.
    rows = []
    for num_qubits in range(1,7):
        dimension = 2**num_qubits
        for circuit in range(12):
            original = rng.normal(size=dimension)+1j*rng.normal(size=dimension)
            original /= np.linalg.norm(original)
            candidate, expected = original.copy(),original.copy()
            for step in range(20):
                width = 1 if num_qubits==1 or step%2==0 else 2
                targets = tuple(int(x) for x in rng.choice(num_qubits,width,replace=False))
                size = 2**width
                matrix = rng.normal(size=(size,size))+1j*rng.normal(size=(size,size))
                gate = np.linalg.qr(matrix)[0]
                candidate = dual_lane_apply(candidate,gate,targets,num_qubits)
                expected = ref.local_gate(expected,gate,targets,num_qubits)
                context = f'dual_lane qubits={num_qubits} circuit={circuit} step={step+1}'
                error = _max_abs_error(candidate,expected,f'{context} state')
                with np.errstate(over='ignore', invalid='ignore'):
                    candidate_p, expected_p = np.abs(candidate)**2, np.abs(expected)**2
                    norm_difference = abs(np.vdot(candidate,candidate).real-1)
                p_error = _max_abs_error(candidate_p,expected_p,f'{context} probability')
                n_error = _finite_float(norm_difference,f'{context} norm error')
                state_error,probability_error,norm_error = max(state_error,error),max(probability_error,p_error),max(norm_error,n_error)
                rows.append({'qubits':num_qubits,'circuit':circuit,'step':step+1,
                             'targets':','.join(map(str,targets)),'max_state_error':error,
                             'max_probability_error':p_error,'norm_error':n_error})
    return {
        'gate_applications':len(rows),'qubit_range':[1,6],'circuits':72,'gates_per_circuit':20,
        'max_state_error':state_error,'max_probability_error':probability_error,'max_norm_error':norm_error,
        'executed_backend':'Unmodified NGC_Real apply_local_gate_dual_lane through validated adapter',
        'comparison_backend':'Independent complex tensor-axis reference',
        'hardware':'CPU; no claim of dual physical cores or GPU execution',
        'state_storage':[{'qubits':n,'real_entries':2*2**n,'dual_lane_bytes':16*2**n,
                          'complex_reference_bytes':16*2**n} for n in range(1,7)],
    }, rows


def finite_shot(seed):
    observations, truth = generate_dataset(seed)
    analyzed = analyze_dataset(observations)
    rows = []
    for record,expected,raw in zip(analyzed['cases'],truth['cases'],observations['cases']):
        context = f"finite_shot case={record['id']}"
        state = _require_finite(expected['initial_state'],f'{context} reference state')
        _require_finite(record['estimate']['state'],f'{context} estimated state')
        calibrated = _finite_float(np.linalg.norm(record['estimate']['state']-state),f'{context} calibrated state error')
        uncorrected = estimate_state(raw['counts'],{'matrix':np.eye(4)})
        _require_finite(uncorrected['state'],f'{context} uncorrected state')
        uncorrected_error = _finite_float(np.linalg.norm(uncorrected['state']-state),f'{context} uncorrected state error')
        _require_finite(record['prediction']['observed_probabilities'],f'{context} predicted probabilities')
        _require_finite(expected['final_observed_probabilities'],f'{context} reference probabilities')
        p_error = _finite_float(.5*np.sum(np.abs(record['prediction']['observed_probabilities']-np.array(expected['final_observed_probabilities']))),f'{context} prediction error')
        _require_finite(record['verification_total_variation'],f'{context} verification total variation')
        _require_finite(record['estimate']['raw_norm'],f'{context} raw norm')
        rows.append({'id':record['id'],'calibrated_state_error':calibrated,
                     'uncorrected_state_error':uncorrected_error,'prediction_total_variation_vs_truth':p_error,
                     'verification_total_variation':record['verification_total_variation'],
                     'raw_norm':record['estimate']['raw_norm'],'projected':record['estimate']['projected']})
    errors = np.array([r['calibrated_state_error'] for r in rows])
    _require_finite(analyzed['mean_verification_total_variation'],'finite_shot mean verification total variation')
    detector_error = _max_abs_error(analyzed['calibration']['matrix'],np.array(truth['detector_matrix']),'finite_shot detector')
    return {
        'calibration_preparations':24,'heldout_preparations':128,'counts_per_record':65536,
        'total_observed_counts':(24+2*128)*65536,
        'mean_state_error':float(errors.mean()),'max_state_error':float(errors.max()),
        'p95_state_error':float(np.quantile(errors,.95)),
        'mean_uncorrected_state_error':float(np.mean([r['uncorrected_state_error'] for r in rows])),
        'mean_prediction_total_variation_vs_truth':float(np.mean([r['prediction_total_variation_vs_truth'] for r in rows])),
        'mean_verification_total_variation':analyzed['mean_verification_total_variation'],
        'projected_estimates':analyzed['projected_estimates'],
        'detector_max_entry_error':detector_error,
        'fitted_detector':analyzed['calibration'],
        'truth_access':'Only this experiment evaluator receives the separate truth object; analyze_dataset accepts counts and calibration only.',
        'sampling':'NumPy multinomial from a declared Born-rule model, not laboratory observations.',
    }, rows, observations, truth, analyzed


def readout_selection(seed):
    rng = rng_for(seed,5)
    calibration_angles = np.linspace(.08,1.49,15)
    heldout_angles = np.linspace(.115,1.455,19)
    shots = 65536
    counts = rng.binomial(shots,np.cos(calibration_angles)**2)
    frequency = counts/shots
    heldout_counts = rng.binomial(shots,np.cos(heldout_angles)**2)
    heldout_frequency = heldout_counts/shots
    def probability(angles,exponent):
        c,s = np.abs(np.cos(angles))**exponent,np.abs(np.sin(angles))**exponent
        return c/(c+s)
    scores = {}
    for exponent in (1,2,4):
        predicted = probability(calibration_angles,exponent)
        _require_finite(predicted,f'readout exponent={exponent} calibration probabilities')
        scores[exponent] = _finite_float(-np.mean(frequency*np.log(predicted)+(1-frequency)*np.log1p(-predicted)),f'readout exponent={exponent} calibration score')
    # Freeze the selection before computing any held-out candidate score.
    winner = min(scores,key=scores.get)
    rows = []
    for exponent in (1,2,4):
        predicted_heldout = probability(heldout_angles,exponent)
        _require_finite(predicted_heldout,f'readout exponent={exponent} heldout probabilities')
        heldout_score = _finite_float(-np.mean(heldout_frequency*np.log(predicted_heldout)+(1-heldout_frequency)*np.log1p(-predicted_heldout)),f'readout exponent={exponent} heldout score')
        heldout_rmse = _finite_float(np.sqrt(np.mean((predicted_heldout-np.cos(heldout_angles)**2)**2)),f'readout exponent={exponent} heldout RMSE')
        rows.append({'exponent':exponent,'calibration_cross_entropy':scores[exponent],
                     'heldout_cross_entropy':heldout_score,
                     'heldout_rmse_vs_declared_truth':heldout_rmse})
    direct,_ = geo.projection_transmission([1,0,0],[[0,1,0]])
    inserted,final = geo.projection_transmission([1,0,0],[[1,1,0],[0,1,0]])
    _require_finite([direct,inserted],'readout projection weights')
    _require_finite(final,'readout final vector')
    return {'selected_exponent_on_calibration':winner,'selection_frozen_before_heldout_scoring':True,
            'calibration_angles':15,'heldout_angles':19,'shots_per_angle':shots,
            'candidate_rule':'p0=|cos(theta)|**alpha/(|cos(theta)|**alpha+|sin(theta)|**alpha)',
            'declared_generator':'p0=cos(theta)**2 (Born/squared-norm rule)',
            'squared_rule_not_independently_derived':True,
            'direct_crossed_weight':direct,'inserted_diagonal_weight':inserted,'final_vector':final,
            'candidate_scores':rows,
            'calibration_records':[{'angle':float(a),'count0':int(c),'count1':shots-int(c)} for a,c in zip(calibration_angles,counts)],
            'heldout_records':[{'angle':float(a),'count0':int(c),'count1':shots-int(c)} for a,c in zip(heldout_angles,heldout_counts)]},rows


def joint_systems(seed):
    rng = rng_for(seed,6)
    p_error = density_error = prediction_error = 0.
    rows = []
    for case in range(128):
        rho = ref.random_density(4,rng,pure=case%2==0)
        measured = ref.joint_tetra_probabilities(rho)
        a,b,c = geo.joint_reconstruct(measured)
        reconstructed = ref.density_from_joint(a,b,c)
        context = f'joint case={case} reconstruction'
        density_error = max(density_error,_max_abs_error(reconstructed,rho,f'{context} density'))
        p_error = max(p_error,_max_abs_error(geo.joint_probabilities(a,b,c),measured,f'{context} probability'))
        for step in range(8):
            axis_a,axis_b = rng.normal(size=(2,3))
            angle_a,angle_b = rng.uniform(-np.pi,np.pi,2)
            ra,rb = geo.rotation(axis_a,angle_a),geo.rotation(axis_b,angle_b)
            a,b,c = ra@a,rb@b,ra@c@rb.T
            unitary = np.kron(ref.rotation_unitary(axis_a,angle_a),ref.rotation_unitary(axis_b,angle_b))
            rho = ref.evolve_density(rho,unitary)
            expected = ref.joint_tetra_probabilities(rho)
            context = f'joint case={case} step={step+1}'
            for coordinate,label in ((a,'local a'),(b,'local b'),(c,'correlation')):
                _require_finite(coordinate,f'{context} {label}')
            error = _max_abs_error(geo.joint_probabilities(a,b,c),expected,f'{context} probability')
            prediction_error = max(prediction_error,error)
            rows.append({'case':case,'pure':case%2==0,'step':step+1,'max_probability_error':error})
    singlet_p = geo.joint_probabilities(np.zeros(3),np.zeros(3),-np.eye(3))
    mixed_p = geo.joint_probabilities(np.zeros(3),np.zeros(3),np.zeros((3,3)))
    z,x = np.array([0.,0,1]),np.array([1.,0,0])
    chsh = abs(geo.chsh_value(-np.eye(3),z,x,(z+x)/np.sqrt(2),(z-x)/np.sqrt(2)))
    vertices = []
    for a0,a1,b0,b1 in itertools.product((-1,1),repeat=4):
        vertices.append({'a0':a0,'a1':a1,'b0':b0,'b1':b1,'chsh':a0*b0+a0*b1+a1*b0-a1*b1})
    positive_probability_nonquantum = geo.joint_probabilities(np.zeros(3),np.zeros(3),np.eye(3))
    nonphysical_rejected = False
    try:
        ref.density_from_joint(np.zeros(3),np.zeros(3),np.eye(3))
    except ValueError:
        nonphysical_rejected = True
    _require_finite(chsh,'joint singlet CHSH')
    marginal_error = max(_max_abs_error(singlet_p.sum(axis=0),mixed_p.sum(axis=0),'joint local marginal a'),
                         _max_abs_error(singlet_p.sum(axis=1),mixed_p.sum(axis=1),'joint local marginal b'))
    _require_finite(positive_probability_nonquantum,'joint positive nonquantum probability control')
    return {
        'states':128,'pure_states':64,'mixed_states':64,'rotation_predictions':1024,
        'max_probability_error':p_error,'max_density_error':density_error,'max_prediction_error':prediction_error,
        'singlet_chsh':chsh,'local_deterministic_max_chsh':max(abs(v['chsh']) for v in vertices),
        'local_vertices_enumerated':len(vertices),'local_vertices':vertices,
        'same_local_marginals_max_error':marginal_error,
        'singlet_vs_mixed_joint_total_variation':float(.5*np.sum(np.abs(singlet_p-mixed_p))),
        'positive_joint_distribution_nonquantum_min_probability':float(positive_probability_nonquantum.min()),
        'positive_joint_distribution_nonquantum_rejected_by_psd':nonphysical_rejected,
        'interpretation':'The CHSH value is a computed prediction, not a local hidden-variable implementation or physical Bell test.',
    },rows


def identifiability():
    c = np.array([[1.,0,0]])
    transition = np.array([[0.,1,0],[0,0,1],[1,0,0]])
    duplicated = np.vstack([c,-c,c,-c])
    dynamic = geo.observability_matrix(c,transition,3)
    plus,minus = np.array([1.,0,0]),np.array([-1.,0,0])
    observe_z = np.array([[0.,0,1]])
    r = geo.rotation([0,1,0],np.pi/2)
    before = float(np.max(np.abs(observe_z@plus-observe_z@minus)))
    after = float(np.max(np.abs(observe_z@r@plus-observe_z@r@minus)))
    return {'duplicate_and_mirror_rank':int(np.linalg.matrix_rank(duplicated)),
            'dynamic_sequence_rank':int(np.linalg.matrix_rank(dynamic)),
            'same_initial_observation_difference':before,'after_permitted_rotation_difference':after,
            'meaning':'Identical present output need not imply identical state; extra independent operations can reveal a previously hidden direction.'}
