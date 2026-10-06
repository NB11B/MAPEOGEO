from mapeogeo.erdos19_degeneracy_falsification import (
    degeneracy,falsify_pair_family,pair_only_family,valid_linear_family,
)


def test_pair_family_is_valid_linear_incidence_structure():
    assert valid_linear_family(pair_only_family(4))


def test_n4_pair_family_falsifies_strict_degeneracy_bridge():
    r=falsify_pair_family(4)
    # Conflict graph is line graph L(K4), 4-regular, hence degeneracy 4.
    assert r["shared_vertices"]==6
    assert r["degeneracy"]==4
    assert r["bridge_holds"] is False


def test_n3_pair_family_is_boundary_counterexample_too():
    r=falsify_pair_family(3)
    # L(K3)=K3 has degeneracy 2 < 3, so n=3 still satisfies the bridge.
    assert r["degeneracy"]==2
    assert r["bridge_holds"] is True


def test_n5_pair_family_is_even_stronger_failure():
    r=falsify_pair_family(5)
    # L(K5) is 6-regular.
    assert r["degeneracy"]==6
    assert r["bridge_holds"] is False
