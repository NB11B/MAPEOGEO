from mapeogeo.erdos19_canonical_augmentation_v8 import incidence_refinement,canonical_augmentation_status


def test_relabelings_have_same_refinement_digest():
    a=({0,1},{0,2},{1,2})
    b=({1,2},{1,0},{2,0})
    assert incidence_refinement(3,a).digest==incidence_refinement(3,b).digest


def test_distinct_line_size_profiles_do_not_collide():
    a=({0,1},{0,2},{1,2})
    b=({0,1,2},)
    assert incidence_refinement(3,a).digest!=incidence_refinement(3,b).digest


def test_symmetric_triangle_fails_closed_as_ambiguous():
    s=incidence_refinement(3,({0,1},{0,2},{1,2}))
    assert s.ambiguous
    assert canonical_augmentation_status(3,(),({0,1},{0,2},{1,2}))=="NEEDS_CANONICAL_BACKEND"


def test_asymmetric_structure_can_refine_uniquely_when_available():
    # We do not require uniqueness; if refinement remains ambiguous it must say so.
    child=({0,1,2},{0,3},{1,4},{2,5})
    status=canonical_augmentation_status(6,(),child)
    assert status in {"REFINEMENT_UNIQUE","NEEDS_CANONICAL_BACKEND"}
