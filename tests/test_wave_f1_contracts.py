"""Tests for Wave F1 Statement-Bound Executable Contracts and Falsification."""

from __future__ import annotations

import pytest

from scripts.wave_f1_contracts import (
    check_eulerian_status,
    compute_pie_union_cardinality,
    construct_finite_csb_bijection,
    execute_all_wave_f1_contracts,
    run_eulerian_graph_contract,
    run_finite_csb_contract,
    run_inclusion_exclusion_contract,
    run_logic_truth_table_contract,
    verify_propositional_tautology,
)


def test_all_wave_f1_contracts_pass_and_have_deterministic_digests() -> None:
    first_run = execute_all_wave_f1_contracts()
    second_run = execute_all_wave_f1_contracts()

    assert len(first_run) == 4
    for cid in ("contract:f1:logic_truth_table_exhaustive",
                "contract:f1:inclusion_exclusion_exact",
                "contract:f1:eulerian_degree_parity",
                "contract:f1:finite_csb_bijection"):
        assert cid in first_run
        ev1 = first_run[cid]
        ev2 = second_run[cid]
        assert ev1.status == "PASS"
        assert ev1.evidence_digest == ev2.evidence_digest
        assert len(ev1.evidence_digest) == 64
        assert len(ev1.witnesses) > 0


def test_logic_truth_table_falsification() -> None:
    # A non-tautology: A -> B
    res = verify_propositional_tautology(
        ["A", "B"],
        lambda env: (not env["A"]) or (not env["B"]), # not a tautology
    )
    assert res["is_tautology"] is False
    assert res["failing_assignment"] is not None
    assert res["failing_assignment"]["A"] == 1
    assert res["failing_assignment"]["B"] == 1


def test_inclusion_exclusion_exact_falsification() -> None:
    s1 = {1, 2, 3}
    s2 = {3, 4, 5}
    actual_union = len(s1 | s2) # 5
    pie_calc = compute_pie_union_cardinality([s1, s2]) # 5
    assert actual_union == pie_calc == 5

    # If we perturb the sets
    s2_perturbed = {3, 4, 5, 6}
    pie_calc_perturbed = compute_pie_union_cardinality([s1, s2_perturbed])
    assert pie_calc_perturbed == 6 != actual_union


def test_eulerian_graph_falsification() -> None:
    # Graph with 4 odd degree vertices (Star graph S_4 with center 0 and leaves 1,2,3)
    vertices = [0, 1, 2, 3]
    edges = [(0, 1), (0, 2), (0, 3)]
    status = check_eulerian_status(vertices, edges)
    assert status["valid"] is True
    assert status["is_connected"] is True
    assert status["has_euler_circuit"] is False
    assert status["has_euler_path"] is False
    assert status["odd_vertex_count"] == 4

    # Disconnected graph with 2 separate triangles (even degrees, but not connected)
    d_vertices = [0, 1, 2, 3, 4, 5]
    d_edges = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
    d_status = check_eulerian_status(d_vertices, d_edges)
    assert d_status["is_connected"] is False
    assert d_status["has_euler_circuit"] is False


def test_csb_bijection_constructor_and_falsification() -> None:
    set_a = {1, 2, 3}
    set_b = {"x", "y", "z"}
    f = {1: "x", 2: "y", 3: "z"}
    g = {"x": 1, "y": 2, "z": 3}

    res = construct_finite_csb_bijection(set_a, set_b, f, g)
    assert res["is_bijection"] is True

    # Falsification: non-injective function f
    f_bad = {1: "x", 2: "x", 3: "z"}
    with pytest.raises(ValueError, match="not an injection"):
        construct_finite_csb_bijection(set_a, set_b, f_bad, g)


def test_missing_or_forged_subject_hash_fails_closed() -> None:
    with pytest.raises(ValueError, match="Missing subject hash"):
        run_logic_truth_table_contract({"decl:OPEN_LOGIC:DEF:prop_valuation": "123"})
