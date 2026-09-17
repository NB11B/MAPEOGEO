"""Slice 7 Tests: Initial Exact & Symbolic Contracts (Q01–Q14)."""

import json
import fractions
from fractions import Fraction
import numpy as np
import pytest
from pathlib import Path

from mapeogeo.wave_f5.operators import (
    verify_q01_contraction,
    verify_q02_adjoint,
    verify_q03_orthogonal_projection,
    verify_q04_neumann_series,
    verify_q05_spectral_decomposition,
)
from mapeogeo.wave_f5.ode import (
    verify_q06_picard_self_map,
    verify_q07_nonuniqueness,
    verify_q08_blowup,
    verify_q09_autonomous_flow,
    verify_q10_nonautonomous_evolution,
    verify_q11_lyapunov_stability,
    verify_q12_nonhyperbolic_stability,
    verify_q13_transient_growth,
    verify_q14_conservative_harmonic,
)

CONTRACTS_FILE = Path(__file__).resolve().parent.parent.parent / "formal" / "wave_f5" / "contracts.json"


def test_contracts_json_registered():
    assert CONTRACTS_FILE.exists(), "formal/wave_f5/contracts.json must exist"
    with open(CONTRACTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    contracts = data.get("contracts", {})
    for i in range(1, 19):
        q_id = f"Q{i:02d}"
        assert q_id in contracts, f"Contract {q_id} must be registered in contracts.json"


def test_q01_contraction_iteration():
    # Positive: T(x) = x/2 + 1 on [0, 2], q = 1/2, fixed point = 2
    res_pos = verify_q01_contraction(
        T=lambda x: Fraction(1, 2) * x + 1,
        interval=(Fraction(0), Fraction(2)),
        q=Fraction(1, 2),
        fixed_point=Fraction(2),
    )
    assert res_pos["verified"] is True
    assert res_pos["fixed_point"] == Fraction(2)

    # Falsification 1: q = 1 (not a contraction)
    res_q1 = verify_q01_contraction(
        T=lambda x: x,
        interval=(Fraction(0), Fraction(2)),
        q=Fraction(1),
        fixed_point=Fraction(1),
    )
    assert res_q1["verified"] is False
    assert "q < 1" in res_q1["error"]

    # Falsification 2: non-invariant interval (e.g. [0, 1] maps 1 to 3/2 > 1)
    res_non_inv = verify_q01_contraction(
        T=lambda x: Fraction(1, 2) * x + 1,
        interval=(Fraction(0), Fraction(1)),
        q=Fraction(1, 2),
        fixed_point=Fraction(2),
    )
    assert res_non_inv["verified"] is False
    assert "invariant" in res_non_inv["error"].lower()


def test_q02_finite_dimensional_adjoint():
    # Real 2x2 matrix under metric G
    A = np.array([[Fraction(1), Fraction(2)], [Fraction(0), Fraction(3)]])
    G = np.array([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(1)]])
    # A^* = G^{-1} A^T G
    # A^T = [[1, 0], [2, 3]]
    # A^T G = [[2, 0], [4, 3]]
    # G^{-1} A^T G = [[1, 0], [4, 3]]
    A_star = np.array([[Fraction(1), Fraction(0)], [Fraction(4), Fraction(3)]])

    res = verify_q02_adjoint(A=A, G=G, A_star=A_star)
    assert res["verified"] is True

    # Falsification: simple transpose without metric weighting G
    res_mut = verify_q02_adjoint(A=A, G=G, A_star=A.T)
    assert res_mut["verified"] is False
    assert "adjoint pairing" in res_mut["error"].lower()


def test_q03_orthogonal_projection():
    # Subspace in R^2: span([1, 1]^T)
    basis = [np.array([Fraction(1), Fraction(1)])]
    # P = v v^T / (v^T v) = [[1/2, 1/2], [1/2, 1/2]]
    P = np.array([[Fraction(1, 2), Fraction(1, 2)], [Fraction(1, 2), Fraction(1, 2)]])

    res = verify_q03_orthogonal_projection(P=P, basis=basis)
    assert res["verified"] is True

    # Falsification: oblique non-symmetric projection P = [[1, 1], [0, 0]]
    P_oblique = np.array([[Fraction(1), Fraction(1)], [Fraction(0), Fraction(0)]])
    res_obl = verify_q03_orthogonal_projection(P=P_oblique, basis=basis)
    assert res_obl["verified"] is False
    assert "symmetric" in res_obl["error"].lower() or "orthogonal" in res_obl["error"].lower()


