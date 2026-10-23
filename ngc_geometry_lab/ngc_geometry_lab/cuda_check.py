"""Optional native CUDA qualification; CPU diagnostics never count as GPU runs."""
import argparse
import ctypes as ct
import hashlib
import json
import math
from numbers import Integral, Real
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

from . import reference

_SOURCE = Path(__file__).parent / '_vendor' / 'ngc_cuda_2' / 'cuda'
_HASHES = {'ngc_rcs_geometric.cu':'e9ef40c34398eaeeb4d0a11f567495042b56b9855e233a6812c16b1d9c5515c4',
           'ngc_rcs_api.h':'bc62266586146096a14f70c5f0779fbf6e3928be0f8b4ba9a97b41db557267ce'}
_COMMIT = 'e825ade2c033ffb9d83a4cd4f89252136443664b'
_TOL = 1e-10
# Source adds n_bins to k % n_bins in signed int: 2*n_bins-1 must fit.
_MAX_PHASE_BINS = 2**30


def _integer(value,name,minimum,maximum):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,Integral) or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return int(value)


def quantize_angle(angle, phase_bins=48):
    """Original C++ fmod, nonnegative round-half-away-from-zero, modulo bins.

    Normalization precedes rounding, so a negative half-bin near zero wraps
    around to the last positive tie and then to bin zero. Python round uses
    ties-to-even and is deliberately not used.
    """
    bins=_integer(phase_bins,'phase_bins',1,_MAX_PHASE_BINS)
    if isinstance(angle,(bool,np.bool_)) or not isinstance(angle,Real) or not math.isfinite(angle):
        raise ValueError('angle must be a finite real scalar')
    norm=math.fmod(float(angle),2*math.pi)
    if norm < 0:
        norm += 2*math.pi
    scaled=bins*(norm/(2*math.pi))
    lower=math.floor(scaled)
    # Adding .5 first can round a value immediately below a half-integer
    # up to an integer, unlike C++ round. Compare the fractional part instead.
    k=(lower+int(scaled-lower >= .5)) % bins
    return (2*math.pi*k)/bins


def reference_target(qubit, num_qubits):
    """Map source least-significant-bit qubits to big-endian tensor targets."""
    n=_integer(num_qubits,'num_qubits',1,30)
    q=_integer(qubit,'qubit',0,n-1)
    return n-1-q


def _source_snapshot():
    observed={}
    for name in _HASHES:
        path=_SOURCE/name
        observed[name]=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return {'commit':_COMMIT,'sha256':observed,'matches_pinned':observed == _HASHES}


def _command_probe(executable, arguments):
    path=shutil.which(executable)
    if path is None:
        return {'available':False,'executable':None,'returncode':None,'output':''}
    try:
        result=subprocess.run([path,*arguments],capture_output=True,text=True,timeout=10,check=False)
        return {'available':result.returncode == 0,'executable':path,'returncode':result.returncode,
                'output':(result.stdout+result.stderr).strip()[:4096]}
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {'available':False,'executable':path,'returncode':None,'output':str(exc)}


def probe_environment():
    """Record observed tool/device inventory; this never runs native kernels."""
    return {'status':'NOT_RUN','native_execution':'NOT_RUN','gate_count':0,
            'reason':'Diagnostic inventory only; no compiled library or kernels executed.',
            'nvcc':_command_probe('nvcc',['--version']),
            'nvidia_smi':_command_probe('nvidia-smi',['--query-gpu=name,driver_version','--format=csv,noheader']),
            'source_snapshot':_source_snapshot()}


class _NativeUnavailable(RuntimeError):
    pass


