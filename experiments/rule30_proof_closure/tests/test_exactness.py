"""Tests for exact Rule 30 bilateral semantics and ANF symbolic constraint engine."""

from __future__ import annotations

from experiments.rule30_proof_closure.core import (
    ANFPolynomial,
    build_bilateral_cone_anf_system,
    evolve_single_seed,
    obs_left_word,
    or_col_word,
    row_at_left,
    row_at_right,
    run_left_word,
    run_right_word,
)


def test_bilateral_word_operators_match_single_seed_evolution():
    rows = evolve_single_seed(20)
    for t in range(1, 10):
        for l_len in range(1, 6):
            w = tuple(rows[t + s].get(0, 0) for s in range(l_len))
            c_after = rows[t + l_len].get(0, 0)
            n = 5
            left_in = row_at_left(rows, t, -1, n + l_len)
            left_out = run_left_word(w, left_in)
            assert left_out == row_at_left(rows, t + l_len, -1, n)

            right_in = row_at_right(rows, t, 1, n + l_len)
            right_out = run_right_word(w, right_in)
            assert right_out == row_at_right(rows, t + l_len, 1, n)

            obs_l = obs_left_word(w, c_after, row_at_left(rows, t, -1, n + l_len + 1))
            obs_r = or_col_word(w, row_at_right(rows, t, 1, n + l_len + 1))
            assert obs_l == obs_r


def test_anf_symbolic_cone_system_exact_evaluation():
    x = ANFPolynomial.var("x")
    y = ANFPolynomial.var("y")
    z = ANFPolynomial.var("z")
    r30 = x ^ (y | z)
    for vx in (0, 1):
        for vy in (0, 1):
            for vz in (0, 1):
                assert r30.evaluate({"x": vx, "y": vy, "z": vz}) == (vx ^ (vy | vz))

    sys_anf = build_bilateral_cone_anf_system(transient_t=2, word=(0, 1), horizon=6)
    assert sys_anf.first_unsat_horizon == 3
    assert len(sys_anf.satisfying_assignments) == 0
