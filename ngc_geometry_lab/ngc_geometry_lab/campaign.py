"""Frozen computational qualification campaign and complete evidence output."""

from __future__ import annotations

from datetime import datetime, timezone
from numbers import Integral
from pathlib import Path
import platform
import shutil
import sys
import traceback

import numpy as np
import scipy

from . import experiments as exp
from .io import canonical_json, plain, sha256, write_csv, write_json


CONFIGURATION = {
    'version': 1, 'default_seed': 20261022, 'absolute_equivalence_tolerance': 1e-10,
    'metric_tolerance': 1e-9,
    'single_states': 256, 'single_rotations_per_state': 12,
    'dual_qubits': [1,2,3,4,5,6], 'dual_circuits_per_size': 12, 'dual_gates_per_circuit': 20,
    'calibration_states': 24, 'heldout_states': 128, 'counts_per_record': 65536,
    'mean_bloch_error_gate': .035,
    'joint_states': 128, 'joint_local_rotations_per_state': 8,
    'readout_exponents': [1,2,4], 'local_deterministic_assignments': 16,
    'rng_streams': {'single_qubit':2,'dual_lane':3,'synthetic_observations':4,'readout':5,'joint':6},
}


def _nonfinite_evidence(value, path='evidence'):
    """Describe invalid numeric leaves without publishing them as valid numbers."""
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, dict):
        return [item for key, child in value.items()
                for item in _nonfinite_evidence(child,f'{path}[{key!r}]')]
    if isinstance(value, (list,tuple)):
        return [item for index, child in enumerate(value)
                for item in _nonfinite_evidence(child,f'{path}[{index}]')]
    if isinstance(value, float) and not np.isfinite(value):
        return [{'path':path,'value':repr(value)}]
    return []


