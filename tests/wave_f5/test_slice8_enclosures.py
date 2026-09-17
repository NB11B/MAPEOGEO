"""Slice 8 Tests: Validated Enclosures, Exact Rational Bounds & Solution Tubes (Q15–Q18)."""

import pytest
from fractions import Fraction
from mapeogeo.wave_f5.enclosures import (
    RationalInterval,
    rational_exp_enclosure,
    rational_exp_upper_bound,
    verify_q15_residual_enclosure,
    verify_q16_logistic_invariant_interval,
    verify_q17_transversal_event,
    verify_q18_regular_dirichlet_bvp,
)


def test_rational_interval_operations():
    i1 = RationalInterval(Fraction(1, 2), Fraction(2, 1))
    i2 = RationalInterval(Fraction(1, 4), Fraction(3, 4))
    i_sum = i1 + i2
    assert i_sum.low == Fraction(3, 4) and i_sum.high == Fraction(11, 4)
    assert i1.contains(Fraction(1, 1))
    assert not i1.contains(Fraction(3, 1))


def test_rational_exp_enclosure_rigor():
    # Enclose exp(1/2): true value e^(1/2) approx 1.64872127...
    encl = rational_exp_enclosure(Fraction(1, 2), order=6)
    assert encl.low <= encl.high
    assert float(encl.low) <= 1.6487212707
    assert float(encl.high) >= 1.6487212707
    assert float(encl.width) < 1e-3


def test_q15_residual_enclosure():
    # y' = y, y(0)=1, approx order 3: y_hat = 1 + t + t^2/2 + t^3/6
    # Residual r(t) = -t^3/6. On [0, 1/2], exact sup|r| = (1/8)/6 = 1/48
    h = Fraction(1, 2)
    R_true = (h ** 3) / 6  # 1/48
    res_pos = verify_q15_residual_enclosure(h=h, degree=3, e0=Fraction(0), claimed_R=R_true)
    assert res_pos["verified"] is True
    assert res_pos["tube_radius"] > Fraction(0)
    assert isinstance(res_pos["tube_radius"], Fraction)

    # Falsification 1: underestimated residual (claimed_R < R_true)
    res_under = verify_q15_residual_enclosure(h=h, degree=3, e0=Fraction(0), claimed_R=R_true / 2)
    assert res_under["verified"] is False
    assert "underestimated residual" in res_under["error"].lower()

    # Falsification 2: missing/ignored initial error (e.g. e0 = 1/10 passed)
    res_e0 = verify_q15_residual_enclosure(h=h, degree=3, e0=Fraction(1, 10), claimed_R=R_true)
    assert res_e0["verified"] is True
    assert res_e0["tube_radius"] > res_pos["tube_radius"]


def test_q16_logistic_invariant_interval():
    # Logistic x' = x(1-x). Invariant interval [0, 1]
    res_pos = verify_q16_logistic_invariant_interval(
        initial_box=RationalInterval(Fraction(1, 10), Fraction(9, 10)),
        invariant_box=RationalInterval(Fraction(0), Fraction(1)),
    )
    assert res_pos["verified"] is True
    assert res_pos["invariant"] is True

    # Falsification: initial box outside invariant region (e.g. [-1/10, 1/2])
    res_out = verify_q16_logistic_invariant_interval(
        initial_box=RationalInterval(Fraction(-1, 10), Fraction(1, 2)),
        invariant_box=RationalInterval(Fraction(0), Fraction(1)),
    )
    assert res_out["verified"] is False
    assert "not subset" in res_out["error"].lower() or "boundary" in res_out["error"].lower()


