from __future__ import annotations

import json
from fractions import Fraction
from typing import Callable

from graph_io import ROOT, read_jsonl


def gz_ell(L: Fraction, n: int, k: int) -> Fraction:
    return 2 * L * (n + 1) * (2 ** k)


def leibniz_product_rhs(x: Fraction, y: Fraction, dx: Fraction, dy: Fraction) -> Fraction:
    return x * dy + y * dx


def leibniz_power_rhs(x: Fraction, a: int, dx: Fraction) -> Fraction:
    return a * (x ** (a - 1)) * dx


def test_gz_scale_l() -> bool:
    for L in (Fraction(1, 2), Fraction(1), Fraction(3)):
        for n in (0, 1, 4):
            for k in (0, 1, 3):
                for s in (Fraction(2), Fraction(5)):
                    if gz_ell(s * L, n, k) != s * gz_ell(L, n, k):
                        return False
    return True


def test_gz_increment_k() -> bool:
    for L in (Fraction(1, 2), Fraction(1), Fraction(3)):
        for n in (0, 1, 4):
            for k in (0, 1, 3):
                if gz_ell(L, n, k + 1) != 2 * gz_ell(L, n, k):
                    return False
    return True


def test_gz_increment_n() -> bool:
    for L in (Fraction(1, 2), Fraction(1), Fraction(3)):
        for n in (0, 1, 4):
            for k in (0, 1, 3):
                lhs = gz_ell(L, n + 1, k) - gz_ell(L, n, k)
                rhs = (2 ** (k + 1)) * L
                if lhs != rhs:
                    return False
    return True


def test_gz_dimensional() -> bool:
    symbols = {item["id"]: item for item in read_jsonl(ROOT / "graph" / "symbols.jsonl")}
    return (
        symbols["SYMBOL:GZ_ELL"].get("dimension") == "length"
        and symbols["SYMBOL:GZ_L"].get("dimension") == "length"
        and symbols["SYMBOL:GZ_N"].get("dimension") == "dimensionless"
        and symbols["SYMBOL:GZ_K"].get("dimension") == "dimensionless"
    )


def test_leibniz_product_dx_zero() -> bool:
    for x, y, dy in (
        (Fraction(2), Fraction(3), Fraction(5)),
        (Fraction(-2), Fraction(7), Fraction(1)),
        (Fraction(1, 2), Fraction(4), Fraction(-3)),
    ):
        if leibniz_product_rhs(x, y, 0, dy) != x * dy:
            return False
    return True


def test_leibniz_product_dy_zero() -> bool:
    for x, y, dx in (
        (Fraction(2), Fraction(3), Fraction(5)),
        (Fraction(-2), Fraction(7), Fraction(1)),
        (Fraction(1, 2), Fraction(4), Fraction(-3)),
    ):
        if leibniz_product_rhs(x, y, dx, 0) != y * dx:
            return False
    return True


def test_leibniz_product_swap() -> bool:
    for x, y, dx, dy in (
        (Fraction(2), Fraction(3), Fraction(5), Fraction(7)),
        (Fraction(-2), Fraction(7), Fraction(1), Fraction(-4)),
        (Fraction(1, 2), Fraction(4), Fraction(-3), Fraction(2)),
    ):
        a = leibniz_product_rhs(x, y, dx, dy)
        b = leibniz_product_rhs(y, x, dy, dx)
        if a != b:
            return False
    return True


def test_leibniz_power_a1() -> bool:
    for x, dx in (
        (Fraction(2), Fraction(3)),
        (Fraction(-2), Fraction(5)),
        (Fraction(1, 2), Fraction(-4)),
    ):
        if leibniz_power_rhs(x, 1, dx) != dx:
            return False
    return True


def test_leibniz_power_a0() -> bool:
    for x, dx in (
        (Fraction(2), Fraction(3)),
        (Fraction(-2), Fraction(5)),
        (Fraction(1, 2), Fraction(-4)),
    ):
        if leibniz_power_rhs(x, 0, dx) != 0:
            return False
    return True


