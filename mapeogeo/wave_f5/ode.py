"""Exact & Scoped ODE Contracts (Q06–Q14) for Wave F5."""

from fractions import Fraction
from typing import Any, Callable, Dict, List, Tuple
import numpy as np
from scipy.linalg import expm


def verify_q06_picard_self_map(
    h: Fraction,
    M: Fraction,
    L: Fraction,
    r: Fraction,
) -> Dict[str, Any]:
    """Verify Picard Operator Self-Map & Contraction (Q06)."""
    # Self-map condition: h * M <= r
    hM = h * M
    if hM > r:
        return {"verified": False, "error": f"Picard step h={h} violates self-map condition: h*M={hM} > ball radius r={r}"}

    # Contraction condition: h * L < 1
    hL = h * L
    if hL >= Fraction(1):
        return {"verified": False, "error": f"Picard step h={h} violates contraction condition: h*L={hL} >= 1"}

    return {
        "verified": True,
        "h": h,
        "hM": hM,
        "hL": hL,
        "error": None,
    }


def verify_q07_nonuniqueness(
    claimed_unique: bool,
    has_existence: bool,
) -> Dict[str, Any]:
    """Verify Nonuniqueness Boundary (Q07) for Peano Cusp y' = 2 sqrt(|y|)."""
    if claimed_unique:
        return {
            "verified": False,
            "error": "Uniqueness assertion rejected on non-Lipschitz cusp (Peano nonuniqueness example admits branching families)",
        }

    if not has_existence:
        return {"verified": False, "error": "Peano existence must hold on continuous vector field"}

    return {
        "verified": True,
        "existence": True,
        "uniqueness": False,
        "error": None,
    }


def verify_q08_blowup(
    t_eval: Fraction,
    t_max: Fraction,
) -> Dict[str, Any]:
    """Verify Continuation and Finite-Time Blow-Up Boundary (Q08)."""
    if t_eval >= t_max:
        return {
            "verified": False,
            "error": f"Evaluation time t={t_eval} crosses or reaches maximal interval boundary / finite-time blow-up t_max={t_max}",
        }

    # Explicit solution y(t) = 1 / (1 - t)
    y_val = Fraction(1) / (t_max - t_eval)
    return {
        "verified": True,
        "t_eval": t_eval,
        "y_val": y_val,
        "error": None,
    }


def verify_q09_autonomous_flow(
    phi: Callable[[Fraction, Fraction], Fraction],
    x: Fraction,
    s: Fraction,
    t: Fraction,
) -> Dict[str, Any]:
    """Verify Autonomous Flow Group Action (Q09): Phi_s(Phi_t(x)) = Phi_{s+t}(x) within maximal connected domain."""
    # Check connected domain condition for Phi_tau(x) = x / (1 - tau x)
    # Pole occurs at tau = 1/x (if x != 0). For path from 0 to t, s, s+t, tau*x must remain < 1.
    if x != 0:
        for tau in [t, s, s + t]:
            if tau * x >= Fraction(1):
                raise ValueError(f"Flow parameter tau={tau} exits connected existence domain (tau*x={tau*x} >= 1)")

    # Evaluate Phi_t(x)
    phi_t = phi(t, x)
    # Evaluate Phi_s(Phi_t(x))
    phi_s_phi_t = phi(s, phi_t)
    # Evaluate Phi_{s+t}(x)
    phi_st = phi(s + t, x)

    if phi_s_phi_t != phi_st:
        return {
            "verified": False,
            "error": f"Autonomous flow composition failed: Phi_s(Phi_t(x))={phi_s_phi_t} != Phi_{{s+t}}(x)={phi_st}",
        }

    return {
        "verified": True,
        "phi_s_phi_t": phi_s_phi_t,
        "phi_st": phi_st,
        "error": None,
    }


def verify_q10_nonautonomous_evolution(
    U: Callable[[float, float], float],
    t: float,
    s: float,
    r: float,
    is_time_homogeneous_claimed: bool = False,
) -> Dict[str, Any]:
    """Verify Nonautonomous Evolution Operator (Q10): U(t,s) U(s,r) = U(t,r)."""
    if is_time_homogeneous_claimed:
        return {
            "verified": False,
            "error": "Claimed time-homogeneous evolution law rejected: nonautonomous evolution operators require two-time parameterization U(t,s)",
        }

    # Check U(t, s) * U(s, r) == U(t, r)
    lhs = U(t, s) * U(s, r)
    rhs = U(t, r)
    if not np.isclose(lhs, rhs, atol=1e-12):
        return {"verified": False, "error": f"Evolution operator composition failed: U(t,s)U(s,r)={lhs} != U(t,r)={rhs}"}

    # Check identity U(t, t) == 1
    if not np.isclose(U(t, t), 1.0, atol=1e-12):
        return {"verified": False, "error": f"Identity law failed: U(t,t)={U(t,t)} != 1.0"}

    return {
        "verified": True,
        "U_ts_sr": lhs,
        "U_tr": rhs,
        "error": None,
    }


