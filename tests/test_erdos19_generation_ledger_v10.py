from mapeogeo.erdos19_generation_ledger_v10 import build_generation_ledger,replay_generation_ledger
from mapeogeo.erdos19_generator_validation_v9 import brute_force_exact_covers


def test_generation_ledger_replays_n3():
    nodes,parents,leaves,manifest=build_generation_ledger(3)
    assert replay_generation_ledger(3,nodes,parents,manifest)
    brute,_=brute_force_exact_covers(3)
    assert set(leaves)==set(brute)


def test_generation_ledger_replays_n4_and_matches_independent_control():
    nodes,parents,leaves,manifest=build_generation_ledger(4)
    assert replay_generation_ledger(4,nodes,parents,manifest)
    brute,_=brute_force_exact_covers(4)
    assert set(leaves)==set(brute)


def test_tampered_manifest_fails():
    nodes,parents,_,manifest=build_generation_ledger(3)
    bad=("0" if manifest[0]!="0" else "1")+manifest[1:]
    assert not replay_generation_ledger(3,nodes,parents,bad)
