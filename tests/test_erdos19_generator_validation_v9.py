from mapeogeo.erdos19_generator_validation_v9 import canonical_generation,brute_force_exact_covers,complete_pair_cover


def test_canonical_generator_matches_independent_bruteforce_n4():
    gen=canonical_generation(4)
    brute,labeled=brute_force_exact_covers(4)
    assert labeled>0
    assert set(gen)==set(brute)
    assert all(complete_pair_cover(4,x) for x in gen.values())


def test_canonical_generator_has_no_extra_or_missing_classes_n3():
    gen=canonical_generation(3)
    brute,_=brute_force_exact_covers(3)
    assert set(gen)==set(brute)
