from mapeogeo.erdos19_exhaustion_cert_v7 import canonical_isomorph,quotient_by_isomorphism,replay_exhaustion


def test_isomorphic_linear_spaces_canonicalize_identically():
    a=({0,1},{0,2},{1,2})
    b=({1,2},{1,0},{2,0})
    assert canonical_isomorph(3,a)==canonical_isomorph(3,b)


def test_symmetry_quotient_and_replay_cover_raw_class():
    raw=[
      ({0,1},{0,2},{1,2}),
      ({0,2},{0,1},{2,1}),
      ({0,1,2},),
    ]
    reps,buckets=quotient_by_isomorphism(3,raw)
    assert len(reps)==2
    replay=replay_exhaustion(3,raw,reps)
    assert replay.raw_count==3
    assert replay.representative_count==2
    assert replay.all_raw_covered
    assert len(replay.manifest_digest)==64


def test_missing_representative_breaks_coverage():
    raw=[({0,1},{0,2},{1,2}),({0,1,2},)]
    reps,_=quotient_by_isomorphism(3,raw)
    replay=replay_exhaustion(3,raw,reps[:1])
    assert not replay.all_raw_covered