class _API:
    """Exact simple signatures from the pinned header; no profiling structs."""
    def __init__(self,path):
        self.library=ct.CDLL(str(path))
        pointer=ct.POINTER(ct.c_double)
        signatures={
            'ngc_rcs_create':[ct.c_int,ct.c_int,ct.POINTER(ct.c_void_p)],
            'ngc_rcs_free':[ct.c_void_p], 'ngc_rcs_reset':[ct.c_void_p],
            'ngc_rcs_rx':[ct.c_void_p,ct.c_int,ct.c_double],
            'ngc_rcs_rz':[ct.c_void_p,ct.c_int,ct.c_double],
            'ngc_rcs_cz':[ct.c_void_p,ct.c_int,ct.c_int],
            'ngc_rcs_get_probabilities':[ct.c_void_p,pointer],
            'ngc_rcs_get_statevector':[ct.c_void_p,pointer,pointer],
            'ngc_rcs_set_phase_resolution':[ct.c_void_p,ct.c_int],
            'ngc_get_device_info':[ct.POINTER(ct.c_char),ct.c_size_t,ct.POINTER(ct.c_size_t),ct.POINTER(ct.c_size_t)]}
        for name,args in signatures.items():
            function=getattr(self.library,name)
            function.argtypes=args
            function.restype=ct.c_int

    def call(self,name,*args):
        code=getattr(self.library,name)(*args)
        if code != 0:
            raise RuntimeError(f'{name} returned error {code}')

    def device(self):
        name=ct.create_string_buffer(256)
        total,free=ct.c_size_t(),ct.c_size_t()
        code=self.library.ngc_get_device_info(name,len(name),ct.byref(total),ct.byref(free))
        if code != 0:
            raise _NativeUnavailable(f'ngc_get_device_info returned {code}; no usable native device')
        return {'name':name.value.decode('utf-8',errors='replace'),'total_memory_bytes':total.value,
                'free_memory_bytes':free.value,'diagnostic_return':code}

    def read(self,handle,size):
        real,imag,probabilities=[np.full(size,np.nan,dtype=np.float64) for _ in range(3)]
        pointer=ct.POINTER(ct.c_double)
        # Source probability getter synchronizes its stream. Call it first:
        # the statevector getter itself uses a synchronous default-stream copy.
        self.call('ngc_rcs_get_probabilities',handle,probabilities.ctypes.data_as(pointer))
        self.call('ngc_rcs_get_statevector',handle,real.ctypes.data_as(pointer),imag.ctypes.data_as(pointer))
        if not all(np.all(np.isfinite(a)) for a in (real,imag,probabilities)):
            raise RuntimeError('native output contained nonfinite or unwritten values')
        return real+1j*imag,probabilities


def _reference_step(state,gate,n,angle):
    targets=[reference_target(q,n) for q in gate['qubits']]
    if gate['kind']=='CZ':
        matrix=np.diag([1.,1,1,-1])
    else:
        axis=[1,0,0] if gate['kind']=='RX' else [0,0,1]
        matrix=reference.rotation_unitary(axis,angle)
    return reference.local_gate(state,matrix,targets,n)


def _run_native(api,report,seed,bins):
    rng=np.random.default_rng(seed)
    records=[]
    max_state=max_probability=0.
    for n in range(1,6):
        handle=ct.c_void_p()
        try:
            api.call('ngc_rcs_create',n,0,ct.byref(handle))
            if not handle.value:
                raise RuntimeError('create returned a null handle')
            api.call('ngc_rcs_set_phase_resolution',handle,bins)
            api.call('ngc_rcs_reset',handle)
            quantized=np.zeros(2**n,complex); quantized[0]=1
            continuous=quantized.copy()
            # Include reset as a checked state in addition to all 120 gates.
            for step in range(-1,24):
                gate=None
                if step >= 0:
                    kind=('RX','RZ','CZ')[step%3]
                    if n==1 and kind=='CZ':
                        kind='RX'
                    qubits=[int(rng.integers(n))]
                    if kind=='CZ':
                        qubits.append(int(rng.choice([q for q in range(n) if q != qubits[0]])))
                    angle=float(rng.uniform(-4*math.pi,4*math.pi)) if kind != 'CZ' else 0.
                    effective=quantize_angle(angle,bins) if kind != 'CZ' else 0.
                    gate={'kind':kind,'qubits':qubits,'angle':angle,'quantized_angle':effective}
                    if kind=='CZ':
                        api.call('ngc_rcs_cz',handle,*qubits)
                    else:
                        api.call('ngc_rcs_'+kind.lower(),handle,qubits[0],angle)
                    report['gate_count'] += 1
                    quantized=_reference_step(quantized,gate,n,effective)
                    continuous=_reference_step(continuous,gate,n,angle)
                native,probabilities=api.read(handle,2**n)
                with np.errstate(over='ignore',invalid='ignore'):
                    state_error=float(np.max(np.abs(native-quantized)))
                    probability_error=float(np.max(np.abs(probabilities-np.abs(quantized)**2)))
                metrics_finite=math.isfinite(state_error) and math.isfinite(probability_error)
                record={'num_qubits':n,'step':step,'gate':gate,
                        'quantized_state_max_abs_error':state_error if math.isfinite(state_error) else None,
                        'quantized_probability_max_abs_error':probability_error if math.isfinite(probability_error) else None,
                        'comparison_metrics_finite':metrics_finite}
                records.append(record)
                report['records']=records
                # Preserve a JSON-safe failure before squaring native amplitudes
                # for approximation diagnostics. Finite corrupt outputs can be huge.
                if not metrics_finite:
                    report.update(status='FAIL',reason='Native comparison metrics were nonfinite; continuous approximation was not evaluated.')
                    return
                if state_error > _TOL or probability_error > _TOL:
                    report.update(status='FAIL',reason='Native mismatch against phase-quantized independent reference; continuous approximation was not evaluated.')
                    return
                max_state=max(max_state,state_error)
                max_probability=max(max_probability,probability_error)
                with np.errstate(over='ignore',invalid='ignore'):
                    overlap=abs(np.vdot(continuous,native))
                    fidelity=float(overlap**2)
                    # Phase-invariant distance from the continuous target is
                    # separate from strict quantized numerical equivalence.
                    distance_squared=float(np.vdot(native,native).real+np.vdot(continuous,continuous).real-2*overlap)
                    continuous_probability_error=float(np.max(np.abs(probabilities-np.abs(continuous)**2)))
                if not all(math.isfinite(value) for value in (fidelity,distance_squared,continuous_probability_error)):
                    record['continuous_approximation_status']='NONFINITE'
                    report.update(status='FAIL',reason='Continuous approximation metrics were nonfinite.')
                    return
                record.update(continuous_target_fidelity=fidelity,
                              continuous_target_phase_invariant_distance=math.sqrt(max(0.,distance_squared)),
                              continuous_target_probability_max_abs_difference=continuous_probability_error)
        finally:
            if handle.value:
                api.call('ngc_rcs_free',handle)
    report.update(status='PASS',quantized_equivalence={'tolerance':_TOL,'max_state_error':max_state,
                  'max_probability_error':max_probability},
                  continuous_approximation={'minimum_fidelity':min(r['continuous_target_fidelity'] for r in records),
                  'maximum_phase_invariant_distance':max(r['continuous_target_phase_invariant_distance'] for r in records)},
                  reason='Native outputs matched quantized reference; continuous-target approximation is reported separately.')


