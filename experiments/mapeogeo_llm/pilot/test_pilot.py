import unittest
import torch
from pilot import OperatorMachine, Step, gp_sign_blade, train_controller, OPS, VOCAB

class PilotTests(unittest.TestCase):
    def setUp(self): self.machine=OperatorMachine()
    def test_examples(self):
        self.assertEqual(self.machine.run(Step('ADD8',250,10)), {'value':4})
        self.assertEqual(self.machine.run(Step('XOR8',170,85)), {'value':255})
        self.assertEqual(self.machine.run(Step('EQ8',81,81)), {'value':1})
        self.assertEqual(self.machine.run(Step('EQ8',81,82)), {'value':0})
    def test_clifford_anticommutation(self):
        self.assertEqual(self.machine.run(Step('GEO_GP3',1,2)),{'sign':1,'blade':3})
        self.assertEqual(self.machine.run(Step('GEO_GP3',2,1)),{'sign':-1,'blade':3})
    def test_clifford_signature(self):
        self.assertEqual(gp_sign_blade(1,1,(-1,1,1)),(-1,0))
    def test_disjoint_pair_training(self):
        from pilot import build_examples
        train,test=build_examples()
        a={(x[3],x[4]) for x in train};b={(x[3],x[4]) for x in test}
        self.assertFalse(a&b)
    def test_no_trainable_operator_weights(self):
        self.assertEqual(sum(p.numel() for p in self.machine.geo.parameters()),0)
        self.assertEqual(sum(p.numel() for p in self.machine.add.parameters()),0)
    def test_clifford_matches_pauli_representation(self):
        from pilot import reference_answer
        for a in range(8):
            for b in range(8):
                self.assertEqual(self.machine.run(Step('GEO_GP3',a,b)),reference_answer('GEO_GP3',a,b))
    def test_end_to_end_is_not_tautological(self):
        # A wrong controller must lower end-to-end accuracy below 1.0.
        from pilot import integration, build_examples, Controller
        _,test=build_examples()
        class Wrong(torch.nn.Module):
            def forward(self,w,x): return torch.tensor([[1.,0.,0.,0.]]).repeat(len(w),1)
        r=integration(Wrong(),test[:200])
        self.assertLess(r['end_to_end_rate'],0.5)
    def test_fail_closed(self):
        with self.assertRaises(ValueError): self.machine.run(Step('UNKNOWN',1,2))
        with self.assertRaises(ValueError): self.machine.run(Step('ADD8',256,2))
        with self.assertRaises(ValueError): self.machine.run(Step('GEO_GP3',8,2))
if __name__=='__main__':unittest.main()
