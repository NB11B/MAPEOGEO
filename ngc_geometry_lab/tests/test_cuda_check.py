"""CPU boundary tests only: these are not native GPU qualification evidence."""
import contextlib
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
from numpy.testing import assert_allclose

from ngc_geometry_lab import cuda_check as cuda
from ngc_geometry_lab import reference


class CudaBoundaryTests(unittest.TestCase):
    def test_quantization_phase_bins_respects_source_signed_integer_limit(self):
        self.assertEqual(cuda.quantize_angle(math.pi,2**30),math.pi)
        with self.assertRaises(ValueError): cuda.quantize_angle(math.pi,2**30+1)

    def test_run_phase_bins_respects_source_signed_integer_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing=Path(tmp)/'absent.so'
            self.assertEqual(cuda.run_check(missing,phase_bins=2**30)['status'],'NOT_RUN')
            with self.assertRaises(ValueError): cuda.run_check(missing,phase_bins=2**30+1)

    def test_cli_phase_bins_respects_source_signed_integer_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing=Path(tmp)/'absent.so'
            out=Path(tmp)/'accepted.json'
            rejected=Path(tmp)/'rejected.json'
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cuda.main(['--library',str(missing),'--phase-bins',str(2**30),'--out',str(out)]),2)
                with self.assertRaises(SystemExit) as error:
                    cuda.main(['--library',str(missing),'--phase-bins',str(2**30+1),'--out',str(rejected)])
            self.assertEqual(error.exception.code,2)
            self.assertEqual(json.loads(out.read_text())['phase_bins'],2**30)
            self.assertFalse(rejected.exists())

    def test_quantization_immediately_below_half_bin_does_not_round_up(self):
        for bins in (4,8):
            tie=math.pi/bins
            angle=math.nextafter(tie,0)
            scaled=bins*(angle/(2*math.pi))
            self.assertLess(scaled,.5)
            self.assertEqual(cuda.quantize_angle(angle,bins),0)
            self.assertEqual(cuda.quantize_angle(tie,bins),2*math.pi/bins)

    def test_cpu_fault_injection_preserves_failure_before_approximation_overflow(self):
        """Mock protocol/error handling only; no CUDA library/device/kernel runs."""
        class FaultAPI:
            def __init__(self,value):
                self.value=value
                self.free_count=0

            def call(self,name,*args):
                if name=='ngc_rcs_create':
                    args[-1]._obj.value=1
                if name=='ngc_rcs_free':
                    self.free_count += 1

            def read(self,handle,size):
                return np.full(size,self.value,dtype=complex),np.full(size,1e308)

        for value in (1e308,complex(1.7e308,1.7e308)):
            with self.subTest(value=value):
                api=FaultAPI(value)
                report={'gate_count':0,'test_scope':'CPU_FAULT_INJECTION_NO_GPU'}
                cuda._run_native(api,report,20261022,48)
                self.assertEqual(report['status'],'FAIL')
                self.assertEqual(api.free_count,1)
                self.assertEqual(len(report['records']),1)
                self.assertNotIn('continuous_target_fidelity',report['records'][0])
                json.dumps(report,allow_nan=False)

    def test_quantization_positive_negative_ties_and_wrap(self):
        # Eight bins give exact analytic quarter/half-bin inputs; do not use round().
        for angle, expected_bin in ((0,0),(math.pi/4,1),(-math.pi/4,7),
                                    (math.pi/8,1),
                                    (3*math.pi/8,2),(2*math.pi,0),
                                    (2*math.pi-math.pi/16,0),(-2*math.pi,0)):
            with self.subTest(angle=angle):
                self.assertAlmostEqual(cuda.quantize_angle(angle,8),expected_bin*math.pi/4)
        # Four-bin ties remain exact through the source's floating normalization.
        self.assertAlmostEqual(cuda.quantize_angle(math.pi/4,4),math.pi/2)
        self.assertEqual(cuda.quantize_angle(-math.pi/4,4),0)
        # At eight bins, normalized -pi/8 is just below the mathematical tie.
        self.assertAlmostEqual(cuda.quantize_angle(-math.pi/8,8),7*math.pi/4)

    def test_quantization_rejects_invalid_arguments(self):
        for angle,bins in ((math.nan,48),(math.inf,48),(1j,48),([0],48),
                           (0,0),(0,-1),(0,1.5),(0,True),(0,2**31)):
            with self.subTest(angle=angle,bins=bins), self.assertRaises(ValueError):
                cuda.quantize_angle(angle,bins)

    def test_lsb_target_mapping_with_analytic_basis_states(self):
        for n in range(1,6):
            for q in range(n):
                target=cuda.reference_target(q,n)
                self.assertEqual(target,n-1-q)
                state=np.zeros(2**n,complex); state[0]=1
                result=reference.local_gate(state,reference.paulis()[1],[target],n)
                expected=np.zeros(2**n,complex); expected[1 << q]=1
                assert_allclose(result,expected,atol=1e-15)

    def test_target_mapping_rejects_out_of_range_and_noninteger(self):
        for q,n in ((-1,3),(3,3),(0,0),(1.5,3),(True,3),(0,True),(0,2.5)):
            with self.subTest(q=q,n=n),self.assertRaises(ValueError): cuda.reference_target(q,n)

    def test_missing_library_is_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=cuda.run_check(Path(tmp)/'absent.so')
        self.assertEqual(report['status'],'NOT_RUN')
        self.assertEqual(report['native_execution'],'NOT_RUN')
        self.assertEqual(report['gate_count'],0)
        self.assertIn('reason',report)

    def test_run_configuration_validation(self):
        for kwargs in ({'seed':-1},{'seed':True},{'seed':2**64},{'phase_bins':0},{'phase_bins':1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): cuda.run_check('absent.so',**kwargs)

    def test_probe_is_diagnostic_not_a_native_test(self):
        report=cuda.probe_environment()
        self.assertEqual(report['status'],'NOT_RUN')
        self.assertEqual(report['native_execution'],'NOT_RUN')
        self.assertIn('nvcc',report)
        self.assertIn('nvidia_smi',report)
        self.assertTrue(report['source_snapshot']['matches_pinned'])

    def test_cli_probe_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'probe.json'
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cuda.main(['--probe','--out',str(out)]),0)
                original=out.read_bytes()
                self.assertEqual(cuda.main(['--probe','--out',str(out)]),2)
            self.assertEqual(out.read_bytes(),original)
            self.assertEqual(json.loads(original)['status'],'NOT_RUN')

    def test_cli_missing_library_nonzero_and_invalid_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'missing.json'
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cuda.main(['--library',str(Path(tmp)/'absent.so'),'--out',str(out)]),2)
                for args in (['--out',str(out)],['--probe','--library','x','--out',str(out)],
                             ['--probe','--phase-bins','0','--out',str(out)]):
                    with self.assertRaises(SystemExit) as error: cuda.main(args)
                    self.assertEqual(error.exception.code,2)
            self.assertEqual(json.loads(out.read_text())['native_execution'],'NOT_RUN')


if __name__=='__main__': unittest.main()
