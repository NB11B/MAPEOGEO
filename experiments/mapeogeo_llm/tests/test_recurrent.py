import unittest
import torch
from experiments.mapeogeo_llm.recurrent.machine import (
    RecurrentMachineState, Value, gp_sign_blade, pauli_check_gp3, ALL_OPS
)
from experiments.mapeogeo_llm.recurrent.policy import (
    TransformerClausePolicy, WORD_IX, PAD
)
from experiments.mapeogeo_llm.recurrent.qualification import encode_clause

class TestRecurrentMachine(unittest.TestCase):
    def setUp(self):
        self.machine = RecurrentMachineState()

    def test_pauli_and_clifford_exact_match(self):
        for a in range(8):
            for b in range(8):
                sign_clifford, blade_clifford = gp_sign_blade(a, b)
                sign_pauli, blade_pauli = pauli_check_gp3(a, b)
                self.assertEqual((sign_clifford, blade_clifford), (sign_pauli, blade_pauli))

    def test_recurrent_arithmetic_step(self):
        self.machine.reset({"a": Value(kind="int", val=100), "b": Value(kind="int", val=50)})
        ok = self.machine.step("ADD", "a", "b", "R0")
        self.assertTrue(ok)
        self.assertEqual(self.machine.registers["R0"].val, 150)

    def test_recurrent_clifford_step(self):
        # e1 * e2 = e12 (sign=1, blade=3)
        self.machine.reset({"a": Value(kind="geo", val=(1, 1)), "b": Value(kind="geo", val=(1, 2))})
        ok = self.machine.step("GEO_GP3", "a", "b", "R0")
        self.assertTrue(ok)
        self.assertEqual(self.machine.registers["R0"].val, (1, 3))

    def test_fail_closed_precondition(self):
        # Type mismatch: arithmetic on geo
        self.machine.reset({"a": Value(kind="geo", val=(1, 1)), "b": Value(kind="int", val=10)})
        ok = self.machine.step("ADD", "a", "b", "R0")
        self.assertFalse(ok)
        self.assertTrue(self.machine.faulted)

    def test_policy_forward_shape(self):
        model = TransformerClausePolicy(d=32)
        clause_tok = torch.tensor([encode_clause("add a and b")])
        is_last = torch.tensor([0])
        h_prev = torch.zeros(1, 32)
        h_t, logits = model(clause_tok, is_last, h_prev)
        self.assertEqual(h_t.shape, (1, 32))
        self.assertEqual(len(logits), 5)

if __name__ == "__main__":
    unittest.main()
