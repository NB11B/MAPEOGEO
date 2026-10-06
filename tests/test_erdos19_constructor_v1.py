from mapeogeo.erdos19_constructor import EFLInstance,shared_vertices,synthesize_shared_coloring,valid_shared_coloring


def test_triangle_of_cliques_constructor():
    # n=3, each pair of cliques shares one distinct vertex.
    inst=EFLInstance(3,(
        frozenset({"ab","ac","a"}),
        frozenset({"ab","bc","b"}),
        frozenset({"ac","bc","c"}),
    ))
    col=synthesize_shared_coloring(inst)
    assert col is not None
    assert valid_shared_coloring(inst,col)
    assert set(shared_vertices(inst))=={"ab","ac","bc"}


def test_all_cliques_share_one_vertex():
    inst=EFLInstance(4,(
        frozenset({"x","a1","a2","a3"}),
        frozenset({"x","b1","b2","b3"}),
        frozenset({"x","c1","c2","c3"}),
        frozenset({"x","d1","d2","d3"}),
    ))
    col=synthesize_shared_coloring(inst)
    assert col is not None and valid_shared_coloring(inst,col)
    assert col=={"x":0}


def test_invalid_efl_intersection_rejected():
    try:
        EFLInstance(3,(
            frozenset({"x","y","a"}),
            frozenset({"x","y","b"}),
            frozenset({"c","d","e"}),
        ))
    except ValueError:
        pass
    else:
        raise AssertionError("pairwise intersection >1 must fail")


def test_constructor_api_never_returns_unverified_coloring():
    instances=[
      EFLInstance(2,(frozenset({"x","a"}),frozenset({"x","b"}))),
      EFLInstance(3,(frozenset({"ab","ac","a"}),frozenset({"ab","bc","b"}),frozenset({"ac","bc","c"}))),
    ]
    for inst in instances:
        c=synthesize_shared_coloring(inst)
        assert c is None or valid_shared_coloring(inst,c)