def tikh_forward(kernel: tuple[tuple[Fraction, ...], ...], z: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return tuple(
        sum((row[j] * z[j] for j in range(len(z))), Fraction(0))
        for row in kernel
    )


def tikh_m_alpha(N: Fraction, alpha: Fraction, omega: Fraction) -> Fraction:
    return N + alpha * omega


def tikh_forward_add() -> bool:
    K = (
        (Fraction(1), Fraction(2), Fraction(-1)),
        (Fraction(3), Fraction(0), Fraction(4)),
    )
    z1 = (Fraction(1), Fraction(2), Fraction(3))
    z2 = (Fraction(-2), Fraction(5), Fraction(1))
    lhs = tikh_forward(K, tuple(a + b for a, b in zip(z1, z2)))
    a = tikh_forward(K, z1)
    b = tikh_forward(K, z2)
    rhs = tuple(x + y for x, y in zip(a, b))
    return lhs == rhs


def tikh_forward_scale() -> bool:
    K = (
        (Fraction(1), Fraction(2), Fraction(-1)),
        (Fraction(3), Fraction(0), Fraction(4)),
    )
    z = (Fraction(1), Fraction(2), Fraction(3))
    c = Fraction(7, 3)
    lhs = tikh_forward(K, tuple(c * x for x in z))
    rhs = tuple(c * x for x in tikh_forward(K, z))
    return lhs == rhs


def tikh_alpha_zero() -> bool:
    for N in (Fraction(0), Fraction(3), Fraction(7, 2)):
        for omega in (Fraction(0), Fraction(5), Fraction(11, 3)):
            if tikh_m_alpha(N, Fraction(0), omega) != N:
                return False
    return True


def tikh_omega_zero() -> bool:
    for N in (Fraction(0), Fraction(3), Fraction(7, 2)):
        for alpha in (Fraction(1, 10), Fraction(1), Fraction(5)):
            if tikh_m_alpha(N, alpha, Fraction(0)) != N:
                return False
    return True


def tikh_positive_penalty() -> bool:
    for N in (Fraction(0), Fraction(3), Fraction(7, 2)):
        for alpha in (Fraction(1, 10), Fraction(1), Fraction(5)):
            for omega in (Fraction(0), Fraction(2), Fraction(11, 3)):
                if tikh_m_alpha(N, alpha, omega) < N:
                    return False
    return True


def tikh_misfit_zero() -> bool:
    residuals = (Fraction(0), Fraction(0), Fraction(0))
    return sum((r * r for r in residuals), Fraction(0)) == 0


def tikh_penalty_zero() -> bool:
    samples = (
        (Fraction(2), Fraction(3), Fraction(0), Fraction(0)),
        (Fraction(5), Fraction(7), Fraction(0), Fraction(0)),
    )
    return all(k * zp * zp + p * z * z == 0 for k, p, zp, z in samples)


def tikh_penalty_nonnegative() -> bool:
    samples = (
        (Fraction(2), Fraction(3), Fraction(4), Fraction(-5)),
        (Fraction(5), Fraction(7), Fraction(-2), Fraction(1)),
        (Fraction(1, 3), Fraction(2, 5), Fraction(7, 4), Fraction(-3, 2)),
    )
    return all(k > 0 and p > 0 and k * zp * zp + p * z * z >= 0 for k, p, zp, z in samples)


def vlasov_reduced_omega2(N: Fraction, e: Fraction, m: Fraction) -> Fraction:
    # 4*pi is a common positive factor and cancels in the exact scaling tests.
    return N * e * e / m


def vlasov_freq_density_scale() -> bool:
    for N in (Fraction(1), Fraction(3), Fraction(7, 2)):
        for e in (Fraction(1), Fraction(-2), Fraction(5, 3)):
            for m in (Fraction(1), Fraction(4), Fraction(9, 2)):
                for s in (Fraction(2), Fraction(5, 3)):
                    if vlasov_reduced_omega2(s * N, e, m) != s * vlasov_reduced_omega2(N, e, m):
                        return False
    return True


def vlasov_freq_charge_sign() -> bool:
    for N in (Fraction(1), Fraction(3)):
        for e in (Fraction(1), Fraction(2), Fraction(5, 3)):
            for m in (Fraction(1), Fraction(4)):
                if vlasov_reduced_omega2(N, -e, m) != vlasov_reduced_omega2(N, e, m):
                    return False
    return True


def vlasov_freq_mass_scale() -> bool:
    for N in (Fraction(1), Fraction(3), Fraction(7, 2)):
        for e in (Fraction(1), Fraction(-2), Fraction(5, 3)):
            for m in (Fraction(1), Fraction(4), Fraction(9, 2)):
                for s in (Fraction(2), Fraction(5, 3)):
                    if vlasov_reduced_omega2(N, e, s * m) != vlasov_reduced_omega2(N, e, m) / s:
                        return False
    return True


def cheb_eq1_residual(error: Fraction, L: Fraction) -> Fraction:
    return error * error - L * L


def cheb_eq1_pos() -> bool:
    for L in (Fraction(1), Fraction(3, 2), Fraction(7)):
        if cheb_eq1_residual(L, L) != 0:
            return False
    return True


def cheb_eq1_neg() -> bool:
    for L in (Fraction(1), Fraction(3, 2), Fraction(7)):
        if cheb_eq1_residual(-L, L) != 0:
            return False
    return True


def cheb_eq1_sign() -> bool:
    for error in (Fraction(-5), Fraction(-1, 2), Fraction(0), Fraction(7, 3)):
        for L in (Fraction(1), Fraction(2)):
            if cheb_eq1_residual(error, L) != cheb_eq1_residual(-error, L):
                return False
    return True


def cheb_eq2_value(x: Fraction, a: Fraction, h: Fraction, derivative: Fraction) -> Fraction:
    return (x - a + h) * (x - a - h) * derivative


def cheb_eq2_left() -> bool:
    for a, h, derivative in (
        (Fraction(0), Fraction(1), Fraction(7)),
        (Fraction(3), Fraction(2), Fraction(-5)),
    ):
        if cheb_eq2_value(a - h, a, h, derivative) != 0:
            return False
    return True


def cheb_eq2_right() -> bool:
    for a, h, derivative in (
        (Fraction(0), Fraction(1), Fraction(7)),
        (Fraction(3), Fraction(2), Fraction(-5)),
    ):
        if cheb_eq2_value(a + h, a, h, derivative) != 0:
            return False
    return True


def cheb_eq2_stationary() -> bool:
    for x, a, h in (
        (Fraction(0), Fraction(0), Fraction(1)),
        (Fraction(5, 2), Fraction(3), Fraction(2)),
    ):
        if cheb_eq2_value(x, a, h, Fraction(0)) != 0:
            return False
    return True


def cheb_map_z(x: Fraction, a: Fraction, h: Fraction) -> Fraction:
    return (x - a) / h


def cheb_map_left() -> bool:
    return all(
        cheb_map_z(a - h, a, h) == -1
        for a, h in ((Fraction(0), Fraction(1)), (Fraction(3), Fraction(2)))
    )


def cheb_map_center() -> bool:
    return all(
        cheb_map_z(a, a, h) == 0
        for a, h in ((Fraction(0), Fraction(1)), (Fraction(3), Fraction(2)))
    )


def cheb_map_right() -> bool:
    return all(
        cheb_map_z(a + h, a, h) == 1
        for a, h in ((Fraction(0), Fraction(1)), (Fraction(3), Fraction(2)))
    )


def pon_dot(psi: tuple[Fraction, ...], f: tuple[Fraction, ...]) -> Fraction:
    return sum((a * b for a, b in zip(psi, f)), Fraction(0))


def pon_cost_zero() -> bool:
    samples = (Fraction(0), Fraction(0), Fraction(0), Fraction(0))
    return sum(samples, Fraction(0)) == 0


def pon_cost_concat() -> bool:
    left = (Fraction(1, 2), Fraction(2), Fraction(-1, 3))
    right = (Fraction(7, 4), Fraction(5, 2))
    total = left + right
    return sum(total, Fraction(0)) == sum(left, Fraction(0)) + sum(right, Fraction(0))


def pon_h_psi_add() -> bool:
    f = (Fraction(2), Fraction(-3), Fraction(5, 2))
    psi1 = (Fraction(1), Fraction(2), Fraction(-1))
    psi2 = (Fraction(4), Fraction(-1), Fraction(3))
    combined = tuple(a + b for a, b in zip(psi1, psi2))
    return pon_dot(combined, f) == pon_dot(psi1, f) + pon_dot(psi2, f)


def pon_h_psi_scale() -> bool:
    f = (Fraction(2), Fraction(-3), Fraction(5, 2))
    psi = (Fraction(1), Fraction(2), Fraction(-1))
    c = Fraction(7, 3)
    scaled = tuple(c * x for x in psi)
    return pon_dot(scaled, f) == c * pon_dot(psi, f)


def pon_max_finite() -> bool:
    values = (Fraction(-3), Fraction(5, 2), Fraction(7), Fraction(1, 3))
    M = max(values)
    return M in values and all(M >= value for value in values)


def gl_linear_operator(F: tuple[tuple[Fraction, ...], ...], K: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    # Finite exact analogue of K + T_F K for fixed F.
    return tuple(
        K[i] + sum((F[i][j] * K[j] for j in range(len(K))), Fraction(0))
        for i in range(len(K))
    )


def gl_f_zero_measure() -> bool:
    weights = (Fraction(0), Fraction(0), Fraction(0))
    phi_x = (Fraction(1), Fraction(2), Fraction(-3))
    phi_y = (Fraction(4), Fraction(-1), Fraction(5))
    f = sum((a * b * w for a, b, w in zip(phi_x, phi_y, weights)), Fraction(0))
    return f == 0


def gl_linear_k_add() -> bool:
    F = (
        (Fraction(1), Fraction(2), Fraction(0)),
        (Fraction(-1), Fraction(3), Fraction(1)),
        (Fraction(2), Fraction(0), Fraction(4)),
    )
    K1 = (Fraction(1), Fraction(2), Fraction(-1))
    K2 = (Fraction(4), Fraction(-3), Fraction(5))
    lhs = gl_linear_operator(F, tuple(a + b for a, b in zip(K1, K2)))
    a = gl_linear_operator(F, K1)
    b = gl_linear_operator(F, K2)
    return lhs == tuple(x + y for x, y in zip(a, b))


def gl_linear_k_scale() -> bool:
    F = (
        (Fraction(1), Fraction(2)),
        (Fraction(-1), Fraction(3)),
    )
    K = (Fraction(4), Fraction(-3))
    c = Fraction(7, 3)
    lhs = gl_linear_operator(F, tuple(c * x for x in K))
    rhs = tuple(c * x for x in gl_linear_operator(F, K))
    return lhs == rhs


def gl_zero_f() -> bool:
    F = (
        (Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(0)),
    )
    # Equation is (I+T_F)K=-f, so with F=f=0 the only exact result is K=0.
    K = (Fraction(0), Fraction(0))
    return gl_linear_operator(F, K) == (Fraction(0), Fraction(0))


def gl_constant_diagonal() -> bool:
    # Exact finite-difference analogue of derivative of a constant diagonal.
    diag = (Fraction(5), Fraction(5), Fraction(5), Fraction(5))
    differences = tuple(diag[i+1] - diag[i] for i in range(len(diag)-1))
    q = tuple(2 * d for d in differences)
    return all(value == 0 for value in q)


def gl_diagonal_scale() -> bool:
    diag = (Fraction(1), Fraction(4), Fraction(9), Fraction(16))
    c = Fraction(5, 2)
    q = tuple(2 * (diag[i+1] - diag[i]) for i in range(len(diag)-1))
    scaled = tuple(c * x for x in diag)
    q_scaled = tuple(2 * (scaled[i+1] - scaled[i]) for i in range(len(scaled)-1))
    return q_scaled == tuple(c * x for x in q)


EVALUATORS: dict[str, Callable[[], bool]] = {
    "gz_scale_l": test_gz_scale_l,
    "gz_increment_k": test_gz_increment_k,
    "gz_increment_n": test_gz_increment_n,
    "gz_dimensional": test_gz_dimensional,
    "leibniz_product_dx_zero": test_leibniz_product_dx_zero,
    "leibniz_product_dy_zero": test_leibniz_product_dy_zero,
    "leibniz_product_swap": test_leibniz_product_swap,
    "leibniz_power_a1": test_leibniz_power_a1,
    "leibniz_power_a0": test_leibniz_power_a0,
    "tikh_forward_add": tikh_forward_add,
    "tikh_forward_scale": tikh_forward_scale,
    "tikh_alpha_zero": tikh_alpha_zero,
    "tikh_omega_zero": tikh_omega_zero,
    "tikh_positive_penalty": tikh_positive_penalty,
    "tikh_misfit_zero": tikh_misfit_zero,
    "tikh_penalty_zero": tikh_penalty_zero,
    "tikh_penalty_nonnegative": tikh_penalty_nonnegative,
    "vlasov_freq_density_scale": vlasov_freq_density_scale,
    "vlasov_freq_charge_sign": vlasov_freq_charge_sign,
    "vlasov_freq_mass_scale": vlasov_freq_mass_scale,
    "cheb_eq1_pos": cheb_eq1_pos,
    "cheb_eq1_neg": cheb_eq1_neg,
    "cheb_eq1_sign": cheb_eq1_sign,
    "cheb_eq2_left": cheb_eq2_left,
    "cheb_eq2_right": cheb_eq2_right,
    "cheb_eq2_stationary": cheb_eq2_stationary,
    "cheb_map_left": cheb_map_left,
    "cheb_map_center": cheb_map_center,
    "cheb_map_right": cheb_map_right,
    "pon_cost_zero": pon_cost_zero,
    "pon_cost_concat": pon_cost_concat,
    "pon_h_psi_add": pon_h_psi_add,
    "pon_h_psi_scale": pon_h_psi_scale,
    "pon_max_finite": pon_max_finite,
    "gl_f_zero_measure": gl_f_zero_measure,
    "gl_linear_k_add": gl_linear_k_add,
    "gl_linear_k_scale": gl_linear_k_scale,
    "gl_zero_f": gl_zero_f,
    "gl_constant_diagonal": gl_constant_diagonal,
    "gl_diagonal_scale": gl_diagonal_scale,
}


def qualify() -> dict[str, object]:
    tests = read_jsonl(ROOT / "graph" / "behavioral_tests.jsonl")
    results = []
    for test in tests:
        if not test.get("automatable"):
            results.append({"id": test["id"], "status": "NOT_AUTOMATED"})
            continue
        name = test.get("evaluator")
        evaluator = EVALUATORS.get(name)
        if evaluator is None:
            results.append({"id": test["id"], "status": "MISSING_EVALUATOR"})
            continue
        passed = bool(evaluator())
        results.append({"id": test["id"], "status": "PASS" if passed else "FAIL"})
    failed = [item for item in results if item["status"] not in {"PASS", "NOT_AUTOMATED"}]
    return {
        "status": "PASS" if not failed else "FAIL",
        "tests": results,
        "pass_count": sum(item["status"] == "PASS" for item in results),
        "fail_count": len(failed),
    }


def main() -> int:
    result = qualify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