def test_q17_transversal_event():
    # x' = 1, x(0)=0. Event H(x) = x - 1 = 0.
    # Flow: x(t) = t. On time interval [t_a, t_b] = [3/4, 5/4],
    # H(x(3/4)) = 3/4 - 1 = -1/4 < 0
    # H(x(5/4)) = 5/4 - 1 = +1/4 > 0
    # Lie derivative L_f H = nabla H . f = 1 . 1 = 1 >= 1 > 0 across tube [3/4, 5/4].
    res_pos = verify_q17_transversal_event(
        H_func=lambda x: x - Fraction(1),
        grad_H_func=lambda x: Fraction(1),
        f_func=lambda t, x: Fraction(1),
        trajectory_enclosure=lambda t: RationalInterval(t - Fraction(1, 100), t + Fraction(1, 100)),
        t_interval=RationalInterval(Fraction(3, 4), Fraction(5, 4)),
        x_interval=RationalInterval(Fraction(7, 10), Fraction(13, 10)),
    )
    assert res_pos["verified"] is True
    assert res_pos["transversal"] is True
    assert res_pos["crossing_isolated"] is True

    # Falsification 1: tangential event where Lie derivative vanishes at x=1
    res_tan = verify_q17_transversal_event(
        H_func=lambda x: x - Fraction(1),
        grad_H_func=lambda x: Fraction(1),
        f_func=lambda t, x: (x - Fraction(1)) ** 2,
        trajectory_enclosure=lambda t: RationalInterval(t, t),
        t_interval=RationalInterval(Fraction(3, 4), Fraction(5, 4)),
        x_interval=RationalInterval(Fraction(7, 10), Fraction(13, 10)),
    )
    assert res_tan["verified"] is False
    assert "transversality" in res_tan["error"].lower() or "tangential" in res_tan["error"].lower()

    # Falsification 2: non-crossing interval (H has same sign at both ends, e.g. [0, 1/2])
    res_no_cross = verify_q17_transversal_event(
        H_func=lambda x: x - Fraction(1),
        grad_H_func=lambda x: Fraction(1),
        f_func=lambda t, x: Fraction(1),
        trajectory_enclosure=lambda t: RationalInterval(t, t),
        t_interval=RationalInterval(Fraction(0), Fraction(1, 2)),
        x_interval=RationalInterval(Fraction(0), Fraction(1, 2)),
    )
    assert res_no_cross["verified"] is False
    assert "sign change" in res_no_cross["error"].lower() or "bracket" in res_no_cross["error"].lower()


def test_q18_regular_dirichlet_bvp():
    # -u'' = 2 on [0, 1], u(0)=0, u(1)=0. Exact solution u(x) = x - x^2.
    # Polynomial coefficients: u(x) = 0 + 1*x - 1*x^2
    # Symbolic differentiation: u'(x) = 1 - 2x, u''(x) = -2, -u''(x) = 2 == f(x).
    res_pos = verify_q18_regular_dirichlet_bvp(
        u_poly_coeffs=[Fraction(0), Fraction(1), Fraction(-1)],  # 0 + x - x^2
        f_poly_coeffs=[Fraction(2)],                             # constant 2
        bc_0=Fraction(0),
        bc_1=Fraction(0),
    )
    assert res_pos["verified"] is True
    assert res_pos["bc_satisfied"] is True
    assert res_pos["ode_satisfied_symbolic"] is True

    # Falsification 1: boundary mismatch (e.g. u(x) = x - x^2 + 1/2 -> u(0)=1/2 != 0)
    res_bc_fail = verify_q18_regular_dirichlet_bvp(
        u_poly_coeffs=[Fraction(1, 2), Fraction(1), Fraction(-1)],
        f_poly_coeffs=[Fraction(2)],
        bc_0=Fraction(0),
        bc_1=Fraction(0),
    )
    assert res_bc_fail["verified"] is False
    assert "boundary" in res_bc_fail["error"].lower()

    # Falsification 2: ODE mismatch (e.g. u(x) = x - x^3 -> -u'' = 6x != 2)
    res_ode_fail = verify_q18_regular_dirichlet_bvp(
        u_poly_coeffs=[Fraction(0), Fraction(1), Fraction(0), Fraction(-1)],
        f_poly_coeffs=[Fraction(2)],
        bc_0=Fraction(0),
        bc_1=Fraction(0),
    )
    assert res_ode_fail["verified"] is False
    assert "ode" in res_ode_fail["error"].lower() or "differential equation" in res_ode_fail["error"].lower()
