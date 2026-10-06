from mapeogeo.erdos_formal_obligations import obligation


def test_problem_19_reduces_to_shared_coloring_bridge():
    o=obligation("19")
    assert "colorable_of_sharedColoring" in o.available_lemmas
    assert "shared vertices" in o.missing_bridge
    assert o.machinery_outcome=="IMPLEMENT_OR_PROVE_LEMMA"


def test_problem_89_is_asymptotic_bridge_not_finite_distance_deficit():
    o=obligation("89")
    assert "n_dvd_log_n" in o.available_lemmas
    assert o.machinery_outcome=="ASYMPTOTIC_BRIDGE_MISSING"


def test_problem_128_exposes_extremal_graph_gap():
    o=obligation("128")
    assert o.available_lemmas==()
    assert o.machinery_outcome=="EXTREMAL_GRAPH_BRIDGE_MISSING"


def test_no_obligation_claims_proved():
    for n in ("19","23","60","89","97","128"):
        assert "PROVED" not in obligation(n).machinery_outcome
