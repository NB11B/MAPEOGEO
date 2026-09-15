from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v07", ROOT/"scripts"/"map_goal_v0_7.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_jaccard():
    assert mod.jaccard({"a","b"},{"b","c"}) == 1/3
    assert mod.jaccard(set(),{"a"}) == 0

def test_average_rank_ties():
    s={"a":1.0,"b":1.0,"c":0.0}
    assert mod.average_rank(s,"a") == 1.5
    assert mod.average_rank(s,"c") == 3.0

def test_exact_contracts():
    for name in mod.CONTRACTS:
        result = mod.CONTRACTS[name]()
        assert len(result) >= 2
        ok, checks = result[:2]
        assert ok, name
        assert checks > 0

def test_holdout_deterministic():
    vals=[mod.hash_holdout(f"edge-{i}") for i in range(100)]
    assert vals == [mod.hash_holdout(f"edge-{i}") for i in range(100)]
    assert 5 < sum(vals) < 40
