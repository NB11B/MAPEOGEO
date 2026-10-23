"""Command-line entry point for qualification and observed-count analysis."""

import argparse
import json
from pathlib import Path
import sys

from .io import canonical_json


def _new_path(value):
    path = Path(value)
    if path.exists():
        raise ValueError(f'output already exists: {path}; choose a new path to preserve evidence')
    return path


def _write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        stream.write(canonical_json(value))


def _unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key]=value
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description='Source-backed NGC/MAPEOGEO computational qualification and tetrahedral count analysis.')
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run',help='Run the complete frozen computational campaign')
    run.add_argument('--seed',type=int,default=20261022)
    run.add_argument('--out',required=True,help='New or empty directory for complete evidence')
    generate=sub.add_parser('generate',help='Generate explicitly synthetic counts and separate evaluator truth')
    generate.add_argument('--seed',type=int,default=20261022)
    generate.add_argument('--out',required=True,help='New observations JSON path')
    generate.add_argument('--truth-out',required=True,help='Different new evaluator-only truth JSON path')
    generate.add_argument('--cases',type=int,default=128)
    generate.add_argument('--shots',type=int,default=65536)
    analyze=sub.add_parser('analyze',help='Calibrate and predict from synthetic or experimental count JSON')
    analyze.add_argument('--input',required=True)
    analyze.add_argument('--out',required=True,help='New analysis JSON path')
    ablations_cmd=sub.add_parser('ablations',help='Run controlled geometric ablation experiments')
    ablations_cmd.add_argument('--seed',type=int,default=20261022)
    ablations_cmd.add_argument('--out',required=True,help='New ablations JSON path')
    cuda_joint_cmd=sub.add_parser('cuda-joint',help='Execute Bell states, GHZ states, and CHSH on GPU')
    cuda_joint_cmd.add_argument('--library',default='build/ngc_rcs_geometric.dll',help='Path to compiled CUDA library')
    cuda_joint_cmd.add_argument('--phase-bins',type=int,default=48)
    cuda_joint_cmd.add_argument('--out',required=True,help='New CUDA joint JSON path')
    args=parser.parse_args(argv)
    try:
        if args.command=='run':
            from .campaign import run_campaign
            result=run_campaign(args.seed,output_dir=args.out,progress=lambda stage:print(f'Running {stage}',flush=True))
            print(f"{'PASS' if result['qualified'] else 'FAIL'}: {sum(g['passed'] for g in result['gates'])}/{len(result['gates'])} computational gates; evidence: {args.out}")
            return 0 if result['qualified'] else 1
        if args.command=='generate':
            from .synthetic import generate_dataset
            observations_path,truth_path=_new_path(args.out),_new_path(args.truth_out)
            if observations_path.resolve()==truth_path.resolve():
                raise ValueError('observations and truth paths must differ')
            observations,truth=generate_dataset(args.seed,case_count=args.cases,shots=args.shots)
            _write_new(observations_path,observations)
            _write_new(truth_path,truth)
            print(f'Synthetic observations: {observations_path}; separate evaluator truth: {truth_path}')
            return 0
        if args.command=='ablations':
            from .ablations import run_all_ablations
            out_path=_new_path(args.out)
            res=run_all_ablations(args.seed)
            _write_new(out_path,res)
            print(f"Executed 5 controlled geometric ablations; output: {out_path}")
            return 0
        if args.command=='cuda-joint':
            from .cuda_joint import run_gpu_chsh_test, run_gpu_ghz_test
            out_path=_new_path(args.out)
            chsh_res=run_gpu_chsh_test(args.library,phase_bins=args.phase_bins)
            ghz3_res=run_gpu_ghz_test(args.library,num_qubits=3,phase_bins=args.phase_bins)
            ghz4_res=run_gpu_ghz_test(args.library,num_qubits=4,phase_bins=args.phase_bins)
            combined={'device':chsh_res['device'],'phase_bins':args.phase_bins,'chsh':chsh_res['chsh'],
                      'angular_curve_samples':len(chsh_res['angular_curve']['sweep_samples']),
                      'ghz_3qubit':ghz3_res,'ghz_4qubit':ghz4_res}
            _write_new(out_path,combined)
            print(f"Executed native GPU joint/CHSH/GHZ campaign (CHSH S={chsh_res['chsh']['S_measured']:.6f}); output: {out_path}")
            return 0
        from .observations import analyze_dataset
        output=_new_path(args.out)
        payload=json.loads(Path(args.input).read_text(encoding='utf-8'),object_pairs_hook=_unique_object)
        result=analyze_dataset(payload)
        _write_new(output,result)
        print(f"Analyzed {len(result['cases'])} {result['data_kind']} records; mean verification TV={result['mean_verification_total_variation']:.6f}; output: {output}")
        return 0
    except (ValueError,TypeError,OSError) as exc:
        print(f'error: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
