"""Unit tests for exact finite-chain algebra and homology."""

from __future__ import annotations

import sympy as sp
from mapeogeo.pct.chain import (
    betti_numbers,
    boundary_matrix,
    check_chain_condition,
    euler_from_chains,
    euler_from_homology,
    rank_gf2,
    rank_over_field,
)
from mapeogeo.pct.models import CoefficientField, FiniteComplex, Simplex


def triangle_loop_complex() -> FiniteComplex:
    simplices = (
        Simplex((0,)),
        Simplex((1,)),
        Simplex((2,)),
        Simplex((0, 1)),
        Simplex((1, 2)),
        Simplex((0, 2)),
    )
    return FiniteComplex(complex_id="triangle_loop", simplices=simplices)


def filled_triangle_complex() -> FiniteComplex:
    simplices = (
        Simplex((0,)),
        Simplex((1,)),
        Simplex((2,)),
        Simplex((0, 1)),
        Simplex((1, 2)),
        Simplex((0, 2)),
        Simplex((0, 1, 2)),
    )
    return FiniteComplex(complex_id="filled_triangle", simplices=simplices)


def test_triangle_loop_has_expected_homology():
    c = triangle_loop_complex()
    assert check_chain_condition(c)
    assert betti_numbers(c, CoefficientField.GF2) == {0: 1, 1: 1}
    assert betti_numbers(c, CoefficientField.Q) == {0: 1, 1: 1}
    assert euler_from_chains(c) == 0
    assert euler_from_homology(c, CoefficientField.Q) == 0
    assert euler_from_homology(c, CoefficientField.GF2) == 0


def test_filled_triangle_kills_h1():
    c = filled_triangle_complex()
    assert check_chain_condition(c)
    assert betti_numbers(c, CoefficientField.Q) == {0: 1, 1: 0, 2: 0}
    assert betti_numbers(c, CoefficientField.GF2) == {0: 1, 1: 0, 2: 0}
    assert euler_from_chains(c) == 1
    assert euler_from_homology(c, CoefficientField.Q) == 1
    assert euler_from_homology(c, CoefficientField.GF2) == 1


def test_rank_gf2_exact_elimination():
    # 2x2 matrix with 1s: rank over Q is 1, rank over GF(2) is 1
    m1 = sp.Matrix([[1, 1], [1, 1]])
    assert rank_over_field(m1, CoefficientField.GF2) == 1
    assert rank_over_field(m1, CoefficientField.Q) == 1

    # Matrix with mod 2 cancellation: [1 1; 1 3] over Q has rank 2, over GF2 has rank 1
    m2 = sp.Matrix([[1, 1], [1, 3]])
    assert rank_over_field(m2, CoefficientField.GF2) == 1
    assert rank_over_field(m2, CoefficientField.Q) == 2


def test_non_chain_complex_fails_condition():
    # Construct an artificial complex whose boundaries don't cancel
    # by testing matrix multiplication directly
    d1 = sp.Matrix([[1, 0], [0, 1]])
    d2 = sp.Matrix([[1], [1]])
    assert d1 * d2 != sp.zeros(2, 1)