def verify_q11_lyapunov_stability(
    A: np.ndarray,
    V: np.ndarray,
) -> Dict[str, Any]:
    """Verify Lyapunov Stability for Linear System x' = A x with V(x) = x^T V x (Q11)."""
    # Check V is symmetric positive definite
    if not np.allclose(V, V.T):
        return {"verified": False, "error": "Lyapunov matrix V must be symmetric"}
    eig_V = np.linalg.eigvalsh(V)
    if np.any(eig_V <= 0):
        return {"verified": False, "error": f"Lyapunov matrix V must be positive-definite, got eigenvalues {eig_V}"}

    # Orbital derivative matrix: Q = A^T V + V A
    Q = np.dot(A.T, V) + np.dot(V, A)
    eig_Q = np.linalg.eigvalsh(Q)

    # For strict asymptotic stability, Q must be negative-definite (all eigenvalues < 0)
    if np.any(eig_Q >= 0):
        return {"verified": False, "error": f"Orbital derivative matrix A^T V + V A must be negative-definite, got eigenvalues {eig_Q}"}

    return {
        "verified": True,
        "eig_V": eig_V.tolist(),
        "eig_Q": eig_Q.tolist(),
        "error": None,
    }


def verify_q12_nonhyperbolic_stability(
    cubic_sign: int,
    linear_eval_only: bool = False,
) -> Dict[str, Any]:
    """Verify Nonhyperbolic Stability Distinction (Q12) for x' = sign * x^3."""
    if linear_eval_only:
        return {
            "verified": False,
            "error": "Inconclusive: stability of nonhyperbolic equilibrium with zero eigenvalue cannot be determined from linearization alone",
        }

    # x' = -x^3 -> V(x) = x^2, V' = 2x(-x^3) = -2x^4 < 0 for x!=0 -> Asymptotically stable
    # x' = +x^3 -> Unstable
    is_stable = (cubic_sign < 0)
    return {
        "verified": True,
        "stable": is_stable,
        "asymptotically_stable": is_stable,
        "error": None,
    }


def verify_q13_transient_growth(
    A: np.ndarray,
    t_sample: float,
    assert_monotonic_decay: bool = False,
) -> Dict[str, Any]:
    """Verify Transient Growth in Nonnormal Systems (Q13)."""
    # Check eigenvalues of A have negative real parts
    eig_A = np.linalg.eigvals(A)
    if np.any(np.real(eig_A) >= 0):
        return {"verified": False, "error": f"Matrix A must have strictly stable spectrum, got eigenvalues {eig_A}"}

    # Compute ||exp(t A)||_2
    exp_tA = expm(t_sample * A)
    norm_exp = float(np.linalg.norm(exp_tA, 2))

    if norm_exp > 1.0:
        if assert_monotonic_decay:
            return {
                "verified": False,
                "error": f"Transient growth observed: ||exp(t A)||_2 = {norm_exp:.4f} > 1.0 contradicts monotonic norm decay assertion",
            }
        return {
            "verified": True,
            "transient_norm_growth": norm_exp,
            "spectral_abscissa": float(np.max(np.real(eig_A))),
            "error": None,
        }

    return {
        "verified": True,
        "transient_norm_growth": norm_exp,
        "error": None,
    }


def verify_q14_conservative_harmonic(
    trajectory: List[Tuple[float, float]],
    claimed_asymptotic_stable: bool = False,
) -> Dict[str, Any]:
    """Verify Conservative Hamiltonian Flow (Q14) for Harmonic Oscillator."""
    if claimed_asymptotic_stable:
        return {
            "verified": False,
            "error": "Conservative Hamiltonian center flow cannot be claimed asymptotically stable (orbits remain on invariant energy surfaces)",
        }

    energies = [0.5 * (x**2 + v**2) for x, v in trajectory]
    e0 = energies[0]
    for e in energies:
        if not np.isclose(e, e0, atol=1e-12):
            return {"verified": False, "error": f"Energy conservation violated: E={e} != E0={e0}"}

    return {
        "verified": True,
        "energy_conserved": True,
        "energy_level": e0,
        "error": None,
    }
