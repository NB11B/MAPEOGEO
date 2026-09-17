"""Slice 8 Tests: Validated Enclosures & Solution-Tube Certificates (Q15–Q18)."""

import numpy as np
import pytest
from fractions import Fraction
from mapeogeo.wave_f5.enclosures import (
    Interval,
    verify_q15_residual_enclosure,
    verify_q16_logistic_invariant_interval,
    verify_q17_transversal_event,
    verify_q18_regular_dirichlet_bvp,
)


def test_interval_operations():
    i1 = Interval(1.0, 2.0)
    i2 = Interval(0.5, 1.5)
    i_sum = i1 + i2
    assert i_sum.low == 1.5 and i_sum.high == 3.5
    assert i1.contains(1.5)
    assert not i1.contains(2.5)


def test_q15_residual_enclosure():
    # y' = y, y(0)=1, approx order 3: y_hat = 1 + t + t^2/2 + t^3/6
    # Residual r(t) = -t^3/6. On [0, 1/2], sup|r| = (1/8)/6 = 1/48
    h = Fraction(1, 2)
    R_true = (h ** 3) / 6  # 1/48
    res_pos = verify_q15_residual_enclosure(h=h, degree=3, e0=Fraction(0), claimed_R=R_true)
    assert res_pos["verified"] is True
    assert res_pos["tube_radius"] > 0

    # Falsification 1: underestimated residual (claimed_R < R_true)
    res_under = verify_q15_residual_enclosure(h=h, degree=3, e0=Fraction(0), claimed_R=R_true / 2)
    assert res_under["verified"] is False
    assert "underestimated residual" in res_under["error"].lower()

    # Falsification 2: missing/ignored initial error (e.g. e0 = 0.1 passed as 0)
    res_e0 = verify_q15_residual_enclosure(h=h, degree=3, e0=Fraction(1, 10), claimed_R=R_true)
    assert res_e0["verified"] is True
    # The tube radius with e0 > 0 must be strictly larger than with e0 == 0
    assert res_e0["tube_radius"] > res_pos["tube_radius"]


def test_q16_logistic_invariant_interval():
    # Logistic x' = x(1-x). Invariant interval [0, 1]
    res_pos = verify_q16_logistic_invariant_interval(
        initial_box=Interval(0.1, 0.9),
        invariant_box=Interval(0.0, 1.0),
    )
    assert res_pos["verified"] is True
    assert res_pos["invariant"] is True

    # Falsification: initial box outside invariant region (e.g. [-0.1, 0.5])
    res_out = verify_q16_logistic_invariant_interval(
        initial_box=Interval(-0.1, 0.5),
        invariant_box=Interval(0.0, 1.0),
    )
    assert res_out["verified"] is False
    assert "not subset" in res_out["error"].lower() or "boundary" in res_out["error"].lower()


def test_q17_transversal_event():
    # x' = 1, x(0)=0. Event H(x) = x - 1 = 0.
    # nabla H = 1, f = 1 -> nabla H . f = 1 > 0 (transversal)
    res_pos = verify_q17_transversal_event(
        grad_H=1.0,
        f_val=1.0,
        t_interval=Interval(0.8, 1.2),
        x_interval=Interval(0.8, 1.2),
    )
    assert res_pos["verified"] is True
    assert res_pos["transversal"] is True

    # Falsification: tangential event where nabla H . f == 0
    res_tan = verify_q17_transversal_event(
        grad_H=1.0,
        f_val=0.0,
        t_interval=Interval(0.8, 1.2),
        x_interval=Interval(0.8, 1.2),
    )
    assert res_tan["verified"] is False
    assert "transversality" in res_tan["error"].lower() or "tangential" in res_tan["error"].lower()


def test_q18_regular_dirichlet_bvp():
    # -u'' = 2 on [0, 1], u(0)=0, u(1)=0. Exact u(x) = x(1-x) = x - x^2.
    def u_exact(x):
        return x * (1.0 - x)

    def u_double_prime(x):
        return -2.0

    def f(x):
        return 2.0

    res_pos = verify_q18_regular_dirichlet_bvp(
        u_func=u_exact,
        u_xx_func=u_double_prime,
        f_func=f,
        bc_0=0.0,
        bc_1=0.0,
    )
    assert res_pos["verified"] is True

    # Falsification: boundary mismatch (e.g. u(1) = 0.5 != 0)
    res_bc_fail = verify_q18_regular_dirichlet_bvp(
        u_func=lambda x: x * (1.0 - x) + 0.5 * x,
        u_xx_func=u_double_prime,
        f_func=f,
        bc_0=0.0,
        bc_1=0.0,
    )
    assert res_bc_fail["verified"] is False
    assert "boundary" in res_bc_fail["error"].lower()
