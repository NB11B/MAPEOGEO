"""Exact bounded LP witnesses, not a general LP duality proof."""
import importlib.util
from fractions import Fraction
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "lp_contract_under_test", Path(__file__).parents[1] / "scripts/map_goal_v0_7.py"
)
lp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(lp)


def test_contract_rejects_nonminimum_selector(monkeypatch):
    # Mutation of the real selection algorithm must fail, not certify bad witnesses.
    monkeypatch.setattr(lp, "min", max, raising=False)
    ok, checks = lp.contract_lp()
    assert not ok
    assert 0 < checks < 2457


def test_original_enumeration_preserved():
    assert lp.contract_lp() == (True, 2457)


def test_witness_validator_exists():
    assert callable(getattr(lp, "validate_positive_1d_lp_witness", None))


@pytest.mark.parametrize("a,b,c,x,y,expected", [
    ((1, 1), (1, 2), 1, 1, (1, 0), True),
    ((1, 1), (1, 2), 1, 2, (0, 1), False),  # infeasible primal
    ((1, 2), (1, 2), 1, 1, (0, Fraction(1, 2)), True),  # tied ratios
    ((1,), (1,), 1, 0, (0,), False),  # infeasible dual despite equal values
    ((1,), (1,), 1, 0, (1,), False),  # feasible but unequal objectives
    ((1,), (1,), 1, -1, (-1,), False),  # negative witnesses
    ((1, 1), (1,), 1, 1, (1, 0), False),
    ((1,), (1,), 1, 1, (1, 0), False),
    ((), (), 1, 0, (), False),
    ((0,), (1,), 1, 0, (1,), False),
    ((-1,), (1,), 1, 0, (1,), False),
    ((1,), (-1,), 1, 0, (1,), False),
    ((1,), (1,), -1, 0, (1,), False),
    ((1,), (0,), 0, 0, (0,), True),
])
def test_exact_witness_conditions(a, b, c, x, y, expected):
    validate = getattr(lp, "validate_positive_1d_lp_witness", None)
    assert callable(validate)
    assert validate(a, b, c, x, y) is expected

@pytest.mark.parametrize('value', [True, 1.0, '1'])
def test_inexact_or_nonnumeric_values_rejected(value):
    assert not lp.validate_positive_1d_lp_witness((value,), (1,), 1, 1, (1,))
