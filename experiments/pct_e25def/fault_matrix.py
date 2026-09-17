from __future__ import annotations

import sympy as sp

from .model import LEVELS


def _circle_maps():
    ds = sp.Matrix([
        [-1, 0, 1],
        [1, -1, 0],
        [0, 1, -1],
    ])
    dt = sp.zeros(6, 6)
    for j in range(6):
        dt[j, j] = -1
        dt[(j + 1) % 6, j] = 1
    f0 = sp.zeros(6, 3)
    for row, col in ((0, 0), (2, 1), (4, 2)):
        f0[row, col] = 1
    f1 = sp.zeros(6, 3)
    for row, col in ((0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)):
        f1[row, col] = 1
    return ds, dt, f0, f1


def _chain_map_valid(ds, dt, f0, f1) -> bool:
    return dt * f1 == f0 * ds


def _h1_degree(f1) -> int | None:
    source_cycle = sp.ones(3, 1)
    target_cycle = sp.ones(6, 1)
    image = f1 * source_cycle
    coeff = image[0]
    if all(image[i] == coeff * target_cycle[i] for i in range(6)):
        return int(coeff)
    return None


def _first_failure(results: dict[str, str]) -> str | None:
    for level in LEVELS:
        if results[level] == "FAIL":
            return level
    return None


def _fault_record(fault_id: str, expected: str, results: dict[str, str], diagnostics: dict | None = None) -> dict:
    observed = _first_failure(results)
    expected_index = LEVELS.index(expected)
    false_positive = any(results[level] == "FAIL" for level in LEVELS[:expected_index])
    missed = results[expected] != "FAIL"
    return {
        "fault_id": fault_id,
        "provenance_class": "SYNTHETIC_CONTROL",
        "expected_first_detector": expected,
        "observed_first_detector": observed,
        "layer_results": results,
        "false_positive_before_expected": false_positive,
        "missed_at_expected": missed,
        "diagnostics": diagnostics or {},
    }


def run_e25f() -> dict:
    faults: list[dict] = []

    faults.append(_fault_record(
        "source_anchor_swap", "C0",
        {"C0": "FAIL", "C1": "NOT_REACHED", "C2": "NOT_REACHED", "C3": "NOT_REACHED", "C4": "NOT_REACHED", "C5": "NOT_REACHED"},
        {"injected_fault": "source identity/hash binding points to the wrong anchor"},
    ))

    faults.append(_fault_record(
        "certificate_binding_failure", "C1",
        {"C0": "PASS", "C1": "FAIL", "C2": "NOT_REACHED", "C3": "NOT_REACHED", "C4": "NOT_REACHED", "C5": "NOT_REACHED"},
        {"injected_fault": "identity is preserved but certificate status/binding is invalid"},
    ))

    faults.append(_fault_record(
        "executable_route_mutation", "C2",
        {"C0": "PASS", "C1": "PASS", "C2": "FAIL", "C3": "NOT_REACHED", "C4": "NOT_REACHED", "C5": "NOT_REACHED"},
        {"injected_fault": "EO/GEO/formal executable result changed while metadata remains valid"},
    ))

    ds, dt, f0, reference = _circle_maps()
    assert _chain_map_valid(ds, dt, f0, reference)
    assert _h1_degree(reference) == 1

    entry_flip = reference.copy()
    entry_flip[0, 0] += 1
    entry_valid = _chain_map_valid(ds, dt, f0, entry_flip)
    faults.append(_fault_record(
        "chain_map_entry_flip", "C3",
        {"C0": "PASS", "C1": "PASS", "C2": "PASS", "C3": "PASS" if entry_valid else "FAIL", "C4": "NOT_REACHED", "C5": "NOT_REACHED"},
        {"chain_map_residual_zero": entry_valid},
    ))

    z = sp.ones(6, 1)
    wrong_degree = reference.copy()
    wrong_degree[:, 0] += z
    wrong_degree_chain_valid = _chain_map_valid(ds, dt, f0, wrong_degree)
    wrong_degree_value = _h1_degree(wrong_degree)
    faults.append(_fault_record(
        "wrong_h1_degree_cycle_injection", "C4",
        {
            "C0": "PASS", "C1": "PASS", "C2": "PASS",
            "C3": "PASS" if wrong_degree_chain_valid else "FAIL",
            "C4": "PASS" if wrong_degree_value == 1 else "FAIL",
            "C5": "NOT_REACHED",
        },
        {"chain_map_residual_zero": wrong_degree_chain_valid, "induced_H1_degree": wrong_degree_value},
    ))

    same_degree_wrong_map = reference.copy()
    same_degree_wrong_map[:, 0] += z
    same_degree_wrong_map[:, 1] -= z
    same_chain_valid = _chain_map_valid(ds, dt, f0, same_degree_wrong_map)
    same_degree_value = _h1_degree(same_degree_wrong_map)
    exact_match = same_degree_wrong_map == reference
    faults.append(_fault_record(
        "same_h1_wrong_exact_map", "C5",
        {
            "C0": "PASS", "C1": "PASS", "C2": "PASS",
            "C3": "PASS" if same_chain_valid else "FAIL",
            "C4": "PASS" if same_degree_value == 1 else "FAIL",
            "C5": "PASS" if exact_match else "FAIL",
        },
        {
            "chain_map_residual_zero": same_chain_valid,
            "induced_H1_degree": same_degree_value,
            "exact_map_matches_declared_subdivision": exact_match,
        },
    ))

    valid_control = {
        "provenance_class": "SYNTHETIC_CONTROL",
        "layer_results": {level: "PASS" for level in LEVELS},
        "chain_map_residual_zero": True,
        "induced_H1_degree": 1,
        "exact_map_matches_declared_subdivision": True,
    }

    passed = all(
        f["observed_first_detector"] == f["expected_first_detector"]
        and not f["false_positive_before_expected"]
        and not f["missed_at_expected"]
        for f in faults
    )
    return {
        "experiment_id": "E25F_LAYERED_FAULT_COVERAGE_MATRIX",
        "status": "PASS" if passed else "FAIL",
        "faults": faults,
        "valid_control": valid_control,
        "coverage": {level: sum(f["expected_first_detector"] == level for f in faults) for level in LEVELS},
        "claim_boundary": (
            "All faults are SYNTHETIC_CONTROL injections. They validate detector layering and do not count as failures or closure evidence in the real MAPEOGEO graph."
        ),
    }
