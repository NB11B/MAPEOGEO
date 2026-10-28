import unittest
import torch
from experiments.mapeogeo_llm.operators import CompiledALU, to_bits, from_bits, reference, verify_exhaustive, OPS
from experiments.mapeogeo_llm.compositional import make_split, build_dataset, parse_program, execute

class TestOperators(unittest.TestCase):
    def setUp(self):
        self.alu = CompiledALU()

    def test_no_learnable_parameters(self):
        self.assertEqual(sum(p.numel() for p in self.alu.parameters()), 0)

    def test_exhaustive_verification(self):
        counts = verify_exhaustive(self.alu)
        for op in OPS:
            self.assertEqual(counts[op], 65536)

    def test_fail_closed_on_bad_inputs(self):
        # Non-binary inputs
        bad = torch.full((8, 2), 0.5, dtype=torch.float64)
        zero = torch.zeros((8, 2), dtype=torch.float64)
        with self.assertRaises(ValueError):
            self.alu("ADD", bad, zero)

    def test_parse_and_execute(self):
        env = {"a": 10, "b": 20, "c": 5}
        tokens = ["ADD", "a", "b", "SUB", "RES", "c"]
        prog = parse_program(tokens)
        self.assertEqual(prog, [("ADD", "a", "b"), ("SUB", "RES", "c")])
        res = execute(self.alu, prog, env)
        self.assertEqual(res, 25)

    def test_splits_disjoint(self):
        split = make_split(seed=42)
        dataset = build_dataset(split, seed=42, n_train=100, n_test=50)
        train_combos = set(split["train_combos"])
        for key in ("L2_heldout_pair", "L3_heldout_pair", "L3_unseen_triple", "L4_length"):
            for ex in dataset["test"][key]:
                self.assertNotIn(ex["combo"], train_combos)

if __name__ == "__main__":
    unittest.main()
