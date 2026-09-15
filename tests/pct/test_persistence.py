"""Unit tests for PCT GF(2) persistence, pairing ledgers, and Euler projections."""

from __future__ import annotations

from mapeogeo.pct.models import Simplex
from mapeogeo.pct.persistence import (
    FilteredSimplex,
    betti_at,
    euler_at,
    pairing_ledger,
    persistent_pairs_gf2,
    validate_filtration_order,
)


def test_loop_birth_death_persistence():
    items = [
        FilteredSimplex(Simplex((0,)), 0.0),
        FilteredSimplex(Simplex((1,)), 0.0),
        FilteredSimplex(Simplex((2,)), 0.0),
        FilteredSimplex(Simplex((0, 1)), 1.0),
        FilteredSimplex(Simplex((1, 2)), 1.0),
        FilteredSimplex(Simplex((0, 2)), 1.0),
        FilteredSimplex(Simplex((0, 1, 2)), 2.0),
    ]

    assert validate_filtration_order(items) is True

    pairs = persistent_pairs_gf2(items)

    # Check H1 interval
    h1_pairs = [p for p in pairs if p.dimension == 1]
    assert len(h1_pairs) == 1
    p1 = h1_pairs[0]
    assert p1.birth == 1.0
    assert p1.death == 2.0
    assert p1.essential is False

    # Check H0 intervals
    h0_pairs = [p for p in pairs if p.dimension == 0]
    assert len(h0_pairs) == 3
    essential_h0 = [p for p in h0_pairs if p.essential]
    assert len(essential_h0) == 1
    assert essential_h0[0].birth == 0.0

    finite_h0 = [p for p in h0_pairs if not p.essential]
    assert len(finite_h0) == 2
    for p in finite_h0:
        assert p.birth == 0.0
        assert p.death == 1.0

    # Euler projections at different filtration values
    # at t=0.5: beta_0 = 3, beta_1 = 0 => chi = 3
    assert betti_at(pairs, 0.5) == {0: 3, 1: 0, 2: 0}
    assert euler_at(pairs, 0.5) == 3

    # at t=1.5: beta_0 = 1, beta_1 = 1 => chi = 0
    assert betti_at(pairs, 1.5) == {0: 1, 1: 1, 2: 0}
    assert euler_at(pairs, 1.5) == 0

    # at t=2.5: beta_0 = 1, beta_1 = 0 => chi = 1
    assert betti_at(pairs, 2.5) == {0: 1, 1: 0, 2: 0}
    assert euler_at(pairs, 2.5) == 1


def test_h0_merge_persistence():
    items = [
        FilteredSimplex(Simplex((0,)), 0.0),
        FilteredSimplex(Simplex((1,)), 0.0),
        FilteredSimplex(Simplex((0, 1)), 1.0),
    ]

    assert validate_filtration_order(items) is True

    pairs = persistent_pairs_gf2(items)
    assert len(pairs) == 2

    # 1 essential H0, 1 dying H0 at 1.0
    essential = [p for p in pairs if p.essential]
    finite = [p for p in pairs if not p.essential]

    assert len(essential) == 1
    assert len(finite) == 1
    assert finite[0].dimension == 0
    assert finite[0].birth == 0.0
    assert finite[0].death == 1.0


def test_pairing_ledger_format():
    items = [
        FilteredSimplex(Simplex((0,)), 0.0),
        FilteredSimplex(Simplex((1,)), 0.0),
        FilteredSimplex(Simplex((0, 1)), 1.0),
    ]
    pairs = persistent_pairs_gf2(items)
    ledger = pairing_ledger(pairs)
    assert len(ledger) == 2
    assert all("dimension" in entry for entry in ledger)
    assert all("birth" in entry for entry in ledger)
    assert all("essential" in entry for entry in ledger)
