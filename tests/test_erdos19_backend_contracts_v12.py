from mapeogeo.erdos19_backend_contracts_v12 import CanonicalResult,ColoringResult,accept_canonical,accept_coloring
def test_canonical_requires_verified_digest():
    assert accept_canonical(CanonicalResult("a"*64,"test",None,True))
    assert not accept_canonical(CanonicalResult("a"*64,"test",None,False))
def test_sat_requires_coloring():
    assert accept_coloring(ColoringResult("SAT",(0,1),"solver",None,True))
    assert not accept_coloring(ColoringResult("SAT",None,"solver",None,True))
def test_unsat_requires_proof():
    assert accept_coloring(ColoringResult("UNSAT",None,"solver","proof.drat",True))
    assert not accept_coloring(ColoringResult("UNSAT",None,"solver",None,True))