def test_q04_neumann_series():
    # Matrix A with ||A||_1 = 1/2 < 1
    A = np.array([[Fraction(1, 4), Fraction(1, 4)], [Fraction(1, 8), Fraction(1, 8)]])
    res = verify_q04_neumann_series(A=A, N=5)
    assert res["verified"] is True
    assert res["tail_bound"] < Fraction(1, 100)

    # Falsification: matrix with norm >= 1
    A_large = np.array([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])
    res_large = verify_q04_neumann_series(A=A_large, N=5)
    assert res_large["verified"] is False
    assert "norm" in res_large["error"].lower() and ">= 1" in res_large["error"].lower()


def test_q05_spectral_decomposition():
    # Symmetric 2x2 matrix: A = [[2, 0], [0, 5]]
    A = np.array([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(5)]])
    eigenvalues = [Fraction(2), Fraction(5)]
    projectors = [
        np.array([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(0)]]),
        np.array([[Fraction(0), Fraction(0)], [Fraction(0), Fraction(1)]]),
    ]
    res = verify_q05_spectral_decomposition(A=A, eigenvalues=eigenvalues, projectors=projectors)
    assert res["verified"] is True

    # Falsification: dropped eigenspace (missing second projector)
    res_dropped = verify_q05_spectral_decomposition(A=A, eigenvalues=eigenvalues[:1], projectors=projectors[:1])
    assert res_dropped["verified"] is False
    assert "identity" in res_dropped["error"].lower() or "sum" in res_dropped["error"].lower()


def test_q06_picard_self_map():
    # y' = y, y(0)=1, t in [0, 1/4], r = 1/2, M = 3/2, L = 1
    # h = 1/4 -> h M = 3/8 <= 1/2 and h L = 1/4 < 1
    res = verify_q06_picard_self_map(h=Fraction(1, 4), M=Fraction(3, 2), L=Fraction(1), r=Fraction(1, 2))
    assert res["verified"] is True

    # Falsification: h = 1/2 -> h M = 3/4 > 1/2 (exits ball)
    res_exit = verify_q06_picard_self_map(h=Fraction(1, 2), M=Fraction(3, 2), L=Fraction(1), r=Fraction(1, 2))
    assert res_exit["verified"] is False
    assert "ball" in res_exit["error"].lower() or "self-map" in res_exit["error"].lower()


def test_q07_nonuniqueness():
    # Positive: existence confirmed, uniqueness FALSE (Peano nonuniqueness y' = 2 sqrt(|y|))
    res = verify_q07_nonuniqueness(claimed_unique=False, has_existence=True)
    assert res["verified"] is True

    # Falsification: asserting uniqueness on non-Lipschitz cusp
    res_fake_uniq = verify_q07_nonuniqueness(claimed_unique=True, has_existence=True)
    assert res_fake_uniq["verified"] is False
    assert "uniqueness" in res_fake_uniq["error"].lower()


def test_q08_blowup():
    # y' = y^2, y(0)=1, maximal interval (-inf, 1)
    res = verify_q08_blowup(t_eval=Fraction(1, 2), t_max=Fraction(1))
    assert res["verified"] is True

    # Falsification: certificate asserting evaluation at or past blow-up time t >= 1
    res_blow = verify_q08_blowup(t_eval=Fraction(1), t_max=Fraction(1))
    assert res_blow["verified"] is False
    assert "blow-up" in res_blow["error"].lower() or "maximal interval" in res_blow["error"].lower()


