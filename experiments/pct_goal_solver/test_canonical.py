from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import sympy as sp

from experiments.pct_goal_solver.canonical import (
    CanonicalizationError,
    canonical_bytes,
    canonical_sha256,
)


def test_golden_canonical_digest_and_map_order():
    left = {"b": 1, "a": True}
    right = {"a": True, "b": 1}
    expected = (
        b'{"t":"map","v":[[{"t":"str","v":"a"},{"t":"bool","v":true}],'
        b'[{"t":"str","v":"b"},{"t":"int","v":"1"}]]}'
    )
    assert canonical_bytes(left) == canonical_bytes(right) == expected
    assert canonical_sha256(left, domain="pct-test-v1") == (
        "1f5fdea03d3e1330d828da8ea04d54c3e205df210f65ce3f17b9f718b8b0964c"
    )


def test_canonical_encoding_separates_python_and_exact_numeric_types():
    values = [
        None,
        True,
        1,
        1.0,
        "1",
        b"1",
        Fraction(1, 1),
        Decimal("1"),
        complex(1, 0),
        [1],
        (1,),
        {1},
        frozenset({1}),
    ]
    encodings = [canonical_bytes(value) for value in values]
    assert len(encodings) == len(set(encodings))


def test_canonical_encoding_normalizes_unicode_negative_zero_and_unordered_sets():
    assert canonical_bytes("e\N{COMBINING ACUTE ACCENT}") == canonical_bytes("\N{LATIN SMALL LETTER E WITH ACUTE}")
    assert canonical_bytes(-0.0) == canonical_bytes(0.0)
    assert canonical_bytes({3, 1, 2}) == canonical_bytes({2, 3, 1})


def test_numpy_and_sympy_are_explicitly_typed_and_deterministic():
    x = sp.Symbol("x", real=True)
    payload = {
        "scalar": np.int64(7),
        "array": np.asarray([[1, 2], [3, 4]], dtype=np.int16),
        "expr": sp.expand((x + 1) ** 2),
    }
    first = canonical_bytes(payload)
    second = canonical_bytes(payload)
    assert first == second
    decoded = json.loads(first)
    assert decoded["t"] == "map"
    assert b'"numpy_array"' in first
    assert b'"sympy"' in first


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), float("-inf"), Decimal("NaN"), lambda: None, object()],
)
def test_canonical_encoding_rejects_nonfinite_callable_and_opaque_values(value):
    with pytest.raises(CanonicalizationError):
        canonical_bytes(value)


def test_decimal_encoding_is_independent_of_active_context():
    from decimal import localcontext

    value = Decimal("123456789012345678901234567890.0000")
    with localcontext() as context:
        context.prec = 5
        low_precision = canonical_bytes(value)
    with localcontext() as context:
        context.prec = 80
        high_precision = canonical_bytes(value)
    assert low_precision == high_precision


def test_canonical_mapping_rejects_unicode_normalization_key_collision():
    with pytest.raises(CanonicalizationError, match="canonical mapping key collision"):
        canonical_bytes({"e\N{COMBINING ACUTE ACCENT}": 1, "\N{LATIN SMALL LETTER E WITH ACUTE}": 2})


def test_canonical_set_rejects_unicode_normalization_element_collision():
    with pytest.raises(CanonicalizationError, match="canonical set element collision"):
        canonical_bytes({"e\N{COMBINING ACUTE ACCENT}", "\N{LATIN SMALL LETTER E WITH ACUTE}"})


@pytest.mark.parametrize("value", [sp.nan, sp.oo, -sp.oo, sp.zoo, sp.Symbol("x") + sp.oo])
def test_canonical_encoding_rejects_nonfinite_sympy_values(value):
    with pytest.raises(CanonicalizationError, match="non-finite SymPy"):
        canonical_bytes(value)


def test_digest_is_stable_across_hash_seeds_timezone_and_locale(tmp_path: Path):
    script = tmp_path / "digest.py"
    script.write_text(
        "from fractions import Fraction\n"
        "from experiments.pct_goal_solver.canonical import canonical_sha256\n"
        "from experiments.pct_goal_solver.goals import goals_for\n"
        "from experiments.pct_goal_solver.model import OperatorFailure\n"
        "from experiments.pct_goal_solver.operators import build_operator_registry\n"
        "print(canonical_sha256({'set': {'z', 'a'}, 'q': Fraction(7, 13)}, domain='subprocess-v1'))\n"
        "goal = goals_for('CALIBRATION', 'G1')[0]\n"
        "output = build_operator_registry()['MOBIUS_INVERT_BOOLEAN'].execute({'cumulative': goal.inputs['cumulative']}, ())\n"
        "assert not isinstance(output, OperatorFailure)\n"
        "print(output.artifact_id)\n",
        encoding="utf-8",
    )
    outputs = []
    for seed in ("1", "987654"):
        repo_root = str(Path(__file__).resolve().parents[2])
        env = dict(
            os.environ,
            PYTHONHASHSEED=seed,
            TZ="UTC",
            LC_ALL="C.UTF-8",
            PYTHONPATH=repo_root,
        )
        outputs.append(
            subprocess.check_output(
                [sys.executable, str(script)],
                cwd=Path(__file__).resolve().parents[2],
                env=env,
                text=True,
            ).strip()
        )
    assert outputs[0] == outputs[1]
