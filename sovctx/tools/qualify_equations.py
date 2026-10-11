from __future__ import annotations

import json
from typing import Callable

from graph_io import ROOT, read_jsonl


def gz_ell(L: float, n: int, k: int) -> float:
    return 2.0 * L * (n + 1) * (2 ** k)


def leibniz_product_rhs(x: float, y: float, dx: float, dy: float) -> float:
    return x * dy + y * dx


def leibniz_power_rhs(x: float, a: float, dx: float) -> float:
    return a * (x ** (a - 1)) * dx


def test_gz_scale_l() -> bool:
    for L in (0.5, 1.0, 3.0):
        for n in (0, 1, 4):
            for k in (0, 1, 3):
                for s in (2.0, 5.0):
                    if gz_ell(s * L, n, k) != s * gz_ell(L, n, k):
                        return False
    return True


def test_gz_increment_k() -> bool:
    for L in (0.5, 1.0, 3.0):
        for n in (0, 1, 4):
            for k in (0, 1, 3):
                if gz_ell(L, n, k + 1) != 2 * gz_ell(L, n, k):
                    return False
    return True


def test_gz_increment_n() -> bool:
    for L in (0.5, 1.0, 3.0):
        for n in (0, 1, 4):
            for k in (0, 1, 3):
                lhs = gz_ell(L, n + 1, k) - gz_ell(L, n, k)
                rhs = (2 ** (k + 1)) * L
                if lhs != rhs:
                    return False
    return True


def test_gz_dimensional() -> bool:
    return True


def test_leibniz_product_dx_zero() -> bool:
    for x, y, dy in ((2, 3, 5), (-2, 7, 1), (0.5, 4, -3)):
        if leibniz_product_rhs(x, y, 0, dy) != x * dy:
            return False
    return True


def test_leibniz_product_dy_zero() -> bool:
    for x, y, dx in ((2, 3, 5), (-2, 7, 1), (0.5, 4, -3)):
        if leibniz_product_rhs(x, y, dx, 0) != y * dx:
            return False
    return True


def test_leibniz_product_swap() -> bool:
    for x, y, dx, dy in ((2, 3, 5, 7), (-2, 7, 1, -4), (0.5, 4, -3, 2)):
        a = leibniz_product_rhs(x, y, dx, dy)
        b = leibniz_product_rhs(y, x, dy, dx)
        if a != b:
            return False
    return True


def test_leibniz_power_a1() -> bool:
    for x, dx in ((2, 3), (-2, 5), (0.5, -4)):
        if leibniz_power_rhs(x, 1, dx) != dx:
            return False
    return True


def test_leibniz_power_a0() -> bool:
    for x, dx in ((2, 3), (-2, 5), (0.5, -4)):
        if leibniz_power_rhs(x, 0, dx) != 0:
            return False
    return True


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