def test_q09_autonomous_flow():
    # Autonomous flow: Phi_t(x) = x / (1 - t x)
    def phi(t, x):
        return x / (Fraction(1) - t * x)

    res = verify_q09_autonomous_flow(
        phi=phi,
        x=Fraction(1, 2),
        s=Fraction(1, 4),
        t=Fraction(1, 4),
    )
    assert res["verified"] is True

    # Falsification: evaluation outside domain where tau * x >= 1 (e.g. x=2, t=1 -> 1*2 >= 1)
    with pytest.raises(ValueError):
        verify_q09_autonomous_flow(phi=phi, x=Fraction(2), s=Fraction(1, 2), t=Fraction(1))


def test_q10_nonautonomous_evolution():
    # Nonautonomous y' = t y -> U(t, s) = exp((t^2 - s^2)/2)
    # U(t, s) * U(s, r) == U(t, r)
    def U(t, s):
        return np.exp((t**2 - s**2) / 2.0)

    res = verify_q10_nonautonomous_evolution(
        U=U,
        t=2.0,
        s=1.0,
        r=0.0,
        is_time_homogeneous_claimed=False,
    )
    assert res["verified"] is True

    # Falsification: claiming time-homogeneity U(t, s) = Psi(t - s)
    res_homo = verify_q10_nonautonomous_evolution(
        U=U,
        t=2.0,
        s=1.0,
        r=0.0,
        is_time_homogeneous_claimed=True,
    )
    assert res_homo["verified"] is False
    assert "time-homogeneous" in res_homo["error"].lower()


def test_q11_lyapunov_stability():
    # A = diag(-1, -2), V = I -> A^T V + V A = diag(-2, -4) < 0
    A = np.array([[-1.0, 0.0], [0.0, -2.0]])
    V = np.eye(2)
    res = verify_q11_lyapunov_stability(A=A, V=V)
    assert res["verified"] is True

    # Falsification: indefinite V
    V_bad = np.array([[1.0, 0.0], [0.0, -1.0]])
    res_bad = verify_q11_lyapunov_stability(A=A, V=V_bad)
    assert res_bad["verified"] is False
    assert "positive-definite" in res_bad["error"].lower()


def test_q12_nonhyperbolic_stability():
    # x' = -x^3: asymptotically stable at 0, despite linearization A = 0
    res_cubic_neg = verify_q12_nonhyperbolic_stability(cubic_sign=-1, linear_eval_only=False)
    assert res_cubic_neg["verified"] is True
    assert res_cubic_neg["stable"] is True

    # Falsification: claiming stability determined solely from zero linear eigenvalue
    res_lin = verify_q12_nonhyperbolic_stability(cubic_sign=-1, linear_eval_only=True)
    assert res_lin["verified"] is False
    assert "inconclusive" in res_lin["error"].lower()


def test_q13_transient_growth():
    # A = [[-1, 10], [0, -2]] has eigenvalues -1, -2, but ||exp(t A)|| > 1 for small t > 0
    A = np.array([[-1.0, 10.0], [0.0, -2.0]])
    res = verify_q13_transient_growth(A=A, t_sample=0.1)
    assert res["verified"] is True
    assert res["transient_norm_growth"] > 1.0

    # Falsification: assert that monotonic norm decay holds for all t > 0
    res_false = verify_q13_transient_growth(A=A, t_sample=0.1, assert_monotonic_decay=True)
    assert res_false["verified"] is False
    assert "transient growth" in res_false["error"].lower()


def test_q14_conservative_harmonic():
    # Harmonic oscillator x' = v, v' = -x preserves E = (x^2 + v^2)/2
    trajectory = [
        (np.cos(t), np.sin(t)) for t in [0.0, np.pi / 4, np.pi / 2, np.pi]
    ]
    res = verify_q14_conservative_harmonic(trajectory=trajectory, claimed_asymptotic_stable=False)
    assert res["verified"] is True
    assert res["energy_conserved"] is True

    # Falsification: claiming asymptotic stability for conservative center
    res_asymp = verify_q14_conservative_harmonic(trajectory=trajectory, claimed_asymptotic_stable=True)
    assert res_asymp["verified"] is False
    assert "conservative" in res_asymp["error"].lower() or "asymptotic" in res_asymp["error"].lower()