def run_check(library, *, seed=20261022, phase_bins=48):
    """Execute native kernels only; never substitute a CPU candidate backend."""
    seed=_integer(seed,'seed',0,2**64-1)
    bins=_integer(phase_bins,'phase_bins',1,_MAX_PHASE_BINS)
    report={'status':'NOT_RUN','native_execution':'NOT_RUN','gate_count':0,'seed':seed,
            'phase_bins':bins,'source_snapshot':_source_snapshot(),
            'binary_provenance':'Caller-supplied build; binary hash is not cryptographic proof of source origin.',
            'tensor_mapping':'CUDA LSB qubit q maps to reference big-endian target n-1-q.'}
    try:
        path=Path(library).expanduser().resolve()
        report['library']=str(path)
        if not report['source_snapshot']['matches_pinned']:
            raise _NativeUnavailable('Local CUDA source/header hashes differ from pinned snapshot.')
        if not path.is_file():
            raise _NativeUnavailable(f'Compiled library does not exist: {path}')
        report['binary_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            api=_API(path)
        except (OSError,AttributeError) as exc:
            raise _NativeUnavailable(f'Unable to load native CUDA ABI: {exc}') from exc
        report['device']=api.device()
        report['native_execution']='ATTEMPTED'
        _run_native(api,report,seed,bins)
        report['native_execution']='EXECUTED'
    except _NativeUnavailable as exc:
        report['reason']=str(exc)
    except (OSError,ValueError,RuntimeError) as exc:
        report.update(status='ERROR',reason=str(exc))
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--library',type=Path)
    mode.add_argument('--probe',action='store_true')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20261022)
    parser.add_argument('--phase-bins',type=int,default=48)
    args=parser.parse_args(argv)
    try:
        _integer(args.seed,'seed',0,2**64-1)
        _integer(args.phase_bins,'phase_bins',1,_MAX_PHASE_BINS)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        # Exclusive creation prevents replacement even under concurrent invocations.
        with args.out.open('x',encoding='utf-8') as output:
            report=probe_environment() if args.probe else run_check(args.library,seed=args.seed,phase_bins=args.phase_bins)
            json.dump(report,output,indent=2,allow_nan=False)
            output.write('\n')
    except OSError as exc:
        print(f'Cannot create result: {exc}',file=sys.stderr)
        return 2
    print(f"{report['status']}: {args.out}")
    return 0 if args.probe or report['status']=='PASS' else 2


if __name__=='__main__':
    raise SystemExit(main())