def run_campaign(seed=20261022, *, output_dir=None, progress=None):
    """Run every experiment, retain failures, and return deterministic results.

    Runtime/environment metadata is stored separately from scientific results.
    Existing nonempty output directories are refused to preserve earlier runs.
    """
    if isinstance(seed,(bool,np.bool_)) or not isinstance(seed,Integral) or seed < 0:
        raise ValueError('seed must be a nonnegative integer')
    seed = int(seed)
    output = Path(output_dir) if output_dir is not None else None
    if output is not None:
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise ValueError('output directory must be new or empty; previous evidence is preserved')
        output.mkdir(parents=True,exist_ok=True)
        write_json(output/'configuration.json',dict(CONFIGURATION,seed=seed))
    experiments,errors,tables,extra = {},{}, {},{}

    def stage(name,function):
        if progress:
            progress(name)
        previous_tables, previous_extra = tables.copy(),extra.copy()
        pending_evidence = None
        try:
            value = function()
            pending_evidence = {
                'summary':value,
                'tables':{key:rows for key,rows in tables.items()
                          if key not in previous_tables or rows is not previous_tables[key]},
                'artifacts':{key:item for key,item in extra.items()
                             if key not in previous_extra or item is not previous_extra[key]},
            }
            # Validate the entire stage, including evidence omitted from the
            # returned summary, inside its exception-capture boundary.
            canonical_json(pending_evidence)
            experiments[name] = value
        except Exception as exc:
            value = {'error_type':type(exc).__name__,'error':str(exc)}
            if pending_evidence is not None:
                invalid = _nonfinite_evidence(pending_evidence)
                if invalid:
                    value['invalid_evidence'] = invalid
            # A failed stage cannot leave unvalidated CSV/JSON for the later
            # publication loop. Its rejected payload is retained separately.
            tables.clear()
            tables.update(previous_tables)
            extra.clear()
            extra.update(previous_extra)
            experiments[name] = value
            errors[name] = value
            if output is not None:
                (output/f'{name}_exception.txt').write_text(traceback.format_exc(),encoding='utf-8')
                if pending_evidence is not None:
                    with np.printoptions(threshold=sys.maxsize):
                        diagnostic = repr(pending_evidence)
                    (output/f'{name}_invalid_evidence.txt').write_text(
                        'Rejected stage evidence; not valid qualification data.\n'+diagnostic+'\n',encoding='utf-8')
        if output is not None:
            write_json(output/'checkpoints'/f'{name}.json',value)
        return value

    def source_integrity():
        from .repository import verify_sources
        return verify_sources()

    def connected():
        from .repository import connected_operator_demo
        result = connected_operator_demo()
        result['upstream_baseline'] = exp.upstream_baselines()
        return result

    def closure():
        from .repository import exact_closure
        full = exact_closure()
        extra['exact_closure.json'] = full
        return {k:v for k,v in full.items() if k not in ('matrices','multiplication_table','shortest_words')}

    def single():
        result,tables['single_qubit.csv'] = exp.single_qubit(seed)
        return result

    def dual():
        result,tables['dual_lane.csv'] = exp.dual_lane(seed)
        return result

    def finite():
        result,tables['finite_shot.csv'],observations,truth,analysis = exp.finite_shot(seed)
        extra.update({'synthetic_observations.json':observations,'synthetic_truth.json':truth,
                      'blind_analysis.json':analysis})
        return result

    def readout():
        result,tables['readout_candidates.csv'] = exp.readout_selection(seed)
        return result

    def joint():
        result,tables['joint_systems.csv'] = exp.joint_systems(seed)
        return result

    stage('source_integrity',source_integrity)
    stage('connected_operators',connected)
    stage('exact_closure',closure)
    stage('metric_and_center',exp.metric_and_center)
    stage('single_qubit',single)
    stage('dual_lane',dual)
    stage('finite_shot',finite)
    stage('readout',readout)
    stage('joint',joint)
    stage('identifiability',exp.identifiability)

    gates=[]
    def gate(identifier,stage_name,check,criterion):
        try:
            passed = stage_name not in errors and bool(check(experiments[stage_name]))
        except (KeyError,TypeError,ValueError):
            passed=False
        gates.append({'id':identifier,'passed':passed,'criterion':criterion,'experiment':stage_name})

    tol=CONFIGURATION['absolute_equivalence_tolerance']
    gate('source_integrity','source_integrity',lambda x:x['verified_files']>0 and not x['mismatches'],
         'All selected source bytes match SHA256 and Git blob SHA1 provenance.')
    gate('connected_operators','connected_operators',lambda x:x['qualified'] and x['upstream_baseline']['unexpected_failures']==0,
         'Actual connected operators agree with independent calculations; all unexpected upstream failures are absent; known bad expectation remains visible.')
    gate('exact_closure','exact_closure',lambda x:x['size']==115 and x['validation']['product_mismatches']==0 and x['validation']['associativity_mismatches']==0 and x['validation']['product_comparisons']==115**2 and x['validation']['associativity_triples']==115**3,
         'New explicit integer generator fixture: 115 elements, all 13225 products and 1520875 associativity triples verified.')
    gate('metric_and_center','metric_and_center',lambda x:x['metric']['status']=='unique_up_to_scale' and x['max_metric_error']<1e-9 and x['center_max_error']<tol and x['insufficient_metric_status']=='underdetermined' and x['contradictory_metric_status']=='no_positive_definite_metric' and x['ill_conditioned_spd_status']=='unresolved_feasibility' and x['nonunique_center_status']=='underdetermined' and x['inconsistent_center_status']=='inconsistent' and x['tetrahedral_face_projections_common_center_status']=='inconsistent',
         'Recover declared metric and center, classify insufficient/contradictory/numerically unresolved controls correctly.')
    gate('tetra_reconstruction','single_qubit',lambda x:x['states']==256 and x['max_state_error']<tol and x['max_probability_error']<tol and x['observation_rank']==3 and x['max_frame_gram_error']<tol and x['max_direction_sum_error']<tol and x['one_hot_distribution_rejected_as_unphysical'],
         '256 independent pure/mixed preparations reconstruct; tetrahedral frame identities and physical-state rejection hold within absolute 1e-10.')
    gate('heldout_rotations','single_qubit',lambda x:x['rotation_predictions']==3072 and x['max_prediction_error']<tol and x['wrong_label_control_mean_error']>.01,
         '3072 held-out rotation predictions agree within absolute 1e-10; a mismatched label/operator frame fails visibly.')
    gate('dual_lane_equivalence','dual_lane',lambda x:x['gate_applications']>=1000 and max(x['max_state_error'],x['max_probability_error'],x['max_norm_error'])<tol,
         'Actual real dual-lane backend agrees with independent complex tensor reference for >=1000 local gates, absolute tolerance 1e-10.')
    gate('finite_shot_prediction','finite_shot',lambda x:x['mean_state_error']<.035 and x['mean_state_error']<x['mean_uncorrected_state_error'],
         'Frozen calibration; mean held-out Bloch error <0.035 and improves over uncorrected detector counts.')
    gate('readout_selection','readout',lambda x:x['selected_exponent_on_calibration']==2 and abs(x['direct_crossed_weight'])<tol and abs(x['inserted_diagonal_weight']-.25)<tol,
         'Synthetic squared-rule data selects exponent2 from1,2,4; crossed projections give0 and inserted diagonal gives1/4.')
    gate('joint_reconstruction','joint',lambda x:x['states']==128 and max(x['max_probability_error'],x['max_density_error'],x['max_prediction_error'])<tol,
         '128 two-system states and1024 local-rotation sequences agree with independent density matrices, absolute1e-10.')
    gate('correlation_controls','joint',lambda x:abs(x['singlet_chsh']-2*np.sqrt(2))<tol and x['local_vertices_enumerated']==16 and x['local_deterministic_max_chsh']==2 and x['same_local_marginals_max_error']<tol and x['singlet_vs_mixed_joint_total_variation']>.01 and x['positive_joint_distribution_nonquantum_rejected_by_psd'],
         'Computed singlet CHSH=2sqrt(2), all16 local assignments bounded by2; equal marginals do not fix joints; invalid quantum state rejected.')
    gate('identifiability','identifiability',lambda x:x['duplicate_and_mirror_rank']==1 and x['dynamic_sequence_rank']==3 and x['same_initial_observation_difference']<tol and abs(x['after_permitted_rotation_difference']-2)<tol,
         'Duplicate/mirrored views add no missing rank; operation sequence restores rank and distinguishes initially equal outputs.')
    result = plain({
        'schema':'ngc_geometry_lab.qualification.v1','seed':seed,'configuration':CONFIGURATION,
        'scope':{'observations':'synthetic','computation':'CPU float64 plus exact integer closure',
                 'cuda_execution':'not_run_cpu_only_campaign','physical_theory_validated':False,
                 'speedup_claim':False,'historical_115_artifact_recovered':False},
        'qualified':all(g['passed'] for g in gates),'gates':gates,'stage_errors':errors,'experiments':experiments,
    })
    if output is not None:
        for name,rows in tables.items():
            write_csv(output/name,rows)
        for name,value in extra.items():
            write_json(output/name,value)
        write_json(output/'results.json',result)
        from .reporting import markdown_report
        (output/'REPORT.md').write_text(markdown_report(result),encoding='utf-8')
        manifest = {
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'environment':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'scipy':scipy.__version__,
                           'nvidia_device_present':Path('/dev/nvidia0').exists(),'nvidia_smi_available':shutil.which('nvidia-smi') is not None,
                           'nvcc_available':shutil.which('nvcc') is not None},
            'command':f'python -m ngc_geometry_lab run --seed {seed} --out <new-directory>',
            'files':{str(path.relative_to(output)):sha256(path) for path in sorted(output.rglob('*')) if path.is_file()},
        }
        write_json(output/'manifest.json',manifest)
    return result
