"""Exact regression checks for the ETH-inspired contraction-search prototype."""
import unittest
from fractions import Fraction

from eth_contraction_search import Tensor, contract, symbolic_search, swap_tensor, singlet_identity_verified


class TestExactContraction(unittest.TestCase):
    def test_swap_identity(self):
        self.assertTrue(singlet_identity_verified())
        self.assertEqual(swap_tensor().at({"a": 0, "b": 1, "c": 1, "d": 0}), 1)

    def test_scalar(self):
        self.assertEqual(contract((Tensor((), (), (Fraction(7),)),)), 7)

    def test_trace(self):
        t = Tensor(("x", "x"), (2, 2), (Fraction(1), Fraction(2), Fraction(3), Fraction(4)))
        with self.assertRaises(AssertionError):
            Tensor(("x", "x"), (2, 2), t.values)

    def test_triangle(self):
        a = Tensor(("x", "y"), (2, 2), tuple(map(Fraction, (1, 2, 3, 4))))
        b = Tensor(("y", "z"), (2, 2), tuple(map(Fraction, (2, 0, 1, 3))))
        c = Tensor(("z", "x"), (2, 2), tuple(map(Fraction, (1, 1, 0, 2))))
        self.assertEqual(contract((a, b, c)), 29)
        self.assertGreater(symbolic_search((a, b, c))["estimated_scalar_operations"], 0)


if __name__ == "__main__":
    unittest.main()
